from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from domain.models.evidence import Evidence


class DocExtractPort(ABC):
    """Port for document extraction operations (PDF, OCR, etc.)."""

    @abstractmethod
    def extract_text_from_pdf(self, file_path: Union[str, Path]) -> Optional[str]:
        """
        Extract text content from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted text content or None if extraction fails
        """
        pass

    @abstractmethod
    def extract_text_from_image(self, file_path: Union[str, Path]) -> Optional[str]:
        """
        Extract text from an image using OCR.

        Args:
            file_path: Path to the image file

        Returns:
            Extracted text content or None if extraction fails
        """
        pass

    @abstractmethod
    def extract_text_from_docx(self, file_path: Union[str, Path]) -> Optional[str]:
        """
        Extract text content from a Word document.

        Args:
            file_path: Path to the DOCX file

        Returns:
            Extracted text content or None if extraction fails
        """
        pass

    @abstractmethod
    def extract_evidence_from_document(self, file_path: Union[str, Path], context: str = "") -> List[Evidence]:
        """
        Extract structured evidence from a document.

        Args:
            file_path: Path to the document
            context: Optional context to guide extraction

        Returns:
            List of Evidence objects extracted from the document
        """
        pass

    @abstractmethod
    def extract_metadata(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Extract metadata from a document.

        Args:
            file_path: Path to the document

        Returns:
            Dict containing document metadata
        """
        pass

    @abstractmethod
    def convert_to_pdf(self, file_path: Union[str, Path], output_path: Union[str, Path]) -> bool:
        """
        Convert a document to PDF format.

        Args:
            file_path: Path to the input document
            output_path: Path for the output PDF

        Returns:
            True if conversion successful, False otherwise
        """
        pass

    @abstractmethod
    def split_document(self, file_path: Union[str, Path], chunk_size: int = 1000) -> List[str]:
        """
        Split a document into chunks for processing.

        Args:
            file_path: Path to the document
            chunk_size: Size of each chunk in characters

        Returns:
            List of text chunks
        """
        pass

    @abstractmethod
    def supported_formats(self) -> List[str]:
        """
        Get list of supported document formats.

        Returns:
            List of supported file extensions
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the document extraction service is available and healthy.

        Returns:
            True if healthy, False otherwise
        """
        pass
