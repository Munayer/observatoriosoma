"""Where the disturbance is, relative to what was authorised.

This is the module that turns a picture into a legal question. Everything
before it measures the world; this one compares the world to the record — the
mining cadastre, the environmental licence, the protected-area register, the
Indigenous-land register — and produces the four questions an enforcement body
actually asks:

  1. Is there extraction where no title exists at all?
  2. Is extraction outside the polygon of the title that authorises it?
  3. Is extraction inside an area where it is categorically prohibited?
  4. Is a title recorded as dormant showing activity?

The cadastral polygons themselves are public in most jurisdictions. In Brazil,
SIGMINE publishes every active and inactive process polygon daily as shapefile
and KML; the EU's Open Data Directive high-value-dataset regime obliges member
states to publish the geospatial and environmental equivalents free, in
machine-readable form, with an API and bulk download, under CC BY 4.0 or looser
(Implementing Regulation (EU) 2023/138).

**Boundary tolerance is not optional.** Cadastral polygons carry their own
positional error, satellite geolocation carries roughly half a pixel, and
re-projection carries more. A finding that says "0.4 ha outside the boundary"
is a finding about coordinate systems, not about mining. Everything within
``BOUNDARY_TOLERANCE_M`` of a line is reported as indeterminate, separately
from the area confidently outside it. This one design decision is the
difference between a system a mining lawyer dismantles in an afternoon and one
that holds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from ..geom import Grid, buffer_ring, geodesic_area_ha
from ..version import ALGORITHM_VERSIONS

# Sentinel-2 geolocation is specified to better than 11 m (95%); cadastral
# vector error in most national registries is of the same order or worse.
BOUNDARY_TOLERANCE_M = 25.0

Vertex = Tuple[float, float]


@dataclass
class Title:
    """A mining right as the registry records it."""

    identifier: str                  # e.g. ANM process 830.123/2018
    holder: str
    ring: Sequence[Vertex]
    status: str                      # "active" | "suspended" | "requested" | "expired"
    phase: str = ""                  # exploration / extraction concession / garimpo permit
    substance: str = ""
    granted: Optional[date] = None
    source: str = ""
    licence_area_ha: float = 0.0

    def __post_init__(self) -> None:
        if not self.licence_area_ha:
            self.licence_area_ha = geodesic_area_ha(self.ring)

    @property
    def authorises_extraction(self) -> bool:
        return self.status == "active" and self.phase.lower() not in ("exploration", "pesquisa")


@dataclass
class RestrictedArea:
    """Somewhere extraction is prohibited or conditioned."""

    identifier: str
    kind: str            # "indigenous_land" | "conservation_unit" | "riparian_buffer" | ...
    name: str
    ring: Sequence[Vertex]
    basis: str = ""      # the legal instrument that creates the restriction
    source: str = ""


@dataclass
class SpatialVerdict:
    site_id: str
    when: date
    total_disturbed_ha: float
    inside_title_ha: float
    outside_title_ha: float
    indeterminate_ha: float
    restricted_overlaps: List[Dict] = field(default_factory=list)
    titles_considered: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "site_id": self.site_id,
            "date": self.when.isoformat(),
            "total_disturbed_ha": round(self.total_disturbed_ha, 3),
            "inside_title_ha": round(self.inside_title_ha, 3),
            "outside_title_ha": round(self.outside_title_ha, 3),
            "indeterminate_boundary_ha": round(self.indeterminate_ha, 3),
            "boundary_tolerance_m": BOUNDARY_TOLERANCE_M,
            "restricted_overlaps": self.restricted_overlaps,
            "titles_considered": self.titles_considered,
            "notes": self.notes,
            "algorithm_version": ALGORITHM_VERSIONS["crosscheck.cadastre"],
        }


def locate(
    site_id: str,
    when: date,
    grid: Grid,
    disturbed: np.ndarray,
    titles: Sequence[Title],
    restricted: Sequence[RestrictedArea] = (),
) -> SpatialVerdict:
    """Split the disturbed footprint against the record."""
    lon, lat = grid.lonlat()

    inner_masks, outer_masks = [], []
    for t in titles:
        from ..geom import points_in_ring
        inner = points_in_ring(lon, lat, buffer_ring(t.ring, -BOUNDARY_TOLERANCE_M))
        outer = points_in_ring(lon, lat, buffer_ring(t.ring, +BOUNDARY_TOLERANCE_M))
        inner_masks.append(inner)
        outer_masks.append(outer)

    any_inner = np.any(inner_masks, axis=0) if inner_masks else np.zeros(grid.shape, bool)
    any_outer = np.any(outer_masks, axis=0) if outer_masks else np.zeros(grid.shape, bool)

    confidently_inside = disturbed & any_inner
    confidently_outside = disturbed & ~any_outer
    indeterminate = disturbed & any_outer & ~any_inner

    overlaps = []
    for r in restricted:
        from ..geom import points_in_ring
        m = points_in_ring(lon, lat, r.ring) & disturbed
        ha = grid.area_ha(m)
        if ha > 0.05:
            overlaps.append({
                "identifier": r.identifier,
                "kind": r.kind,
                "name": r.name,
                "overlap_ha": round(ha, 3),
                "legal_basis": r.basis,
                "source": r.source,
            })

    notes: List[str] = []
    dormant = [t.identifier for t in titles
               if t.status in ("suspended", "expired", "requested")]
    if dormant and grid.area_ha(confidently_inside) > 1.0:
        notes.append(
            "Disturbance observed inside the polygon of a title recorded as "
            + ", ".join(sorted(set(t.status for t in titles if t.identifier in dormant)))
            + f" ({', '.join(dormant)}). Verify the registry status for the observation date."
        )
    if not titles:
        notes.append(
            "No title of any status covers this footprint in the cadastral extract used. "
            "Treat as a candidate unlicensed operation and verify against the registry "
            "of record before any action."
        )
    exploration_only = [t.identifier for t in titles if t.status == "active"
                        and not t.authorises_extraction]
    if exploration_only:
        notes.append(
            "Footprint falls within exploration-phase title(s) "
            f"({', '.join(exploration_only)}), which do not authorise extraction. "
            "Exploration works of limited extent may be lawful; scale is the question."
        )

    return SpatialVerdict(
        site_id=site_id,
        when=when,
        total_disturbed_ha=grid.area_ha(disturbed),
        inside_title_ha=grid.area_ha(confidently_inside),
        outside_title_ha=grid.area_ha(confidently_outside),
        indeterminate_ha=grid.area_ha(indeterminate),
        restricted_overlaps=overlaps,
        titles_considered=[t.identifier for t in titles],
        notes=notes,
    )


def masks(
    grid: Grid,
    disturbed: np.ndarray,
    titles: Sequence[Title],
) -> Dict[str, np.ndarray]:
    """The three masks, for rendering the map in the dossier."""
    from ..geom import points_in_ring
    lon, lat = grid.lonlat()
    inner = np.zeros(grid.shape, bool)
    outer = np.zeros(grid.shape, bool)
    for t in titles:
        inner |= points_in_ring(lon, lat, buffer_ring(t.ring, -BOUNDARY_TOLERANCE_M))
        outer |= points_in_ring(lon, lat, buffer_ring(t.ring, +BOUNDARY_TOLERANCE_M))
    return {
        "inside": disturbed & inner,
        "outside": disturbed & ~outer,
        "indeterminate": disturbed & outer & ~inner,
    }
