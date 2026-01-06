"""
Tesseract OCR implementation for text extraction from documents.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Union, List
import subprocess

logger = logging.getLogger(__name__)


class TesseractOCR:
    """
    Wrapper for Tesseract OCR engine with optimizations for low-legibility documents.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Tesseract OCR.
        
        Args:
            config: Configuration dictionary with Tesseract options
        """
        self.config = config or {}
        self.language = self.config.get('language', 'eng')
        self.psm = self.config.get('psm', 3)  # Page segmentation mode
        self.oem = self.config.get('oem', 3)  # OCR Engine mode
        
        # Image preprocessing options
        self.enhance_contrast = self.config.get('enhance_contrast', True)
        self.denoise = self.config.get('denoise', True)
        self.deskew = self.config.get('deskew', True)
        
        logger.info(f"TesseractOCR initialized with language={self.language}, psm={self.psm}")
    
    def extract_text(self, image_path: Union[str, Path]) -> str:
        """
        Extract text from an image using Tesseract.
        
        Args:
            image_path: Path to the image file
        
        Returns:
            Extracted text as string
        """
        try:
            import pytesseract
            from PIL import Image
            
            image_path = Path(image_path)
            logger.info(f"Extracting text from: {image_path}")
            
            # Open image
            image = Image.open(image_path)
            
            # Preprocess image for better OCR results
            if self.enhance_contrast or self.denoise or self.deskew:
                image = self._preprocess_image(image)
            
            # Configure Tesseract
            custom_config = f'--oem {self.oem} --psm {self.psm}'
            if self.config.get('tesseract_config'):
                custom_config += f" {self.config['tesseract_config']}"
            
            # Extract text
            text = pytesseract.image_to_string(
                image,
                lang=self.language,
                config=custom_config
            )
            
            logger.info(f"Extracted {len(text)} characters")
            return text
            
        except ImportError:
            logger.error("pytesseract not installed. Install with: pip install pytesseract")
            raise
        except Exception as e:
            logger.error(f"Error during OCR: {str(e)}")
            raise
    
    def extract_data(self, image_path: Union[str, Path]) -> Dict:
        """
        Extract detailed OCR data including bounding boxes and confidence scores.
        
        Args:
            image_path: Path to the image file
        
        Returns:
            Dictionary with detailed OCR data
        """
        try:
            import pytesseract
            from PIL import Image
            
            image_path = Path(image_path)
            image = Image.open(image_path)
            
            if self.enhance_contrast or self.denoise or self.deskew:
                image = self._preprocess_image(image)
            
            # Get detailed data
            data = pytesseract.image_to_data(
                image,
                lang=self.language,
                output_type=pytesseract.Output.DICT
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Error during detailed OCR: {str(e)}")
            raise
    
    def _preprocess_image(self, image):
        """
        Preprocess image for better OCR results on low-legibility documents.
        
        Args:
            image: PIL Image object
        
        Returns:
            Preprocessed PIL Image
        """
        try:
            from PIL import ImageEnhance, ImageFilter
            import numpy as np
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Enhance contrast
            if self.enhance_contrast:
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(2.0)
            
            # Denoise
            if self.denoise:
                image = image.filter(ImageFilter.MedianFilter(size=3))
            
            # Deskew (basic implementation)
            if self.deskew:
                image = self._deskew_image(image)
            
            return image
            
        except Exception as e:
            logger.warning(f"Preprocessing failed: {str(e)}, using original image")
            return image
    
    def _deskew_image(self, image):
        """
        Detect and correct image skew.
        
        Args:
            image: PIL Image object
        
        Returns:
            Deskewed PIL Image
        """
        try:
            import cv2
            import numpy as np
            
            # Convert PIL to OpenCV format
            img_array = np.array(image)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Detect edges
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Detect lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
            
            if lines is not None and len(lines) > 0:
                # Calculate average angle
                angles = []
                for rho, theta in lines[:, 0]:
                    angle = np.degrees(theta) - 90
                    angles.append(angle)
                
                median_angle = np.median(angles)
                
                # Rotate image if skew is significant
                if abs(median_angle) > 0.5:
                    from PIL import Image
                    return image.rotate(median_angle, expand=True, fillcolor='white')
            
            return image
            
        except Exception as e:
            logger.warning(f"Deskew failed: {str(e)}")
            return image
    
    def set_config(self, config: Dict):
        """Update configuration options."""
        self.config.update(config)
        if 'enhance_contrast' in config:
            self.enhance_contrast = config['enhance_contrast']
        if 'denoise' in config:
            self.denoise = config['denoise']
        if 'deskew' in config:
            self.deskew = config['deskew']
