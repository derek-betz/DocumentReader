"""
Utility functions for document processing.
"""

import logging
from pathlib import Path
from typing import Union, List, Optional
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


def pdf_to_images(
    pdf_path: Union[str, Path],
    output_dir: Union[str, Path],
    dpi: int = 300,
    poppler_path: Optional[Union[str, Path]] = None,
) -> List[Path]:
    """
    Convert PDF pages to images.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save images
        dpi: Resolution for conversion
    
    Returns:
        List of paths to generated images
    """
    def _pdf_to_images_pymupdf(_pdf_path: Path, _output_dir: Path) -> List[Path]:
        try:
            import fitz  # PyMuPDF
        except ImportError as import_error:
            raise RuntimeError(
                "PDF conversion requires either Poppler (for pdf2image) or PyMuPDF. "
                "Install Poppler and add its 'bin' folder to PATH / set 'pdf.poppler_path', "
                "or install PyMuPDF with: pip install PyMuPDF"
            ) from import_error

        logger.info("Converting PDF to images using PyMuPDF fallback")
        doc = fitz.open(str(_pdf_path))
        try:
            zoom = float(dpi) / 72.0
            matrix = fitz.Matrix(zoom, zoom)
            image_paths: List[Path] = []
            for i in range(doc.page_count):
                page = doc.load_page(i)
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                image_path = _output_dir / f"{_pdf_path.stem}_page_{i+1}.png"
                pix.save(str(image_path))
                image_paths.append(image_path)
            logger.info(f"Converted {len(image_paths)} pages to images")
            return image_paths
        finally:
            doc.close()

    try:
        from pdf2image import convert_from_path
        from pdf2image.exceptions import PDFInfoNotInstalledError
        
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Converting PDF to images: {pdf_path}")
        
        poppler_path_str = str(poppler_path) if poppler_path else None
        images = convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path_str)
        
        image_paths = []
        for i, image in enumerate(images):
            image_path = output_dir / f"{pdf_path.stem}_page_{i+1}.png"
            image.save(image_path, 'PNG')
            image_paths.append(image_path)
        
        logger.info(f"Converted {len(images)} pages to images")
        return image_paths
        
    except ImportError:
        logger.error("pdf2image not installed. Install with: pip install pdf2image")
        # If pdf2image isn't available, try PyMuPDF fallback.
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        return _pdf_to_images_pymupdf(pdf_path, output_dir)
    except PDFInfoNotInstalledError as e:
        # Poppler missing (common on Windows). Try PyMuPDF fallback.
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        return _pdf_to_images_pymupdf(pdf_path, output_dir)
    except Exception as e:
        # Common Windows failure: Poppler not installed / not on PATH
        message = str(e)
        if "poppler" in message.lower() or "pdftoppm" in message.lower() or "pdfinfo" in message.lower():
            try:
                pdf_path = Path(pdf_path)
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                return _pdf_to_images_pymupdf(pdf_path, output_dir)
            except Exception:
                raise RuntimeError(
                    "PDF conversion requires Poppler or PyMuPDF. On Windows: install Poppler and add its 'bin' folder to PATH, "
                    "or set config 'pdf.poppler_path' to the Poppler bin directory, or install PyMuPDF with: pip install PyMuPDF"
                ) from e

        logger.error(f"Error converting PDF to images: {message}")
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
