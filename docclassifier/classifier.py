from __future__ import annotations

import re
from typing import Mapping, Protocol, Sequence

from .models import UNCATEGORIZED, Classification, ExtractedContent


class Classifier(Protocol):
    def classify(self, content: ExtractedContent, filename: str = "") -> Classification: ...


DEFAULT_RULES: dict[str, tuple[str, ...]] = {
    "invoice": ("invoice", "bill to", "amount due", "invoice number", "remit", "purchase order"),
    "contract": ("agreement", "hereinafter", "party", "terms and conditions", "governing law", "witness"),
    "budget": ("budget", "forecast", "expenses", "revenue", "quarter", "fiscal", "variance"),
    "report": ("report", "executive summary", "findings", "analysis", "conclusion"),
    "meeting-notes": ("meeting", "agenda", "minutes", "attendees", "action items"),
    "resume": ("resume", "curriculum vitae", "work experience", "education", "skills"),
    "proposal": ("proposal", "scope of work", "deliverables", "timeline", "statement of work"),
}


class KeywordClassifier:
    """Scores each category by weighted keyword hits; filename hits count triple."""

    FILENAME_WEIGHT = 3

    def __init__(self, rules: Mapping[str, Sequence[str]] = DEFAULT_RULES, min_score: int = 2):
        self._patterns = {
            cat: [re.compile(r"\b" + re.escape(k.lower()) + r"\b") for k in kws]
            for cat, kws in rules.items()
        }
        self._min_score = min_score

    def classify(self, content: ExtractedContent, filename: str = "") -> Classification:
        text = content.text.lower()
        name = filename.lower()
        best = Classification(UNCATEGORIZED, 0)
        for category, patterns in self._patterns.items():
            score = sum(
                len(p.findall(text)) + self.FILENAME_WEIGHT * len(p.findall(name))
                for p in patterns
            )
            if score > best.score:
                best = Classification(category, score)
        return best if best.score >= self._min_score else Classification(UNCATEGORIZED, best.score)
