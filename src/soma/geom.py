"""Geometry on the ellipsoid, without a geospatial stack.

Everything here works on lists of (lon, lat) vertices in decimal degrees,
WGS84. Three operations are needed by the rest of the library and no more:

  * area of a polygon, in hectares, accurate enough for a legal document;
  * membership of raster cells in a polygon (rasterisation);
  * a local metric grid so that a scene has a defined pixel size on the ground.

Why not shapely/pyproj: those are excellent and should be used in production
(see ``requirements-full.txt``). But a public body must be able to reproduce a
finding on an unprivileged machine with numpy alone, and the reviewer of a
finding must be able to read the area computation rather than trust a binary.
The implementations below are the textbook ones and are unit-tested against
closed-form cases.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

import numpy as np

# WGS84
_A = 6378137.0                 # semi-major axis, metres
_F = 1.0 / 298.257223563       # flattening
_E2 = _F * (2.0 - _F)          # first eccentricity squared

Vertex = Tuple[float, float]


# --------------------------------------------------------------------------
# Area
# --------------------------------------------------------------------------

def geodesic_area_m2(ring: Sequence[Vertex]) -> float:
    """Area of a simple polygon on the WGS84 ellipsoid, in square metres.

    Each geodetic latitude is first converted to its **authalic** latitude —
    the latitude on the equal-area sphere that subtends the same area from the
    equator — and the spherical-excess integral is then evaluated on the
    authalic sphere. That construction is area-exact for the ellipsoid; the
    only residual error comes from treating edges as great circles rather than
    geodesics, which for edges of a few kilometres is far below a millionth.

    Doing the naive thing instead (spherical excess on geodetic latitudes with
    a mean radius) costs about 0.6% at the equator. On a 40 ha finding that is
    a quarter of a hectare of nothing, and it is the sort of error an expert
    witness is paid to find.

    The ring may be open or closed and may be given in either winding order;
    the result is always positive.
    """
    pts = _close(ring)
    if len(pts) < 4:
        return 0.0

    r = _authalic_radius()
    total = 0.0
    for (lon1, lat1), (lon2, lat2) in zip(pts[:-1], pts[1:]):
        l1 = math.radians(lon1)
        l2 = math.radians(lon2)
        b1 = _authalic_latitude(math.radians(lat1))
        b2 = _authalic_latitude(math.radians(lat2))
        dl = l2 - l1
        # keep the shortest way round, so a polygon spanning the antimeridian
        # is not mistaken for one that wraps the globe
        if dl > math.pi:
            dl -= 2 * math.pi
        elif dl < -math.pi:
            dl += 2 * math.pi
        total += dl * (2.0 + math.sin(b1) + math.sin(b2))
    return abs(total * r * r / 2.0)


def geodesic_area_ha(ring: Sequence[Vertex]) -> float:
    """Polygon area in hectares."""
    return geodesic_area_m2(ring) / 10_000.0


def _q(sin_phi: float) -> float:
    e = math.sqrt(_E2)
    es = e * sin_phi
    return (1.0 - _E2) * (
        sin_phi / (1.0 - es * es)
        - (1.0 / (2.0 * e)) * math.log((1.0 - es) / (1.0 + es))
    )


def _authalic_latitude(phi: float) -> float:
    qp = _q(1.0)
    ratio = max(-1.0, min(1.0, _q(math.sin(phi)) / qp))
    return math.asin(ratio)


def _authalic_radius() -> float:
    # R_q = a * sqrt(q_p / 2): the radius of the sphere with the ellipsoid's
    # surface area.
    return _A * math.sqrt(_q(1.0) / 2.0)


def _close(ring: Sequence[Vertex]) -> List[Vertex]:
    pts = [(float(x), float(y)) for x, y in ring]
    if not pts:
        return []
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    return pts


# --------------------------------------------------------------------------
# Point in polygon
# --------------------------------------------------------------------------

def points_in_ring(lons: np.ndarray, lats: np.ndarray, ring: Sequence[Vertex]) -> np.ndarray:
    """Vectorised even-odd (ray casting) test.

    ``lons``/``lats`` are arrays of any matching shape; the return is a boolean
    array of that shape. Points exactly on an edge are not guaranteed either
    way — for a legal application always report a boundary buffer alongside the
    inside/outside split rather than relying on the knife edge (see
    ``crosscheck.cadastre.BOUNDARY_TOLERANCE_M``).
    """
    pts = _close(ring)
    if len(pts) < 4:
        return np.zeros(np.shape(lons), dtype=bool)

    x = np.asarray(lons, dtype=float)
    y = np.asarray(lats, dtype=float)
    inside = np.zeros(x.shape, dtype=bool)

    for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
        if y1 == y2:
            continue
        # Does a ray cast in +x from the point cross this edge?
        crosses_band = ((y1 > y) != (y2 > y))
        with np.errstate(divide="ignore", invalid="ignore"):
            x_at_y = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
        inside ^= crosses_band & (x < x_at_y)
    return inside


def polygon_with_holes_mask(
    lons: np.ndarray,
    lats: np.ndarray,
    shell: Sequence[Vertex],
    holes: Iterable[Sequence[Vertex]] = (),
) -> np.ndarray:
    mask = points_in_ring(lons, lats, shell)
    for hole in holes:
        mask &= ~points_in_ring(lons, lats, hole)
    return mask


def bbox(ring: Sequence[Vertex]) -> Tuple[float, float, float, float]:
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return min(xs), min(ys), max(xs), max(ys)


def centroid(ring: Sequence[Vertex]) -> Vertex:
    pts = _close(ring)[:-1]
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


# --------------------------------------------------------------------------
# Local metric grid
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Grid:
    """A north-up raster grid defined in geographic coordinates.

    The grid is a local equirectangular approximation anchored at
    ``(origin_lon, origin_lat)``, the *upper-left* corner. Over a scene a few
    kilometres across this is indistinguishable from a proper UTM grid, and it
    keeps the whole pipeline free of a projection library. ``pixel_m`` is the
    nominal ground sample distance; Sentinel-2's 10 m bands give ``pixel_m=10``.
    """

    origin_lon: float
    origin_lat: float
    pixel_m: float
    width: int
    height: int

    # -- derived -----------------------------------------------------------
    @property
    def deg_per_pixel_lat(self) -> float:
        return self.pixel_m / 111_320.0

    @property
    def deg_per_pixel_lon(self) -> float:
        lat0 = math.radians(self.origin_lat)
        return self.pixel_m / (111_320.0 * max(math.cos(lat0), 1e-6))

    @property
    def pixel_area_ha(self) -> float:
        return (self.pixel_m ** 2) / 10_000.0

    @property
    def shape(self) -> Tuple[int, int]:
        return self.height, self.width

    def lonlat(self) -> Tuple[np.ndarray, np.ndarray]:
        """Cell-centre longitude and latitude arrays of shape (height, width)."""
        cols = np.arange(self.width, dtype=float) + 0.5
        rows = np.arange(self.height, dtype=float) + 0.5
        lon = self.origin_lon + cols * self.deg_per_pixel_lon
        lat = self.origin_lat - rows * self.deg_per_pixel_lat
        return np.meshgrid(lon, lat)

    def bounds(self) -> Tuple[float, float, float, float]:
        """(min_lon, min_lat, max_lon, max_lat)."""
        max_lon = self.origin_lon + self.width * self.deg_per_pixel_lon
        min_lat = self.origin_lat - self.height * self.deg_per_pixel_lat
        return self.origin_lon, min_lat, max_lon, self.origin_lat

    def rasterize(self, shell: Sequence[Vertex], holes: Iterable[Sequence[Vertex]] = ()) -> np.ndarray:
        lon, lat = self.lonlat()
        return polygon_with_holes_mask(lon, lat, shell, holes)

    def area_ha(self, mask: np.ndarray) -> float:
        """Ground area of a boolean mask, in hectares.

        Latitude convergence is accounted for row by row: at the equator the
        difference is nil, at 60 degrees it is a factor of two, and a finding
        that got that wrong would be indefensible.
        """
        mask = np.asarray(mask, dtype=bool)
        rows = np.arange(self.height, dtype=float) + 0.5
        lat = self.origin_lat - rows * self.deg_per_pixel_lat
        row_area_m2 = (self.pixel_m ** 2) * np.cos(np.radians(lat)) / max(
            math.cos(math.radians(self.origin_lat)), 1e-6
        )
        per_row = mask.sum(axis=1) * row_area_m2
        return float(per_row.sum() / 10_000.0)

    @classmethod
    def covering(
        cls,
        ring: Sequence[Vertex],
        pixel_m: float = 10.0,
        margin_m: float = 500.0,
    ) -> "Grid":
        """Smallest grid covering ``ring`` plus a margin.

        The margin matters: unlicensed extraction characteristically appears
        just *outside* the licence boundary, so a scene clipped to the licence
        is a scene that cannot see the offence.
        """
        min_lon, min_lat, max_lon, max_lat = bbox(ring)
        lat0 = (min_lat + max_lat) / 2.0
        dlat = margin_m / 111_320.0
        dlon = margin_m / (111_320.0 * max(math.cos(math.radians(lat0)), 1e-6))
        min_lon, max_lon = min_lon - dlon, max_lon + dlon
        min_lat, max_lat = min_lat - dlat, max_lat + dlat

        deg_lat = pixel_m / 111_320.0
        deg_lon = pixel_m / (111_320.0 * max(math.cos(math.radians(max_lat)), 1e-6))
        width = int(math.ceil((max_lon - min_lon) / deg_lon))
        height = int(math.ceil((max_lat - min_lat) / deg_lat))
        return cls(origin_lon=min_lon, origin_lat=max_lat, pixel_m=pixel_m,
                   width=width, height=height)


def ring_from_bbox(min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> List[Vertex]:
    return [
        (min_lon, min_lat),
        (max_lon, min_lat),
        (max_lon, max_lat),
        (min_lon, max_lat),
        (min_lon, min_lat),
    ]


def buffer_ring(ring: Sequence[Vertex], metres: float) -> List[Vertex]:
    """Offset a simple polygon by ``metres`` (positive out, negative in).

    Implemented as an edge-normal offset with adjacent-edge intersection, which
    is the exact Minkowski offset for a **convex** polygon. Mining titles are
    convex or near-convex almost everywhere — Brazilian polygons are defined by
    bearings and distances from a marked vertex and are usually rectangles —
    so this is the right trade for a dependency-free core.

    For a concave ring the offset corners can self-intersect. When the result
    is degenerate the function falls back to a radial scaling about the
    centroid and the caller should prefer shapely if it is available. This is
    documented rather than hidden because the boundary tolerance derived from
    it goes into legal findings.
    """
    pts = _close(ring)[:-1]
    if len(pts) < 3 or abs(metres) < 1e-9:
        return _close(ring)

    cx, cy = centroid(ring)
    m_lat = 111_320.0
    m_lon = 111_320.0 * max(math.cos(math.radians(cy)), 1e-6)

    P = [((x - cx) * m_lon, (y - cy) * m_lat) for x, y in pts]
    if _shoelace(P) < 0:                      # force counter-clockwise
        P = P[::-1]
        flipped = True
    else:
        flipped = False

    lines = []
    n = len(P)
    for i in range(n):
        (x0, y0), (x1, y1) = P[i], P[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy)
        if length < 1e-9:
            continue
        ux, uy = dx / length, dy / length
        nx, ny = uy, -ux                      # outward normal for CCW winding
        lines.append(((x0 + nx * metres, y0 + ny * metres), (ux, uy)))

    out_m = []
    for i in range(len(lines)):
        p, d = lines[i]
        q, e = lines[(i + 1) % len(lines)]
        cross = d[0] * e[1] - d[1] * e[0]
        if abs(cross) < 1e-9:                 # parallel edges: keep the endpoint
            out_m.append((p[0] + d[0] * 1e-6, p[1] + d[1] * 1e-6))
            continue
        t = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / cross
        out_m.append((p[0] + d[0] * t, p[1] + d[1] * t))

    if not out_m or not all(math.isfinite(v) for xy in out_m for v in xy):
        return _radial_buffer(ring, metres)
    if metres < 0 and _shoelace(out_m) <= 0:  # collapsed through itself
        return _radial_buffer(ring, metres)

    if flipped:
        out_m = out_m[::-1]
    out = [(cx + x / m_lon, cy + y / m_lat) for x, y in out_m]
    out.append(out[0])
    return out


def _shoelace(pts: Sequence[Tuple[float, float]]) -> float:
    s = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        s += x0 * y1 - x1 * y0
    return s / 2.0


def _radial_buffer(ring: Sequence[Vertex], metres: float) -> List[Vertex]:
    cx, cy = centroid(ring)
    m_lat = 111_320.0
    m_lon = 111_320.0 * max(math.cos(math.radians(cy)), 1e-6)
    out: List[Vertex] = []
    for x, y in _close(ring)[:-1]:
        ex, ny = (x - cx) * m_lon, (y - cy) * m_lat
        norm = math.hypot(ex, ny)
        if norm < 1e-9:
            out.append((x, y))
            continue
        new = norm + metres
        if new < 0.05 * norm:
            new = 0.05 * norm
        out.append((cx + (ex / norm) * new / m_lon, cy + (ny / norm) * new / m_lat))
    out.append(out[0])
    return out
