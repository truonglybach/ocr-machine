from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

UNCATEGORIZED = "other"


@dataclass(frozen=True)
class ExtractedContent:
    """Text and metadata pulled out of a single file."""
    text: str
    title: str | None = None
    document_date: date | None = None


@dataclass(frozen=True)
class Classification:
    category: str
    score: int = 0


@dataclass(frozen=True)
class DocumentInfo:
    """Everything a naming convention needs to build a file name."""
    path: Path
    content: ExtractedContent
    classification: Classification
    fallback_date: date
