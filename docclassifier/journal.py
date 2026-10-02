"""Append-only rename journal: the single owner of the undo-log format."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class UndoResult:
    restored: int
    not_restored: tuple[Path, ...] = ()  # current (renamed) paths that could not be reverted


class JournalError(Exception):
    """Raised when a journal cannot be read."""


def default_journal_path(directory: Path = Path(".")) -> Path:
    """A fresh timestamped path, so one run never overwrites another run's undo log."""
    return directory / f"rename_log_{datetime.now():%Y%m%d_%H%M%S_%f}.jsonl"


class RenameJournal:
    """One JSON line per completed rename, flushed immediately.

    Written incrementally so a crash midway still leaves a usable undo log.
    """

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)  # fail early, not mid-batch

    def record(self, source: Path, target: Path) -> None:
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"from": str(source), "to": str(target)}) + "\n")
            fh.flush()

    def entries(self) -> list[tuple[Path, Path]]:
        try:
            lines = [ln for ln in self.path.read_text(encoding="utf-8").splitlines() if ln.strip()]
            rows = []
            for i, line in enumerate(lines):
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    if i == len(lines) - 1:  # a crash mid-write may truncate only the last line
                        break
                    raise
            return [(Path(r["from"]), Path(r["to"])) for r in rows]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise JournalError(f"Cannot read journal {self.path}: {exc}") from exc

    def undo(self) -> UndoResult:
        restored, conflicts = 0, []
        for original, renamed in reversed(self.entries()):
            if not (renamed.exists() and not original.exists()):
                conflicts.append(renamed)
                continue
            try:
                renamed.rename(original)
                restored += 1
            except OSError:
                conflicts.append(renamed)
        return UndoResult(restored, tuple(conflicts))
