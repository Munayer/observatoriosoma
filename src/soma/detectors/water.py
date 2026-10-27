"""Impounded water and turbidity.

Two distinct regulatory questions, deliberately separated:

  * **Pond extent.** How much water is impounded behind a tailings structure,
    and is that extent growing? A rising pond against a fixed crest is the
    freeboard problem — the mechanism in a large share of tailings failures —
    and it is observable from orbit without any cooperation from the operator.
  * **Turbidity.** Is the water downstream of a site more turbid than the water
    upstream, and more turbid than its own history? Turbidity is a proxy, never
    a contamination finding: it is the trigger for a sampling campaign, and the
    dossier says so in those words.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

try:
    from scipy import ndimage as _ndi
except Exception:  # pragma: no cover
    _ndi = None

from .. import indices
from ..scene import Scene
from ..version import ALGORITHM_VERSIONS
from .base import Observation, grade_reliability

DETECTOR = "water.pond_extent"


@dataclass
class WaterParams:
    mndwi_min: float = 0.10
    ndvi_max: float = 0.20
    min_pond_ha: float = 0.5
    ok_above: float = 0.85
    unusable_below: float = 0.40
    aoi_mask: Optional[np.ndarray] = None
    assessment_mask: Optional[np.ndarray] = None
    # A process pond differs from a forest stream by being turbid and bright.
    turbid_ndti_min: float = 0.03
    turbid_green_min: float = 0.055

    def to_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items()
             if k not in ("aoi_mask", "assessment_mask")}
        d["aoi_restricted"] = self.aoi_mask is not None
        d["assessment_area_restricted"] = self.assessment_mask is not None
        return d


def water_mask(scene: Scene, p: WaterParams) -> np.ndarray:
    m = (indices.mndwi(scene) > p.mndwi_min) & (indices.ndvi(scene) < p.ndvi_max) & scene.valid
    if p.aoi_mask is not None:
        m &= p.aoi_mask
    if _ndi is not None and m.any():
        m = _ndi.binary_opening(m, structure=np.ones((3, 3), dtype=bool))
        labels, n = _ndi.label(m)
        if n:
            min_px = max(int(round(p.min_pond_ha * 10_000 / scene.grid.pixel_m ** 2)), 1)
            counts = np.bincount(labels.ravel())
            keep = np.zeros(counts.shape, dtype=bool)
            keep[1:] = counts[1:] >= min_px
            m = keep[labels]
    return m


def detect_pond(scene: Scene, params: WaterParams | None = None) -> Observation:
    p = params or WaterParams()
    water = water_mask(scene, p)
    ndti = indices.ndti(scene)
    green = scene.band("B03")
    process = water & (ndti > p.turbid_ndti_min) & (green > p.turbid_green_min)

    area_ha = scene.grid.area_ha(water)
    process_ha = scene.grid.area_ha(process)
    judge_on = p.assessment_mask if p.assessment_mask is not None else p.aoi_mask
    observable = (float((scene.valid & judge_on).sum() / judge_on.sum())
                  if judge_on is not None and judge_on.any()
                  else scene.valid_fraction)

    return Observation(
        site_id=scene.site_id,
        acquired=scene.acquired,
        detector=DETECTOR,
        algorithm_version=ALGORITHM_VERSIONS[DETECTOR],
        quantity="impounded_water_area",
        value=area_ha,
        units="ha",
        valid_fraction=observable,
        reliability=grade_reliability(observable, degraded_below=p.ok_above,
                                      unusable_below=p.unusable_below),
        params=p.to_dict(),
        mask=water,
        detail={
            "process_water_ha": round(process_ha, 3),
            "natural_water_ha": round(max(area_ha - process_ha, 0.0), 3),
            "mean_ndti_over_water": float(np.nanmean(ndti[water])) if water.any() else None,
            "index_references": {k: indices.INDEX_REFERENCES[k] for k in ("mndwi", "ndti")},
            "caveat": "Turbidity is a screening proxy. It is not a determination of "
                      "contamination and must not be reported as one.",
        },
    )


def turbidity_gradient(
    scene: Scene,
    upstream: np.ndarray,
    downstream: np.ndarray,
    params: WaterParams | None = None,
) -> Observation:
    """Difference in turbidity index between two reaches of the same river.

    Using the river as its own control removes most of the atmospheric and
    illumination error that would otherwise dominate an absolute turbidity
    number, which is why this is expressed as a gradient and never as a
    concentration.
    """
    p = params or WaterParams()
    water = water_mask(scene, p)
    ndti = indices.ndti(scene)

    up = ndti[water & upstream]
    down = ndti[water & downstream]
    if up.size < 20 or down.size < 20:
        return Observation(
            site_id=scene.site_id, acquired=scene.acquired, detector="water.turbidity_gradient",
            algorithm_version=ALGORITHM_VERSIONS[DETECTOR], quantity="ndti_gradient",
            value=float("nan"), units="index", valid_fraction=scene.valid_fraction,
            reliability="unusable", params=p.to_dict(),
            detail={"reason": "insufficient water pixels in one or both reaches",
                    "upstream_px": int(up.size), "downstream_px": int(down.size)},
        )

    delta = float(np.median(down) - np.median(up))
    return Observation(
        site_id=scene.site_id,
        acquired=scene.acquired,
        detector="water.turbidity_gradient",
        algorithm_version=ALGORITHM_VERSIONS[DETECTOR],
        quantity="ndti_gradient",
        value=delta,
        units="index",
        valid_fraction=scene.valid_fraction,
        reliability=grade_reliability(scene.valid_fraction),
        params=p.to_dict(),
        detail={
            "upstream_median_ndti": float(np.median(up)),
            "downstream_median_ndti": float(np.median(down)),
            "upstream_px": int(up.size),
            "downstream_px": int(down.size),
            "caveat": "Screening proxy for suspended sediment. Trigger for sampling, "
                      "not a water-quality determination.",
        },
    )


def freeboard_proxy(
    pond_series: Tuple[Tuple[str, float], ...],
    crest_area_ha: float,
) -> dict:
    """Pond area as a share of the impoundment's maximum footprint.

    A crude but genuinely useful indicator: when the water surface approaches
    the full extent of the impoundment, freeboard is being consumed. It cannot
    replace the operator's instrumented crest survey, and the dossier says so.
    """
    if crest_area_ha <= 0:
        return {"available": False}
    ratios = [(d, a / crest_area_ha) for d, a in pond_series]
    last_d, last_r = ratios[-1]
    peak_d, peak_r = max(ratios, key=lambda t: t[1])
    return {
        "available": True,
        "latest_date": last_d,
        "latest_fill_ratio": round(last_r, 3),
        "peak_date": peak_d,
        "peak_fill_ratio": round(peak_r, 3),
        "interpretation": (
            "fill ratio above 0.90 indicates the water surface is approaching the "
            "impoundment's mapped extent; verify against the operator's declared "
            "freeboard and the structure's emergency level"
        ),
    }
