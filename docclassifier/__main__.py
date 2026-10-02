"""Classify .docx/.xlsx (and text) documents and rename them to a consistent convention."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .classifier import KeywordClassifier
from .extractors import default_registry
from .journal import JournalError, RenameJournal, default_journal_path
from .naming import DEFAULT_TEMPLATE, FIELDS, NamingConvention
from .pipeline import RenamePipeline


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="docclassifier", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("rename", help="classify and rename documents under a folder")
    run.add_argument("folder", type=Path)
    run.add_argument("--template", default=DEFAULT_TEMPLATE,
                     help="fields: " + " ".join("{%s}" % f for f in sorted(FIELDS)) + " (default: %(default)s)")
    run.add_argument("--apply", action="store_true", help="actually rename (default is a dry run)")
    run.add_argument("--log", type=Path, default=None,
                     help="undo journal path (default: rename_log_<timestamp>.jsonl in the current folder)")
    un = sub.add_parser("undo", help="reverse a previous rename using its journal")
    un.add_argument("log", type=Path)
    return ap


def _rename(args: argparse.Namespace) -> int:
    if not args.folder.is_dir():
        print(f"Not a folder: {args.folder}", file=sys.stderr)
        return 2
    pipeline = RenamePipeline(default_registry(), KeywordClassifier(), NamingConvention(args.template))
    plan = pipeline.plan(args.folder)
    for a in plan.actions:
        print(f"{a.source}  ->  {a.target.name}  [{a.category}]")
    for s in plan.skipped:
        print(f"SKIP {s.path}: {s.reason.value} {s.detail}".rstrip(), file=sys.stderr)
    if not args.apply:
        print(f"Dry run: {len(plan.actions)} rename(s) planned. Re-run with --apply to proceed.")
        return 0
    log_path = args.log or default_journal_path()
    if log_path.exists():
        print(f"Refusing to append to existing journal: {log_path}", file=sys.stderr)
        return 2
    journal = RenameJournal(log_path)
    result = pipeline.apply(plan, journal)
    print(f"Renamed {len(result.renamed)} file(s). Undo journal: {journal.path}")
    for a in result.conflicts:
        print(f"CONFLICT (target exists, left unchanged): {a.source}", file=sys.stderr)
    for f in result.failed:
        print(f"FAILED {f.action.source}: {f.error}", file=sys.stderr)
    return 1 if (result.failed or result.conflicts) else 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.cmd == "undo":
            res = RenameJournal(args.log).undo()
            print(f"Restored {res.restored} file(s).")
            for p in res.not_restored:
                print(f"NOT RESTORED (missing, or original name taken): {p}", file=sys.stderr)
            return 1 if res.not_restored else 0
        return _rename(args)
    except (ValueError, JournalError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
