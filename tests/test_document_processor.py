"""
Unit tests for document processor.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
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


# Run tests with: pytest tests/test_document_processor.py
