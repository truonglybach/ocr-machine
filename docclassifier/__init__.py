"""Classify documents by content and rename them to a consistent convention."""
from .classifier import DEFAULT_RULES, Classifier, KeywordClassifier
from .extractors import ContentReader, ExtractionError, ExtractorRegistry, TextExtractor, default_registry
from .journal import JournalError, RenameJournal, UndoResult, default_journal_path
from .models import UNCATEGORIZED, Classification, DocumentInfo, ExtractedContent
from .naming import Namer, NamingConvention, slugify
from .pipeline import ApplyResult, FailedRename, RenameAction, RenamePipeline, RenamePlan, SkippedFile, SkipReason

__all__ = [
    "ApplyResult", "Classification", "Classifier", "ContentReader", "DEFAULT_RULES", "DocumentInfo",
    "ExtractedContent", "ExtractionError", "FailedRename", "ExtractorRegistry", "JournalError",
    "KeywordClassifier", "Namer", "NamingConvention", "RenameAction", "RenameJournal",
    "RenamePipeline", "RenamePlan", "SkipReason", "SkippedFile", "TextExtractor",
    "UNCATEGORIZED", "UndoResult", "default_journal_path", "default_registry", "slugify",
]
