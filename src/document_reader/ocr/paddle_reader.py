"""
PaddleOCR implementation for advanced text extraction from documents.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class PaddleOCRReader:
    """
    Wrapper for PaddleOCR engine with support for multiple languages and document types.
    PaddleOCR is particularly effective for low-quality and challenging documents.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize PaddleOCR.
        
        Args:
            config: Configuration dictionary with PaddleOCR options
        """
        self.config = config or {}
        self.language = self.config.get('language', 'en')
        self.use_angle_cls = self.config.get('use_angle_cls', True)
        self.use_gpu = self.config.get('use_gpu', False)
        
        self.ocr = None
        self._initialize_ocr()
        
        logger.info(f"PaddleOCRReader initialized with language={self.language}")
    
    def _initialize_ocr(self):
        """Initialize the PaddleOCR model."""
        try:
            from paddleocr import PaddleOCR
            
            self.ocr = PaddleOCR(
                use_angle_cls=self.use_angle_cls,
                lang=self.language,
                use_gpu=self.use_gpu,
                show_log=False
            )
            
        except ImportError:
            logger.error("PaddleOCR not installed. Install with: pip install paddleocr")
            raise
        except Exception as e:
            logger.error(f"Error initializing PaddleOCR: {str(e)}")
            raise
    
    def extract_text(self, image_path: Union[str, Path]) -> str:
        """
        Extract text from an image using PaddleOCR.
        
        Args:
            image_path: Path to the image file
        
        Returns:
            Extracted text as string
        """
        try:
            image_path = Path(image_path)
            logger.info(f"Extracting text from: {image_path}")
            
            if not self.ocr:
                self._initialize_ocr()
            
            # Run OCR
            result = self.ocr.ocr(str(image_path), cls=self.use_angle_cls)
            
            # Extract text from results
            text_lines = []
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) >= 2:
                        text_lines.append(line[1][0])  # Get text content
            
            text = '\n'.join(text_lines)
            logger.info(f"Extracted {len(text)} characters")
            
            return text
            
        except Exception as e:
            logger.error(f"Error during OCR: {str(e)}")
            raise
    
    def extract_data(self, image_path: Union[str, Path]) -> List[Dict]:
        """
        Extract detailed OCR data including bounding boxes and confidence scores.
        
        Args:
            image_path: Path to the image file
        
        Returns:
            List of dictionaries with detailed OCR data
        """
        try:
            image_path = Path(image_path)
            
            if not self.ocr:
                self._initialize_ocr()
            
            # Run OCR
            result = self.ocr.ocr(str(image_path), cls=self.use_angle_cls)
            
            # Structure the data
            structured_data = []
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) >= 2:
                        bbox, (text, confidence) = line[0], line[1]
                        structured_data.append({
                            'bbox': bbox,
                            'text': text,
                            'confidence': confidence
                        })
            
            return structured_data
            
        except Exception as e:
            logger.error(f"Error during detailed OCR: {str(e)}")
            raise
    
    def extract_tables(self, image_path: Union[str, Path]) -> List[Dict]:
        """
        Extract table structures from documents.
        
        Args:
            image_path: Path to the image file
        
        Returns:
            List of detected tables with their structure
        """
        try:
            # This is a placeholder for table extraction functionality
            # In practice, you would use PaddleOCR's table recognition or a separate model
            logger.info(f"Table extraction from: {image_path}")
            
            data = self.extract_data(image_path)
            
            # Simple table detection based on alignment
            # This is a basic implementation; PaddleOCR has specialized table recognition
            tables = []
            
            return tables
            
        except Exception as e:
            logger.error(f"Error during table extraction: {str(e)}")
            raise
    
    def set_config(self, config: Dict):
        """Update configuration options."""
        self.config.update(config)
        if 'language' in config and config['language'] != self.language:
            self.language = config['language']
            self._initialize_ocr()  # Reinitialize with new language
