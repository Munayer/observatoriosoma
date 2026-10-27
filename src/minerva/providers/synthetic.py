"""A deterministic simulated site.

Why a simulator is part of the product, not a hack for the demo:

  1. **Testing.** A detector cannot be regression-tested against real imagery
     without shipping gigabytes and pinning an external service. Here the
     ground truth is known exactly, so a threshold change that costs 3 ha of
     recall shows up in CI.
  2. **Training and acceptance.** An agency evaluating the platform needs to
     see it find something it already knows the answer to before it trusts it
     on something it does not. Regulators are right to demand this.
  3. **Air-gapped operation.** The pipeline must be demonstrable with no
     network at all — in a prosecutor's office, in a hearing room, on a
     plane.

Spectra are plausible Sentinel-2 L2A surface reflectances for a humid-tropical
lateritic setting. They are *simulated*: every artefact this provider produces
is stamped ``provider="synthetic"``, and ``dossier`` refuses to issue a legal
notice from synthetic evidence.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Dict, List, Sequence, Tuple

import numpy as np

try:  # optional accelerator
    from scipy import ndimage as _ndi
except Exception:  # pragma: no cover
    _ndi = None

from ..geom import Grid
from ..scene import BANDS, Scene, SourceRef
from ..version import ALGORITHM_VERSIONS
from .base import SceneProvider, Vertex

# Surface reflectance signatures, [B02, B03, B04, B08, B11, B12]
SPECTRA: Dict[str, Tuple[float, ...]] = {
    "forest":       (0.020, 0.040, 0.025, 0.320, 0.140, 0.060),
    "pasture":      (0.035, 0.060, 0.055, 0.280, 0.220, 0.120),
    "bare_soil":    (0.090, 0.120, 0.180, 0.260, 0.340, 0.300),
    "waste_rock":   (0.120, 0.150, 0.190, 0.230, 0.300, 0.270),
    "water_clear":  (0.045, 0.040, 0.025, 0.012, 0.006, 0.004),
    "water_tailing":(0.090, 0.120, 0.150, 0.080, 0.030, 0.020),
    "cloud":        (0.780, 0.800, 0.810, 0.820, 0.640, 0.520),
}


@dataclass
class SyntheticSite:
    """Parameters of the simulated mine."""

    site_id: str = "DEMO-001"
    centre_lon: float = -56.1200
    centre_lat: float = -6.4500
    pixel_m: float = 10.0
    width: int = 440
    height: int = 440
    seed: int = 20260819

    # licence polygon, as a fraction of the scene (left, bottom, right, top)
    licence_frac: Tuple[float, float, float, float] = (0.16, 0.18, 0.62, 0.70)

    # pit growth, in hectares, as (date, area) control points
    # Two regimes: routine expansion at about 0.7 ha/month, then a step change
    # in July 2025 to about 4.5 ha/month — the pattern a fleet expansion or a
    # change of contractor produces, and the one a rate-change test should find.
    growth: Sequence[Tuple[str, float]] = (
        ("2023-01-01", 11.0),
        ("2024-01-01", 19.5),
        ("2025-01-01", 28.0),
        ("2025-07-01", 32.5),
        ("2026-07-01", 86.5),
    )
    # Two months into the acceleration the working face runs out of room inside
    # the licence and crosses the boundary to the north-east.
    breakout_date: str = "2025-09-01"
    tailings_area_ha: float = 21.0
    river: bool = True


class SyntheticProvider(SceneProvider):
    """Generates monthly median composites for a simulated site."""

    name = "synthetic"
    licence = "simulation — not evidence"

    def __init__(self, site: SyntheticSite | None = None) -> None:
        self.site = site or SyntheticSite()
        self._rng = np.random.default_rng(self.site.seed)
        self._grid = Grid(
            origin_lon=self.site.centre_lon
            - (self.site.width / 2) * self.site.pixel_m
            / (111_320.0 * math.cos(math.radians(self.site.centre_lat))),
            origin_lat=self.site.centre_lat
            + (self.site.height / 2) * self.site.pixel_m / 111_320.0,
            pixel_m=self.site.pixel_m,
            width=self.site.width,
            height=self.site.height,
        )
        self._static = self._build_static_layers()

    # -- public API --------------------------------------------------------

    @property
    def grid(self) -> Grid:
        return self._grid

    def licence_ring(self) -> List[Vertex]:
        l, b, r, t = self.site.licence_frac
        min_lon, min_lat, max_lon, max_lat = self._grid.bounds()
        w = max_lon - min_lon
        h = max_lat - min_lat
        return [
            (min_lon + l * w, min_lat + b * h),
            (min_lon + r * w, min_lat + b * h),
            (min_lon + r * w, min_lat + t * h),
            (min_lon + l * w, min_lat + t * h),
            (min_lon + l * w, min_lat + b * h),
        ]

    def protected_area_ring(self) -> List[Vertex]:
        """A conservation unit abutting the licence on the north-east."""
        min_lon, min_lat, max_lon, max_lat = self._grid.bounds()
        w = max_lon - min_lon
        h = max_lat - min_lat
        return [
            (min_lon + 0.58 * w, min_lat + 0.55 * h),
            (min_lon + 0.99 * w, min_lat + 0.55 * h),
            (min_lon + 0.99 * w, min_lat + 0.99 * h),
            (min_lon + 0.58 * w, min_lat + 0.99 * h),
            (min_lon + 0.58 * w, min_lat + 0.55 * h),
        ]

    def search(
        self,
        site_id: str,
        aoi: Sequence[Vertex],
        start: date,
        end: date,
        grid: Grid | None = None,
        max_cloud: float = 0.6,
    ) -> List[Scene]:
        del aoi, grid  # the simulator owns its own geometry
        scenes: List[Scene] = []
        for d in _month_starts(start, end):
            scene = self._render(site_id, d)
            scenes.append(scene)
        return scenes

    def truth(self, when: date) -> Dict[str, float]:
        """Ground truth for tests: the areas the simulator actually drew."""
        pit = self._pit_mask(when)
        tail = self._static["tailings"]
        return {
            "pit_ha": self._grid.area_ha(pit),
            "tailings_ha": self._grid.area_ha(tail),
            "disturbed_ha": self._grid.area_ha(pit | self._static["waste"] | self._static["roads"]),
        }

    def dem_pair(self, before: date, after: date) -> Tuple[np.ndarray, np.ndarray]:
        """Two elevation surfaces, in metres, for volumetric differencing."""
        base = self._static["terrain"]
        return base - self._excavation_depth(before), base - self._excavation_depth(after)

    # -- construction ------------------------------------------------------

    def _build_static_layers(self) -> Dict[str, np.ndarray]:
        h, w = self._grid.shape
        rng = np.random.default_rng(self.site.seed)

        terrain = 180.0 + 40.0 * _fbm(rng, (h, w), octaves=5)
        veg = _smooth(rng.random((h, w)), 9)
        forest = veg > 0.42

        yy, xx = np.mgrid[0:h, 0:w]

        river = np.zeros((h, w), dtype=bool)
        if self.site.river:
            spine = (0.78 * w + 0.10 * w * np.sin(yy[:, 0] / h * 3.1 * math.pi)
                     + 0.03 * w * np.sin(yy[:, 0] / h * 9.7 * math.pi))
            river = np.abs(xx - spine[:, None]) < 3.0

        # tailings impoundment, south-west of the pit, inside the licence
        t_cy, t_cx = int(0.68 * h), int(0.30 * w)
        t_r = math.sqrt(self.site.tailings_area_ha * 10_000 / math.pi) / self.site.pixel_m
        tailings = ((yy - t_cy) ** 2 / (t_r * 0.85) ** 2
                    + (xx - t_cx) ** 2 / (t_r * 1.25) ** 2) < 1.0
        # its retaining embankment, on the downstream (south) side
        dam = (((yy - t_cy) ** 2 / (t_r * 1.05) ** 2 + (xx - t_cx) ** 2 / (t_r * 1.45) ** 2) < 1.0)
        dam &= ~tailings
        dam &= yy > t_cy

        # waste rock dumps
        w_cy, w_cx = int(0.34 * h), int(0.22 * w)
        w_r = 28.0
        waste = ((yy - w_cy) ** 2 + (xx - w_cx) ** 2) < w_r ** 2

        # haul roads: pit -> plant -> tailings, plus an access road to the north
        roads = np.zeros((h, w), dtype=bool)
        for (y0, x0, y1, x1) in [
            (int(0.44 * h), int(0.44 * w), t_cy, t_cx),
            (int(0.44 * h), int(0.44 * w), w_cy, w_cx),
            (int(0.44 * h), int(0.44 * w), 0, int(0.50 * w)),
        ]:
            roads |= _line_mask((h, w), y0, x0, y1, x1, half_width=2.0)

        return {
            "terrain": terrain,
            "forest": forest,
            "river": river,
            "tailings": tailings,
            "dam": dam,
            "waste": waste,
            "roads": roads,
        }

    # -- time-varying ------------------------------------------------------

    def _pit_area_ha(self, when: date) -> float:
        xs = [datetime.strptime(d, "%Y-%m-%d").date().toordinal() for d, _ in self.site.growth]
        ys = [a for _, a in self.site.growth]
        x = when.toordinal()
        return float(np.interp(x, xs, ys))

    def _pit_mask(self, when: date) -> np.ndarray:
        h, w = self._grid.shape
        yy, xx = np.mgrid[0:h, 0:w]
        px_area_ha = (self.site.pixel_m ** 2) / 10_000.0
        target_px = self._pit_area_ha(when) / px_area_ha

        cy, cx = 0.44 * h, 0.44 * w
        breakout = datetime.strptime(self.site.breakout_date, "%Y-%m-%d").date()

        if when < breakout:
            r = math.sqrt(target_px / math.pi)
            return ((yy - cy) ** 2 / (r * 0.92) ** 2 + (xx - cx) ** 2 / (r * 1.12) ** 2) < 1.0

        # After breakout the main pit keeps growing slowly while a second
        # working face opens to the north-east, crossing the licence line.
        at_breakout = self._pit_area_ha(breakout)
        main_ha = at_breakout + 0.35 * (self._pit_area_ha(when) - at_breakout)
        lobe_ha = self._pit_area_ha(when) - main_ha

        r1 = math.sqrt((main_ha / px_area_ha) / math.pi)
        main = ((yy - cy) ** 2 / (r1 * 0.92) ** 2 + (xx - cx) ** 2 / (r1 * 1.12) ** 2) < 1.0

        ly, lx = 0.30 * h, 0.70 * w
        r2 = math.sqrt((max(lobe_ha, 0.0) / px_area_ha) / math.pi)
        lobe = ((yy - ly) ** 2 / (max(r2, 1.0) * 1.05) ** 2
                + (xx - lx) ** 2 / (max(r2, 1.0) * 0.95) ** 2) < 1.0
        link = _line_mask((h, w), int(cy), int(cx), int(ly), int(lx), half_width=2.5)
        return main | lobe | (link & (r2 > 4))

    def _excavation_depth(self, when: date) -> np.ndarray:
        """Depth removed, in metres — a bowl deepest at the pit centre."""
        pit = self._pit_mask(when)
        if _ndi is not None:
            dist = _ndi.distance_transform_edt(pit)
        else:  # pragma: no cover
            dist = pit.astype(float)
        if dist.max() <= 0:
            return np.zeros_like(dist)
        # 15 m bench height per 100 m of horizontal distance from the rim,
        # capped at a 90 m pit depth.
        return np.minimum(dist * self.site.pixel_m * 0.15, 90.0)

    def _cloud_mask(self, when: date, rng: np.random.Generator) -> np.ndarray:
        """Residual cloud in a monthly median composite.

        A single Sentinel-2 acquisition over the southern Amazon in February is
        usually unusable. A monthly median of five or six acquisitions is
        usually usable, and that is why the pipeline composites. What is left
        is the residual: persistent cloud that never cleared over part of the
        scene, plus the occasional month that is a total loss.
        """
        h, w = self._grid.shape
        wet = when.month in (11, 12, 1, 2, 3, 4)
        if wet and rng.random() < 0.09:
            target = rng.uniform(0.80, 0.98)      # a month that never cleared
        elif wet:
            target = rng.uniform(0.04, 0.38)
        else:
            target = rng.uniform(0.0, 0.10)
        if target <= 0.005:
            return np.zeros((h, w), dtype=bool)
        field = _smooth(rng.random((h, w)), 25)
        return field > np.quantile(field, 1.0 - target)

    def _render(self, site_id: str, when: date) -> Scene:
        h, w = self._grid.shape
        rng = np.random.default_rng(self.site.seed + when.toordinal())
        s = self._static

        pit = self._pit_mask(when)
        # classes, later ones win
        classes = np.full((h, w), "pasture", dtype=object)
        classes[s["forest"]] = "forest"
        classes[s["river"]] = "water_clear"
        classes[s["roads"]] = "bare_soil"
        classes[s["waste"]] = "waste_rock"
        classes[s["dam"]] = "waste_rock"
        classes[s["tailings"]] = "water_tailing"
        classes[pit] = "bare_soil"

        bands = {b: np.zeros((h, w), dtype=np.float32) for b in BANDS}
        for label, spec in SPECTRA.items():
            m = classes == label
            if not m.any():
                continue
            for i, b in enumerate(BANDS):
                bands[b][m] = spec[i]

        # texture, illumination and a mild seasonal greening cycle
        shade = 1.0 + 0.06 * _fbm(rng, (h, w), octaves=4)
        season = 1.0 + 0.05 * math.sin((when.month - 3) / 12.0 * 2 * math.pi)
        for b in BANDS:
            noise = 1.0 + 0.035 * rng.standard_normal((h, w)).astype(np.float32)
            bands[b] = np.clip(bands[b] * shade * noise, 0.0, 1.2).astype(np.float32)
            if b in ("B08",):
                bands[b] = np.clip(bands[b] * season, 0.0, 1.2).astype(np.float32)

        cloud = self._cloud_mask(when, rng)
        shadow = np.zeros_like(cloud)
        if cloud.any():
            shadow = np.roll(np.roll(cloud, 9, axis=0), -6, axis=1) & ~cloud
        for i, b in enumerate(BANDS):
            bands[b][cloud] = SPECTRA["cloud"][i] * (0.9 + 0.2 * rng.random(cloud.sum()))
            bands[b][shadow] *= 0.35

        valid = ~(cloud | shadow)
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return Scene(
            site_id=site_id,
            acquired=when,
            grid=self._grid,
            bands=bands,
            valid=valid,
            provider=self.name,
            processing_baseline="synthetic/" + ALGORITHM_VERSIONS["provider.synthetic"],
            cloud_fraction=float(cloud.mean()),
            sources=[
                SourceRef(
                    kind="granule",
                    identifier=f"SYNTH_{site_id}_{when.isoformat()}",
                    source="minerva.providers.synthetic",
                    retrieved_utc=now,
                    licence="simulation — not evidence",
                    note="deterministic simulation, seed "
                         f"{self.site.seed + when.toordinal()}",
                )
            ],
        )


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def _month_starts(start: date, end: date) -> List[date]:
    out = []
    y, m = start.year, start.month
    while date(y, m, 1) <= end:
        d = date(y, m, 1)
        if d >= start:
            out.append(d)
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return out


def _smooth(a: np.ndarray, sigma: float) -> np.ndarray:
    if _ndi is not None:
        return _ndi.gaussian_filter(a.astype(float), sigma)
    # separable box blur fallback
    out = a.astype(float)
    k = max(int(sigma), 1)
    for axis in (0, 1):
        c = np.cumsum(np.pad(out, [(k, k) if ax == axis else (0, 0) for ax in (0, 1)],
                             mode="edge"), axis=axis)
        sl_hi = [slice(None)] * 2
        sl_lo = [slice(None)] * 2
        sl_hi[axis] = slice(2 * k, None)
        sl_lo[axis] = slice(0, -2 * k)
        out = (c[tuple(sl_hi)] - c[tuple(sl_lo)]) / (2 * k)
    return out


def _fbm(rng: np.random.Generator, shape: Tuple[int, int], octaves: int = 5) -> np.ndarray:
    """Fractional Brownian motion — smooth terrain-like noise in [-1, 1]."""
    total = np.zeros(shape, dtype=float)
    amp, sigma = 1.0, max(shape) / 6.0
    norm = 0.0
    for _ in range(octaves):
        total += amp * _smooth(rng.standard_normal(shape), sigma)
        norm += amp
        amp *= 0.55
        sigma = max(sigma / 2.0, 1.0)
    total /= max(norm, 1e-9)
    m = np.abs(total).max()
    return total / max(m, 1e-9)


def _line_mask(shape: Tuple[int, int], y0: int, x0: int, y1: int, x1: int,
               half_width: float = 2.0) -> np.ndarray:
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w]
    dy, dx = y1 - y0, x1 - x0
    length2 = dy * dy + dx * dx
    if length2 == 0:
        return ((yy - y0) ** 2 + (xx - x0) ** 2) < half_width ** 2
    t = np.clip(((yy - y0) * dy + (xx - x0) * dx) / length2, 0.0, 1.0)
    py, px = y0 + t * dy, x0 + t * dx
    return ((yy - py) ** 2 + (xx - px) ** 2) < half_width ** 2
