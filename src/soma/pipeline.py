"""End-to-end run for one site.

Reads like the sequence a human analyst would follow, and is meant to: look at
the site over time, measure the disturbance, ask where it is relative to what
was authorised, ask whether it is accelerating, ask whether the structures are
moving, ask whether what is declared is consistent with what is visible, then
assemble the record and hand it to a named official.

Nothing here decides anything. It prepares a decision.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

from . import render
from .cases import Case, CaseRegister, CaseState, Response
from .crosscheck import cadastre as cad
from .crosscheck.declaration import (Declaration, build_peer_stat, cross_filing_check,
                                     reconcile)
from .detectors import change, deformation, footprint, volume, water
from .detectors.base import Observation
from .dossier import BRAZIL, Dossier, LegalFrame, build_manifest_for_case
from .geom import buffer_ring, geodesic_area_ha
from .providers.base import SceneProvider
from .providers.synthetic import SyntheticProvider, SyntheticSite


@dataclass
class SiteConfig:
    site_id: str
    title: cad.Title
    restricted: Sequence[cad.RestrictedArea] = ()
    start: date = date(2023, 1, 1)
    end: date = date(2026, 7, 1)
    frame: LegalFrame = field(default_factory=lambda: BRAZIL)
    tailings_structure: str = ""
    # Simulator-only: how the crest of the simulated structure behaves. A real
    # deployment reads EGMS or its own InSAR time series instead.
    deformation_profile: Dict[str, float] = field(default_factory=dict)
    declared: Optional[Declaration] = None
    peer_intensities: Sequence[float] = ()
    other_filings: Dict[str, float] = field(default_factory=dict)


@dataclass
class RunResult:
    site_id: str
    scenes: int
    footprint_obs: List[Observation]
    water_obs: List[Observation]
    verdict: cad.SpatialVerdict
    trend: change.TrendResult
    trend_obs: Observation
    gaps: List[dict]
    deformation_obs: Optional[Observation]
    volume_obs: Optional[Observation]
    reconciliation: Optional[dict]
    filing_notes: List[str]
    case: Case
    dossier: Dossier
    outputs: Dict[str, str]
    # area outside the title on each fully observed date, aligned with the
    # dates returned by render.observations_to_series
    outside_series: List[float] = field(default_factory=list)
    grid: object = None


def run_site(
    cfg: SiteConfig,
    provider: SceneProvider,
    out_dir: Path,
    register: CaseRegister,
    themes: Sequence[str] = ("light", "dark"),
) -> RunResult:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. observe -----------------------------------------------------------
    scenes = provider.search(cfg.site_id, cfg.title.ring, cfg.start, cfg.end)
    if not scenes:
        raise RuntimeError("no scenes returned for the period")
    grid = scenes[0].grid

    # Visibility is judged over the licence plus a 1 km apron — wide enough to
    # contain a plausible excursion, narrow enough that weather in the far
    # corner of the scene does not discard a good measurement of the workings.
    assessment = grid.rasterize(buffer_ring(cfg.title.ring, 1000.0))

    fp_params = footprint.FootprintParams(assessment_mask=assessment)
    fp_obs = [footprint.detect(s, fp_params) for s in scenes]
    # Impounded water is asked about *inside the licence*: the question is how
    # much water the operator is holding behind its own structures, and a river
    # running through the corner of the scene is not that.
    inside_licence = grid.rasterize(cfg.title.ring)
    w_params = water.WaterParams(aoi_mask=inside_licence, assessment_mask=assessment)
    w_obs = [water.detect_pond(s, w_params) for s in scenes]

    usable = [o for o in fp_obs if o.reliability != "unusable"]
    if not usable:
        raise RuntimeError(
            "every observation in the period was unusable. That is a finding: the "
            "site is not observable optically and needs a radar or overflight "
            "strategy."
        )
    latest = usable[-1]
    latest_scene = next(s for s in scenes if s.acquired == latest.acquired)

    # 2. attribute ---------------------------------------------------------
    verdict = cad.locate(
        site_id=cfg.site_id,
        when=latest.acquired,
        grid=grid,
        disturbed=latest.mask,
        titles=[cfg.title],
        restricted=cfg.restricted,
    )

    # 3. change ------------------------------------------------------------
    trend, trend_obs = change.analyse(fp_obs)
    gaps = change.observation_gaps(fp_obs)

    # 4. structures --------------------------------------------------------
    def_obs = None
    if cfg.tailings_structure:
        series = deformation.simulate_crest(
            lon=cfg.title.ring[0][0] + 0.004, lat=cfg.title.ring[0][1] + 0.004,
            **cfg.deformation_profile,
        ) if isinstance(provider, SyntheticProvider) else []
        if series:
            def_obs = deformation.screen(cfg.site_id, series, cfg.tailings_structure)

    # 5. volume ------------------------------------------------------------
    vol_obs = None
    if isinstance(provider, SyntheticProvider):
        dem_a, dem_b = provider.dem_pair(scenes[0].acquired, latest.acquired)
        vol_obs = volume.difference(
            cfg.site_id, grid, dem_a, dem_b, latest.acquired,
            mask=latest.mask | (dem_b < dem_a - 1.0),
        )

    # 6. declaration -------------------------------------------------------
    recon = None
    if cfg.declared is not None or cfg.peer_intensities:
        peers = build_peer_stat(
            cfg.title.substance or "unspecified", "open pit", cfg.frame.jurisdiction,
            cfg.peer_intensities,
        )
        growth_pct = 0.95 if trend.slope_per_month > 1.0 else 0.5
        recon = reconcile(
            site_id=cfg.site_id,
            period=f"{cfg.start.isoformat()}..{cfg.end.isoformat()}",
            observed_active_ha=latest.value,
            observed_growth_ha_per_month=trend.slope_per_month,
            declaration=cfg.declared,
            peers=peers,
            growth_percentile=growth_pct,
        ).to_dict()
    filing_notes = cross_filing_check(cfg.other_filings) if cfg.other_filings else []

    # 7. record ------------------------------------------------------------
    all_sources = [src for s in scenes for src in s.sources]
    observations: List[Observation] = list(fp_obs) + list(w_obs) + [trend_obs]
    if def_obs:
        observations.append(def_obs)
    if vol_obs:
        observations.append(vol_obs)

    manifest = build_manifest_for_case(
        site_id=cfg.site_id,
        question=(
            "Is the disturbed mining surface at this site confined to the polygon of "
            "the title of record, and is its rate of expansion consistent with what "
            "has been declared?"
        ),
        scenes_sources=all_sources,
        observations=observations,
        frame=cfg.frame,
        extra_datasets=[
            {
                "identifier": cfg.title.identifier,
                "source": cfg.title.source or "national mining cadastre",
                "licence": "public registry data",
                "note": f"title polygon, {cfg.title.licence_area_ha:.1f} ha, "
                        f"status {cfg.title.status}",
            }
        ] + [
            {
                "identifier": r.identifier,
                "source": r.source or "protected area register",
                "licence": "public registry data",
                "note": f"{r.kind}: {r.name}",
            }
            for r in cfg.restricted
        ],
        prev_hash=register.ledger.head(),
    )
    manifest.add_output("disturbed_area_latest_ha", round(latest.value, 3), "ha")
    manifest.add_output("outside_title_ha", round(verdict.outside_title_ha, 3), "ha")
    manifest.add_output("indeterminate_boundary_ha",
                        round(verdict.indeterminate_ha, 3), "ha")
    manifest.add_output("growth_rate_ha_per_month",
                        round(trend.slope_per_month, 4), "ha/month")
    for ov in verdict.restricted_overlaps:
        manifest.add_output(f"overlap_{ov['kind']}_{ov['identifier']}_ha",
                            ov["overlap_ha"], "ha")
    if vol_obs:
        manifest.add_output("net_excavated_volume_m3",
                            round(vol_obs.value, 1), "m3")
    if def_obs and np.isfinite(def_obs.value):
        manifest.add_output("crest_velocity_mm_yr", round(def_obs.value, 2), "mm/yr")
    if gaps:
        manifest.note_limitation(
            f"{len(gaps)} observation gap(s) longer than 75 days: "
            + "; ".join(f"{g['from']}→{g['to']} ({g['days']} d)" for g in gaps)
        )

    severity = assess_severity(verdict, cfg.title, def_obs, recon)
    case = register.open_case(
        site_id=cfg.site_id,
        title_id=cfg.title.identifier,
        holder=cfg.title.holder,
        question=manifest.question,
        manifest=manifest,
        severity=severity,
        jurisdiction=cfg.frame.jurisdiction,
        legal_basis=[b for b in (cfg.frame.extraction_outside_title,
                                 cfg.frame.protected_area) if b],
    )
    case.findings = [
        {"quantity": o["name"], "value": o["value"], "units": o["units"]}
        for o in manifest.outputs
    ]
    register.save(case)

    # 8. render ------------------------------------------------------------
    outputs: Dict[str, str] = {}
    masks = cad.masks(grid, latest.mask, [cfg.title])
    first_scene = scenes[0]
    outputs["image_first"] = str(render.true_colour_png(
        first_scene, out_dir / f"{cfg.site_id}_first.png"))
    outputs["image_latest"] = str(render.true_colour_png(
        latest_scene, out_dir / f"{cfg.site_id}_latest.png"))
    outputs["image_overlay"] = str(render.overlay_png(
        latest_scene, out_dir / f"{cfg.site_id}_overlay.png", masks,
        rings=[(cfg.title.ring, "#2a78d6", f"title {cfg.title.identifier}")]
        + [(r.ring, "#9085e9", r.name) for r in cfg.restricted],
        areas_ha={
            "inside": verdict.inside_title_ha,
            "outside": verdict.outside_title_ha,
            "indeterminate": verdict.indeterminate_ha,
        },
    ))

    dates, totals, _rel = render.observations_to_series(fp_obs)
    degraded = render.degraded_points(fp_obs)
    outside_series = _outside_series(fp_obs, grid, cfg.title)
    wdates, wvals, _ = render.observations_to_series(w_obs)
    dfdates, dfrows = ([], [])
    if def_obs is not None and isinstance(provider, SyntheticProvider):
        series = deformation.simulate_crest(
            lon=cfg.title.ring[0][0] + 0.004, lat=cfg.title.ring[0][1] + 0.004,
            **cfg.deformation_profile)
        dfdates, dfrows = deformation.series_to_table(series)

    for theme in themes:
        suffix = "" if theme == "light" else "_dark"
        outputs[f"chart_footprint{suffix}"] = str(render.footprint_chart(
            out_dir / f"{cfg.site_id}_footprint{suffix}.png",
            dates, totals, outside_series, degraded, trend.breakpoint, theme=theme,
            title="Disturbed surface, total and outside the licensed polygon",
        ))
        outputs[f"chart_water{suffix}"] = str(render.water_chart(
            out_dir / f"{cfg.site_id}_water{suffix}.png", wdates, wvals, theme=theme))
        if dfrows:
            outputs[f"chart_deformation{suffix}"] = str(render.deformation_chart(
                out_dir / f"{cfg.site_id}_deformation{suffix}.png",
                dfdates, dfrows, theme=theme))

    # 9. translate ---------------------------------------------------------
    doss = Dossier(
        case=case,
        manifest=manifest,
        frame=cfg.frame,
        verdict=verdict,
        trend=trend.to_dict(),
        observations=observations,
        figures={k: Path(v).name for k, v in outputs.items()},
        reconciliation=recon,
        deformation=None if def_obs is None else def_obs.detail,
    )
    (out_dir / f"{case.case_id}_technical_annex.md").write_text(
        doss.technical_annex(), encoding="utf-8")
    outputs["technical_annex"] = str(out_dir / f"{case.case_id}_technical_annex.md")

    (out_dir / f"{case.case_id}_public_card.json").write_text(
        json.dumps(doss.public_card(), indent=2, ensure_ascii=False), encoding="utf-8")
    outputs["public_card"] = str(out_dir / f"{case.case_id}_public_card.json")

    return RunResult(
        site_id=cfg.site_id,
        scenes=len(scenes),
        footprint_obs=fp_obs,
        water_obs=w_obs,
        verdict=verdict,
        trend=trend,
        trend_obs=trend_obs,
        gaps=gaps,
        deformation_obs=def_obs,
        volume_obs=vol_obs,
        reconciliation=recon,
        filing_notes=filing_notes,
        case=case,
        dossier=doss,
        outputs=outputs,
        outside_series=outside_series,
        grid=grid,
    )


def assess_severity(verdict: cad.SpatialVerdict, title: cad.Title,
                    deformation_obs: Optional[Observation],
                    reconciliation: Optional[dict]) -> str:
    """Rank a case for the queue, and be able to say why in one line.

    Ranking is by *what is at stake*, not by hectares. Ten hectares inside a
    conservation unit outranks fifty hectares of lawful expansion, and a
    structure whose crest is accelerating outranks both — nothing else on this
    list can kill anyone.
    """
    if deformation_obs is not None and deformation_obs.detail.get("flags"):
        return "critical"
    if verdict.restricted_overlaps and \
            max(o["overlap_ha"] for o in verdict.restricted_overlaps) > 5.0:
        return "critical"
    if title.status in ("requested", "expired") and verdict.total_disturbed_ha > 5.0:
        return "critical"
    if title.status == "suspended" and verdict.total_disturbed_ha > 5.0:
        return "high"
    if verdict.outside_title_ha > 5.0:
        return "high"
    if verdict.restricted_overlaps:
        return "high"
    if reconciliation and reconciliation.get("audit_priority_score", 0) >= 0.5:
        return "high"
    if verdict.outside_title_ha > 1.0 or (
            reconciliation and reconciliation.get("flags")):
        return "medium"
    return "low"


def _outside_series(obs: Sequence[Observation], grid, title: cad.Title) -> List[float]:
    """Area outside the title, per date — the series that carries the finding."""
    out = []
    for o in obs:
        if o.reliability != "ok" or o.mask is None:
            continue
        m = cad.masks(grid, o.mask, [title])
        out.append(grid.area_ha(m["outside"]))
    return out


# --------------------------------------------------------------------------
# The worked example
# --------------------------------------------------------------------------

def demo_site(provider: SyntheticProvider) -> SiteConfig:
    """A simulated Brazilian site with a licence, a neighbouring conservation
    unit, a tailings structure and a declaration that does not fit."""
    ring = provider.licence_ring()
    return SiteConfig(
        site_id="DEMO-001",
        title=cad.Title(
            identifier="830.123/2018",
            holder="Mineradora Exemplo S.A. (simulated)",
            ring=ring,
            status="active",
            phase="lavra",
            substance="minério de ferro",
            granted=date(2018, 6, 14),
            source="ANM SIGMINE (simulated extract)",
            licence_area_ha=geodesic_area_ha(ring),
        ),
        restricted=[
            cad.RestrictedArea(
                identifier="UC-SIM-04",
                kind="conservation_unit",
                name="Floresta Nacional Simulada",
                ring=provider.protected_area_ring(),
                basis="Lei 9.985/2000 (SNUC), art. 17",
                source="CNUC (simulated extract)",
            )
        ],
        start=date(2023, 1, 1),
        end=date(2026, 7, 1),
        frame=BRAZIL,
        tailings_structure="Barragem B1 (simulated)",
        declared=Declaration(
            site_id="DEMO-001",
            title_id="830.123/2018",
            period_start=date(2025, 1, 1),
            period_end=date(2026, 7, 1),
            substance="minério de ferro",
            declared_tonnes=430_000,
            royalty_paid=8_600_000,
            currency="BRL",
            source="ANM CFEM open data (simulated extract)",
            filing_reference="CFEM/2026/SIM/0001",
        ),
        peer_intensities=[
            520, 610, 700, 760, 810, 880, 940, 1010, 1090, 1180,
            1260, 1350, 1470, 1590, 1720, 1880, 2060, 2300, 2610, 3100,
        ],
        other_filings={
            "CFEM declaration": 430_000,
            "company annual report": 512_000,
            "EU Ch.10 payments to governments": 505_000,
        },
    )


def run_demo(out_dir: str | Path = "data/out", seed: int = 20260819) -> RunResult:
    provider = SyntheticProvider(SyntheticSite(seed=seed))
    cfg = demo_site(provider)
    register = CaseRegister(Path(out_dir) / "cases")
    result = run_site(cfg, provider, Path(out_dir), register)

    # Walk the case through the procedure, as a real one would be walked.
    c = result.case
    c.advance(CaseState.SCREENED, "A. Analista", "remote sensing analyst",
              "footprint outside title exceeds the 5 ha screening threshold")
    c.advance(CaseState.CORROBORATED, "B. Geólogo", "senior technical officer",
              "confirmed on two independent dates and against the DEM difference")
    c.advance(CaseState.NOTIFIED, "C. Fiscal", "inspecting official",
              "notice of observed facts issued to the title holder")
    c.record_response(
        Response(
            received_utc="2026-08-05T14:22:00+00:00",
            submitted_by="Mineradora Exemplo S.A. (simulated)",
            channel="electronic protocol",
            summary=("Holder states that 6.2 ha of the area identified as outside the "
                     "title is a haul road authorised under a separate easement, and "
                     "supplies the instrument. The remainder is not addressed."),
            documents=["easement-2024-117.pdf", "survey-2026-06.dxf"],
        ),
        "C. Fiscal", "inspecting official",
    )
    register.save(c)
    result.case = c
    result.dossier.case = c
    return result
