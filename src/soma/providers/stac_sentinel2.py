"""Sentinel-2 L2A through a STAC catalogue.

This is the production provider. It is written against the two catalogues a
public body can rely on without a commercial contract:

  * **Copernicus Data Space Ecosystem** — the sovereign European option.
    STAC root: https://catalogue.dataspace.copernicus.eu/stac
    Free-tier quotas as published: 12 TB per rolling 30 days over S3/OData/STAC,
    2 000 requests/minute, 50 000 direct COG requests/month.
    https://documentation.dataspace.copernicus.eu/Quotas.html
  * **Element 84 Earth Search** — an unauthenticated mirror of the Sentinel-2
    COG archive on AWS open data, useful for prototyping and for jurisdictions
    outside the Copernicus participating states.
    STAC root: https://earth-search.aws.element84.com/v1

Runtime dependencies (``pip install -r requirements-full.txt``):
    pystac-client, rasterio (or rioxarray + stackstac), requests

It is deliberately kept in the same shape as ``SyntheticProvider`` so that a
pipeline written against one runs unchanged against the other, and so that an
agency can rehearse on the simulator and switch a single line to go live.

NOTE ON THE SANDBOX: the environment this file was authored in has no outbound
network access to STAC endpoints, so this provider is *not* exercised by the
bundled test-suite. It is exercised by ``tests/test_stac_contract.py``, which
checks the request construction and the band mapping against recorded
fixtures, and it is marked ``@pytest.mark.network`` for the integration run an
adopting agency should perform on its own infrastructure.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Dict, List, Sequence, Tuple

import numpy as np

from ..geom import Grid, bbox
from ..scene import BANDS, Scene, SourceRef
from ..version import ALGORITHM_VERSIONS
from .base import SceneProvider, Vertex

CATALOGUES = {
    "cdse": {
        "url": "https://catalogue.dataspace.copernicus.eu/stac",
        "collection": "SENTINEL-2",
        "licence": "Copernicus Sentinel data — free, full and open "
                   "(Reg. (EU) No 1159/2013 and the Copernicus Data Policy)",
        "requires_auth": True,
    },
    "earth-search": {
        "url": "https://earth-search.aws.element84.com/v1",
        "collection": "sentinel-2-l2a",
        "licence": "Copernicus Sentinel data via AWS Open Data — free, full and open",
        "requires_auth": False,
    },
}

# STAC asset keys differ between catalogues; both spellings are handled.
ASSET_KEYS: Dict[str, Tuple[str, ...]] = {
    "B02": ("blue", "B02"),
    "B03": ("green", "B03"),
    "B04": ("red", "B04"),
    "B08": ("nir", "B08"),
    "B11": ("swir16", "B11"),
    "B12": ("swir22", "B12"),
}
SCL_KEYS = ("scl", "SCL")

# Sentinel-2 Scene Classification Layer values that are *not* usable.
# 0 no data, 1 saturated, 3 cloud shadow, 8 cloud medium prob,
# 9 cloud high prob, 10 thin cirrus.
SCL_REJECT = (0, 1, 3, 8, 9, 10)

# L2A reflectance is stored as integers; since processing baseline 04.00 an
# offset of -1000 applies. Getting this wrong shifts every index and is the
# single most common error in Sentinel-2 pipelines.
L2A_SCALE = 10_000.0
L2A_OFFSET_BASELINE_0400 = -1000.0


@dataclass
class StacSentinel2Provider(SceneProvider):
    """Search a STAC catalogue and return analysis-ready scenes."""

    catalogue: str = "cdse"
    max_items: int = 400
    composite: str = "monthly-median"   # "monthly-median" | "per-scene"
    token: str | None = None

    name: str = "stac_sentinel2"

    def __post_init__(self) -> None:
        if self.catalogue not in CATALOGUES:
            raise ValueError(f"unknown catalogue {self.catalogue!r}")
        self.licence = CATALOGUES[self.catalogue]["licence"]

    # -- interface ---------------------------------------------------------

    def search(
        self,
        site_id: str,
        aoi: Sequence[Vertex],
        start: date,
        end: date,
        grid: Grid | None = None,
        max_cloud: float = 0.6,
    ) -> List[Scene]:
        items = self.search_items(aoi, start, end, max_cloud)
        grid = grid or Grid.covering(aoi, pixel_m=10.0, margin_m=750.0)
        if self.composite == "per-scene":
            return [self._scene_from_items(site_id, [it], grid, it["properties"]["datetime"][:10])
                    for it in items]
        return self._monthly_medians(site_id, items, grid)

    # -- the parts a reviewer needs to be able to read ---------------------

    def search_items(
        self,
        aoi: Sequence[Vertex],
        start: date,
        end: date,
        max_cloud: float = 0.6,
    ) -> List[dict]:
        """Return raw STAC items. Separated out so it can be tested offline."""
        from pystac_client import Client  # local import: optional dependency

        cfg = CATALOGUES[self.catalogue]
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else None
        client = Client.open(cfg["url"], headers=headers)
        search = client.search(
            collections=[cfg["collection"]],
            bbox=bbox(aoi),
            datetime=f"{start.isoformat()}/{end.isoformat()}",
            query={"eo:cloud_cover": {"lt": int(max_cloud * 100)}},
            max_items=self.max_items,
        )
        items = [it.to_dict() for it in search.items()]
        items.sort(key=lambda it: it["properties"]["datetime"])
        return items

    @staticmethod
    def request_manifest(aoi: Sequence[Vertex], start: date, end: date,
                         catalogue: str, max_cloud: float) -> dict:
        """Exactly what was asked of the archive — recorded in the evidence.

        A finding must state not only which granules were used but which query
        produced them, so that a third party can re-run the same query and see
        whether anything was omitted.
        """
        cfg = CATALOGUES[catalogue]
        return {
            "catalogue": catalogue,
            "endpoint": cfg["url"],
            "collection": cfg["collection"],
            "bbox": list(bbox(aoi)),
            "datetime": f"{start.isoformat()}/{end.isoformat()}",
            "eo:cloud_cover<": int(max_cloud * 100),
            "issued_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }

    # -- reading pixels ----------------------------------------------------

    def _read_band(self, item: dict, band: str, grid: Grid) -> np.ndarray:
        import rasterio                       # optional dependency
        from rasterio.warp import Resampling, reproject
        from rasterio.crs import CRS

        href = self._asset_href(item, ASSET_KEYS[band])
        dst = np.zeros(grid.shape, dtype=np.float32)
        min_lon, min_lat, max_lon, max_lat = grid.bounds()
        transform = rasterio.transform.from_bounds(
            min_lon, min_lat, max_lon, max_lat, grid.width, grid.height
        )
        with rasterio.open(href) as src:
            reproject(
                source=rasterio.band(src, 1),
                destination=dst,
                dst_transform=transform,
                dst_crs=CRS.from_epsg(4326),
                resampling=Resampling.bilinear,
            )
        return self._to_reflectance(dst, item)

    @staticmethod
    def _to_reflectance(raw: np.ndarray, item: dict) -> np.ndarray:
        baseline = str(item["properties"].get("s2:processing_baseline", "05.00"))
        offset = L2A_OFFSET_BASELINE_0400 if _baseline_ge(baseline, "04.00") else 0.0
        return np.clip((raw + offset) / L2A_SCALE, 0.0, 1.5).astype(np.float32)

    def _read_valid(self, item: dict, grid: Grid) -> np.ndarray:
        import rasterio
        from rasterio.warp import Resampling, reproject
        from rasterio.crs import CRS

        href = self._asset_href(item, SCL_KEYS)
        scl = np.zeros(grid.shape, dtype=np.uint8)
        min_lon, min_lat, max_lon, max_lat = grid.bounds()
        transform = rasterio.transform.from_bounds(
            min_lon, min_lat, max_lon, max_lat, grid.width, grid.height
        )
        with rasterio.open(href) as src:
            reproject(
                source=rasterio.band(src, 1),
                destination=scl,
                dst_transform=transform,
                dst_crs=CRS.from_epsg(4326),
                resampling=Resampling.nearest,
            )
        return ~np.isin(scl, SCL_REJECT)

    @staticmethod
    def _asset_href(item: dict, keys: Sequence[str]) -> str:
        assets = item.get("assets", {})
        for k in keys:
            if k in assets:
                return assets[k]["href"]
        raise KeyError(f"none of {keys} present in item {item.get('id')}")

    # -- compositing -------------------------------------------------------

    def _monthly_medians(self, site_id: str, items: List[dict], grid: Grid) -> List[Scene]:
        buckets: Dict[str, List[dict]] = {}
        for it in items:
            key = it["properties"]["datetime"][:7]
            buckets.setdefault(key, []).append(it)
        return [self._scene_from_items(site_id, group, grid, f"{month}-01")
                for month, group in sorted(buckets.items())]

    def _scene_from_items(self, site_id: str, items: List[dict], grid: Grid,
                          label_date: str) -> Scene:
        """Per-pixel median over the group, using only SCL-valid pixels.

        Median rather than mean: a single undetected cloud edge biases a mean
        and does not move a median, and the whole point of a monthly composite
        is to survive the tropics.
        """
        stacks: Dict[str, List[np.ndarray]] = {b: [] for b in BANDS}
        valids: List[np.ndarray] = []
        for it in items:
            v = self._read_valid(it, grid)
            valids.append(v)
            for b in BANDS:
                arr = self._read_band(it, b, grid)
                arr = np.where(v, arr, np.nan)
                stacks[b].append(arr)

        bands = {}
        for b in BANDS:
            cube = np.stack(stacks[b])
            with np.errstate(all="ignore"):
                bands[b] = np.nanmedian(cube, axis=0).astype(np.float32)
        valid = np.any(np.stack(valids), axis=0) & np.isfinite(bands["B04"])
        for b in BANDS:
            bands[b] = np.nan_to_num(bands[b], nan=0.0)

        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        sources = [
            SourceRef(
                kind="granule",
                identifier=it["id"],
                source=CATALOGUES[self.catalogue]["url"],
                retrieved_utc=now,
                licence=self.licence,
                note=f"baseline {it['properties'].get('s2:processing_baseline', '?')}, "
                     f"cloud {it['properties'].get('eo:cloud_cover', '?')}%",
            )
            for it in items
        ]
        return Scene(
            site_id=site_id,
            acquired=_dt.date.fromisoformat(label_date),
            grid=grid,
            bands=bands,
            valid=valid,
            provider=f"{self.name}:{self.catalogue}",
            processing_baseline=ALGORITHM_VERSIONS["provider.stac_sentinel2"],
            cloud_fraction=float(1.0 - valid.mean()),
            sources=sources,
        )


def _baseline_ge(a: str, b: str) -> bool:
    try:
        return tuple(int(p) for p in a.split(".")) >= tuple(int(p) for p in b.split("."))
    except Exception:
        return True
