"""OCR module initialization."""

from .tesseract_reader import TesseractOCR
from .paddle_reader import PaddleOCRReader

__all__ = ["TesseractOCR", "PaddleOCRReader"]
