"""
Contact Information Extraction Module
"""
from .contact_extractor import ContactExtractor, ContactInfo
from .contact_validator import ContactValidator, ValidationResult
from .html_parser import HTMLContactParser, PageAnalysis
from .institution_classifier import InstitutionClassifier, ClassificationResult

__all__ = [
    'ContactExtractor',
    'ContactInfo',
    'ContactValidator',
    'ValidationResult',
    'HTMLContactParser',
    'PageAnalysis',
    'InstitutionClassifier',
    'ClassificationResult',
]
