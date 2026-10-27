"""Provider interface.

A provider turns (site geometry, date range) into a list of ``Scene``. Two
implementations ship: ``stac_sentinel2`` for real Copernicus data, and
``synthetic`` for a deterministic simulated site used in tests, training and
demonstrations.

The interface is deliberately narrow so that a national deployment can add a
provider for its own archive (a Brazilian deployment might add CBERS-4A, an
African one might add a regional receiving station) without touching a
detector.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Sequence, Tuple

from ..geom import Grid
from ..scene import Scene

Vertex = Tuple[float, float]


class SceneProvider(ABC):
    """Source of surface-reflectance scenes."""

    name: str = "abstract"
    licence: str = ""

    @abstractmethod
    def search(
        self,
        site_id: str,
        aoi: Sequence[Vertex],
        start: date,
        end: date,
        grid: Grid | None = None,
        max_cloud: float = 0.6,
    ) -> List[Scene]:
        """Return every usable scene over ``aoi`` in [start, end], time-ordered.

        Implementations must not silently drop scenes. A scene rejected for
        cloud must still be counted, because "we looked and could not see" is
        itself a fact a regulator needs — a site that is never observable is a
        site that needs a radar-based or overflight strategy, and the absence
        of observations must not be mistaken for the absence of activity.
        """

    def describe(self) -> dict:
        return {"provider": self.name, "licence": self.licence}
