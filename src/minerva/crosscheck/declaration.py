"""Comparing what is observed with what is declared.

This is the module that mirrors metallurgical accounting — the INVENTEO /
AMIRA P754 layer of the operator's stack — from outside the fence.

The temptation is to convert a satellite footprint into a tonnage and compare
it with the tonnage on which royalties were paid. **Do not do that as a
finding.** The conversion needs stripping ratio, ore grade, moisture, waste
handling and stockpile movement, none of which are public, and a regulator who
serves a demand built on that chain will lose. It has been tried and it does
not survive contest.

What survives is *relative* reasoning:

  * **Intensity.** Declared production per hectare of active footprint, for
    this site, benchmarked against the distribution of the same ratio across
    peer sites — same commodity, same method, same region. An operator whose
    intensity sits in the bottom decile while its footprint growth sits in the
    top decile is not necessarily under-declaring; it is necessarily *worth
    auditing*, and that is a defensible thing for a screening system to say.
  * **Internal consistency.** Declared production against the operator's own
    history, against its own reported reserves depletion, and against the
    company-level figures it files under securities and payments-to-governments
    regimes (EU Accounting Directive Chapter 10, Canada's ESTMA, EITI country
    reports). Discrepancies between an operator's own filings are the strongest
    signal available and require no remote sensing at all.
  * **Non-payment against observed activity.** The clean case: a site that is
    visibly and materially active across a reporting period for which no
    royalty was declared at all. No conversion factor is needed to state that.

The output is a *screening score with reasons*, routed to an auditor. It is
never an assessment.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Sequence

from ..version import ALGORITHM_VERSIONS


@dataclass
class Declaration:
    """What the operator told the state, for one site and one period."""

    site_id: str
    title_id: str
    period_start: date
    period_end: date
    substance: str
    declared_tonnes: Optional[float] = None
    royalty_paid: Optional[float] = None
    currency: str = ""
    source: str = ""                  # e.g. "ANM CFEM open data, extract 2026-08-01"
    filing_reference: str = ""

    @property
    def months(self) -> float:
        return max((self.period_end - self.period_start).days, 1) / 30.4375


@dataclass
class PeerStat:
    """The benchmark distribution this site is scored against."""

    substance: str
    method: str
    region: str
    n: int
    intensity_deciles: List[float] = field(default_factory=list)  # t / active ha / month

    def decile_of(self, value: float) -> int:
        for i, cut in enumerate(self.intensity_deciles, start=1):
            if value <= cut:
                return i
        return 10


@dataclass
class ReconciliationResult:
    site_id: str
    period: str
    observed_active_ha: float
    observed_growth_ha_per_month: float
    declared_tonnes: Optional[float]
    intensity_t_per_ha_month: Optional[float]
    intensity_decile: Optional[int]
    flags: List[str]
    reasons: List[str]
    score: float
    peer_basis: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "site_id": self.site_id,
            "period": self.period,
            "observed_active_ha": round(self.observed_active_ha, 2),
            "observed_growth_ha_per_month": round(self.observed_growth_ha_per_month, 3),
            "declared_tonnes": self.declared_tonnes,
            "intensity_t_per_ha_month": None if self.intensity_t_per_ha_month is None
            else round(self.intensity_t_per_ha_month, 2),
            "intensity_decile": self.intensity_decile,
            "peer_basis": self.peer_basis,
            "flags": self.flags,
            "reasons": self.reasons,
            "audit_priority_score": round(self.score, 3),
            "algorithm_version": ALGORITHM_VERSIONS["crosscheck.declaration"],
            "status": "SCREENING RESULT — audit prioritisation only. Not an assessment "
                      "of tax or royalty owed, and not evidence of under-declaration.",
        }


def reconcile(
    site_id: str,
    period: str,
    observed_active_ha: float,
    observed_growth_ha_per_month: float,
    declaration: Optional[Declaration],
    peers: Optional[PeerStat] = None,
    growth_percentile: Optional[float] = None,
) -> ReconciliationResult:
    flags: List[str] = []
    reasons: List[str] = []
    score = 0.0

    if declaration is None or declaration.declared_tonnes in (None, 0):
        if observed_active_ha >= 5.0:
            flags.append("activity_without_declaration")
            reasons.append(
                f"{observed_active_ha:.1f} ha of active disturbed surface observed in "
                f"{period}, with no production declared for the period in the "
                "extract used."
            )
            score += 0.55
        intensity = None
        decile = None
    else:
        months = declaration.months
        intensity = declaration.declared_tonnes / max(observed_active_ha, 0.01) / max(months, 0.01)
        decile = peers.decile_of(intensity) if peers and peers.intensity_deciles else None
        if decile is not None and decile <= 2:
            flags.append("low_declared_intensity_vs_peers")
            reasons.append(
                f"Declared production of {declaration.declared_tonnes:,.0f} t over "
                f"{observed_active_ha:.1f} active ha is {intensity:,.1f} t/ha/month, in "
                f"decile {decile} of {peers.n} comparable {peers.substance} operations "
                f"in {peers.region}."
            )
            score += 0.30

    if growth_percentile is not None and growth_percentile >= 0.9:
        flags.append("footprint_growth_top_decile")
        reasons.append(
            f"Footprint growth of {observed_growth_ha_per_month:.2f} ha/month is in the "
            f"top decile for comparable operations."
        )
        score += 0.25

    if "low_declared_intensity_vs_peers" in flags and "footprint_growth_top_decile" in flags:
        flags.append("divergence_growth_vs_declaration")
        reasons.append(
            "The site is expanding quickly while declaring little per unit of worked "
            "area. This combination is the specific pattern an audit should resolve; it "
            "has innocent explanations (waste stripping ahead of ore, stockpile build, "
            "pre-production development) and the audit exists to test them."
        )
        score += 0.20

    return ReconciliationResult(
        site_id=site_id,
        period=period,
        observed_active_ha=observed_active_ha,
        observed_growth_ha_per_month=observed_growth_ha_per_month,
        declared_tonnes=None if declaration is None else declaration.declared_tonnes,
        intensity_t_per_ha_month=intensity,
        intensity_decile=decile,
        flags=flags,
        reasons=reasons,
        score=min(score, 1.0),
        peer_basis=None if peers is None else
        f"{peers.n} {peers.substance} operations, {peers.method}, {peers.region}",
    )


def build_peer_stat(
    substance: str,
    method: str,
    region: str,
    intensities: Sequence[float],
) -> PeerStat:
    xs = sorted(x for x in intensities if x is not None and x > 0)
    if len(xs) < 10:
        return PeerStat(substance, method, region, len(xs), [])
    cuts = [statistics.quantiles(xs, n=10)[i] for i in range(9)]
    return PeerStat(substance, method, region, len(xs), cuts)


def cross_filing_check(filings: Dict[str, float], tolerance: float = 0.05) -> List[str]:
    """Compare the same quantity as reported to different regimes.

    ``filings`` maps a regime label to a figure for the same site and period —
    for example {"CFEM declaration": 812_000, "annual report": 905_000,
    "EU Ch.10 payments to governments": 799_000}. Discrepancies beyond
    ``tolerance`` are listed. This requires no remote sensing whatsoever and is
    frequently the most productive check available.
    """
    out: List[str] = []
    if len(filings) < 2:
        return out
    vals = list(filings.values())
    base = statistics.median(vals)
    for label, v in filings.items():
        if base > 0 and abs(v - base) / base > tolerance:
            out.append(
                f"{label} reports {v:,.0f} against a median of {base:,.0f} across "
                f"{len(filings)} filings — a {abs(v - base) / base * 100:.1f}% divergence."
            )
    return out
