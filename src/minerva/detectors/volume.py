"""Excavated volume by elevation differencing.

This is the closest open analogue to the drone-volumetrics products operators
buy (Propeller, Strayos, and the survey modules of the major suites). Those
products are better: centimetric, flown on demand, tied to ground control. This
one is free, global, retrospective to the early 2010s, and available whether or
not the operator cooperates — which for a regulator is a different and
sometimes more valuable property.

Inputs, all public:
  * Copernicus DEM GLO-30 — 30 m global, absolute vertical accuracy < 4 m
    (90% linear error), relative < 2 m on slopes up to 20%. Free worldwide.
  * NASADEM / SRTM (2000) — a pre-boom baseline for sites that predate GLO-30.
  * TanDEM-X 90 m, ALOS World 3D 30 m — independent cross-checks.
  * Photogrammetric DSMs from stereo optical imagery, where a national mapping
    agency already produces them.

The output is deliberately an interval, not a number. A 4 m vertical error over
a 40 ha pit is ±1.6 million m³, which is larger than many years of production.
Any deployment that reports a single volume figure without its interval is
setting up its own findings to be destroyed on contest.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional, Tuple

import numpy as np

from ..geom import Grid
from ..version import ALGORITHM_VERSIONS
from .base import Observation

DETECTOR = "volume.dem_difference"


@dataclass
class VolumeParams:
    vertical_sigma_m: float = 2.0       # 1-sigma *random* vertical error of the pair
    bias_sigma_m: float = 0.5           # 1-sigma residual *systematic* offset
    correlation_length_cells: float = 10.0
    bulk_density_t_m3: float = 2.6      # typical for iron formation / hard rock waste
    swell_factor: float = 1.0           # set >1 if comparing to loose-measure tonnes
    min_change_m: float = 1.0           # ignore differences inside the noise floor

    def to_dict(self) -> dict:
        return dict(self.__dict__)


def difference(
    site_id: str,
    grid: Grid,
    dem_before: np.ndarray,
    dem_after: np.ndarray,
    when: date,
    mask: Optional[np.ndarray] = None,
    params: VolumeParams | None = None,
) -> Observation:
    """Cut and fill between two elevation surfaces."""
    p = params or VolumeParams()
    if dem_before.shape != dem_after.shape:
        raise ValueError("DEMs must share a grid")

    diff = dem_after.astype(float) - dem_before.astype(float)
    if mask is not None:
        diff = np.where(mask, diff, 0.0)
    diff = np.where(np.abs(diff) >= p.min_change_m, diff, 0.0)

    cell_m2 = _cell_areas_m2(grid)
    cut_m3 = float(-(np.where(diff < 0, diff, 0.0) * cell_m2).sum())
    fill_m3 = float((np.where(diff > 0, diff, 0.0) * cell_m2).sum())
    net_m3 = cut_m3 - fill_m3

    n_cells = int((np.abs(diff) > 0).sum())
    mean_cell_m2 = float(cell_m2.mean())
    changed_area_m2 = mean_cell_m2 * n_cells

    # Two error terms, and the second is the one people forget.
    #
    # Random: DEM errors are spatially correlated, so the naive sqrt(n)
    # reduction is far too generous. With a correlation length of L cells the
    # standard deviation of the summed volume is A·sigma·L·sqrt(n), not
    # A·sigma·sqrt(n).
    #
    # Systematic: any residual vertical offset between the two surfaces
    # multiplies by the *whole* changed area, and for a large pit it dominates
    # everything else. It is reduced by co-registering the DEMs on stable
    # ground outside the workings, which every deployment must do and must
    # record having done.
    L = max(p.correlation_length_cells, 1.0)
    sigma_random = p.vertical_sigma_m * mean_cell_m2 * L * np.sqrt(max(n_cells, 1))
    sigma_bias = p.bias_sigma_m * changed_area_m2
    sigma_m3 = float(np.hypot(sigma_random, sigma_bias))

    tonnes = net_m3 * p.bulk_density_t_m3 / max(p.swell_factor, 1e-9)
    tonnes_sigma = sigma_m3 * p.bulk_density_t_m3 / max(p.swell_factor, 1e-9)

    return Observation(
        site_id=site_id,
        acquired=when,
        detector=DETECTOR,
        algorithm_version=ALGORITHM_VERSIONS[DETECTOR],
        quantity="net_excavated_volume",
        value=net_m3,
        units="m3",
        valid_fraction=1.0 if mask is None else float(mask.mean()),
        reliability="ok" if abs(net_m3) > 2 * sigma_m3 else "degraded",
        params=p.to_dict(),
        detail={
            "cut_m3": round(cut_m3, 1),
            "fill_m3": round(fill_m3, 1),
            "net_m3": round(net_m3, 1),
            "sigma_m3": round(float(sigma_m3), 1),
            "net_m3_interval_95": [round(net_m3 - 1.96 * sigma_m3, 1),
                                   round(net_m3 + 1.96 * sigma_m3, 1)],
            "implied_tonnes": round(tonnes, 1),
            "implied_tonnes_interval_95": [round(tonnes - 1.96 * tonnes_sigma, 1),
                                           round(tonnes + 1.96 * tonnes_sigma, 1)],
            "cells_changed": n_cells,
            "sigma_random_m3": round(float(sigma_random), 1),
            "sigma_systematic_m3": round(float(sigma_bias), 1),
            "error_model": (
                f"random term = sigma_z x cell_area x L x sqrt(n) with L="
                f"{L:g} cells of spatial correlation; systematic term = residual "
                f"vertical bias ({p.bias_sigma_m} m) x changed area "
                f"({changed_area_m2 / 10_000:.1f} ha), combined in quadrature. The "
                "systematic term normally dominates and is reduced only by "
                "co-registering the two surfaces on stable ground outside the "
                "workings; a deployment must record that this was done."
            ),
            "caveat": "Material moved, not material sold. Waste rock, overburden and "
                      "stockpile rehandling are all included. Use as an upper bound "
                      "on extraction, never as a production figure.",
        },
    )


def _cell_areas_m2(grid: Grid) -> np.ndarray:
    rows = np.arange(grid.height, dtype=float) + 0.5
    lat = grid.origin_lat - rows * grid.deg_per_pixel_lat
    import math
    scale = np.cos(np.radians(lat)) / max(math.cos(math.radians(grid.origin_lat)), 1e-9)
    return np.repeat((grid.pixel_m ** 2 * scale)[:, None], grid.width, axis=1)


def sanity_bounds(area_ha: float, mean_depth_m: float,
                  bulk_density_t_m3: float = 2.6) -> Tuple[float, float]:
    """A back-of-envelope tonnage range from footprint alone.

    Used to sanity-check a DEM difference, and to give an order-of-magnitude
    figure where no DEM pair is available. Returns (low, high) tonnes on a
    deliberately wide ±50% depth assumption, because that is the honest width
    of an estimate made from area alone.
    """
    v = area_ha * 10_000.0 * mean_depth_m
    return (v * 0.5 * bulk_density_t_m3, v * 1.5 * bulk_density_t_m3)
