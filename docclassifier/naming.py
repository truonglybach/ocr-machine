from __future__ import annotations

import re
import unicodedata
from string import Formatter

from .models import DocumentInfo

DEFAULT_TEMPLATE = "{date}_{category}_{title}"
FIELDS = {"date", "category", "title", "original"}


def slugify(value: str, max_len: int = 50) -> str:
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug[:max_len].strip("-")


class NamingConvention:
    """Builds file stems from a template, e.g. ``{date}_{category}_{title}``.

    Fields: date (YYYY-MM-DD), category, title (slugified), original (original stem).
    The file extension is always preserved by the caller.
    """

    def __init__(self, template: str = DEFAULT_TEMPLATE, date_format: str = "%Y-%m-%d"):
        used = {f for _, f, _, _ in Formatter().parse(template) if f}
        unknown = used - FIELDS
        if unknown:
            raise ValueError(f"Unknown template fields {sorted(unknown)}; allowed: {sorted(FIELDS)}")
        self._template = template
        self._date_format = date_format

    def stem_for(self, info: DocumentInfo) -> str:
        doc_date = info.content.document_date or info.fallback_date
        title = slugify(info.content.title or "") or slugify(info.path.stem) or "untitled"
        stem = self._template.format(
            date=doc_date.strftime(self._date_format),
            category=info.classification.category,
            title=title,
            original=slugify(info.path.stem) or "untitled",
        )
        return stem
