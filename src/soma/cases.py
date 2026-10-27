"""From detection to decision — with the defendant in the loop from the start.

A monitoring platform that only accuses is a platform that will be used once
and then distrusted. The whole value of putting satellite evidence in front of
a regulator depends on the regulator being able to say, truthfully, that the
person affected was told what was alleged, on what basis, with the underlying
data, in time to answer, and that the answer was recorded and considered.

So the case model here is built around the contradictory procedure, not bolted
onto it:

  * a detection cannot be published before the affected party has been notified
    (``PublicationState``);
  * notification opens a response window, and the case cannot advance while it
    is open;
  * the operator's response is stored as evidence of the same rank as the
    state's, in the same ledger, with the same hashing;
  * a response that supplies a lawful explanation closes the case *and* feeds
    back into the detector as a labelled negative — an operator who explains
    themselves improves the system, which is the incentive you want;
  * every transition names a human being. No case advances because software
    decided it should.

None of this is exotic. It is ordinary administrative due process — Brazilian
CF/88 art. 5, LV; the EU's right to good administration in art. 41 of the
Charter — expressed as a state machine so that the software cannot skip it.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .evidence import EvidenceManifest, Ledger, sha256_of


class CaseState(str, Enum):
    OBSERVED = "observed"              # a detector fired
    SCREENED = "screened"              # a human triaged it as worth pursuing
    CORROBORATED = "corroborated"      # confirmed by an independent line of evidence
    NOTIFIED = "notified"              # the affected party has been told; clock running
    CONTESTED = "contested"            # a response was received
    REVIEWED = "reviewed"              # the response has been assessed
    SUBSTANTIATED = "substantiated"    # the finding stands
    DISMISSED = "dismissed"            # the finding falls
    REFERRED = "referred"              # passed to another authority
    CLOSED = "closed"


class PublicationState(str, Enum):
    INTERNAL = "internal"
    PARTY_ONLY = "notified_party_only"
    PUBLIC_SUMMARY = "public_summary"
    PUBLIC_FULL = "public_full"


ALLOWED: Dict[CaseState, tuple] = {
    CaseState.OBSERVED: (CaseState.SCREENED, CaseState.DISMISSED),
    CaseState.SCREENED: (CaseState.CORROBORATED, CaseState.DISMISSED),
    CaseState.CORROBORATED: (CaseState.NOTIFIED, CaseState.DISMISSED),
    CaseState.NOTIFIED: (CaseState.CONTESTED, CaseState.REVIEWED),
    CaseState.CONTESTED: (CaseState.REVIEWED,),
    CaseState.REVIEWED: (CaseState.SUBSTANTIATED, CaseState.DISMISSED, CaseState.REFERRED),
    CaseState.SUBSTANTIATED: (CaseState.REFERRED, CaseState.CLOSED),
    CaseState.DISMISSED: (CaseState.CLOSED,),
    CaseState.REFERRED: (CaseState.CLOSED,),
    CaseState.CLOSED: (),
}


class DueProcessError(RuntimeError):
    """Raised when the software is asked to skip a step it must not skip."""


@dataclass
class Transition:
    at_utc: str
    frm: str
    to: str
    actor: str            # a named person, not a service account
    actor_role: str
    note: str = ""
    attachment_digest: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Response:
    """What the notified party said."""

    received_utc: str
    submitted_by: str
    channel: str
    summary: str
    documents: List[str] = field(default_factory=list)
    accepted_explanation: Optional[bool] = None
    reviewer: str = ""
    review_note: str = ""

    def digest(self) -> str:
        return sha256_of(asdict(self))


@dataclass
class Case:
    case_id: str
    site_id: str
    title_id: str
    holder: str
    opened: str
    question: str
    state: CaseState = CaseState.OBSERVED
    publication: PublicationState = PublicationState.INTERNAL
    severity: str = "medium"                 # low | medium | high | critical
    manifests: List[str] = field(default_factory=list)   # manifest ids
    findings: List[Dict[str, Any]] = field(default_factory=list)
    history: List[Transition] = field(default_factory=list)
    response: Optional[Response] = None
    response_due: Optional[str] = None
    response_window_days: int = 30
    jurisdiction: str = ""
    legal_basis: List[str] = field(default_factory=list)
    assigned_to: str = ""

    # -- lifecycle ---------------------------------------------------------

    def advance(self, to: CaseState, actor: str, actor_role: str, note: str = "",
                attachment_digest: str = "") -> "Case":
        if not actor or not actor_role:
            raise DueProcessError(
                "every transition must name a responsible person and their role; "
                "automated advancement is not permitted"
            )
        if to not in ALLOWED[self.state]:
            raise DueProcessError(
                f"cannot move a case from {self.state.value} to {to.value}. "
                f"Permitted: {[s.value for s in ALLOWED[self.state]]}"
            )
        if self.state is CaseState.NOTIFIED and to is CaseState.REVIEWED:
            if not self._window_expired() and self.response is None:
                raise DueProcessError(
                    f"the response window is open until {self.response_due}. "
                    "A case cannot be reviewed before the notified party has had the "
                    "opportunity to respond."
                )
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.history.append(Transition(now, self.state.value, to.value, actor,
                                       actor_role, note, attachment_digest))
        self.state = to
        if to is CaseState.NOTIFIED:
            self.publication = PublicationState.PARTY_ONLY
            self.response_due = (datetime.now(timezone.utc)
                                 + timedelta(days=self.response_window_days)) \
                .isoformat(timespec="seconds")
        if to in (CaseState.SUBSTANTIATED, CaseState.REFERRED):
            self.publication = PublicationState.PUBLIC_FULL
        if to is CaseState.DISMISSED:
            self.publication = PublicationState.PUBLIC_SUMMARY
        return self

    def record_response(self, response: Response, actor: str, actor_role: str) -> "Case":
        if self.state is not CaseState.NOTIFIED:
            raise DueProcessError(
                "a response can only be recorded against a notified case; "
                f"this case is {self.state.value}"
            )
        self.response = response
        return self.advance(CaseState.CONTESTED, actor, actor_role,
                            note=f"response received via {response.channel}",
                            attachment_digest=response.digest())

    def _window_expired(self) -> bool:
        if not self.response_due:
            return False
        return datetime.now(timezone.utc) >= datetime.fromisoformat(self.response_due)

    # -- publication -------------------------------------------------------

    def public_view(self) -> Optional[dict]:
        """What may lawfully be shown on the open portal, at this moment."""
        if self.publication is PublicationState.INTERNAL:
            return None
        base = {
            "case_id": self.case_id,
            "site_id": self.site_id,
            "state": self.state.value,
            "opened": self.opened,
            "question": self.question,
            "severity": self.severity,
        }
        if self.publication is PublicationState.PARTY_ONLY:
            return None    # visible to the party, not to the world
        if self.publication is PublicationState.PUBLIC_SUMMARY:
            return base | {"outcome": self.state.value}
        return base | {
            "title_id": self.title_id,
            "holder": self.holder,
            "findings": self.findings,
            "manifests": self.manifests,
            "legal_basis": self.legal_basis,
            "response_recorded": self.response is not None,
            "history": [t.to_dict() for t in self.history],
        }

    def to_dict(self) -> dict:
        d = asdict(self)
        d["state"] = self.state.value
        d["publication"] = self.publication.value
        return d


class CaseRegister:
    """Cases on disk, with the evidence ledger beside them."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.ledger = Ledger(self.root / "ledger.jsonl")

    def open_case(
        self,
        site_id: str,
        title_id: str,
        holder: str,
        question: str,
        manifest: EvidenceManifest,
        severity: str = "medium",
        jurisdiction: str = "",
        legal_basis: Optional[List[str]] = None,
    ) -> Case:
        sealed = self.ledger.append(manifest)
        case_id = f"CASE-{date.today().year}-{sealed.manifest_id[4:12].upper()}"
        case = Case(
            case_id=case_id,
            site_id=site_id,
            title_id=title_id,
            holder=holder,
            opened=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            question=question,
            severity=severity,
            manifests=[sealed.manifest_id],
            jurisdiction=jurisdiction,
            legal_basis=legal_basis or [],
        )
        self.save(case)
        return case

    def attach(self, case: Case, manifest: EvidenceManifest) -> Case:
        sealed = self.ledger.append(manifest)
        case.manifests.append(sealed.manifest_id)
        self.save(case)
        return case

    def save(self, case: Case) -> Path:
        p = self.root / f"{case.case_id}.json"
        p.write_text(json.dumps(case.to_dict(), indent=2, ensure_ascii=False),
                     encoding="utf-8")
        return p

    def load(self, case_id: str) -> Case:
        d = json.loads((self.root / f"{case_id}.json").read_text(encoding="utf-8"))
        d["state"] = CaseState(d["state"])
        d["publication"] = PublicationState(d["publication"])
        d["history"] = [Transition(**t) for t in d.get("history", [])]
        if d.get("response"):
            d["response"] = Response(**d["response"])
        return Case(**d)

    def all_cases(self) -> List[Case]:
        return [self.load(p.stem) for p in sorted(self.root.glob("CASE-*.json"))]
