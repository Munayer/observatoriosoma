"""Ground movement over a tailings structure.

This is the module that mirrors the operator's instrumented geotechnical
monitoring — the inclinometers, piezometers and prisms behind products like
Rocscience and the GEOVIA/Deswik geotechnical suites — with the one signal a
regulator can obtain without the operator's cooperation: satellite radar
interferometry.

Two input paths, both public:

  * **European Ground Motion Service (EGMS).** Sentinel-1 InSAR, millimetre
    accuracy, Europe-wide, updated annually, downloadable per tile. Point
    measurements with a velocity and a displacement time series. For a European
    deployment this needs no processing at all — it is a table.
    https://egms.land.copernicus.eu/
  * **Self-processed Sentinel-1.** Outside Europe, or where annual EGMS
    cadence is too slow, the same product can be built with the open stack:
    ISCE2 or ESA SNAP for interferograms, MintPy or LiCSBAS for the time
    series. Slower and heavier, but wholly open and wholly reproducible.

What this module does *not* do: predict failure. Displacement is a hazard
indicator, and the honest output of a satellite screen is "this structure's
crest is moving faster than it was, and faster than its neighbours — send an
engineer". Anything stronger would be a technical claim the data does not
support and a legal exposure nobody should take on.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from ..version import ALGORITHM_VERSIONS
from .base import Observation

DETECTOR = "deformation.velocity_screen"


@dataclass
class DeformationSeries:
    """One persistent-scatterer point: a velocity and a displacement history."""

    point_id: str
    lon: float
    lat: float
    dates: List[date]
    displacement_mm: List[float]     # cumulative, line-of-sight, relative to t0
    velocity_mm_yr: Optional[float] = None
    coherence: float = 1.0
    metadata: Dict = field(default_factory=dict)

    def fitted_velocity(self, window_days: Optional[int] = None) -> float:
        """Linear velocity, optionally over the most recent window only.

        The whole-history velocity is the wrong number for a decision. A crest
        that crept at 2 mm/yr for four years and 30 mm/yr for the last six
        months has a whole-history velocity of about 6 mm/yr, which is
        reassuring and wrong. Screening uses the recent window; the
        whole-history figure is reported beside it for context.
        """
        if window_days is None and self.velocity_mm_yr is not None:
            return self.velocity_mm_yr
        t = np.array([d.toordinal() for d in self.dates], dtype=float)
        y = np.array(self.displacement_mm, dtype=float)
        if window_days is not None:
            keep = t >= (t[-1] - window_days)
            if keep.sum() >= 3:
                t, y = t[keep], y[keep]
        A = np.vstack([(t - t[0]) / 365.25, np.ones_like(t)]).T
        return float(np.linalg.lstsq(A, y, rcond=None)[0][0])

    def acceleration_mm_yr2(self) -> float:
        """Quadratic term ×2 — the sign that matters most in creep."""
        t = np.array([d.toordinal() for d in self.dates], dtype=float)
        if len(t) < 4:
            return 0.0
        x = (t - t[0]) / 365.25
        y = np.array(self.displacement_mm, dtype=float)
        coef = np.polyfit(x, y, 2)
        return float(2.0 * coef[0])


@dataclass
class DeformationParams:
    velocity_alert_mm_yr: float = -10.0    # subsidence is negative in LOS convention
    acceleration_alert_mm_yr2: float = -6.0
    min_coherence: float = 0.55
    min_points_in_cluster: int = 5
    recent_window_days: int = 365          # the window the threshold is applied to

    def to_dict(self) -> dict:
        return dict(self.__dict__)


def screen(
    site_id: str,
    series: Sequence[DeformationSeries],
    structure_name: str,
    params: DeformationParams | None = None,
) -> Observation:
    """Flag a structure whose crest points are moving, or accelerating."""
    p = params or DeformationParams()
    kept = [s for s in series if s.coherence >= p.min_coherence]
    if len(kept) < p.min_points_in_cluster:
        return Observation(
            site_id=site_id,
            acquired=max((s.dates[-1] for s in series), default=date.today()),
            detector=DETECTOR,
            algorithm_version=ALGORITHM_VERSIONS[DETECTOR],
            quantity="crest_velocity",
            value=float("nan"),
            units="mm/yr",
            valid_fraction=0.0,
            reliability="unusable",
            params=p.to_dict(),
            detail={
                "structure": structure_name,
                "reason": "too few coherent scatterers over the structure",
                "points_available": len(series),
                "points_coherent": len(kept),
                "recommendation": "vegetated or freshly reworked crests decorrelate; "
                                  "use corner reflectors or an alternative technique",
            },
        )

    v_all = np.array([s.fitted_velocity() for s in kept])
    v_recent = np.array([s.fitted_velocity(window_days=p.recent_window_days)
                         for s in kept])
    accelerations = np.array([s.acceleration_mm_yr2() for s in kept])
    v_med = float(np.median(v_recent))
    v_hist = float(np.median(v_all))
    v_p10 = float(np.percentile(v_recent, 10))
    a_med = float(np.median(accelerations))

    flags = []
    if v_p10 <= p.velocity_alert_mm_yr:
        flags.append("velocity_exceeds_threshold")
    if a_med <= p.acceleration_alert_mm_yr2:
        flags.append("accelerating")
    if v_hist != 0 and v_med / v_hist >= 2.0 and v_med < 0:
        flags.append("recent_velocity_at_least_double_historic")

    last = max(s.dates[-1] for s in kept)
    return Observation(
        site_id=site_id,
        acquired=last,
        detector=DETECTOR,
        algorithm_version=ALGORITHM_VERSIONS[DETECTOR],
        quantity="crest_velocity",
        value=v_med,
        units="mm/yr",
        valid_fraction=float(len(kept) / max(len(series), 1)),
        reliability="ok" if len(kept) >= 2 * p.min_points_in_cluster else "degraded",
        params=p.to_dict(),
        detail={
            "structure": structure_name,
            "points_used": len(kept),
            "median_velocity_recent_mm_yr": round(v_med, 2),
            "median_velocity_whole_history_mm_yr": round(v_hist, 2),
            "p10_velocity_recent_mm_yr": round(v_p10, 2),
            "median_acceleration_mm_yr2": round(a_med, 2),
            "flags": flags,
            "caveat": "Line-of-sight displacement from InSAR. Not a stability "
                      "assessment and not a failure prediction. Indicates that an "
                      "engineering inspection is warranted.",
            "method_note": "EGMS Level-2b/3 points, or Sentinel-1 SBAS processed with "
                           "ISCE2/SNAP and MintPy or LiCSBAS.",
        },
    )


# --------------------------------------------------------------------------
# Simulation, for tests and demonstrations
# --------------------------------------------------------------------------

def simulate_crest(
    n_points: int = 24,
    start: date = date(2023, 1, 1),
    months: int = 42,
    creep_mm_yr: float = -3.5,
    accelerate_from_month: Optional[int] = 26,
    acceleration_mm_yr2: float = -13.0,
    seed: int = 7,
    lon: float = -56.126,
    lat: float = -6.457,
) -> List[DeformationSeries]:
    """Points on a dam crest with slow creep that later accelerates."""
    rng = np.random.default_rng(seed)
    out: List[DeformationSeries] = []
    dates = []
    y, m = start.year, start.month
    for _ in range(months):
        dates.append(date(y, m, 12))
        m += 1
        if m > 12:
            m, y = 1, y + 1

    for i in range(n_points):
        base_rate = creep_mm_yr * rng.uniform(0.7, 1.3)
        noise = rng.normal(0.0, 1.4, size=months)
        disp = []
        cum = 0.0
        for k, _d in enumerate(dates):
            rate = base_rate
            if accelerate_from_month is not None and k >= accelerate_from_month:
                extra = acceleration_mm_yr2 * ((k - accelerate_from_month) / 12.0)
                rate = base_rate + extra
            cum += rate / 12.0
            disp.append(cum + noise[k])
        out.append(
            DeformationSeries(
                point_id=f"PS-{i:03d}",
                lon=lon + rng.normal(0, 0.0006),
                lat=lat + rng.normal(0, 0.0004),
                dates=list(dates),
                displacement_mm=disp,
                coherence=float(rng.uniform(0.5, 0.95)),
                metadata={"simulated": True},
            )
        )
    return out


def series_to_table(series: Sequence[DeformationSeries]) -> Tuple[List[str], List[List[float]]]:
    """Dates and a matrix of displacements, for plotting and for the table view."""
    dates = [d.isoformat() for d in series[0].dates]
    rows = [s.displacement_mm for s in series]
    return dates, rows
