"""Classify documents by content and rename them to a consistent convention."""
from .classifier import DEFAULT_RULES, Classifier, KeywordClassifier
from .extractors import ExtractionError, ExtractorRegistry, TextExtractor, default_registry
from .journal import JournalError, RenameJournal, UndoResult, default_journal_path
from .models import Classification, DocumentInfo, ExtractedContent
from .naming import Namer, NamingConvention, slugify
from .pipeline import ApplyResult, RenameAction, RenamePipeline, RenamePlan, SkippedFile, SkipReason

__all__ = [
    "ApplyResult", "Classification", "Classifier", "DEFAULT_RULES", "DocumentInfo",
    "ExtractedContent", "ExtractionError", "ExtractorRegistry", "JournalError",
    "KeywordClassifier", "Namer", "NamingConvention", "RenameAction", "RenameJournal",
    "RenamePipeline", "RenamePlan", "SkipReason", "SkippedFile", "TextExtractor",
    "UndoResult", "default_journal_path", "default_registry", "slugify",
]
