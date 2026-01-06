"""
Utility functions for document processing.
"""

import logging
from pathlib import Path
from typing import Union, List
import hashlib

logger = logging.getLogger(__name__)


def get_file_hash(file_path: Union[str, Path]) -> str:
    """
    Calculate SHA256 hash of a file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Hexadecimal hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def is_image_file(file_path: Union[str, Path]) -> bool:
    """
    Check if file is an image.
    
    Args:
        file_path: Path to the file
    
    Returns:
        True if file is an image
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif'}
    return Path(file_path).suffix.lower() in image_extensions


def is_pdf_file(file_path: Union[str, Path]) -> bool:
    """
    Check if file is a PDF.
    
    Args:
        file_path: Path to the file
    
    Returns:
        True if file is a PDF
    """
    return Path(file_path).suffix.lower() == '.pdf'


def pdf_to_images(pdf_path: Union[str, Path], output_dir: Union[str, Path], dpi: int = 300) -> List[Path]:
    """
    Convert PDF pages to images.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save images
        dpi: Resolution for conversion
    
    Returns:
        List of paths to generated images
    """
    try:
        from pdf2image import convert_from_path
        
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Converting PDF to images: {pdf_path}")
        
        images = convert_from_path(pdf_path, dpi=dpi)
        
        image_paths = []
        for i, image in enumerate(images):
            image_path = output_dir / f"{pdf_path.stem}_page_{i+1}.png"
            image.save(image_path, 'PNG')
            image_paths.append(image_path)
        
        logger.info(f"Converted {len(images)} pages to images")
        return image_paths
        
    except ImportError:
        logger.error("pdf2image not installed. Install with: pip install pdf2image")
        raise
    except Exception as e:
        logger.error(f"Error converting PDF to images: {str(e)}")
        raise


def load_config(config_path: Union[str, Path]) -> dict:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file
    
    Returns:
        Configuration dictionary
    """
    try:
        import yaml
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        return config or {}
        
    except ImportError:
        logger.error("PyYAML not installed. Install with: pip install pyyaml")
        raise
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        raise


def save_config(config: dict, config_path: Union[str, Path]):
    """
    Save configuration to YAML file.
    
    Args:
        config: Configuration dictionary
        config_path: Path to save config
    """
    try:
        import yaml
        
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        logger.info(f"Config saved to: {config_path}")
        
    except ImportError:
        logger.error("PyYAML not installed. Install with: pip install pyyaml")
        raise
    except Exception as e:
        logger.error(f"Error saving config: {str(e)}")
        raise


def ensure_dir(directory: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        directory: Path to directory
    
    Returns:
        Path object for the directory
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory
