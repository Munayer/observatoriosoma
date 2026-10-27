"""Detector behaviour, checked against the simulator's known ground truth.

This is the regression net. If a threshold changes and recall drops by 5 ha,
these tests say so before a finding does.
"""

from datetime import date

import numpy as np
import pytest

from minerva.detectors import change, deformation, footprint, volume, water
from minerva.detectors.base import grade_reliability
from minerva.providers.synthetic import SyntheticProvider, SyntheticSite


def _provider():
    return SyntheticProvider(SyntheticSite(seed=20260819))


def test_footprint_tracks_ground_truth_on_a_clear_scene():
    p = _provider()
    scenes = p.search("T", p.licence_ring(), date(2023, 7, 1), date(2023, 7, 1))
    s = scenes[0]
    if s.valid_fraction < 0.9:
        pytest.skip("simulated scene happened to be cloudy")
    obs = footprint.detect(s)
    truth = p.truth(s.acquired)["disturbed_ha"]
    assert obs.value == pytest.approx(truth, rel=0.10), (obs.value, truth)


def test_footprint_grows_over_the_series():
    p = _provider()
    early = p.search("T", p.licence_ring(), date(2023, 6, 1), date(2023, 8, 1))
    late = p.search("T", p.licence_ring(), date(2026, 5, 1), date(2026, 7, 1))
    e = max(footprint.detect(s).value for s in early)
    l = max(footprint.detect(s).value for s in late)
    assert l > e * 1.5, (e, l)


def test_forest_is_not_mistaken_for_mining():
    """The single most important false-positive check."""
    p = _provider()
    s = p.search("T", p.licence_ring(), date(2023, 7, 1), date(2023, 7, 1))[0]
    obs = footprint.detect(s)
    forest = p._static["forest"] & ~p._pit_mask(s.acquired)
    forest &= ~p._static["waste"] & ~p._static["roads"] & ~p._static["dam"]
    overlap = (obs.mask & forest).sum() / max(forest.sum(), 1)
    assert overlap < 0.01, overlap


def test_water_is_not_mistaken_for_mining():
    p = _provider()
    s = p.search("T", p.licence_ring(), date(2023, 7, 1), date(2023, 7, 1))[0]
    obs = footprint.detect(s)
    ponds = p._static["tailings"] | p._static["river"]
    overlap = (obs.mask & ponds).sum() / max(ponds.sum(), 1)
    assert overlap < 0.02, overlap


def test_pond_detector_finds_the_impoundment():
    p = _provider()
    s = p.search("T", p.licence_ring(), date(2023, 7, 1), date(2023, 7, 1))[0]
    obs = water.detect_pond(s)
    truth = p.truth(s.acquired)["tailings_ha"]
    assert obs.value >= truth * 0.7, (obs.value, truth)
    assert obs.detail["process_water_ha"] > 0


def test_reliability_grading():
    assert grade_reliability(0.95) == "ok"
    assert grade_reliability(0.60) == "degraded"
    assert grade_reliability(0.20) == "unusable"


def test_trend_recovers_the_simulated_breakpoint():
    """The simulator steps up growth on 2025-07-01; the detector must find it."""
    p = _provider()
    scenes = p.search("T", p.licence_ring(), date(2023, 1, 1), date(2026, 7, 1))
    obs = [footprint.detect(s) for s in scenes]
    trend, _ = change.analyse(obs)
    assert trend.slope_per_month > 0
    assert trend.breakpoint is not None
    delta_months = abs((trend.breakpoint - date(2025, 7, 1)).days) / 30.4
    assert delta_months <= 4, trend.breakpoint
    assert trend.slope_after > trend.slope_before * 2


def test_trend_refuses_to_fit_too_few_points():
    p = _provider()
    scenes = p.search("T", p.licence_ring(), date(2023, 1, 1), date(2023, 2, 1))
    obs = [footprint.detect(s) for s in scenes]
    with pytest.raises(ValueError):
        change.analyse(obs)


def test_theil_sen_ignores_outliers():
    x = np.arange(20, dtype=float)
    y = 2.0 * x + 1.0
    y[3] = 900.0
    y[11] = -400.0
    slope, _lo, _hi = change.theil_sen(x, y)
    assert slope == pytest.approx(2.0, rel=0.01)


def test_deformation_flags_an_accelerating_crest():
    series = deformation.simulate_crest()
    obs = deformation.screen("T", series, "dam")
    assert obs.reliability != "unusable"
    assert "velocity_exceeds_threshold" in obs.detail["flags"]
    assert obs.detail["median_velocity_recent_mm_yr"] < \
        obs.detail["median_velocity_whole_history_mm_yr"]


def test_deformation_reports_decorrelation_rather_than_guessing():
    series = deformation.simulate_crest(n_points=3)
    obs = deformation.screen("T", series, "dam")
    assert obs.reliability == "unusable"
    assert "reason" in obs.detail


def test_volume_error_is_dominated_by_the_systematic_term():
    p = _provider()
    scenes = p.search("T", p.licence_ring(), date(2023, 1, 1), date(2023, 1, 1))
    grid = scenes[0].grid
    a, b = p.dem_pair(date(2023, 1, 1), date(2026, 7, 1))
    obs = volume.difference("T", grid, a, b, date(2026, 7, 1))
    d = obs.detail
    assert d["net_m3"] > 0
    assert d["sigma_systematic_m3"] > d["sigma_random_m3"]
    lo, hi = d["net_m3_interval_95"]
    assert lo < d["net_m3"] < hi


def test_volume_interval_is_not_absurdly_tight():
    """A DEM-difference volume with a sub-1% interval is a bug, not a triumph."""
    p = _provider()
    scenes = p.search("T", p.licence_ring(), date(2023, 1, 1), date(2023, 1, 1))
    grid = scenes[0].grid
    a, b = p.dem_pair(date(2023, 1, 1), date(2026, 7, 1))
    obs = volume.difference("T", grid, a, b, date(2026, 7, 1))
    width = obs.detail["net_m3_interval_95"][1] - obs.detail["net_m3_interval_95"][0]
    assert width / obs.detail["net_m3"] > 0.02


def test_no_breakpoint_on_a_steady_site():
    """A quiet site must not be reported as having changed pace.

    Regression guard for the failure that erodes trust fastest: a screening
    system that tells a regulator about a regime change every time a short,
    cloud-thinned series wobbles.
    """
    from minerva.detectors.base import Observation
    from minerva.version import ALGORITHM_VERSIONS
    rng = np.random.default_rng(3)
    obs = []
    for i in range(30):
        d = date(2024, 1, 1) + __import__("datetime").timedelta(days=30 * i)
        obs.append(Observation(
            site_id="steady", acquired=d, detector="footprint.spectral_rule",
            algorithm_version=ALGORITHM_VERSIONS["footprint.spectral_rule"],
            quantity="disturbed_area", value=20.0 + 0.25 * i + rng.normal(0, 1.2),
            units="ha", valid_fraction=0.97, reliability="ok"))
    trend, _ = change.analyse(obs)
    assert trend.breakpoint is None, trend.to_dict()
    assert trend.current_rate_per_month == pytest.approx(0.25, abs=0.08)


def test_breakpoint_is_found_when_the_change_is_real():
    from minerva.detectors.base import Observation
    from minerva.version import ALGORITHM_VERSIONS
    import datetime as _dt
    rng = np.random.default_rng(4)
    obs = []
    for i in range(30):
        d = date(2024, 1, 1) + _dt.timedelta(days=30 * i)
        v = 20.0 + (0.25 * i if i < 15 else 0.25 * 15 + 3.0 * (i - 15))
        obs.append(Observation(
            site_id="stepped", acquired=d, detector="footprint.spectral_rule",
            algorithm_version=ALGORITHM_VERSIONS["footprint.spectral_rule"],
            quantity="disturbed_area", value=v + rng.normal(0, 1.2),
            units="ha", valid_fraction=0.97, reliability="ok"))
    trend, _ = change.analyse(obs)
    assert trend.breakpoint is not None
    assert trend.slope_after > 2.0
    assert trend.current_rate_per_month == pytest.approx(3.0, rel=0.25)
