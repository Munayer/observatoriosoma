from .base import SceneProvider  # noqa: F401
from .synthetic import SyntheticProvider, SyntheticSite  # noqa: F401

__all__ = ["SceneProvider", "SyntheticProvider", "SyntheticSite", "StacSentinel2Provider"]


def __getattr__(name):  # lazy: the STAC provider pulls optional dependencies
    if name == "StacSentinel2Provider":
        from .stac_sentinel2 import StacSentinel2Provider
        return StacSentinel2Provider
    raise AttributeError(name)
