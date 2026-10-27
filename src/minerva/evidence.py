"""Chain of custody.

The claim this library makes about its own outputs is narrow and testable:

    Given the manifest, a third party with no access to this system can obtain
    the same inputs, run the same code at the same version with the same
    parameters, and get the same numbers.

Everything here exists to make that sentence true. Three mechanisms:

  * **The manifest.** Inputs (identified, sourced, timestamped, hashed),
    algorithms (named and versioned), parameters (all of them), outputs
    (hashed). Canonicalised and hashed itself.
  * **The ledger.** An append-only JSONL file in which each entry carries the
    hash of the previous entry. Altering or removing a past finding breaks the
    chain, and the break is detectable by anyone holding a later entry — which
    in practice means the operator who received a notice can prove the state's
    record has not been rewritten, and the state can prove the same to a court.
  * **Re-execution.** ``replay_recipe`` emits the exact commands that reproduce
    a finding.

This is a modest, standard construction — a hash chain, not a blockchain, with
no consensus, no tokens and no distributed anything. Public administration does
not need distributed trust; it needs a record it can be held to. If stronger
guarantees are wanted, the ledger head can be timestamped with RFC 3161 or
published periodically in an official gazette, which is how notarial practice
has solved this for a century.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .scene import SourceRef
from .version import ALGORITHM_VERSIONS, __version__

GENESIS = "0" * 64


def canonical_json(obj: Any) -> str:
    """One serialisation, so one hash. Sorted keys, no incidental whitespace."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      default=str)


def sha256_of(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


@dataclass
class AlgorithmRef:
    name: str
    version: str
    params: Dict[str, Any] = field(default_factory=dict)
    reference: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name, "version": self.version,
                "params": self.params, "reference": self.reference}


@dataclass
class OutputRef:
    name: str
    value: Any
    units: str = ""
    digest: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name, "value": self.value,
                "units": self.units, "digest": self.digest}


@dataclass
class EvidenceManifest:
    """Everything needed to re-derive one stated fact."""

    manifest_id: str
    site_id: str
    question: str                       # the regulatory question this answers
    created_utc: str
    software: Dict[str, str]
    inputs: List[Dict[str, Any]] = field(default_factory=list)
    algorithms: List[Dict[str, Any]] = field(default_factory=list)
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    jurisdiction: str = ""
    evidential_status: str = "screening"   # screening | corroborated | field-verified
    prev_hash: str = GENESIS
    manifest_hash: str = ""

    # -- construction ------------------------------------------------------

    @classmethod
    def create(
        cls,
        site_id: str,
        question: str,
        jurisdiction: str = "",
        prev_hash: str = GENESIS,
    ) -> "EvidenceManifest":
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        seed = sha256_of({"site": site_id, "q": question, "t": now})[:16]
        return cls(
            manifest_id=f"MNV-{seed}",
            site_id=site_id,
            question=question,
            created_utc=now,
            software={"minerva": __version__, "python": os.sys.version.split()[0]},
            jurisdiction=jurisdiction,
            prev_hash=prev_hash,
        )

    def add_sources(self, sources: Sequence[SourceRef]) -> "EvidenceManifest":
        for s in sources:
            self.inputs.append(s.to_dict())
        return self

    def add_dataset(self, identifier: str, source: str, licence: str,
                    retrieved_utc: Optional[str] = None, checksum: str = "",
                    note: str = "") -> "EvidenceManifest":
        self.inputs.append({
            "kind": "dataset",
            "identifier": identifier,
            "source": source,
            "licence": licence,
            "retrieved_utc": retrieved_utc or datetime.now(timezone.utc)
            .isoformat(timespec="seconds"),
            "checksum": checksum,
            "note": note,
        })
        return self

    def add_algorithm(self, name: str, params: Dict[str, Any] | None = None,
                      reference: str = "", version: str | None = None) -> "EvidenceManifest":
        self.algorithms.append(AlgorithmRef(
            name=name,
            version=version or ALGORITHM_VERSIONS.get(name, "unversioned"),
            params=params or {},
            reference=reference,
        ).to_dict())
        return self

    def add_output(self, name: str, value: Any, units: str = "") -> "EvidenceManifest":
        self.outputs.append(OutputRef(
            name=name, value=value, units=units, digest=sha256_of(value)
        ).to_dict())
        return self

    def note_assumption(self, text: str) -> "EvidenceManifest":
        self.assumptions.append(text)
        return self

    def note_limitation(self, text: str) -> "EvidenceManifest":
        self.limitations.append(text)
        return self

    # -- sealing -----------------------------------------------------------

    def body(self) -> dict:
        d = asdict(self)
        d.pop("manifest_hash", None)
        return d

    def seal(self) -> "EvidenceManifest":
        self.manifest_hash = sha256_of(self.body())
        return self

    def verify(self) -> bool:
        return bool(self.manifest_hash) and self.manifest_hash == sha256_of(self.body())

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


class Ledger:
    """Append-only, hash-chained record of every sealed manifest."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def head(self) -> str:
        last = GENESIS
        if not self.path.exists():
            return last
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    last = json.loads(line)["manifest_hash"]
        return last

    def append(self, manifest: EvidenceManifest) -> EvidenceManifest:
        manifest.prev_hash = self.head()
        manifest.seal()
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(canonical_json(manifest.to_dict()) + "\n")
        return manifest

    def entries(self) -> List[dict]:
        if not self.path.exists():
            return []
        out = []
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def verify_chain(self) -> Dict[str, Any]:
        """Check every link. Returns a report, never raises.

        A broken chain is a fact to be reported to whoever is responsible for
        the register, not an exception to be swallowed.
        """
        entries = self.entries()
        problems: List[str] = []
        prev = GENESIS
        for i, e in enumerate(entries):
            if e.get("prev_hash") != prev:
                problems.append(
                    f"entry {i} ({e.get('manifest_id')}) claims prev_hash "
                    f"{e.get('prev_hash')!r}, expected {prev!r}"
                )
            body = dict(e)
            body.pop("manifest_hash", None)
            recomputed = sha256_of(body)
            if recomputed != e.get("manifest_hash"):
                problems.append(
                    f"entry {i} ({e.get('manifest_id')}) hash mismatch: stored "
                    f"{e.get('manifest_hash')}, recomputed {recomputed}"
                )
            prev = e.get("manifest_hash", prev)
        return {
            "entries": len(entries),
            "intact": not problems,
            "head": prev,
            "problems": problems,
        }


def replay_recipe(manifest: EvidenceManifest) -> str:
    """Human-readable instructions to reproduce a finding."""
    lines = [
        f"# Reproduction recipe for {manifest.manifest_id}",
        f"# Question: {manifest.question}",
        f"# Sealed:   {manifest.created_utc} (hash {manifest.manifest_hash[:16]}…)",
        "",
        "# 1. Software",
        f"pip install 'minerva=={manifest.software.get('minerva', __version__)}'",
        "",
        "# 2. Inputs",
    ]
    for i in manifest.inputs:
        lines.append(f"#   [{i.get('kind')}] {i.get('identifier')}")
        lines.append(f"#       from {i.get('source')}")
        if i.get("licence"):
            lines.append(f"#       licence: {i['licence']}")
        if i.get("checksum"):
            lines.append(f"#       sha256: {i['checksum']}")
    lines += ["", "# 3. Algorithms and parameters"]
    for a in manifest.algorithms:
        lines.append(f"#   {a['name']} v{a['version']}")
        for k, v in sorted(a.get("params", {}).items()):
            lines.append(f"#       {k} = {v!r}")
    lines += ["", "# 4. Expected outputs"]
    for o in manifest.outputs:
        lines.append(f"#   {o['name']} = {o['value']} {o['units']} "
                     f"(digest {o['digest'][:16]}…)")
    lines += ["", "minerva replay --manifest " + manifest.manifest_id + ".json"]
    return "\n".join(lines)
