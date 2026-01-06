"""
Image preprocessing utilities for improving OCR quality.
"""

import logging
from pathlib import Path
from typing import Union, Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)


def enhance_image_for_ocr(image_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None):
    """
    Enhance image quality for better OCR results.
    
    Args:
        image_path: Path to input image
        output_path: Path to save enhanced image (optional)
    
    Returns:
        Enhanced image (PIL Image or numpy array)
    """
    try:
        from PIL import Image, ImageEnhance, ImageFilter
        import cv2
        
        # Load image
        image = Image.open(image_path)
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.5)
        
        # Denoise
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        if output_path:
            image.save(output_path)
            logger.info(f"Enhanced image saved to: {output_path}")
        
        return image
        
    except Exception as e:
        logger.error(f"Error enhancing image: {str(e)}")
        raise


def deskew_image(image_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None):
    """
    Detect and correct image skew.
    
    Args:
        image_path: Path to input image
        output_path: Path to save deskewed image (optional)
    
    Returns:
        Deskewed image
    """
    try:
        import cv2
        import numpy as np
        from PIL import Image
        
        # Load image
        image = cv2.imread(str(image_path))
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect edges
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Detect lines
        lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
        
        if lines is not None and len(lines) > 0:
            # Calculate median angle
            angles = []
            for rho, theta in lines[:, 0]:
                angle = np.degrees(theta) - 90
                angles.append(angle)
            
            median_angle = np.median(angles)
            
            # Rotate image if skew is significant
            if abs(median_angle) > 0.5:
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                image = cv2.warpAffine(
                    image, M, (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )
        
        if output_path:
            cv2.imwrite(str(output_path), image)
            logger.info(f"Deskewed image saved to: {output_path}")
        
        return image
        
    except Exception as e:
        logger.error(f"Error deskewing image: {str(e)}")
        raise


def binarize_image(image_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None):
    """
    Binarize image using adaptive thresholding.
    
    Args:
        image_path: Path to input image
        output_path: Path to save binarized image (optional)
    
    Returns:
        Binarized image
    """
    try:
        import cv2
        
        # Load image
        image = cv2.imread(str(image_path))
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )
        
        if output_path:
            cv2.imwrite(str(output_path), binary)
            logger.info(f"Binarized image saved to: {output_path}")
        
        return binary
        
    except Exception as e:
        logger.error(f"Error binarizing image: {str(e)}")
        raise


def remove_noise(image_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None):
    """
    Remove noise from image.
    
    Args:
        image_path: Path to input image
        output_path: Path to save denoised image (optional)
    
    Returns:
        Denoised image
    """
    try:
        import cv2
        
        # Load image
        image = cv2.imread(str(image_path))
        
        # Apply non-local means denoising
        denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        
        if output_path:
            cv2.imwrite(str(output_path), denoised)
            logger.info(f"Denoised image saved to: {output_path}")
        
        return denoised
        
    except Exception as e:
        logger.error(f"Error removing noise: {str(e)}")
        raise


def resize_image(
    image_path: Union[str, Path],
    target_size: Tuple[int, int],
    output_path: Optional[Union[str, Path]] = None
):
    """
    Resize image to target size.
    
    Args:
        image_path: Path to input image
        target_size: Tuple of (width, height)
        output_path: Path to save resized image (optional)
    
    Returns:
        Resized image
    """
    try:
        from PIL import Image
        
        image = Image.open(image_path)
        resized = image.resize(target_size, Image.LANCZOS)
        
        if output_path:
            resized.save(output_path)
            logger.info(f"Resized image saved to: {output_path}")
        
        return resized
        
    except Exception as e:
        logger.error(f"Error resizing image: {str(e)}")
        raise
