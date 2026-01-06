"""
Unit tests for OCR modules.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from src.document_reader.ocr.tesseract_reader import TesseractOCR
from src.document_reader.ocr.paddle_reader import PaddleOCRReader


class TestTesseractOCR:
    """Tests for TesseractOCR class."""
    
    def test_initialization(self):
        """Test OCR initialization."""
        ocr = TesseractOCR()
        assert ocr.language == 'eng'
        assert ocr.psm == 3
        assert ocr.oem == 3
    
    def test_initialization_with_config(self):
        """Test OCR initialization with custom config."""
        config = {
            'language': 'fra',
            'psm': 6,
            'enhance_contrast': False
        }
        ocr = TesseractOCR(config)
        assert ocr.language == 'fra'
        assert ocr.psm == 6
        assert ocr.enhance_contrast is False
    
    def test_set_config(self):
        """Test configuration updates."""
        ocr = TesseractOCR()
        ocr.set_config({'enhance_contrast': False, 'denoise': False})
        assert ocr.enhance_contrast is False
        assert ocr.denoise is False


class TestPaddleOCRReader:
    """Tests for PaddleOCRReader class."""
    
    def test_initialization(self):
        """Test OCR initialization."""
        with patch('src.document_reader.ocr.paddle_reader.PaddleOCRReader._initialize_ocr'):
            ocr = PaddleOCRReader()
            assert ocr.language == 'en'
            assert ocr.use_angle_cls is True
    
    def test_initialization_with_config(self):
        """Test OCR initialization with custom config."""
        config = {
            'language': 'ch',
            'use_angle_cls': False
        }
        with patch('src.document_reader.ocr.paddle_reader.PaddleOCRReader._initialize_ocr'):
            ocr = PaddleOCRReader(config)
            assert ocr.language == 'ch'
            assert ocr.use_angle_cls is False


# Run tests with: pytest tests/test_ocr.py
