from datetime import datetime
import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# PDF processing libraries
try:
    import pdfplumber
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# OCR libraries
try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Word document processing
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

from domain.models.evidence import Evidence, EvidenceSource
from ports.doc_extract_port import DocExtractPort

logger = logging.getLogger(__name__)

class PDFExtractorAdapter(DocExtractPort):
    """PDF and document extraction adapter implementing DocExtractPort."""

    def __init__(self):
        self.supported_extensions = []

        if PDF_AVAILABLE:
            self.supported_extensions.extend([".pdf"])
        if OCR_AVAILABLE:
            self.supported_extensions.extend([".png", ".jpg", ".jpeg", ".tiff", ".bmp"])
        if DOCX_AVAILABLE:
            self.supported_extensions.extend([".docx"])

        logger.info(f"PDFExtractorAdapter initialized. Supported formats: {self.supported_extensions}")

    def extract_text_from_pdf(self, file_path: Union[str, Path]) -> Optional[str]:
        """Extract text content from a PDF file."""
        if not PDF_AVAILABLE:
            logger.error("PDF extraction not available. Install PyPDF2 and pdfplumber.")
            return None

        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None

        try:
            # Try pdfplumber first (better text extraction)
            with pdfplumber.open(file_path) as pdf:
                text_content = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)

                if text_content:
                    return "\\n\\n".join(text_content)

            # Fallback to PyPDF2
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = []

                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text:
                        text_content.append(text)

                return "\\n\\n".join(text_content) if text_content else None

        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            return None

    def extract_text_from_image(self, file_path: Union[str, Path]) -> Optional[str]:
        """Extract text from an image using OCR."""
        if not OCR_AVAILABLE:
            logger.error("OCR not available. Install pytesseract and Pillow.")
            return None

        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None

        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text.strip() if text.strip() else None

        except Exception as e:
            logger.error(f"Error extracting text from image {file_path}: {e}")
            return None

    def extract_text_from_docx(self, file_path: Union[str, Path]) -> Optional[str]:
        """Extract text content from a Word document."""
        if not DOCX_AVAILABLE:
            logger.error("DOCX extraction not available. Install python-docx.")
            return None

        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None

        try:
            doc = Document(file_path)
            text_content = []

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)

            return "\\n".join(text_content) if text_content else None

        except Exception as e:
            logger.error(f"Error extracting text from DOCX {file_path}: {e}")
            return None

    def extract_evidence_from_document(self, file_path: Union[str, Path], context: str = "") -> List[Evidence]:
        """Extract structured evidence from a document."""
        file_path = Path(file_path)
        text_content = None

        # Determine file type and extract text
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            text_content = self.extract_text_from_pdf(file_path)
        elif suffix == ".docx":
            text_content = self.extract_text_from_docx(file_path)
        elif suffix in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
            text_content = self.extract_text_from_image(file_path)
        else:
            logger.warning(f"Unsupported file type: {suffix}")
            return []

        if not text_content:
            logger.warning(f"No text content extracted from {file_path}")
            return []

        # Split content into chunks and create evidence objects
        chunks = self.split_document_content(text_content)
        evidence_list = []

        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 50:  # Skip very short chunks
                continue

            # Create evidence ID
            evidence_id = f"doc_{hashlib.md5(f'{file_path}_{i}'.encode()).hexdigest()[:8]}"

            # Create evidence source
            source = EvidenceSource(
                url=f"file://{file_path.absolute()}",
                title=file_path.name,
                fetched_at=datetime.utcnow()
            )

            # Create evidence object
            evidence = Evidence(
                id=evidence_id,
                source=source,
                excerpt=chunk[:1000],  # Limit excerpt to 1000 chars
                tool_call_id=f"extract:doc:{evidence_id}",
                score=0.9,  # High confidence for directly extracted content
                tags=["document", "extracted", suffix[1:]],  # Remove the dot from extension
                cit_key=f"Doc{file_path.stem}_{i+1}"
            )
            evidence_list.append(evidence)

        return evidence_list

    def extract_metadata(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Extract metadata from a document."""
        file_path = Path(file_path)
        metadata = {
            "filename": file_path.name,
            "file_size": file_path.stat().st_size if file_path.exists() else 0,
            "file_extension": file_path.suffix.lower(),
            "modified_date": datetime.fromtimestamp(file_path.stat().st_mtime) if file_path.exists() else None
        }

        # Add format-specific metadata
        if file_path.suffix.lower() == ".pdf" and PDF_AVAILABLE:
            try:
                with open(file_path, "rb") as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    metadata.update({
                        "page_count": len(pdf_reader.pages),
                        "pdf_info": pdf_reader.metadata._data if pdf_reader.metadata else {}
                    })
            except Exception as e:
                logger.warning(f"Could not extract PDF metadata: {e}")

        return metadata

    def convert_to_pdf(self, file_path: Union[str, Path], output_path: Union[str, Path]) -> bool:
        """Convert a document to PDF format."""
        # This is a placeholder implementation
        # In practice, you would use libraries like python-docx2pdf or similar
        logger.warning("PDF conversion not implemented in this basic version")
        return False

    def split_document(self, file_path: Union[str, Path], chunk_size: int = 1000) -> List[str]:
        """Split a document into chunks for processing."""
        text_content = None
        file_path = Path(file_path)

        # Extract text based on file type
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            text_content = self.extract_text_from_pdf(file_path)
        elif suffix == ".docx":
            text_content = self.extract_text_from_docx(file_path)
        elif suffix in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
            text_content = self.extract_text_from_image(file_path)

        if not text_content:
            return []

        return self.split_document_content(text_content, chunk_size)

    def split_document_content(self, content: str, chunk_size: int = 1000) -> List[str]:
        """Split text content into chunks."""
        if not content:
            return []

        # Simple chunking by sentences, then by words if needed
        sentences = content.split(". ")
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def supported_formats(self) -> List[str]:
        """Get list of supported document formats."""
        return self.supported_extensions

    def health_check(self) -> bool:
        """Check if the document extraction service is available and healthy."""
        checks = {
            "pdf_available": PDF_AVAILABLE,
            "ocr_available": OCR_AVAILABLE,
            "docx_available": DOCX_AVAILABLE
        }

        # Consider healthy if at least one format is supported
        return any(checks.values())
