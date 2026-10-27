"""What a detector returns.

Not a number — an ``Observation``: a measured quantity, the conditions under
which it was measured, and enough metadata to re-measure it. A detector that
returns a float is a detector whose output cannot be defended.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, Optional

import numpy as np


@dataclass
class Observation:
    site_id: str
    acquired: date
    detector: str
    algorithm_version: str
    quantity: str                    # e.g. "disturbed_area"
    value: float
    units: str
    valid_fraction: float            # share of the AOI actually observable
    params: Dict[str, Any] = field(default_factory=dict)
    mask: Optional[np.ndarray] = None      # not serialised; kept for rendering
    detail: Dict[str, Any] = field(default_factory=dict)
    reliability: str = "ok"          # ok | degraded | unusable

    def to_dict(self) -> dict:
        return {
            "site_id": self.site_id,
            "acquired": self.acquired.isoformat(),
            "detector": self.detector,
            "algorithm_version": self.algorithm_version,
            "quantity": self.quantity,
            "value": round(float(self.value), 4),
            "units": self.units,
            "valid_fraction": round(float(self.valid_fraction), 4),
            "reliability": self.reliability,
            "params": self.params,
            "detail": {k: _jsonable(v) for k, v in self.detail.items()},
        }


def _jsonable(v):
    """Coerce numpy scalars and arrays recursively.

    A numpy float that reaches json.dumps becomes a string and silently
    changes the hash of the manifest it sits in. Serialisation bugs are
    evidence bugs here, so this recurses.
    """
    if isinstance(v, (np.floating, np.integer)):
        return v.item()
    if isinstance(v, np.bool_):
        return bool(v)
    if isinstance(v, np.ndarray):
        return _jsonable(v.tolist())
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    return v


def grade_reliability(valid_fraction: float,
                      degraded_below: float = 0.75,
                      unusable_below: float = 0.40) -> str:
    """Three states, not two.

    A regulator needs to distinguish "we measured it" from "we half-measured
    it" from "we could not see". Collapsing the last two into a null is how
    monitoring systems end up under-reporting activity in exactly the wet
    season when illegal operators prefer to work.
    """
    if valid_fraction < unusable_below:
        return "unusable"
    if valid_fraction < degraded_below:
        return "degraded"
    return "ok"
