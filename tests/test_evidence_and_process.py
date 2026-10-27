"""The properties that make this a rule-of-law tool rather than a surveillance tool.

If any test in this file fails, the platform should not be deployed.
"""

import json
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from soma.cases import (Case, CaseRegister, CaseState, DueProcessError,
                           PublicationState, Response)
from soma.crosscheck import cadastre as cad
from soma.crosscheck.declaration import (Declaration, build_peer_stat,
                                            cross_filing_check, reconcile)
from soma.dossier import BRAZIL, Dossier, SyntheticEvidenceError
from soma.evidence import EvidenceManifest, Ledger, sha256_of
from soma.geom import Grid, ring_from_bbox


# --------------------------------------------------------------------------
# Evidence integrity
# --------------------------------------------------------------------------

def _manifest(site="S1", q="test question"):
    m = EvidenceManifest.create(site, q)
    m.add_dataset("GRANULE-1", "https://example.invalid", "CC BY 4.0")
    m.add_algorithm("footprint.spectral_rule", {"ndvi_max": 0.3})
    m.add_output("area_ha", 12.5, "ha")
    return m


def test_manifest_seals_and_verifies():
    m = _manifest().seal()
    assert m.verify()


def test_tampering_with_a_manifest_is_detected():
    m = _manifest().seal()
    m.outputs[0]["value"] = 999.0
    assert not m.verify()


def test_ledger_chains_entries():
    with tempfile.TemporaryDirectory() as tmp:
        led = Ledger(Path(tmp) / "ledger.jsonl")
        a = led.append(_manifest("S1", "first"))
        b = led.append(_manifest("S2", "second"))
        assert b.prev_hash == a.manifest_hash
        assert led.verify_chain()["intact"]


def test_ledger_detects_a_deleted_entry():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "ledger.jsonl"
        led = Ledger(path)
        led.append(_manifest("S1", "first"))
        led.append(_manifest("S2", "second"))
        led.append(_manifest("S3", "third"))
        lines = path.read_text().splitlines()
        path.write_text("\n".join([lines[0], lines[2]]) + "\n")
        report = led.verify_chain()
        assert not report["intact"]
        assert report["problems"]


def test_ledger_detects_an_edited_entry():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "ledger.jsonl"
        led = Ledger(path)
        led.append(_manifest("S1", "first"))
        led.append(_manifest("S2", "second"))
        lines = path.read_text().splitlines()
        doc = json.loads(lines[0])
        doc["outputs"][0]["value"] = 0.1
        lines[0] = json.dumps(doc, sort_keys=True, separators=(",", ":"))
        path.write_text("\n".join(lines) + "\n")
        assert not led.verify_chain()["intact"]


def test_canonical_hash_is_key_order_independent():
    assert sha256_of({"a": 1, "b": 2}) == sha256_of({"b": 2, "a": 1})


# --------------------------------------------------------------------------
# Due process
# --------------------------------------------------------------------------

def _case(**kw) -> Case:
    return Case(
        case_id="CASE-TEST-1", site_id="S1", title_id="T1", holder="Holder",
        opened=datetime.now(timezone.utc).isoformat(), question="q", **kw
    )


def test_a_case_cannot_skip_notification():
    c = _case()
    c.advance(CaseState.SCREENED, "A", "analyst")
    c.advance(CaseState.CORROBORATED, "B", "officer")
    with pytest.raises(DueProcessError):
        c.advance(CaseState.SUBSTANTIATED, "C", "official")


def test_a_transition_requires_a_named_human():
    c = _case()
    with pytest.raises(DueProcessError):
        c.advance(CaseState.SCREENED, "", "")


def test_review_is_blocked_while_the_response_window_is_open():
    c = _case()
    c.advance(CaseState.SCREENED, "A", "analyst")
    c.advance(CaseState.CORROBORATED, "B", "officer")
    c.advance(CaseState.NOTIFIED, "C", "official")
    with pytest.raises(DueProcessError):
        c.advance(CaseState.REVIEWED, "C", "official")


def test_review_is_allowed_once_the_window_has_expired():
    c = _case()
    c.advance(CaseState.SCREENED, "A", "analyst")
    c.advance(CaseState.CORROBORATED, "B", "officer")
    c.advance(CaseState.NOTIFIED, "C", "official")
    c.response_due = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    c.advance(CaseState.REVIEWED, "C", "official")
    assert c.state is CaseState.REVIEWED


def test_a_response_can_always_be_recorded_and_moves_the_case():
    c = _case()
    c.advance(CaseState.SCREENED, "A", "analyst")
    c.advance(CaseState.CORROBORATED, "B", "officer")
    c.advance(CaseState.NOTIFIED, "C", "official")
    c.record_response(
        Response(received_utc=datetime.now(timezone.utc).isoformat(),
                 submitted_by="Holder", channel="post", summary="we have an easement"),
        "C", "official")
    assert c.state is CaseState.CONTESTED
    assert c.history[-1].attachment_digest


def test_nothing_is_public_before_notification():
    c = _case()
    assert c.public_view() is None
    c.advance(CaseState.SCREENED, "A", "analyst")
    assert c.public_view() is None
    c.advance(CaseState.CORROBORATED, "B", "officer")
    assert c.public_view() is None
    c.advance(CaseState.NOTIFIED, "C", "official")
    assert c.publication is PublicationState.PARTY_ONLY
    assert c.public_view() is None


def test_a_dismissal_publishes_only_a_summary():
    c = _case()
    c.advance(CaseState.SCREENED, "A", "analyst")
    c.advance(CaseState.DISMISSED, "A", "analyst", "explained by the holder")
    view = c.public_view()
    assert view is not None
    assert "holder" not in view


def test_case_register_round_trip():
    with tempfile.TemporaryDirectory() as tmp:
        reg = CaseRegister(tmp)
        c = reg.open_case("S1", "T1", "Holder", "q", _manifest())
        c.advance(CaseState.SCREENED, "A", "analyst")
        reg.save(c)
        again = reg.load(c.case_id)
        assert again.state is CaseState.SCREENED
        assert again.manifests == c.manifests


# --------------------------------------------------------------------------
# Spatial attribution
# --------------------------------------------------------------------------

def _grid_and_title():
    ring = ring_from_bbox(-56.20, -6.50, -56.18, -6.48)
    grid = Grid.covering(ring, pixel_m=10.0, margin_m=400.0)
    title = cad.Title(identifier="T1", holder="H", ring=ring, status="active",
                      phase="lavra")
    return grid, title, ring


def test_boundary_tolerance_favours_the_holder():
    """Disturbance straddling the line must land in 'indeterminate', not 'outside'."""
    grid, title, ring = _grid_and_title()
    lon, lat = grid.lonlat()
    band = (np.abs(lon - ring[1][0]) < (10.0 / (111_320 * 0.99))) if False else None
    del band
    import numpy as _np
    edge_lon = ring[1][0]
    disturbed = _np.abs(lon - edge_lon) < (12.0 / 111_320.0)     # a ~12 m sliver
    disturbed &= (lat > ring[0][1]) & (lat < ring[2][1])
    v = cad.locate("S1", date.today(), grid, disturbed, [title])
    assert v.indeterminate_ha > 0
    assert v.outside_title_ha == pytest.approx(0.0, abs=0.05)


def test_clear_excursion_is_reported_as_outside():
    grid, title, ring = _grid_and_title()
    lon, lat = grid.lonlat()
    import numpy as _np
    far = ring[1][0] + (200.0 / 111_320.0)
    disturbed = (lon > far) & (lon < far + 300.0 / 111_320.0)
    disturbed &= (lat > ring[0][1]) & (lat < ring[2][1])
    v = cad.locate("S1", date.today(), grid, disturbed, [title])
    assert v.outside_title_ha > 1.0
    assert v.inside_title_ha == pytest.approx(0.0, abs=0.05)


def test_no_title_produces_an_explicit_note():
    grid, _title, ring = _grid_and_title()
    mask = grid.rasterize(ring)
    v = cad.locate("S1", date.today(), grid, mask, [])
    assert v.notes and "unlicensed" in " ".join(v.notes).lower()


def test_exploration_phase_title_is_flagged():
    grid, _t, ring = _grid_and_title()
    title = cad.Title(identifier="T2", holder="H", ring=ring, status="active",
                      phase="exploration")
    mask = grid.rasterize(ring)
    v = cad.locate("S1", date.today(), grid, mask, [title])
    assert any("exploration" in n.lower() for n in v.notes)


# --------------------------------------------------------------------------
# Declaration screening
# --------------------------------------------------------------------------

def test_activity_without_declaration_is_flagged():
    r = reconcile("S1", "2026", 40.0, 1.2, None)
    assert "activity_without_declaration" in r.flags
    assert r.score > 0


def test_screening_result_never_claims_to_be_an_assessment():
    peers = build_peer_stat("iron", "open pit", "BR", list(range(100, 2100, 100)))
    d = Declaration("S1", "T1", date(2025, 1, 1), date(2026, 1, 1), "iron",
                    declared_tonnes=1_000)
    r = reconcile("S1", "2025", 50.0, 2.0, d, peers, growth_percentile=0.95).to_dict()
    assert "not an assessment" in r["status"].lower()


def test_cross_filing_check_finds_divergence():
    notes = cross_filing_check({"a": 100.0, "b": 100.0, "c": 140.0})
    assert notes and "c" in notes[0]


def test_cross_filing_check_is_quiet_when_consistent():
    assert cross_filing_check({"a": 100.0, "b": 101.0}) == []


# --------------------------------------------------------------------------
# The synthetic-evidence guard
# --------------------------------------------------------------------------

def test_no_legal_act_from_simulated_evidence():
    m = EvidenceManifest.create("S1", "q")
    m.add_dataset("SYNTH-1", "soma.providers.synthetic",
                  "simulation — not evidence")
    m.seal()
    c = _case()
    c.advance(CaseState.SCREENED, "A", "analyst")
    c.advance(CaseState.CORROBORATED, "B", "officer")
    d = Dossier(case=c, manifest=m, frame=BRAZIL)
    with pytest.raises(SyntheticEvidenceError):
        d.administrative_notice()
    with pytest.raises(SyntheticEvidenceError):
        d.judicial_dossier()
    # but the technical annex is allowed, with a banner
    annex = d.technical_annex()
    assert "SIMULATION" in annex


def test_notice_requires_a_corroborated_case():
    m = EvidenceManifest.create("S1", "q")
    m.add_dataset("S2A_REAL", "https://catalogue.dataspace.copernicus.eu/stac",
                  "Copernicus free and open")
    m.seal()
    c = _case()
    d = Dossier(case=c, manifest=m, frame=BRAZIL)
    with pytest.raises(RuntimeError):
        d.administrative_notice()


import numpy as np  # noqa: E402  (used by the spatial tests above)
