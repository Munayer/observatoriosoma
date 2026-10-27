"""A small portfolio of sites, so the queue looks like a real working day.

One detection is a demo. What a regulator has to believe is that the system
produces a *queue they can work* — that it ranks, that it says why, that some
of what it raises turns out to be nothing, and that the nothing is disposed of
visibly rather than left hanging over an operator.

So the demo portfolio contains, deliberately:

  * a site where the finding is strong and the operator has answered in part;
  * a site being worked on nothing more than a pending application;
  * a site whose title is suspended but which is plainly active;
  * a site that is entirely compliant, which the system must be willing to say.

The fourth is the most important one for adoption. A screening system that
never clears anyone is a system nobody will let near their sector.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .cases import CaseRegister, CaseState, Response
from .crosscheck import cadastre as cad
from .crosscheck.declaration import Declaration
from .dossier import BRAZIL
from .geom import geodesic_area_ha
from .pipeline import RunResult, SiteConfig, run_site
from .providers.synthetic import SyntheticProvider, SyntheticSite

PEERS = [
    520, 610, 700, 760, 810, 880, 940, 1010, 1090, 1180,
    1260, 1350, 1470, 1590, 1720, 1880, 2060, 2300, 2610, 3100,
]


@dataclass
class SiteSpec:
    site: SyntheticSite
    title_id: str
    holder: str
    status: str
    phase: str
    substance: str
    tailings: str = ""
    deformation_profile: Optional[Dict[str, float]] = None
    declared_tonnes: Optional[float] = None
    other_filings: Dict[str, float] = None
    with_protected_area: bool = True
    start: date = date(2023, 1, 1)
    end: date = date(2026, 7, 1)
    narrative: str = ""


def specs() -> List[SiteSpec]:
    return [
        SiteSpec(
            site=SyntheticSite(site_id="BR-PA-0001", seed=20260819,
                               centre_lon=-56.12, centre_lat=-6.45),
            title_id="830.123/2018",
            holder="Mineradora Exemplo S.A. (simulated)",
            status="active", phase="lavra", substance="minério de ferro",
            tailings="Barragem B1 (simulated)",
            declared_tonnes=430_000,
            other_filings={"CFEM declaration": 430_000,
                           "company annual report": 512_000,
                           "EU Ch.10 payments to governments": 505_000},
            narrative=("Expansion accelerates sharply, then crosses the licence "
                       "boundary into a conservation unit. Declaration does not "
                       "keep pace. The holder has answered on part of it."),
        ),
        SiteSpec(
            site=SyntheticSite(site_id="BR-MT-0002", seed=515151,
                               centre_lon=-55.02, centre_lat=-10.11,
                               width=320, height=320,
                               licence_frac=(0.20, 0.22, 0.66, 0.72),
                               tailings_area_ha=6.0,
                               growth=(("2024-01-01", 4.0), ("2025-01-01", 14.0),
                                       ("2026-07-01", 41.0)),
                               breakout_date="2025-06-01"),
            title_id="906.774/2023",
            holder="Requerente pessoa física (simulated)",
            status="requested", phase="requerimento de pesquisa",
            substance="ouro",
            with_protected_area=True,
            start=date(2024, 1, 1),
            narrative=("Sustained extraction on nothing more than a pending "
                       "application. A requerimento authorises no works at all."),
        ),
        SiteSpec(
            site=SyntheticSite(site_id="BR-MG-0003", seed=778899,
                               centre_lon=-43.55, centre_lat=-20.31,
                               width=320, height=320,
                               licence_frac=(0.14, 0.16, 0.70, 0.74),
                               tailings_area_ha=11.0,
                               growth=(("2024-01-01", 22.0), ("2025-01-01", 26.0),
                                       ("2026-07-01", 33.0)),
                               breakout_date="2099-01-01"),
            title_id="831.400/2011",
            holder="Companhia Mineral do Vale Simulado",
            status="suspended", phase="lavra", substance="minério de ferro",
            tailings="Barragem Norte (simulated)",
            # a structure that is creeping slowly and steadily, with no
            # acceleration — the case the screen must NOT escalate
            deformation_profile={"creep_mm_yr": -2.2, "accelerate_from_month": None,
                                 "months": 30},
            declared_tonnes=0,
            start=date(2024, 1, 1),
            with_protected_area=False,
            narrative=("Title recorded as suspended, yet the working surface keeps "
                       "growing and no production is declared."),
        ),
        SiteSpec(
            site=SyntheticSite(site_id="BR-GO-0004", seed=246810,
                               centre_lon=-49.80, centre_lat=-15.62,
                               width=320, height=320,
                               licence_frac=(0.03, 0.03, 0.97, 0.97),
                               tailings_area_ha=8.0,
                               growth=(("2024-01-01", 19.0), ("2025-01-01", 22.0),
                                       ("2026-07-01", 27.0)),
                               breakout_date="2099-01-01"),
            title_id="860.055/2015",
            holder="Cooperativa Mineral Simulada",
            status="active", phase="lavra", substance="calcário",
            declared_tonnes=1_450_000,
            start=date(2024, 1, 1),
            with_protected_area=False,
            narrative=("Everything inside the licence, growth modest, declaration "
                       "in the middle of the peer distribution. The system's job "
                       "here is to say so and stop."),
        ),
    ]


def _config(spec: SiteSpec, provider: SyntheticProvider) -> SiteConfig:
    ring = provider.licence_ring()
    restricted = []
    if spec.with_protected_area:
        restricted = [
            cad.RestrictedArea(
                identifier=f"UC-SIM-{spec.site.seed % 100:02d}",
                kind="conservation_unit",
                name="Floresta Nacional Simulada",
                ring=provider.protected_area_ring(),
                basis="Lei 9.985/2000 (SNUC), art. 17",
                source="CNUC (simulated extract)",
            )
        ]
    declared = None
    if spec.declared_tonnes is not None:
        declared = Declaration(
            site_id=spec.site.site_id, title_id=spec.title_id,
            period_start=date(2025, 1, 1), period_end=date(2026, 7, 1),
            substance=spec.substance, declared_tonnes=spec.declared_tonnes,
            source="ANM CFEM open data (simulated extract)",
            filing_reference=f"CFEM/SIM/{spec.site.seed}",
        )
    return SiteConfig(
        site_id=spec.site.site_id,
        title=cad.Title(
            identifier=spec.title_id, holder=spec.holder, ring=ring,
            status=spec.status, phase=spec.phase, substance=spec.substance,
            source="ANM SIGMINE (simulated extract)",
            licence_area_ha=geodesic_area_ha(ring),
        ),
        restricted=restricted,
        start=spec.start,
        end=spec.end,
        frame=BRAZIL,
        tailings_structure=spec.tailings,
        deformation_profile=spec.deformation_profile or {},
        declared=declared,
        peer_intensities=PEERS,
        other_filings=spec.other_filings or {},
    )


def run_portfolio(out_dir: str | Path = "data/out") -> List[RunResult]:
    out = Path(out_dir)
    register = CaseRegister(out / "cases")
    results: List[RunResult] = []

    for spec in specs():
        provider = SyntheticProvider(spec.site)
        cfg = _config(spec, provider)
        r = run_site(cfg, provider, out, register, themes=("light", "dark"))
        r.case.findings.append({"quantity": "narrative", "value": spec.narrative,
                                "units": ""})
        _walk(r, spec, register)
        # The public card is a function of the case's *current* publication
        # state, so it is re-rendered after the procedure has moved, not before.
        (out / f"{r.case.case_id}_public_card.json").write_text(
            json.dumps(r.dossier.public_card(), indent=2, ensure_ascii=False),
            encoding="utf-8")
        results.append(r)

    (out / "portfolio.json").write_text(
        json.dumps(_bundle(results), indent=2, ensure_ascii=False), encoding="utf-8")
    return results


def _walk(r: RunResult, spec: SiteSpec, register: CaseRegister) -> None:
    """Move each case to the state its story implies, naming a human each time."""
    c = r.case
    sid = spec.site.site_id

    if sid == "BR-GO-0004":
        c.advance(CaseState.SCREENED, "A. Analista", "remote sensing analyst",
                  "raised by the routine screen")
        c.advance(CaseState.DISMISSED, "A. Analista", "remote sensing analyst",
                  "all disturbance inside the titled polygon; declared intensity "
                  "mid-distribution; no further action")
        c.advance(CaseState.CLOSED, "D. Coordenadora", "unit coordinator",
                  "closed and published as cleared")
        register.save(c)
        return

    c.advance(CaseState.SCREENED, "A. Analista", "remote sensing analyst",
              "exceeds the screening threshold")

    if sid == "BR-MG-0003":
        register.save(c)
        return

    c.advance(CaseState.CORROBORATED, "B. Geólogo", "senior technical officer",
              "confirmed on two independent dates")
    c.advance(CaseState.NOTIFIED, "C. Fiscal", "inspecting official",
              "notice of observed facts issued to the title holder")

    if sid == "BR-PA-0001":
        c.record_response(
            Response(
                received_utc="2026-08-05T14:22:00+00:00",
                submitted_by=spec.holder,
                channel="electronic protocol",
                summary=("Holder states that 6.2 ha of the area identified as outside "
                         "the title is a haul road authorised under a separate "
                         "easement, and supplies the instrument. The remainder is not "
                         "addressed."),
                documents=["easement-2024-117.pdf", "survey-2026-06.dxf"],
            ),
            "C. Fiscal", "inspecting official")
    register.save(c)


def _bundle(results: Sequence[RunResult]) -> dict:
    """Everything the dashboard needs, and nothing it may not lawfully show."""
    sites = []
    for r in results:
        dates, totals, degraded = [], [], []
        for o in r.footprint_obs:
            if o.reliability == "ok":
                dates.append(o.acquired.isoformat())
                totals.append(round(o.value, 2))
            elif o.reliability == "degraded":
                degraded.append([o.acquired.isoformat(), round(o.value, 2)])

        pond = [[o.acquired.isoformat(), round(o.value, 2)]
                for o in r.water_obs if o.reliability == "ok"]

        sites.append({
            "site_id": r.site_id,
            "case_id": r.case.case_id,
            "state": r.case.state.value,
            "publication": r.case.publication.value,
            "severity": r.case.severity,
            "title_id": r.case.title_id,
            "holder": r.case.holder,
            "title_status": next(
                (i["note"] for i in r.dossier.manifest.inputs
                 if i.get("identifier") == r.case.title_id), ""),
            "verdict": r.verdict.to_dict(),
            "trend": r.trend.to_dict(),
            "gaps": r.gaps,
            "reconciliation": r.reconciliation,
            "filing_notes": r.filing_notes,
            "deformation": None if r.deformation_obs is None
            else r.deformation_obs.to_dict(),
            "volume": None if r.volume_obs is None else r.volume_obs.to_dict(),
            "series": {
                "dates": dates,
                "disturbed_ha": totals,
                "outside_ha": [round(v, 2) for v in r.outside_series],
                "degraded": degraded,
                "pond_ha": pond,
            },
            "manifest": {
                "id": r.dossier.manifest.manifest_id,
                "hash": r.dossier.manifest.manifest_hash,
                "prev_hash": r.dossier.manifest.prev_hash,
                "created_utc": r.dossier.manifest.created_utc,
                "inputs": len(r.dossier.manifest.inputs),
                "algorithms": [f"{a['name']} v{a['version']}"
                               for a in r.dossier.manifest.algorithms],
                "limitations": r.dossier.manifest.limitations,
                "assumptions": r.dossier.manifest.assumptions,
            },
            "history": [t.to_dict() for t in r.case.history],
            "response": None if r.case.response is None else {
                "received_utc": r.case.response.received_utc,
                "submitted_by": r.case.response.submitted_by,
                "channel": r.case.response.channel,
                "summary": r.case.response.summary,
                "documents": r.case.response.documents,
                "digest": r.case.response.digest(),
            },
            "public_card": r.dossier.public_card(),
            "figures": {k: Path(v).name for k, v in r.outputs.items()},
            "narrative": next((f["value"] for f in r.case.findings
                               if f["quantity"] == "narrative"), ""),
        })
    return {"generated_utc": _now(), "simulation": True, "sites": sites}


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
