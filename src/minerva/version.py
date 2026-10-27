"""Version pins.

Algorithm versions are part of the evidence record. Changing the behaviour of a
detector without bumping its version here silently invalidates every prior
finding produced with it, which is the geospatial equivalent of losing the
chain of custody. Bump on any behavioural change, including threshold changes.
"""

__version__ = "0.1.0"

ALGORITHM_VERSIONS = {
    "indices": "1.0.0",
    "footprint.spectral_rule": "1.0.0",
    "water.pond_extent": "1.0.0",
    "change.robust_trend": "1.0.0",
    "deformation.velocity_screen": "1.0.0",
    "crosscheck.cadastre": "1.0.0",
    "crosscheck.declaration": "1.0.0",
    "volume.dem_difference": "1.0.0",
    "provider.synthetic": "1.0.0",
    "provider.stac_sentinel2": "1.0.0",
}
