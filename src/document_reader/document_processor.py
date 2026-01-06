"""
Main document processor that orchestrates OCR, layout detection, and vision-language processing.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
import json
import re

from .ocr.tesseract_reader import TesseractOCR
from .ocr.paddle_reader import PaddleOCRReader
from .vision.vl_model import VisionLanguageModel
from .layout.detector import LayoutDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Main document processing pipeline for handling difficult documents like 
    photocopied engineering plans and complex PDFs.
    """
    
    def __init__(
        self,
        ocr_engine: str = "tesseract",
        use_vision_model: bool = False,
        vision_model: str = "gpt-4o",
        detect_layout: bool = True,
        config: Optional[Dict] = None
    ):
        """
        Initialize the document processor.
        
        Args:
            ocr_engine: OCR engine to use ('tesseract' or 'paddleocr')
            use_vision_model: Whether to use vision-language models for interpretation
            vision_model: Vision-language model to use ('gpt-4o' or 'claude')
            detect_layout: Whether to perform layout detection
            config: Additional configuration options
        """
        self.config = config or {}
        
        # Initialize OCR engine
        if ocr_engine == "tesseract":
            self.ocr = TesseractOCR(self.config.get("tesseract", {}))
        elif ocr_engine == "paddleocr":
            self.ocr = PaddleOCRReader(self.config.get("paddleocr", {}))
        else:
            raise ValueError(f"Unsupported OCR engine: {ocr_engine}")
        
        # Initialize layout detector
        self.layout_detector = LayoutDetector(self.config.get("layout", {})) if detect_layout else None
        
        # Initialize vision-language model
        self.vision_model = None
        if use_vision_model:
            self.vision_model = VisionLanguageModel(
                model_name=vision_model,
                config=self.config.get("vision", {})
            )
        
        logger.info(f"DocumentProcessor initialized with OCR: {ocr_engine}, "
                   f"Vision Model: {vision_model if use_vision_model else 'None'}, "
                   f"Layout Detection: {detect_layout}")
    
    def process_document(
        self,
        document_path: Union[str, Path],
        output_format: str = "json"
    ) -> Dict:
        """
        Process a document through the complete pipeline.
        
        Args:
            document_path: Path to the document (image or PDF)
            output_format: Output format ('json', 'text', or 'structured')
        
        Returns:
            Dictionary containing extracted information
        """
        document_path = Path(document_path)
        logger.info(f"Processing document: {document_path}")
        
        if not document_path.exists():
            raise FileNotFoundError(f"Document not found: {document_path}")
        
        results = {
            "document_path": str(document_path),
            "ocr_text": None,
            "layout_analysis": None,
            "vision_interpretation": None,
            "extracted_data": {}
        }
        
        # Step 1: Layout detection (if enabled)
        if self.layout_detector:
            logger.info("Performing layout detection...")
            results["layout_analysis"] = self.layout_detector.detect_layout(document_path)
        
        # Step 2: OCR extraction
        logger.info("Performing OCR extraction...")
        results["ocr_text"] = self.ocr.extract_text(document_path)
        
        # Step 3: Vision-language model interpretation (if enabled)
        if self.vision_model:
            logger.info("Using vision-language model for interpretation...")
            results["vision_interpretation"] = self.vision_model.interpret_document(
                document_path,
                context=results.get("ocr_text")
            )
        
        # Step 4: Extract structured data
        results["extracted_data"] = self._extract_structured_data(results)
        
        logger.info("Document processing complete")
        return results
    
    def process_engineering_plan(
        self,
        plan_path: Union[str, Path],
        extract_measurements: bool = True,
        extract_annotations: bool = True
    ) -> Dict:
        """
        Specialized processing for engineering plans and technical drawings.
        
        Args:
            plan_path: Path to the engineering plan
            extract_measurements: Whether to extract measurements and dimensions
            extract_annotations: Whether to extract text annotations
        
        Returns:
            Dictionary with engineering-specific extracted data
        """
        plan_path = Path(plan_path)
        logger.info(f"Processing engineering plan: {plan_path}")
        
        # Configure OCR for better handling of technical text
        if hasattr(self.ocr, 'set_config'):
            self.ocr.set_config({
                'enhance_contrast': True,
                'denoise': True,
                'detect_orientation': True
            })
        
        results = self.process_document(plan_path)
        
        # Additional engineering-specific processing
        engineering_data = {
            "measurements": [] if extract_measurements else None,
            "annotations": [] if extract_annotations else None,
            "symbols": [],
            "drawing_metadata": {}
        }
        
        if extract_measurements:
            engineering_data["measurements"] = self._extract_measurements(results)
        
        if extract_annotations:
            engineering_data["annotations"] = self._extract_annotations(results)
        
        results["engineering_data"] = engineering_data
        
        return results
    
    def _extract_structured_data(self, results: Dict) -> Dict:
        """Extract structured data from processing results."""
        structured_data = {
            "text_blocks": [],
            "tables": [],
            "headers": [],
            "metadata": {}
        }
        
        # Parse OCR text into structured blocks
        if results.get("ocr_text"):
            # Simple text block extraction
            text = results["ocr_text"]
            if isinstance(text, str):
                structured_data["text_blocks"] = [
                    {"content": block.strip(), "type": "paragraph"}
                    for block in text.split("\n\n") if block.strip()
                ]
        
        return structured_data
    
    def _extract_measurements(self, results: Dict) -> List[Dict]:
        """Extract measurements and dimensions from engineering documents."""
        measurements = []
        text = results.get("ocr_text", "")
        
        if isinstance(text, str):
            # Pattern for common measurement formats (e.g., "10mm", "5.5 cm", "3'6\"")
            patterns = [
                r'(\d+\.?\d*)\s*(?:mm|cm|m|km|in|ft|yd)',
                r'(\d+)\'(\d+)\"',  # Feet and inches
                r'(\d+\.?\d*)\s*x\s*(\d+\.?\d*)'  # Dimensions
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    measurements.append({
                        "value": match.group(0),
                        "position": match.span()
                    })
        
        return measurements
    
    def _extract_annotations(self, results: Dict) -> List[Dict]:
        """Extract text annotations from engineering documents."""
        annotations = []
        
        # Use layout analysis if available
        if results.get("layout_analysis"):
            layout = results["layout_analysis"]
            if "text_regions" in layout:
                for region in layout["text_regions"]:
                    if region.get("type") == "annotation":
                        annotations.append(region)
        
        return annotations
    
    def save_results(self, results: Dict, output_path: Union[str, Path]):
        """Save processing results to file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to: {output_path}")
