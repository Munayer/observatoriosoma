"""
MINERVA — Mineral Extraction Verification & Regulatory Accountability.

An open mirror of the mining operator's software stack, built for the public
sector out of public data.

Design contract (read this before changing anything):

    Every number this library puts on a screen must be re-derivable, by a
    third party, from public inputs, using only the manifest that accompanies
    it. A figure without a manifest is an opinion, not evidence.

The library therefore never returns a bare number. Detectors return
``Observation`` objects, cross-checks return ``Finding`` objects, and both
carry an ``EvidenceManifest`` recording inputs, algorithm versions, parameters
and hashes. The audit ledger chains those manifests so that deletion or
alteration of a past finding is detectable.

Dependency policy: the core has no mandatory geospatial dependencies. numpy is
required; scipy and scikit-image are used where present and degraded
gracefully where not. GDAL, rasterio, shapely and pyproj are *optional
accelerators*, never requirements. A municipal environment agency with one
laptop and no procurement budget must be able to run this.
"""

from .version import __version__, ALGORITHM_VERSIONS  # noqa: F401

__all__ = ["__version__", "ALGORITHM_VERSIONS"]
