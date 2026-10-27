"""Turning a series of areas into a statement about change.

The measurement that matters to a regulator is almost never the footprint on
one date. It is the *rate*, and the date the rate changed. A site that grew
4 ha/year for a decade and 4 ha/month since October is telling you something
that no single image tells you.

Three things are computed, and the third is the one that ends up in the notice:

  * a robust trend (Theil–Sen), because a single mis-segmented cloudy month
    should not move the answer;
  * a single-breakpoint fit, giving the date the growth rate changed and the
    magnitude of the change;
  * the observed delta between two dates that were actually well observed,
    which is the claim with the fewest assumptions behind it and therefore the
    one that survives contest.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Sequence, Tuple

import numpy as np

from ..version import ALGORITHM_VERSIONS
from .base import Observation

DETECTOR = "change.robust_trend"
DAYS_PER_MONTH = 30.4375


@dataclass
class TrendResult:
    n_used: int
    n_rejected: int
    first: Tuple[date, float]
    last: Tuple[date, float]
    delta: float
    delta_pct: Optional[float]
    slope_per_month: float
    slope_lo: float
    slope_hi: float
    breakpoint: Optional[date]
    slope_before: Optional[float]
    slope_after: Optional[float]
    breakpoint_improvement: Optional[float]

    @property
    def current_rate_per_month(self) -> float:
        """The rate that is running *now*.

        When the series has a regime change, the whole-period slope is a blend
        of two rates and describes neither. A regulator deciding whether to
        send someone this month needs the current one, with the historic one
        beside it for context.
        """
        if self.breakpoint is not None and self.slope_after is not None:
            return self.slope_after
        return self.slope_per_month

    def to_dict(self) -> dict:
        return {
            "observations_used": self.n_used,
            "observations_excluded_cloud_limited": self.n_rejected,
            "first": {"date": self.first[0].isoformat(), "value": round(self.first[1], 3)},
            "last": {"date": self.last[0].isoformat(), "value": round(self.last[1], 3)},
            "delta": round(self.delta, 3),
            "delta_pct": None if self.delta_pct is None else round(self.delta_pct, 2),
            "slope_per_month": round(self.slope_per_month, 4),
            "current_rate_per_month": round(self.current_rate_per_month, 4),
            "slope_ci68": [round(self.slope_lo, 4), round(self.slope_hi, 4)],
            "breakpoint": None if self.breakpoint is None else self.breakpoint.isoformat(),
            "slope_before_breakpoint": None if self.slope_before is None else round(self.slope_before, 4),
            "slope_after_breakpoint": None if self.slope_after is None else round(self.slope_after, 4),
            "breakpoint_rss_improvement": None if self.breakpoint_improvement is None
            else round(self.breakpoint_improvement, 3),
        }


def analyse(
    observations: Sequence[Observation],
    include_degraded: bool = False,
    min_segment: int = 5,
) -> Tuple[TrendResult, Observation]:
    """Fit a trend to a series of same-quantity observations."""
    usable = [o for o in observations
              if o.reliability == "ok" or (include_degraded and o.reliability == "degraded")]
    usable.sort(key=lambda o: o.acquired)
    rejected = len(observations) - len(usable)
    if len(usable) < 3:
        raise ValueError(
            f"only {len(usable)} usable observations; a trend needs at least 3. "
            "Report the observation gap instead of a trend — an unobservable site "
            "is a finding in itself."
        )

    t = np.array([o.acquired.toordinal() for o in usable], dtype=float)
    y = np.array([o.value for o in usable], dtype=float)
    tm = (t - t[0]) / DAYS_PER_MONTH

    slope, lo, hi = theil_sen(tm, y)
    bp = _best_breakpoint(tm, y, min_segment=min_segment)

    first = (usable[0].acquired, float(y[0]))
    last = (usable[-1].acquired, float(y[-1]))
    delta = last[1] - first[1]
    delta_pct = (delta / first[1] * 100.0) if first[1] > 1e-9 else None

    result = TrendResult(
        n_used=len(usable),
        n_rejected=rejected,
        first=first,
        last=last,
        delta=delta,
        delta_pct=delta_pct,
        slope_per_month=slope,
        slope_lo=lo,
        slope_hi=hi,
        breakpoint=None if bp is None else usable[bp["index"]].acquired,
        slope_before=None if bp is None else bp["slope_before"],
        slope_after=None if bp is None else bp["slope_after"],
        breakpoint_improvement=None if bp is None else bp["improvement"],
    )

    proto = usable[-1]
    obs = Observation(
        site_id=proto.site_id,
        acquired=proto.acquired,
        detector=DETECTOR,
        algorithm_version=ALGORITHM_VERSIONS[DETECTOR],
        quantity=f"{proto.quantity}_growth_rate",
        value=slope,
        units=f"{proto.units}/month",
        valid_fraction=float(np.mean([o.valid_fraction for o in usable])),
        reliability="ok" if len(usable) >= 6 else "degraded",
        params={"include_degraded": include_degraded, "min_segment": min_segment,
                "estimator": "Theil-Sen median slope; 68% interval from the "
                             "16th/84th percentile of pairwise slopes"},
        detail=result.to_dict(),
    )
    return result, obs


def theil_sen(x: np.ndarray, y: np.ndarray) -> Tuple[float, float, float]:
    """Median of pairwise slopes, with a percentile interval.

    Breakdown point 29%: up to nearly a third of the series can be badly wrong
    before the estimate is. Ordinary least squares has a breakdown point of
    zero, which is the wrong property for a series built from cloud-screened
    satellite composites.
    """
    n = len(x)
    slopes = []
    for i in range(n - 1):
        dx = x[i + 1:] - x[i]
        dy = y[i + 1:] - y[i]
        ok = np.abs(dx) > 1e-9
        slopes.append(dy[ok] / dx[ok])
    s = np.concatenate(slopes) if slopes else np.array([0.0])
    return float(np.median(s)), float(np.percentile(s, 16)), float(np.percentile(s, 84))


def _best_breakpoint(x: np.ndarray, y: np.ndarray, min_segment: int = 5,
                    min_improvement: float = 0.25,
                    min_segment_months: float = 5.0) -> Optional[dict]:
    """Exhaustive single-breakpoint search.

    Three guards, each of which exists because without it the fit reports a
    regime change that is not there:

      * a minimum of ``min_segment`` observations on each side, so a couple of
        noisy months at the end of the record cannot invent an acceleration;
      * a minimum time span on each side, because five observations crammed
        into one dry season are not a regime;
      * a residual-sum-of-squares improvement of at least ``min_improvement``
        over the single-line fit, because every breakpoint improves the fit
        somewhat and only a large improvement is a finding.

    Segment slopes are estimated with Theil-Sen rather than least squares, for
    the same reason the headline trend is: one mis-segmented month must not
    move the number that goes into a notice.
    """
    n = len(x)
    if n < 2 * min_segment:
        return None
    rss_single = _rss(x, y)
    best = None
    for k in range(min_segment, n - min_segment + 1):
        if (x[k - 1] - x[0]) < min_segment_months:
            continue
        if (x[-1] - x[k]) < min_segment_months:
            continue
        rss = _rss(x[:k], y[:k]) + _rss(x[k:], y[k:])
        if best is None or rss < best[1]:
            best = (k, rss)
    if best is None or rss_single <= 0:
        return None
    k, rss = best
    improvement = (rss_single - rss) / rss_single
    if improvement < min_improvement:
        return None

    b_slope, b_lo, b_hi = theil_sen(x[:k], y[:k])
    a_slope, a_lo, a_hi = theil_sen(x[k:], y[k:])

    # Final guard, and the one that does the most work: the two segment slopes
    # must be *separated*. If the 68% intervals of the pairwise-slope
    # distributions overlap, the two segments are consistent with a single rate
    # and the apparent regime change is the noise in a short, cloud-thinned
    # series. Without this, a quiet compliant site reports a "rate change"
    # every time its first few months wobble — and a regulator who is told
    # about a rate change that is not there stops believing the ones that are.
    separated = (b_hi < a_lo) or (a_hi < b_lo)
    if not separated:
        return None

    return {
        "index": k,
        "improvement": improvement * 100.0,
        "slope_before": b_slope,
        "slope_after": a_slope,
        "slope_before_ci68": [b_lo, b_hi],
        "slope_after_ci68": [a_lo, a_hi],
    }


def _slope(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) < 2:
        return 0.0
    A = np.vstack([x, np.ones_like(x)]).T
    return float(np.linalg.lstsq(A, y, rcond=None)[0][0])


def _rss(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) < 2:
        return 0.0
    A = np.vstack([x, np.ones_like(x)]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    resid = y - A @ coef
    return float(np.sum(resid ** 2))


def observation_gaps(observations: Sequence[Observation],
                     max_gap_days: int = 75) -> List[dict]:
    """Periods during which the site could not be seen.

    Reported alongside every trend. A site with a four-month hole in the wet
    season has a four-month hole in its enforcement record, and pretending
    otherwise is how monitoring programmes lose credibility the first time an
    operator points at the gap.
    """
    usable = sorted([o for o in observations if o.reliability != "unusable"],
                    key=lambda o: o.acquired)
    gaps = []
    for a, b in zip(usable[:-1], usable[1:]):
        days = (b.acquired - a.acquired).days
        if days > max_gap_days:
            gaps.append({"from": a.acquired.isoformat(), "to": b.acquired.isoformat(),
                         "days": days})
    return gaps
