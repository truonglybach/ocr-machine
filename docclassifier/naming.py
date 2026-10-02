from __future__ import annotations

import re
import unicodedata
from datetime import date
from string import Formatter
from typing import Protocol

from .models import UNCATEGORIZED, DocumentInfo

DEFAULT_TEMPLATE = "{date}_{category}_{title}"
FIELDS = frozenset({"date", "category", "title", "original"})


def slugify(value: str, max_len: int = 50) -> str:
    """Lowercase ASCII, hyphen-separated, safe for any filesystem."""
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug[:max_len].strip("-")


class Namer(Protocol):
    def stem_for(self, info: DocumentInfo) -> str: ...


class NamingConvention:
    """Builds file stems from a template, e.g. ``{date}_{category}_{title}``.

    Fields: date (YYYY-MM-DD), category, title (slugified), original (original stem).
    The file extension is preserved by the caller. Raises ValueError for an invalid template.
    """

    def __init__(self, template: str = DEFAULT_TEMPLATE, date_format: str = "%Y-%m-%d"):
        parsed = [(f, spec, conv) for _, f, spec, conv in Formatter().parse(template) if f is not None]
        fields = [f for f, _, _ in parsed]
        if any(spec or conv for _, spec, conv in parsed):
            raise ValueError("Format specs and conversions (':' / '!') are not supported in templates")
        if not fields:
            raise ValueError("Template must contain at least one field")
        bad = [f for f in fields if f not in FIELDS]
        if bad:
            raise ValueError(f"Unknown template fields {bad}; allowed: {sorted(FIELDS)}")
        if re.search(r"[\\/]", template) or ".." in template:
            raise ValueError("Template must not contain path separators or '..'")
        try:
            sample = date(2000, 1, 2).strftime(date_format)
        except ValueError as exc:
            raise ValueError(f"Invalid date_format: {exc}") from exc
        if not sample or re.search(r"[\\/]|\.\.", sample):
            raise ValueError("date_format must not be empty or produce path separators or '..'")
        self._template = template
        self._date_format = date_format

    def stem_for(self, info: DocumentInfo) -> str:
        doc_date = info.content.document_date or info.fallback_date
        title = slugify(info.content.title or "") or slugify(info.path.stem) or "untitled"
        return self._template.format(
            date=doc_date.strftime(self._date_format),
            category=slugify(info.classification.category) or UNCATEGORIZED,
            title=title,
            original=slugify(info.path.stem) or "untitled",
        )
