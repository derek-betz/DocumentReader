"""
Document AI Agent - Advanced Document Reading and Interpretation System

Core mission: Reading and interpreting difficult documents like photocopied road 
engineering plans and complex PDFs using advanced OCR, vision-language models, 
and layout detection.
"""

__version__ = "0.1.0"
__author__ = "DocumentReader Team"

from .ocr.tesseract_reader import TesseractOCR
from .ocr.paddle_reader import PaddleOCRReader
from .vision.vl_model import VisionLanguageModel
from .layout.detector import LayoutDetector
from .document_processor import DocumentProcessor

__all__ = [
    "TesseractOCR",
    "PaddleOCRReader", 
    "VisionLanguageModel",
    "LayoutDetector",
    "DocumentProcessor",
]
