"""
Document extraction adapters package.

This package contains adapters for extracting text and structured data
from various document formats including PDF, Word documents, images, etc.
"""

from .pdf_extractor import PDFExtractorAdapter

__all__ = [
    "PDFExtractorAdapter",
]
