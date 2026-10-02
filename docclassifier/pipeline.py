from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from .classifier import Classifier
from .extractors import ExtractionError, ExtractorRegistry
from .models import DocumentInfo
from .naming import NamingConvention


@dataclass(frozen=True)
class RenameAction:
    source: Path
    target: Path
    category: str


@dataclass(frozen=True)
class Skipped:
    path: Path
    reason: str


@dataclass
class RenamePlan:
    actions: list[RenameAction] = field(default_factory=list)
    skipped: list[Skipped] = field(default_factory=list)


class RenamePipeline:
    """Scan -> extract -> classify -> name -> (optionally) rename."""

    def __init__(self, registry: ExtractorRegistry, classifier: Classifier, naming: NamingConvention):
        self._registry = registry
        self._classifier = classifier
        self._naming = naming

    def plan(self, root: Path) -> RenamePlan:
        plan = RenamePlan()
        taken: set[Path] = set()
        files = sorted(p for p in root.rglob("*") if p.is_file())
        taken.update(files)  # existing names are never overwritten
        for path in files:
            if path.name.startswith(("~$", ".")) or not self._registry.supports(path):
                plan.skipped.append(Skipped(path, "unsupported or temporary file"))
                continue
            try:
                content = self._registry.extract(path)
            except ExtractionError as exc:
                plan.skipped.append(Skipped(path, str(exc)))
                continue
            info = DocumentInfo(
                path=path,
                content=content,
                classification=self._classifier.classify(content, path.stem),
                fallback_date=date.fromtimestamp(path.stat().st_mtime),
            )
            target = self._unique(path.with_name(self._naming.stem_for(info) + path.suffix.lower()), path, taken)
            if target != path:
                taken.discard(path)
                taken.add(target)
                plan.actions.append(RenameAction(path, target, info.classification.category))
        return plan

    @staticmethod
    def _unique(target: Path, source: Path, taken: set[Path]) -> Path:
        if target == source or target not in taken:
            return target
        n = 2
        while True:
            candidate = target.with_name(f"{target.stem}_{n}{target.suffix}")
            if candidate not in taken:
                return candidate
            n += 1

    def apply(self, plan: RenamePlan, log_path: Path | None = None) -> int:
        done: list[RenameAction] = []
        for action in plan.actions:
            if action.target.exists():  # re-check at execution time
                continue
            action.source.rename(action.target)
            done.append(action)
        if log_path and done:
            log_path.write_text(json.dumps(
                {"time": datetime.now().isoformat(),
                 "renames": [{"from": str(a.source), "to": str(a.target)} for a in done]},
                indent=2))
        return len(done)


def undo(log_path: Path) -> int:
    """Reverse a rename log written by ``RenamePipeline.apply``."""
    renames = json.loads(log_path.read_text())["renames"]
    count = 0
    for r in reversed(renames):
        src, dst = Path(r["to"]), Path(r["from"])
        if src.exists() and not dst.exists():
            src.rename(dst)
            count += 1
    return count
