"""The unit of observation: one cloud-screened, georeferenced image stack."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

import numpy as np

from .geom import Grid

# The six Sentinel-2 bands this library needs. Deliberately a small set: every
# detector here is explainable from these, and restricting the input keeps the
# method portable to Landsat 8/9 (which carries equivalents of all six).
BANDS = ("B02", "B03", "B04", "B08", "B11", "B12")
BAND_LABELS = {
    "B02": "blue 490 nm",
    "B03": "green 560 nm",
    "B04": "red 665 nm",
    "B08": "NIR 842 nm",
    "B11": "SWIR-1 1610 nm",
    "B12": "SWIR-2 2190 nm",
}


@dataclass
class SourceRef:
    """One traceable input. This is what makes a finding auditable."""

    kind: str                      # "granule" | "dataset" | "declaration" | "vector"
    identifier: str                # e.g. S2A_MSIL2A_20260114T140711_N0511_R010_T21MYT
    source: str                    # publisher or endpoint
    retrieved_utc: str
    licence: str = ""
    checksum: str = ""             # sha256 of the bytes as received, where available
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "identifier": self.identifier,
            "source": self.source,
            "retrieved_utc": self.retrieved_utc,
            "licence": self.licence,
            "checksum": self.checksum,
            "note": self.note,
        }


@dataclass
class Scene:
    """Surface reflectance for one acquisition date over one site.

    ``bands`` values are float arrays in [0, 1] surface reflectance, all
    resampled to ``grid``. ``valid`` is True where the pixel is usable — i.e.
    not cloud, not cloud shadow, not saturated, not outside the granule. Every
    area figure this library reports is accompanied by the valid fraction that
    produced it, because an area measured through a hole in the clouds is not
    the same claim as an area measured on a clear day.
    """

    site_id: str
    acquired: date
    grid: Grid
    bands: Dict[str, np.ndarray]
    valid: np.ndarray
    provider: str
    sources: List[SourceRef] = field(default_factory=list)
    processing_baseline: str = ""
    cloud_fraction: Optional[float] = None

    def __post_init__(self) -> None:
        for name in BANDS:
            if name not in self.bands:
                raise ValueError(f"scene is missing band {name}")
            if self.bands[name].shape != self.grid.shape:
                raise ValueError(
                    f"band {name} has shape {self.bands[name].shape}, "
                    f"grid is {self.grid.shape}"
                )
        if self.valid.shape != self.grid.shape:
            raise ValueError("valid mask shape does not match grid")

    @property
    def valid_fraction(self) -> float:
        return float(self.valid.mean())

    def band(self, name: str) -> np.ndarray:
        return self.bands[name]

    def digest(self) -> str:
        """Content hash of the pixel data actually used.

        Recomputed from the arrays rather than trusted from the provider, so a
        reviewer can verify that the imagery behind a finding is the imagery
        the manifest names.
        """
        h = hashlib.sha256()
        h.update(self.site_id.encode())
        h.update(self.acquired.isoformat().encode())
        for name in BANDS:
            arr = np.ascontiguousarray(self.bands[name].astype(np.float32))
            h.update(name.encode())
            h.update(arr.tobytes())
        h.update(np.ascontiguousarray(self.valid).tobytes())
        return h.hexdigest()

    def true_colour(self, gain: float = 3.2, gamma: float = 2.1) -> np.ndarray:
        """An 8-bit RGB rendering for the dossier.

        A **fixed** gain and gamma, never per-scene auto-contrast. Two dates
        rendered side by side in a legal annex must be comparable, and
        auto-contrast makes them not be — it is the visual equivalent of
        changing the units between two rows of a table. The gamma is there
        because closed tropical canopy sits at 2–4% reflectance and a purely
        linear stretch renders it as near-black, which is accurate and
        useless.
        """
        rgb = np.dstack([self.bands["B04"], self.bands["B03"], self.bands["B02"]])
        rgb = np.clip(rgb * gain, 0.0, 1.0) ** (1.0 / gamma)
        return (rgb * 255).astype(np.uint8)
