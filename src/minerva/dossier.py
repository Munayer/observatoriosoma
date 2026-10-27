"""The translation layer.

This is the module the whole project exists for, and the one most monitoring
platforms do not have.

A detection is a communication in the register of remote sensing. It is
meaningless to the legal system, which processes communications coded
lawful/unlawful; to the administrative system, which processes them as
competence, procedure and act; to the political system, which processes them as
budget and mandate; and to the public sphere, which processes them as harm and
who is responsible. A number that cannot cross those boundaries stays inside
the technical system and changes nothing — which is the observed fate of a
great deal of excellent environmental monitoring.

So the same sealed finding is rendered five ways. Not five summaries of it:
five *translations* of it, each carrying the whole of the finding into a form
the receiving system can operate on, and each explicit about what it is not
claiming.

    technical_annex        → the technical system: method, parameters, hashes
    administrative_notice  → the administrative system: fact, norm, act, deadline
    judicial_dossier       → the legal system: custody, admissibility, limits
    public_card            → the public sphere: what, where, how much, what next
    oversight_brief        → the political system: aggregate, cost, capacity

Every one of them names its limits in its own register. The technical annex
gives error bars; the notice gives the response deadline and the right to
contest; the judicial dossier gives the admissibility caveats; the public card
says in plain words that a detection is not a conviction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Dict, List, Optional, Sequence

from .cases import Case, CaseState
from .crosscheck.cadastre import BOUNDARY_TOLERANCE_M, SpatialVerdict
from .detectors.base import Observation
from .evidence import EvidenceManifest, replay_recipe

SYNTHETIC_MARKERS = ("synthetic", "simulation")


class SyntheticEvidenceError(RuntimeError):
    """Raised when someone tries to issue a real act from simulated data."""


@dataclass
class LegalFrame:
    """The norms a deployment operates under. Configured per jurisdiction."""

    jurisdiction: str
    authority: str
    unlicensed_extraction: str = ""
    extraction_outside_title: str = ""
    protected_area: str = ""
    dam_safety: str = ""
    royalty: str = ""
    information_access: str = ""
    due_process: str = ""
    response_window_days: int = 30
    language: str = "en"


BRAZIL = LegalFrame(
    jurisdiction="Brazil (federal)",
    authority="Agência Nacional de Mineração (ANM)",
    unlicensed_extraction="Decreto-Lei 227/1967 (Código de Mineração), arts. 2º e 47; "
                          "Lei 9.605/1998, art. 55 (crime de usurpação/extração sem "
                          "autorização)",
    extraction_outside_title="Decreto-Lei 227/1967, art. 47, IX; Portaria/Resolução ANM "
                             "sobre limites da área do título",
    protected_area="CF/88, art. 231, §3º (terras indígenas); Lei 9.985/2000 (SNUC); "
                   "Lei 12.651/2012 (APP)",
    dam_safety="Lei 12.334/2010 e Lei 14.066/2020 (Política Nacional de Segurança de "
               "Barragens); Resolução ANM 95/2022",
    royalty="Lei 8.001/1990 e Lei 13.540/2017 (CFEM)",
    information_access="Lei 12.527/2011 (Lei de Acesso à Informação); Lei 10.650/2003 "
                       "(informação ambiental)",
    due_process="CF/88, art. 5º, LIV e LV (devido processo legal, contraditório e "
                "ampla defesa); Lei 9.784/1999 (processo administrativo federal)",
    response_window_days=30,
    language="pt",
)

EUROPEAN_UNION = LegalFrame(
    jurisdiction="European Union / member state",
    authority="competent national mining and environmental authority",
    unlicensed_extraction="national mining act; Directive 2006/21/EC on the management "
                          "of waste from extractive industries",
    extraction_outside_title="national mining act; permit conditions",
    protected_area="Directive 92/43/EEC (Habitats) and Directive 2009/147/EC (Birds); "
                   "Directive 2000/60/EC (Water Framework)",
    dam_safety="Directive 2006/21/EC, art. 11 and Annex III; national dam-safety law",
    royalty="national mining fiscal regime; Directive 2013/34/EU, Chapter 10 "
            "(payments to governments)",
    information_access="Directive 2003/4/EC (access to environmental information), "
                       "implementing the Aarhus Convention; Directive (EU) 2019/1024 "
                       "and Implementing Regulation (EU) 2023/138 (high-value datasets)",
    due_process="Charter of Fundamental Rights, art. 41 (right to good administration) "
                "and art. 47 (effective remedy); national administrative procedure act",
    response_window_days=30,
    language="en",
)


@dataclass
class Dossier:
    case: Case
    manifest: EvidenceManifest
    frame: LegalFrame
    verdict: Optional[SpatialVerdict] = None
    trend: Optional[Dict] = None
    observations: Sequence[Observation] = field(default_factory=tuple)
    figures: Dict[str, str] = field(default_factory=dict)
    reconciliation: Optional[Dict] = None
    deformation: Optional[Dict] = None

    # -- guards ------------------------------------------------------------

    def _is_synthetic(self) -> bool:
        blob = " ".join(
            str(i.get("source", "")) + str(i.get("licence", "")) + str(i.get("note", ""))
            for i in self.manifest.inputs
        ).lower()
        return any(m in blob for m in SYNTHETIC_MARKERS)

    def _require_real(self, what: str) -> None:
        if self._is_synthetic():
            raise SyntheticEvidenceError(
                f"refusing to produce {what}: the evidence chain contains simulated "
                "inputs. Simulated runs are for testing, training and demonstration. "
                "Use technical_annex() or public_card() with the SIMULATION banner "
                "instead."
            )

    # ------------------------------------------------------------------
    # 1. technical system
    # ------------------------------------------------------------------

    def technical_annex(self) -> str:
        m = self.manifest
        sim = self._is_synthetic()
        out: List[str] = []
        if sim:
            out += ["> **SIMULATION — NOT EVIDENCE.** This annex was produced from "
                    "simulated imagery. It demonstrates the method and the record "
                    "structure. It states nothing about any real site or party.", ""]
        out += [
            f"# Technical annex — {self.case.case_id}",
            "",
            f"**Question examined.** {m.question}",
            "",
            f"**Site.** `{self.case.site_id}`  ·  **Title of record.** "
            f"`{self.case.title_id}`  ·  **Holder of record.** {self.case.holder}",
            "",
            f"**Manifest.** `{m.manifest_id}`  ·  sealed {m.created_utc}  ·  "
            f"hash `{m.manifest_hash}`",
            f"**Previous ledger entry.** `{m.prev_hash}`",
            f"**Software.** " + ", ".join(f"{k} {v}" for k, v in m.software.items()),
            "",
            "## 1. Inputs",
            "",
            "| Kind | Identifier | Source | Retrieved (UTC) | Licence |",
            "|---|---|---|---|---|",
        ]
        for i in m.inputs:
            out.append(
                f"| {i.get('kind','')} | `{i.get('identifier','')}` | "
                f"{i.get('source','')} | {i.get('retrieved_utc','')} | "
                f"{i.get('licence','')} |"
            )
        out += ["", "## 2. Method", ""]
        for a in m.algorithms:
            out.append(f"**{a['name']}** v{a['version']}")
            if a.get("reference"):
                out.append(f"  \n*{a['reference']}*")
            if a.get("params"):
                out.append("")
                out.append("| Parameter | Value |")
                out.append("|---|---|")
                for k, v in sorted(a["params"].items()):
                    out.append(f"| `{k}` | `{v}` |")
            out.append("")

        out += ["## 3. Results", "", "| Quantity | Value | Units | Digest |", "|---|---|---|---|"]
        for o in m.outputs:
            out.append(f"| {o['name']} | {o['value']} | {o['units']} | "
                       f"`{o['digest'][:16]}…` |")

        if self.verdict:
            v = self.verdict.to_dict()
            out += [
                "", "### Spatial attribution", "",
                f"- Total disturbed surface: **{v['total_disturbed_ha']} ha**",
                f"- Confidently inside the titled polygon: **{v['inside_title_ha']} ha**",
                f"- Confidently outside it: **{v['outside_title_ha']} ha**",
                f"- Within the ±{v['boundary_tolerance_m']} m boundary tolerance, "
                f"therefore indeterminate: **{v['indeterminate_boundary_ha']} ha**",
            ]
            for ov in v.get("restricted_overlaps", []):
                out.append(f"- Overlap with {ov['kind']} *{ov['name']}* "
                           f"(`{ov['identifier']}`): **{ov['overlap_ha']} ha** — "
                           f"{ov['legal_basis']}")
            for n in v.get("notes", []):
                out.append(f"- Note: {n}")

        if self.trend:
            out += ["", "### Change over time", ""]
            for k, val in self.trend.items():
                out.append(f"- `{k}`: {val}")

        if self.deformation:
            out += ["", "### Ground movement", ""]
            for k, val in self.deformation.items():
                out.append(f"- `{k}`: {val}")

        if self.reconciliation:
            out += ["", "### Declaration screening", ""]
            for k, val in self.reconciliation.items():
                out.append(f"- `{k}`: {val}")

        if m.assumptions:
            out += ["", "## 4. Assumptions", ""] + [f"- {a}" for a in m.assumptions]
        if m.limitations:
            out += ["", "## 5. Limitations", ""] + [f"- {l}" for l in m.limitations]

        out += ["", "## 6. Reproduction", "", "```", replay_recipe(m), "```", ""]
        return "\n".join(out)

    # ------------------------------------------------------------------
    # 2. administrative system
    # ------------------------------------------------------------------

    def administrative_notice(self) -> str:
        """The act that opens the contradictory procedure.

        Deliberately a *notice*, not a penalty. The software's competence ends
        at telling the holder what has been observed and inviting an answer.
        Whether an infraction exists is a judgement reserved to the official
        who signs, and the template says so where the signature goes.
        """
        self._require_real("an administrative notice")
        if self.case.state not in (CaseState.CORROBORATED, CaseState.NOTIFIED):
            raise RuntimeError(
                "a notice may only be issued from a corroborated case; this case is "
                f"{self.case.state.value}. Corroboration by an independent line of "
                "evidence is not a formality — a single-sensor detection is not a "
                "sufficient basis for a coercive act."
            )
        return (self._notice_pt() if self.frame.language == "pt" else self._notice_en())

    def _notice_en(self) -> str:
        v = self.verdict.to_dict() if self.verdict else {}
        return "\n".join([
            f"# Notice of observed facts — {self.case.case_id}",
            "",
            f"**Issuing authority.** {self.frame.authority}",
            f"**Addressee.** {self.case.holder} — title of record "
            f"`{self.case.title_id}`",
            f"**Date of issue.** {date.today().isoformat()}",
            f"**Evidence manifest.** `{self.manifest.manifest_id}` "
            f"(hash `{self.manifest.manifest_hash[:24]}…`)",
            "",
            "## 1. What has been observed",
            "",
            self._facts_paragraph(v),
            "",
            "## 2. On what basis",
            "",
            "The observation was made from publicly available satellite imagery of the "
            "Copernicus programme, processed with published methods. The complete "
            "method, every parameter, the identifiers of every image used and the "
            "cryptographic hashes of the results are set out in the technical annex "
            "accompanying this notice. You may reproduce the result independently; "
            "the annex contains the instructions to do so.",
            "",
            "## 3. What this notice is, and is not",
            "",
            "This notice records observed facts and opens a procedure. **It is not a "
            "finding of infraction, a penalty, or a determination of any amount owed.** "
            "No such determination will be made before your response has been received "
            "and considered.",
            "",
            "## 4. Your right to respond",
            "",
            f"You have **{self.frame.response_window_days} days** from receipt to "
            "present a response, in any form, including: evidence that the works are "
            "authorised by an instrument not reflected in the registry extract used; "
            "evidence that the boundary of record is incorrect; survey data; or any "
            "other explanation.",
            "",
            "Your response will be recorded in the same evidence register as this "
            "notice, with the same integrity protections, and will be considered "
            "before any further step. If your response resolves the matter, the case "
            "will be closed and the closure published.",
            "",
            f"Legal basis for this procedure: {self.frame.due_process}",
            f"Applicable substantive provisions: {self._applicable_norms()}",
            "",
            "## 5. Access to the underlying data",
            "",
            "The satellite imagery is public and free. The registry data is public. "
            "You are entitled to all of it and to the derived products; the annex "
            "lists where each item may be obtained. "
            f"({self.frame.information_access})",
            "",
            "---",
            "",
            "_Signature of the responsible official, who alone determines whether the "
            "observed facts constitute an infraction:_",
            "",
            "Name: ______________________  Post: ______________________  "
            "Date: ____________",
        ])

    def _notice_pt(self) -> str:
        v = self.verdict.to_dict() if self.verdict else {}
        return "\n".join([
            f"# Notificação de fatos observados — {self.case.case_id}",
            "",
            f"**Autoridade emitente.** {self.frame.authority}",
            f"**Destinatário.** {self.case.holder} — título de registro "
            f"`{self.case.title_id}`",
            f"**Data de emissão.** {date.today().isoformat()}",
            f"**Manifesto de evidência.** `{self.manifest.manifest_id}` "
            f"(hash `{self.manifest.manifest_hash[:24]}…`)",
            "",
            "## 1. O que foi observado",
            "",
            self._facts_paragraph_pt(v),
            "",
            "## 2. Com que base",
            "",
            "A observação foi feita a partir de imagens de satélite públicas do "
            "programa Copernicus, processadas por métodos publicados. O método "
            "completo, todos os parâmetros, os identificadores de cada imagem "
            "utilizada e os hashes criptográficos dos resultados constam do anexo "
            "técnico que acompanha esta notificação. V. Sa. pode reproduzir o "
            "resultado de forma independente; o anexo traz as instruções.",
            "",
            "## 3. O que esta notificação é — e o que não é",
            "",
            "Esta notificação registra fatos observados e instaura procedimento. "
            "**Não constitui auto de infração, penalidade, nem apuração de valor "
            "devido.** Nenhuma dessas providências será adotada antes de recebida e "
            "apreciada a manifestação de V. Sa.",
            "",
            "## 4. Direito de manifestação",
            "",
            f"V. Sa. dispõe de **{self.frame.response_window_days} dias** contados do "
            "recebimento para apresentar manifestação, por qualquer meio, inclusive: "
            "comprovação de que as obras estão autorizadas por instrumento não "
            "refletido no extrato cadastral utilizado; demonstração de erro no limite "
            "poligonal de registro; levantamento topográfico; ou qualquer outra "
            "explicação.",
            "",
            "A manifestação será registrada no mesmo registro de evidências desta "
            "notificação, com as mesmas garantias de integridade, e será apreciada "
            "antes de qualquer providência ulterior. Se a manifestação resolver a "
            "questão, o caso será arquivado e o arquivamento publicado.",
            "",
            f"Fundamento processual: {self.frame.due_process}",
            f"Dispositivos materiais aplicáveis: {self._applicable_norms()}",
            "",
            "## 5. Acesso aos dados subjacentes",
            "",
            "As imagens de satélite são públicas e gratuitas. Os dados cadastrais são "
            "públicos. V. Sa. tem direito a todos eles e aos produtos derivados; o "
            "anexo indica onde obter cada item. "
            f"({self.frame.information_access})",
            "",
            "---",
            "",
            "_Assinatura do servidor responsável, a quem compete exclusivamente decidir "
            "se os fatos observados configuram infração:_",
            "",
            "Nome: ______________________  Cargo: ______________________  "
            "Data: ____________",
        ])

    def _facts_paragraph(self, v: Dict) -> str:
        if not v:
            return "See the technical annex."
        parts = [
            f"Between the first and last usable observation, the disturbed surface at "
            f"this site measured **{v['total_disturbed_ha']} hectares**."
        ]
        if v.get("outside_title_ha", 0) > 0.5:
            parts.append(
                f"Of that, **{v['outside_title_ha']} hectares lie outside the polygon "
                f"of title `{self.case.title_id}`**, measured with a boundary tolerance "
                f"of ±{BOUNDARY_TOLERANCE_M} m in your favour. A further "
                f"{v['indeterminate_boundary_ha']} hectares fall within that tolerance "
                "and are **not** counted against you."
            )
        for ov in v.get("restricted_overlaps", []):
            parts.append(
                f"**{ov['overlap_ha']} hectares** of the disturbed surface fall inside "
                f"{ov['name']} ({ov['kind']}), an area subject to {ov['legal_basis']}."
            )
        if self.trend and self.trend.get("breakpoint"):
            parts.append(
                f"The rate of expansion changed around **{self.trend['breakpoint']}**, "
                f"from {self.trend.get('slope_before_breakpoint')} to "
                f"{self.trend.get('slope_after_breakpoint')} hectares per month."
            )
        return " ".join(parts)

    def _facts_paragraph_pt(self, v: Dict) -> str:
        if not v:
            return "Ver anexo técnico."
        parts = [
            f"Entre a primeira e a última observação utilizável, a superfície "
            f"antropizada no local mediu **{v['total_disturbed_ha']} hectares**."
        ]
        if v.get("outside_title_ha", 0) > 0.5:
            parts.append(
                f"Desse total, **{v['outside_title_ha']} hectares situam-se fora do "
                f"polígono do título `{self.case.title_id}`**, apurados com tolerância "
                f"de ±{BOUNDARY_TOLERANCE_M} m em favor do administrado. Outros "
                f"{v['indeterminate_boundary_ha']} hectares recaem dentro dessa "
                "tolerância e **não** são computados."
            )
        for ov in v.get("restricted_overlaps", []):
            parts.append(
                f"**{ov['overlap_ha']} hectares** da superfície antropizada recaem em "
                f"{ov['name']} ({ov['kind']}), área sujeita a {ov['legal_basis']}."
            )
        if self.trend and self.trend.get("breakpoint"):
            parts.append(
                f"A taxa de expansão alterou-se por volta de "
                f"**{self.trend['breakpoint']}**, passando de "
                f"{self.trend.get('slope_before_breakpoint')} para "
                f"{self.trend.get('slope_after_breakpoint')} hectares por mês."
            )
        return " ".join(parts)

    def _applicable_norms(self) -> str:
        f = self.frame
        picks = []
        v = self.verdict.to_dict() if self.verdict else {}
        if v.get("outside_title_ha", 0) > 0.5:
            picks.append(f.extraction_outside_title)
        if v.get("restricted_overlaps"):
            picks.append(f.protected_area)
        if not self.case.title_id:
            picks.append(f.unlicensed_extraction)
        return "; ".join(p for p in picks if p) or f.unlicensed_extraction

    # ------------------------------------------------------------------
    # 3. legal system
    # ------------------------------------------------------------------

    def judicial_dossier(self) -> str:
        self._require_real("a judicial dossier")
        m = self.manifest
        return "\n".join([
            f"# Evidence dossier — {self.case.case_id}",
            "",
            "## Custody",
            "",
            f"- Manifest `{m.manifest_id}`, sealed {m.created_utc}.",
            f"- Manifest hash `{m.manifest_hash}`.",
            f"- Preceding ledger entry `{m.prev_hash}`.",
            "- The ledger is append-only and hash-chained: every entry carries the "
            "hash of its predecessor, so removal or alteration of any earlier entry "
            "invalidates every later one. The chain may be verified independently "
            "with `minerva ledger verify`.",
            "",
            "## Nature of the evidence",
            "",
            "- **Primary data** are satellite images acquired by public instruments "
            "and distributed under a free and open licence. They were not created for "
            "this proceeding, are held by a third party, and can be obtained "
            "independently by any party.",
            "- **Derived products** are the output of published algorithms at recorded "
            "versions with recorded parameters, applied to those images. Every "
            "derivation step is listed; none is proprietary; none is irreproducible.",
            "- The distinction matters: the imagery is a record of the world, while "
            "the derived products are an interpretation of that record. The "
            "interpretation is contestable on its merits and the dossier is built to "
            "make contesting it possible rather than difficult.",
            "",
            "## Limitations that must be put before the court",
            "",
            *[f"- {l}" for l in (m.limitations or ["none recorded — this is itself a defect"])],
            "",
            "## Procedural history",
            "",
            *[f"- {t.at_utc}: {t.frm} → {t.to} ({t.actor}, {t.actor_role})"
              + (f" — {t.note}" if t.note else "")
              for t in self.case.history],
            "",
            "## Response of the affected party",
            "",
            (self._response_block() if self.case.response else
             "- No response recorded. The response window "
             f"{'has closed' if self.case.response_due else 'was not opened'}; "
             f"due {self.case.response_due or 'n/a'}."),
            "",
            "## Statement on scope",
            "",
            "This dossier establishes what was observed and how. It does not "
            "establish intent, authorship of the works, or the existence of an "
            "infraction, all of which require evidence this method cannot supply.",
        ])

    def _response_block(self) -> str:
        r = self.case.response
        return "\n".join([
            f"- Received {r.received_utc} from {r.submitted_by} via {r.channel}.",
            f"- Digest `{r.digest()}`.",
            f"- Summary: {r.summary}",
            f"- Documents: {', '.join(r.documents) if r.documents else 'none'}",
            f"- Reviewer: {r.reviewer or 'not yet assessed'}"
            + (f" — {r.review_note}" if r.review_note else ""),
        ])

    # ------------------------------------------------------------------
    # 4. public sphere
    # ------------------------------------------------------------------

    def public_card(self) -> Dict:
        """What may be published, in words a non-specialist can act on."""
        from .cases import PublicationState

        pub = self.case.public_view()
        if pub is None:
            if self.case.publication is PublicationState.PARTY_ONLY:
                reason = (
                    "The holder has been notified and the response window is running. "
                    "The case is visible to the notified party, and to nobody else, "
                    "until it is resolved. Publishing an unresolved allegation would "
                    "impose the reputational penalty before the procedure that is "
                    "supposed to decide it."
                )
            else:
                reason = (
                    "The affected party has not yet been notified. Publishing before "
                    "notification would be unfair and would compromise the procedure."
                )
            return {"publishable": False, "reason": reason,
                    "publication_state": self.case.publication.value}
        v = self.verdict.to_dict() if self.verdict else {}
        sim = self._is_synthetic()
        return {
            "publishable": True,
            "simulation": sim,
            "banner": "SIMULATED EXAMPLE — not a real site" if sim else None,
            "case_id": self.case.case_id,
            "headline": self._headline(v),
            "plain_language": self._plain(v),
            "what_this_is_not": (
                "A detection is not a conviction and not a finding of wrongdoing. It "
                "means an authority has seen something in public satellite imagery "
                "that it has asked the operator to explain. Many detections have "
                "lawful explanations."
            ),
            "status": self.case.state.value,
            "operator_responded": self.case.response is not None,
            "evidence_manifest": self.manifest.manifest_id,
            "how_to_check_this_yourself": (
                "Every image used is free to download and every step is published. "
                "The technical annex lists the image identifiers and the exact "
                "parameters."
            ),
            "figures": self.figures,
        }

    def _headline(self, v: Dict) -> str:
        if v.get("outside_title_ha", 0) > 0.5:
            return (f"{v['outside_title_ha']:,.1f} hectares of mining disturbance outside "
                    f"the licensed area")
        if v.get("restricted_overlaps"):
            ov = v["restricted_overlaps"][0]
            return f"{ov['overlap_ha']:,.1f} hectares of disturbance inside {ov['name']}"
        return (f"{v.get('total_disturbed_ha', 0):,.1f} hectares of mining disturbance "
                "mapped, all of it inside the licensed area")

    def _plain(self, v: Dict) -> str:
        bits = [
            f"Satellite images show about {v.get('total_disturbed_ha', 0):,.0f} hectares "
            f"of ground stripped for mining at this site."
        ]
        if v.get("outside_title_ha", 0) > 0.5:
            bits.append(
                f"About {v['outside_title_ha']:,.0f} hectares of that is outside the area "
                "the company is licensed to work. The measurement leaves a margin of "
                f"{BOUNDARY_TOLERANCE_M} metres around the boundary in the company's "
                "favour, so the true figure is unlikely to be smaller."
            )
        if self.trend and self.trend.get("breakpoint"):
            bits.append(
                f"The site started expanding much faster around "
                f"{self.trend['breakpoint']}."
            )
        return " ".join(bits)

    # ------------------------------------------------------------------
    # 5. political system
    # ------------------------------------------------------------------

    @staticmethod
    def oversight_brief(cases: Sequence[Case], period: str,
                        inspector_headcount: Optional[int] = None,
                        sites_monitored: Optional[int] = None) -> str:
        """The aggregate view — capacity, coverage, and what it costs.

        Written for the register in which oversight budgets are actually
        decided: not hectares, but how many sites one official can now cover.
        """
        by_state: Dict[str, int] = {}
        for c in cases:
            by_state[c.state.value] = by_state.get(c.state.value, 0) + 1
        notified = by_state.get("notified", 0) + by_state.get("contested", 0)
        resolved = by_state.get("substantiated", 0) + by_state.get("dismissed", 0)
        dismissed = by_state.get("dismissed", 0)

        lines = [
            f"# Oversight brief — {period}",
            "",
            f"- Sites under continuous satellite observation: "
            f"**{sites_monitored if sites_monitored is not None else 'n/a'}**",
            f"- Cases opened: **{len(cases)}**",
            f"- Cases at or past notification: **{notified}**",
            f"- Cases resolved: **{resolved}** (of which dismissed after the operator "
            f"responded: **{dismissed}**)",
        ]
        if inspector_headcount:
            per = (sites_monitored or 0) / max(inspector_headcount, 1)
            lines += [
                f"- Inspecting staff: **{inspector_headcount}**",
                f"- Sites observed per member of staff: **{per:,.0f}**",
                "",
                "The relevant comparison is not with a fully staffed inspectorate but "
                "with the counterfactual: how many of these sites would have been "
                "looked at this period without continuous observation.",
            ]
        lines += [
            "",
            "## Dismissal rate is a quality metric, not a failure",
            "",
            "A screening system with a zero dismissal rate is a system that is not "
            "screening — it is only confirming what was already known. A dismissal "
            "following an operator's explanation is the procedure working, and each "
            "one is fed back as a labelled negative that improves the next screen.",
        ]
        return "\n".join(lines)


def build_manifest_for_case(
    site_id: str,
    question: str,
    scenes_sources: Sequence,
    observations: Sequence[Observation],
    frame: LegalFrame,
    extra_datasets: Sequence[Dict] = (),
    prev_hash: str = "0" * 64,
) -> EvidenceManifest:
    """Assemble the manifest that a case will be opened on."""
    m = EvidenceManifest.create(site_id=site_id, question=question,
                                jurisdiction=frame.jurisdiction, prev_hash=prev_hash)
    m.add_sources(list(scenes_sources))
    for d in extra_datasets:
        m.add_dataset(**d)

    seen = set()
    for o in observations:
        key = (o.detector, o.algorithm_version)
        if key in seen:
            continue
        seen.add(key)
        refs = o.detail.get("index_references") or {}
        if isinstance(refs, dict):
            reference = "  \n".join(f"{k.upper()}: {v}" for k, v in sorted(refs.items()))
        else:
            reference = str(refs)
        m.add_algorithm(o.detector, params=o.params, reference=reference)

    m.note_limitation(
        "Optical satellite observation cannot see through cloud. Periods with no "
        "usable observation are listed explicitly and must not be read as periods "
        "of inactivity."
    )
    m.note_limitation(
        "The footprint rule delineates disturbed bare mineral surface. It does not "
        "distinguish active extraction from a stockpile, a haul road, an exploration "
        "clearing or a recently abandoned working."
    )
    m.note_limitation(
        f"Boundary attribution carries a ±{BOUNDARY_TOLERANCE_M} m tolerance, applied "
        "in favour of the title holder. Area within that tolerance is reported "
        "separately and is never counted as a violation."
    )
    m.note_limitation(
        "Cadastral geometry is taken from the public registry extract identified in "
        "the inputs. If the registry is wrong, this result is wrong in the same way, "
        "and the holder's response is the mechanism for correcting it."
    )
    m.note_assumption(
        "Detection thresholds are the humid-tropical defaults and have not been "
        "recalibrated against local ground truth unless an input above says otherwise."
    )
    return m
