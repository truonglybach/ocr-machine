"""Classify documents by content and rename them to a consistent convention."""
from .classifier import KeywordClassifier, DEFAULT_RULES
from .extractors import ExtractorRegistry, default_registry
from .naming import NamingConvention
from .pipeline import RenamePipeline, RenamePlan, RenameAction

__all__ = [
    "KeywordClassifier", "DEFAULT_RULES", "ExtractorRegistry", "default_registry",
    "NamingConvention", "RenamePipeline", "RenamePlan", "RenameAction",
]
