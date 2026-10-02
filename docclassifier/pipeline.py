from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from pathlib import Path

from .classifier import Classifier
from .extractors import ContentReader, ExtractionError
from .journal import RenameJournal
from .models import DocumentInfo
from .naming import Namer


class SkipReason(Enum):
    UNSUPPORTED = "unsupported file type"
    TEMPORARY = "temporary or hidden file"
    UNREADABLE = "could not be read"


@dataclass(frozen=True)
class RenameAction:
    source: Path
    target: Path
    category: str


@dataclass(frozen=True)
class SkippedFile:
    path: Path
    reason: SkipReason
    detail: str = ""


@dataclass
class RenamePlan:
    actions: list[RenameAction] = field(default_factory=list)
    skipped: list[SkippedFile] = field(default_factory=list)


@dataclass(frozen=True)
class ApplyResult:
    renamed: tuple[RenameAction, ...] = ()
    conflicts: tuple[RenameAction, ...] = ()  # target appeared after planning
    failed: tuple[tuple[RenameAction, str], ...] = ()  # OS error message


def _is_hidden(path: Path, root: Path) -> bool:
    parts = path.relative_to(root).parts
    return any(p.startswith((".", "~$")) for p in parts)


class RenamePipeline:
    """Scan -> extract -> classify -> name (plan), then rename (apply)."""

    def __init__(self, reader: ContentReader, classifier: Classifier, namer: Namer):
        self._reader = reader
        self._classifier = classifier
        self._namer = namer

    def plan(self, root: Path) -> RenamePlan:
        plan = RenamePlan()
        files = sorted(p for p in root.rglob("*") if p.is_file())
        taken = {p.resolve().as_posix().casefold() for p in files}  # never overwrite; case-insensitive safe
        for path in files:
            if _is_hidden(path, root):
                plan.skipped.append(SkippedFile(path, SkipReason.TEMPORARY))
                continue
            if not self._reader.supports(path):
                plan.skipped.append(SkippedFile(path, SkipReason.UNSUPPORTED))
                continue
            try:
                content = self._reader.extract(path)
            except ExtractionError as exc:
                plan.skipped.append(SkippedFile(path, SkipReason.UNREADABLE, str(exc)))
                continue
            info = DocumentInfo(
                path=path,
                content=content,
                classification=self._classifier.classify(content, path.stem),
                fallback_date=date.fromtimestamp(path.stat().st_mtime),
            )
            wanted = path.with_name(self._namer.stem_for(info) + path.suffix.lower())
            target = self._unique(wanted, path, taken)
            if target != path:
                taken.discard(path.resolve().as_posix().casefold())
                taken.add(target.resolve().as_posix().casefold())
                plan.actions.append(RenameAction(path, target, info.classification.category))
        return plan

    @staticmethod
    def _unique(target: Path, source: Path, taken: set[str]) -> Path:
        key = lambda p: p.resolve().as_posix().casefold()  # noqa: E731
        if target == source or key(target) == key(source) or key(target) not in taken:
            return target
        n = 2
        while True:
            candidate = target.with_name(f"{target.stem}_{n}{target.suffix}")
            if key(candidate) not in taken:
                return candidate
            n += 1

    def apply(self, plan: RenamePlan, journal: RenameJournal) -> ApplyResult:
        """Rename every planned file, recording each success in ``journal`` immediately."""
        renamed, conflicts, failed = [], [], []
        for action in plan.actions:
            if action.target.exists():
                conflicts.append(action)
                continue
            try:
                action.source.rename(action.target)
            except OSError as exc:
                failed.append((action, str(exc)))
                continue
            journal.record(action.source, action.target)
            renamed.append(action)
        return ApplyResult(tuple(renamed), tuple(conflicts), tuple(failed))
