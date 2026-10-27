"""Spectral indices.

Every index here is a published, citable formula. That is not pedantry: a
finding whose method cannot be named in one line of a technical annex is a
finding that will not survive cross-examination, and an index nobody can look
up is exactly the sort of thing an operator's expert witness will attack.

References are given in ``INDEX_REFERENCES`` and are reproduced verbatim in the
evidence manifest.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from .scene import Scene

INDEX_REFERENCES: Dict[str, str] = {
    "ndvi": "Rouse, J. W., et al. \"Monitoring Vegetation Systems in the Great Plains "
            "with ERTS.\" Third ERTS Symposium, NASA SP-351, 1974, pp. 309-17.",
    "ndwi": "McFeeters, S. K. \"The Use of the Normalized Difference Water Index (NDWI) "
            "in the Delineation of Open Water Features.\" International Journal of "
            "Remote Sensing, vol. 17, no. 7, 1996, pp. 1425-32.",
    "mndwi": "Xu, Hanqiu. \"Modification of Normalised Difference Water Index (NDWI) to "
             "Enhance Open Water Features in Remotely Sensed Imagery.\" International "
             "Journal of Remote Sensing, vol. 27, no. 14, 2006, pp. 3025-33.",
    "ndmi": "Gao, Bo-Cai. \"NDWI—A Normalized Difference Water Index for Remote Sensing "
            "of Vegetation Liquid Water from Space.\" Remote Sensing of Environment, "
            "vol. 58, no. 3, 1996, pp. 257-66.",
    "bsi": "Rikimaru, A., P. S. Roy, and S. Miyatake. \"Tropical Forest Cover Density "
           "Mapping.\" Tropical Ecology, vol. 43, no. 1, 2002, pp. 39-47.",
    "nbr": "Key, C. H., and N. C. Benson. \"Landscape Assessment: Sampling and Analysis "
           "Methods.\" FIREMON: Fire Effects Monitoring and Inventory System, USDA "
           "Forest Service RMRS-GTR-164-CD, 2006.",
    "ndti": "Lacaux, J. P., et al. \"Classification of Ponds from High-Spatial "
            "Resolution Remote Sensing: Application to Rift Valley Fever Epidemics in "
            "Senegal.\" Remote Sensing of Environment, vol. 106, no. 1, 2007, pp. 66-74.",
    "brightness": "Simple mean of the six reflectance bands used here; no external "
                  "reference claimed.",
}


def _nd(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Normalised difference, safe at the origin."""
    num = a - b
    den = a + b
    out = np.zeros_like(num, dtype=np.float32)
    np.divide(num, den, out=out, where=np.abs(den) > 1e-6)
    return np.clip(out, -1.0, 1.0)


def ndvi(s: Scene) -> np.ndarray:
    """Vegetation. High over canopy, near zero over bare ground."""
    return _nd(s.band("B08"), s.band("B04"))


def ndwi(s: Scene) -> np.ndarray:
    """McFeeters water index (green/NIR)."""
    return _nd(s.band("B03"), s.band("B08"))


def mndwi(s: Scene) -> np.ndarray:
    """Modified NDWI (green/SWIR-1). Preferred where built or bare surfaces
    surround the water, which is exactly the mining case."""
    return _nd(s.band("B03"), s.band("B11"))


def ndmi(s: Scene) -> np.ndarray:
    """Canopy moisture (NIR/SWIR-1)."""
    return _nd(s.band("B08"), s.band("B11"))


def nbr(s: Scene) -> np.ndarray:
    """Normalised burn ratio — separates burn scars from mining scars, both of
    which strip vegetation but differ sharply in SWIR-2."""
    return _nd(s.band("B08"), s.band("B12"))


def bsi(s: Scene) -> np.ndarray:
    """Bare Soil Index."""
    a = s.band("B11") + s.band("B04")
    b = s.band("B08") + s.band("B02")
    return _nd(a, b)


def ndti(s: Scene) -> np.ndarray:
    """Turbidity index for water bodies (red/green)."""
    return _nd(s.band("B04"), s.band("B03"))


def brightness(s: Scene) -> np.ndarray:
    return np.mean([s.band(b) for b in ("B02", "B03", "B04", "B08", "B11", "B12")], axis=0)


ALL = {
    "ndvi": ndvi,
    "ndwi": ndwi,
    "mndwi": mndwi,
    "ndmi": ndmi,
    "nbr": nbr,
    "bsi": bsi,
    "ndti": ndti,
    "brightness": brightness,
}


def compute(s: Scene, names=None) -> Dict[str, np.ndarray]:
    names = names or list(ALL)
    return {n: ALL[n](s) for n in names}
