"""Geometry tests against closed-form answers.

These are the tests that matter most: an area computation that is wrong by a
few percent produces findings that are wrong by a few percent, and nobody will
notice until an operator's surveyor does.
"""

import math

import numpy as np
import pytest

from minerva.geom import (Grid, buffer_ring, geodesic_area_ha, geodesic_area_m2,
                          points_in_ring, ring_from_bbox)


# WGS84 arc lengths at the equator, to build boxes of known size.
DEG_LON_EQUATOR_M = 111_319.4908   # a * pi/180
DEG_LAT_EQUATOR_M = 110_574.3888   # a(1-e^2) * pi/180


def test_square_area_at_equator():
    """A true 1000 m x 1000 m box at the equator is 100 ha to within 0.05%."""
    ring = ring_from_bbox(0.0, 0.0,
                          1000.0 / DEG_LON_EQUATOR_M,
                          1000.0 / DEG_LAT_EQUATOR_M)
    ha = geodesic_area_ha(ring)
    assert ha == pytest.approx(100.0, rel=0.0005), ha


def test_hemisphere_area():
    """Sanity bound: the northern hemisphere is half the ellipsoid's surface."""
    from minerva.geom import geodesic_area_m2
    ring = [(-180.0, 0.0), (-90.0, 0.0), (0.0, 0.0), (90.0, 0.0), (180.0, 0.0),
            (180.0, 90.0), (-180.0, 90.0), (-180.0, 0.0)]
    got = geodesic_area_m2(ring)
    expected = 5.100656e14 / 2.0        # WGS84 surface area / 2
    assert got == pytest.approx(expected, rel=0.001), got


def test_area_shrinks_with_latitude():
    """The same degree box at 60 N covers the exact ellipsoidal fraction.

    Checked against the closed form M(phi)·N(phi)·cos(phi), not against the
    spherical cos(phi) approximation — the spherical version is wrong by about
    1% here, and it is precisely the sort of "close enough" that puts a wrong
    number in a legal document.
    """
    a, f = 6378137.0, 1 / 298.257223563
    e2 = f * (2 - f)

    def meridian_radius(p):
        s = math.sin(p)
        return a * (1 - e2) / (1 - e2 * s * s) ** 1.5

    def prime_vertical(p):
        s = math.sin(p)
        return a / math.sqrt(1 - e2 * s * s)

    box = ring_from_bbox(0.0, 0.0, 0.01, 0.01)
    box60 = ring_from_bbox(0.0, 60.0, 0.01, 60.01)
    ratio = geodesic_area_m2(box60) / geodesic_area_m2(box)

    p0, p60 = math.radians(0.005), math.radians(60.005)
    expected = ((meridian_radius(p60) * prime_vertical(p60) * math.cos(p60))
                / (meridian_radius(p0) * prime_vertical(p0) * math.cos(p0)))
    assert ratio == pytest.approx(expected, rel=1e-6), (ratio, expected)


def test_area_is_winding_independent():
    ring = ring_from_bbox(-56.2, -6.5, -56.1, -6.4)
    assert geodesic_area_m2(ring) == pytest.approx(geodesic_area_m2(ring[::-1]))


def test_point_in_ring():
    ring = ring_from_bbox(0.0, 0.0, 1.0, 1.0)
    lons = np.array([0.5, 1.5, -0.5, 0.99])
    lats = np.array([0.5, 0.5, 0.5, 0.01])
    got = points_in_ring(lons, lats, ring)
    assert got.tolist() == [True, False, False, True]


def test_point_in_concave_ring():
    """An L shape: the notch must not be counted as inside."""
    ring = [(0, 0), (2, 0), (2, 1), (1, 1), (1, 2), (0, 2), (0, 0)]
    lons = np.array([0.5, 1.5, 1.5, 0.5])
    lats = np.array([0.5, 0.5, 1.5, 1.5])
    got = points_in_ring(lons, lats, ring)
    assert got.tolist() == [True, True, False, True]


def test_grid_area_matches_geodesic():
    ring = ring_from_bbox(-56.20, -6.50, -56.15, -6.45)
    grid = Grid.covering(ring, pixel_m=10.0, margin_m=0.0)
    mask = grid.rasterize(ring)
    assert grid.area_ha(mask) == pytest.approx(geodesic_area_ha(ring), rel=0.01)


def test_grid_area_accounts_for_latitude():
    """A grid built at 60 N must not report equatorial pixel areas."""
    ring = ring_from_bbox(10.0, 60.0, 10.05, 60.03)
    grid = Grid.covering(ring, pixel_m=20.0, margin_m=0.0)
    mask = grid.rasterize(ring)
    assert grid.area_ha(mask) == pytest.approx(geodesic_area_ha(ring), rel=0.02)


def test_buffer_out_and_in():
    ring = ring_from_bbox(-56.20, -6.50, -56.10, -6.40)
    a = geodesic_area_ha(ring)
    out = geodesic_area_ha(buffer_ring(ring, 200.0))
    inn = geodesic_area_ha(buffer_ring(ring, -200.0))
    assert out > a > inn > 0
    # For a rectangle, a d-metre offset adds perimeter*d + 4d^2 of area.
    per_m = 2 * (0.10 * 111_320 * math.cos(math.radians(-6.45)) + 0.10 * 111_320)
    expected_gain_ha = (per_m * 200.0 + 4 * 200.0 ** 2) / 10_000.0
    assert (out - a) == pytest.approx(expected_gain_ha, rel=0.05)


def test_buffer_symmetry():
    """Buffering out then in returns approximately the original area."""
    ring = ring_from_bbox(-56.20, -6.50, -56.10, -6.40)
    roundtrip = buffer_ring(buffer_ring(ring, 150.0), -150.0)
    assert geodesic_area_ha(roundtrip) == pytest.approx(
        geodesic_area_ha(ring), rel=0.01)
