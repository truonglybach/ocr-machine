from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .classifier import KeywordClassifier
from .extractors import default_registry
from .naming import DEFAULT_TEMPLATE, NamingConvention
from .pipeline import RenamePipeline, undo


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="docclassifier", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("rename", help="classify and rename documents under a folder")
    run.add_argument("folder", type=Path)
    run.add_argument("--template", default=DEFAULT_TEMPLATE,
                     help="fields: {date} {category} {title} {original} (default: %(default)s)")
    run.add_argument("--apply", action="store_true", help="actually rename (default is a dry run)")
    run.add_argument("--log", type=Path, default=Path("rename_log.json"), help="undo log path")
    un = sub.add_parser("undo", help="reverse a previous rename using its log")
    un.add_argument("log", type=Path)
    args = ap.parse_args(argv)

    if args.cmd == "undo":
        print(f"Restored {undo(args.log)} file(s).")
        return 0
    if not args.folder.is_dir():
        print(f"Not a folder: {args.folder}", file=sys.stderr)
        return 2
    pipeline = RenamePipeline(default_registry(), KeywordClassifier(), NamingConvention(args.template))
    plan = pipeline.plan(args.folder)
    for a in plan.actions:
        print(f"{a.source}  ->  {a.target.name}  [{a.category}]")
    for s in plan.skipped:
        print(f"SKIP {s.path}: {s.reason}", file=sys.stderr)
    if args.apply:
        print(f"Renamed {pipeline.apply(plan, args.log)} file(s). Undo log: {args.log}")
    else:
        print(f"Dry run: {len(plan.actions)} rename(s) planned. Re-run with --apply to proceed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
