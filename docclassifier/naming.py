from __future__ import annotations

import re
import unicodedata
from string import Formatter
from typing import Protocol

from .models import DocumentInfo

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
        fields = [f for _, f, _, _ in Formatter().parse(template) if f is not None]
        if not fields:
            raise ValueError("Template must contain at least one field")
        bad = [f for f in fields if f not in FIELDS]
        if bad:
            raise ValueError(f"Unknown template fields {bad}; allowed: {sorted(FIELDS)}")
        if re.search(r"[\\/]", template) or ".." in template:
            raise ValueError("Template must not contain path separators or '..'")
        self._template = template
        self._date_format = date_format

    def stem_for(self, info: DocumentInfo) -> str:
        doc_date = info.content.document_date or info.fallback_date
        title = slugify(info.content.title or "") or slugify(info.path.stem) or "untitled"
        return self._template.format(
            date=doc_date.strftime(self._date_format),
            category=slugify(info.classification.category) or "other",
            title=title,
            original=slugify(info.path.stem) or "untitled",
        )
