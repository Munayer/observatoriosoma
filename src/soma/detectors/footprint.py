"""Delineation of the disturbed mining surface.

**Why a rule and not a neural network.** A convolutional classifier is more
accurate; Earth Genome's Amazon Mining Watch ensemble reports 99.4% specificity
and 89.5% sensitivity on a geographic holdout, which this rule does not
approach on hard scenes. The rule is the *default* here for three reasons, and
the CNN path is provided as an upgrade (see ``detectors/learned.py`` in the
roadmap), not excluded:

  1. **It can be written into a decision.** "Pixels with NDVI below 0.30, MNDWI
     below 0.10, BSI above 0.00 and SWIR-1 reflectance above 0.12, aggregated
     with a 0.5 ha minimum mapping unit" is a sentence an administrative
     lawyer can put in an act and an operator can contest on the merits. "The
     ensemble scored 0.87" is not.
  2. **It has no training-set provenance problem.** A learned model imports the
     biases of wherever its labels came from. When the model is used to justify
     coercive action against a specific party, that provenance becomes
     discoverable, and few civic-tech training sets would survive discovery.
  3. **It degrades legibly.** When it fails you can see which term failed.

The right architecture is both: the rule as the accountable baseline, the model
as a recall booster whose extra detections are triaged by a human before they
enter a case. Never the model alone.

Thresholds below are defaults for humid-tropical lateritic terrain. They are
parameters, they are recorded in every manifest, and a deployment is expected
to calibrate them against local ground truth before issuing anything.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

try:
    from scipy import ndimage as _ndi
except Exception:  # pragma: no cover
    _ndi = None

from .. import indices
from ..scene import Scene
from ..version import ALGORITHM_VERSIONS
from .base import Observation, grade_reliability

DETECTOR = "footprint.spectral_rule"


@dataclass
class FootprintParams:
    ndvi_max: float = 0.30          # vegetation removed
    mndwi_max: float = 0.10         # not open water
    bsi_min: float = 0.00           # soil signature dominant
    swir1_min: float = 0.12         # bright in SWIR-1: dry mineral surface
    nbr_max: float = 0.62           # excludes healthy canopy that slipped through
    min_mapping_unit_ha: float = 0.5
    # An area measurement needs a stricter visibility bar than a yes/no
    # detection: 15% of the assessment area behind cloud can hide 15 ha.
    ok_above: float = 0.85
    unusable_below: float = 0.40
    open_radius_px: int = 1         # remove speckle
    close_radius_px: int = 2        # close haul-road gaps within a pit
    aoi_mask: Optional[np.ndarray] = None
    # Where visibility is *judged*. Cloud over an empty corner of the scene
    # says nothing about how well the workings were seen; cloud over the
    # workings says everything. Judging visibility across the whole scene
    # throws away good measurements and keeps bad ones.
    assessment_mask: Optional[np.ndarray] = None

    def to_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items()
             if k not in ("aoi_mask", "assessment_mask")}
        d["aoi_restricted"] = self.aoi_mask is not None
        d["assessment_area_restricted"] = self.assessment_mask is not None
        return d


def detect(scene: Scene, params: FootprintParams | None = None) -> Observation:
    p = params or FootprintParams()

    ndvi = indices.ndvi(scene)
    mndwi = indices.mndwi(scene)
    bsi = indices.bsi(scene)
    nbr = indices.nbr(scene)
    swir1 = scene.band("B11")

    raw = (
        (ndvi < p.ndvi_max)
        & (mndwi < p.mndwi_max)
        & (bsi > p.bsi_min)
        & (swir1 > p.swir1_min)
        & (nbr < p.nbr_max)
        & scene.valid
    )
    if p.aoi_mask is not None:
        raw &= p.aoi_mask

    cleaned = _morphology(raw, p)
    cleaned = _drop_small(cleaned, scene, p.min_mapping_unit_ha)

    area_ha = scene.grid.area_ha(cleaned)
    judge_on = p.assessment_mask if p.assessment_mask is not None else p.aoi_mask
    if judge_on is not None and judge_on.any():
        observable = float((scene.valid & judge_on).sum() / judge_on.sum())
    else:
        observable = scene.valid_fraction

    return Observation(
        site_id=scene.site_id,
        acquired=scene.acquired,
        detector=DETECTOR,
        algorithm_version=ALGORITHM_VERSIONS[DETECTOR],
        quantity="disturbed_area",
        value=area_ha,
        units="ha",
        valid_fraction=observable,
        reliability=grade_reliability(observable, degraded_below=p.ok_above,
                                      unusable_below=p.unusable_below),
        params=p.to_dict(),
        mask=cleaned,
        detail={
            "pixels": int(cleaned.sum()),
            "pixel_m": scene.grid.pixel_m,
            "cloud_fraction": scene.cloud_fraction,
            "index_references": {
                k: indices.INDEX_REFERENCES[k] for k in ("ndvi", "mndwi", "bsi", "nbr")
            },
        },
    )


def _morphology(mask: np.ndarray, p: FootprintParams) -> np.ndarray:
    if _ndi is None:  # pragma: no cover
        return mask
    out = mask
    if p.open_radius_px > 0:
        out = _ndi.binary_opening(out, structure=_disk(p.open_radius_px))
    if p.close_radius_px > 0:
        out = _ndi.binary_closing(out, structure=_disk(p.close_radius_px))
    return out


def _disk(r: int) -> np.ndarray:
    y, x = np.mgrid[-r:r + 1, -r:r + 1]
    return (x * x + y * y) <= r * r


def _drop_small(mask: np.ndarray, scene: Scene, min_ha: float) -> np.ndarray:
    """Enforce a minimum mapping unit.

    Two isolated pixels are not a mine; they are noise, and an enforcement
    system that reports them will be ignored within a month. 0.5 ha at 10 m is
    50 pixels — roughly the smallest thing a field team could usefully be sent
    to look at.
    """
    if _ndi is None or not mask.any():  # pragma: no cover
        return mask
    labels, n = _ndi.label(mask)
    if n == 0:
        return mask
    min_px = max(int(round(min_ha * 10_000 / (scene.grid.pixel_m ** 2))), 1)
    counts = np.bincount(labels.ravel())
    keep = np.zeros(counts.shape, dtype=bool)
    keep[1:] = counts[1:] >= min_px
    return keep[labels]
