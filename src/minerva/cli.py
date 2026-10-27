"""Command line.

    minerva demo            run the simulated site end to end
    minerva ledger verify   check the integrity of the evidence chain
    minerva case show       print a case and its dossiers
    minerva notice          emit the administrative notice for a case
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .cases import CaseRegister
from .dossier import SyntheticEvidenceError


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="minerva", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("demo", help="run the simulated site end to end")
    d.add_argument("--out", default="data/out")
    d.add_argument("--seed", type=int, default=20260819)

    lv = sub.add_parser("ledger", help="evidence ledger operations")
    lv.add_argument("action", choices=["verify", "head", "list"])
    lv.add_argument("--root", default="data/out/cases")

    cs = sub.add_parser("case", help="inspect a case")
    cs.add_argument("action", choices=["show", "list", "annex", "notice", "public"])
    cs.add_argument("--root", default="data/out/cases")
    cs.add_argument("--id", default="")

    args = ap.parse_args(argv)

    if args.cmd == "demo":
        from .pipeline import run_demo
        r = run_demo(args.out, seed=args.seed)
        print(f"site      {r.site_id}")
        print(f"scenes    {r.scenes}")
        print(f"disturbed {r.verdict.total_disturbed_ha:,.1f} ha")
        print(f"outside   {r.verdict.outside_title_ha:,.1f} ha "
              f"(+{r.verdict.indeterminate_ha:,.1f} ha indeterminate)")
        for ov in r.verdict.restricted_overlaps:
            print(f"overlap   {ov['overlap_ha']:,.1f} ha in {ov['name']}")
        print(f"growth    {r.trend.current_rate_per_month:,.2f} ha/month now"
              + (f", rate change at {r.trend.breakpoint}" if r.trend.breakpoint else ""))
        print(f"case      {r.case.case_id} [{r.case.state.value}]")
        print(f"outputs   {args.out}")
        return 0

    if args.cmd == "ledger":
        reg = CaseRegister(args.root)
        if args.action == "verify":
            report = reg.ledger.verify_chain()
            print(json.dumps(report, indent=2))
            return 0 if report["intact"] else 2
        if args.action == "head":
            print(reg.ledger.head())
            return 0
        for e in reg.ledger.entries():
            print(f"{e['manifest_id']}  {e['created_utc']}  {e['site_id']}  "
                  f"{e['manifest_hash'][:16]}…")
        return 0

    if args.cmd == "case":
        reg = CaseRegister(args.root)
        if args.action == "list":
            for c in reg.all_cases():
                print(f"{c.case_id}  {c.state.value:<14} {c.severity:<8} {c.site_id}  "
                      f"{c.holder}")
            return 0
        if not args.id:
            print("--id is required", file=sys.stderr)
            return 1
        c = reg.load(args.id)
        if args.action == "show":
            print(json.dumps(c.to_dict(), indent=2, ensure_ascii=False))
            return 0
        annex = Path(args.root).parent / f"{c.case_id}_technical_annex.md"
        if args.action == "annex":
            print(annex.read_text(encoding="utf-8") if annex.exists()
                  else "no annex on disk; re-run the pipeline")
            return 0
        if args.action == "public":
            card = Path(args.root).parent / f"{c.case_id}_public_card.json"
            print(card.read_text(encoding="utf-8") if card.exists() else "{}")
            return 0
        if args.action == "notice":
            print("Rebuilding a notice requires the run context; use the pipeline API. "
                  "This subcommand exists to make the guard visible:", file=sys.stderr)
            try:
                raise SyntheticEvidenceError(
                    "notices are never issued from the CLI against a stored case "
                    "without re-verifying the evidence chain"
                )
            except SyntheticEvidenceError as e:
                print(str(e), file=sys.stderr)
                return 3
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
