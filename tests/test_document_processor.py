"""
Unit tests for document processor.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import sys
import types
from src.document_reader.document_processor import DocumentProcessor


class TestDocumentProcessor:
    """Tests for DocumentProcessor class."""
    
    def test_initialization_default(self):
        """Test processor initialization with defaults."""
        with patch('src.document_reader.document_processor.TesseractOCR'):
            with patch('src.document_reader.document_processor.LayoutDetector'):
                processor = DocumentProcessor()
                assert processor.ocr is not None
                assert processor.layout_detector is not None
                assert processor.vision_model is None
    
    def test_initialization_with_vision(self):
        """Test processor initialization with vision model."""
        with patch('src.document_reader.document_processor.TesseractOCR'):
            with patch('src.document_reader.document_processor.LayoutDetector'):
                with patch('src.document_reader.document_processor.VisionLanguageModel'):
                    processor = DocumentProcessor(use_vision_model=True)
                    assert processor.vision_model is not None
    
    def test_initialization_invalid_ocr(self):
        """Test processor initialization with invalid OCR engine."""
        with pytest.raises(ValueError, match="Unsupported OCR engine"):
            processor = DocumentProcessor(ocr_engine="invalid")

    def test_process_document_pdf_converts_and_aggregates_pages(self, tmp_path: Path):
        """PDFs should be converted to page images and processed page-by-page."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

        page1 = tmp_path / "page1.png"
        page2 = tmp_path / "page2.png"

        ocr_instance = Mock()
        ocr_instance.extract_text.side_effect = ["page one", "page two"]

        layout_instance = Mock()
        layout_instance.detect_layout.return_value = {"regions": [], "num_regions": 0}

        with patch('src.document_reader.document_processor.TesseractOCR', return_value=ocr_instance):
            with patch('src.document_reader.document_processor.LayoutDetector', return_value=layout_instance):
                with patch('src.document_reader.document_processor.is_pdf_file', return_value=True):
                    with patch('src.document_reader.document_processor.pdf_to_images', return_value=[page1, page2]):
                        processor = DocumentProcessor()
                        results = processor.process_document(pdf_path)

        assert "page one" in results["ocr_text"]
        assert "page two" in results["ocr_text"]
        assert "pages" in results
        assert len(results["pages"]) == 2
        assert results["pages"][0]["page"] == 1
        assert results["pages"][1]["page"] == 2

    def test_pdf_to_images_falls_back_to_pymupdf_when_poppler_missing(self, tmp_path: Path):
        """If pdf2image can't run due to missing Poppler, pdf_to_images should use PyMuPDF."""
        from pdf2image.exceptions import PDFInfoNotInstalledError
        from src.document_reader.utils.file_utils import pdf_to_images

        pdf_path = tmp_path / "sample.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        out_dir = tmp_path / "out"

        class _FakePixmap:
            def save(self, path: str):
                Path(path).write_bytes(b"PNG")

        class _FakePage:
            def get_pixmap(self, matrix=None, alpha=False):
                return _FakePixmap()

        class _FakeDoc:
            page_count = 2

            def load_page(self, i: int):
                return _FakePage()

            def close(self):
                return None

        fake_fitz = types.SimpleNamespace(
            open=lambda _: _FakeDoc(),
            Matrix=lambda x, y: (x, y),
        )

        with patch('pdf2image.convert_from_path', side_effect=PDFInfoNotInstalledError("no pdfinfo")):
            with patch.dict(sys.modules, {'fitz': fake_fitz}):
                images = pdf_to_images(pdf_path, out_dir, dpi=144)

        assert len(images) == 2
        assert images[0].exists()
        assert images[1].exists()


# Run tests with: pytest tests/test_document_processor.py
