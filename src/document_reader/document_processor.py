"""
Main document processor that orchestrates OCR, layout detection, and vision-language processing.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
import json
import re
import tempfile

from .ocr.tesseract_reader import TesseractOCR
from .ocr.paddle_reader import PaddleOCRReader
from .vision.vl_model import VisionLanguageModel
from .layout.detector import LayoutDetector
from .utils.file_utils import is_pdf_file, pdf_to_images

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
        
        if is_pdf_file(document_path):
            pdf_config = self.config.get("pdf") or self.config.get("processing", {}).get("pdf", {})
            dpi = int(pdf_config.get("dpi", 300))
            poppler_path = pdf_config.get("poppler_path")
            with tempfile.TemporaryDirectory(prefix="document_reader_pdf_") as temp_dir:
                page_images = pdf_to_images(
                    document_path,
                    output_dir=temp_dir,
                    dpi=dpi,
                    poppler_path=poppler_path,
                )
                return self._process_image_pages(document_path, page_images)

        return self._process_image_pages(document_path, [document_path])

    def _process_image_pages(self, original_path: Path, image_paths: List[Path]) -> Dict:
        """Process one or more image pages and aggregate results."""
        results: Dict = {
            "document_path": str(original_path),
            "ocr_text": None,
            "layout_analysis": None,
            "vision_interpretation": None,
            "extracted_data": {},
            "pages": [],
        }

        ocr_text_parts: List[str] = []

        for page_index, image_path in enumerate(image_paths, start=1):
            page_result: Dict = {
                "page": page_index,
                "image_path": str(image_path),
                "ocr_text": None,
                "layout_analysis": None,
                "vision_interpretation": None,
            }

            if self.layout_detector:
                logger.info(f"Performing layout detection (page {page_index})...")
                page_result["layout_analysis"] = self.layout_detector.detect_layout(image_path)

            logger.info(f"Performing OCR extraction (page {page_index})...")
            page_result["ocr_text"] = self.ocr.extract_text(image_path)
            if isinstance(page_result["ocr_text"], str) and page_result["ocr_text"].strip():
                ocr_text_parts.append(page_result["ocr_text"].strip())

            if self.vision_model:
                logger.info(f"Using vision-language model for interpretation (page {page_index})...")
                page_result["vision_interpretation"] = self.vision_model.interpret_document(
                    image_path,
                    context=page_result.get("ocr_text"),
                )

            results["pages"].append(page_result)

        # Backwards compatible top-level fields
        if results["pages"]:
            results["layout_analysis"] = results["pages"][0].get("layout_analysis")
            results["vision_interpretation"] = results["pages"][0].get("vision_interpretation")
        results["ocr_text"] = "\n\n".join(ocr_text_parts) if ocr_text_parts else ""

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
    
    def identify_indot_sheet_headers(self, results: Dict) -> Dict:
        """
        Identify INDOT-standard sheet headers from roadway construction plans.
        
        INDOT (Indiana Department of Transportation) standard sheet types include:
        - Title Sheet (TS): Project overview and index
        - General Notes (GN): Project-wide notes and specifications
        - Plan and Profile (PP): Horizontal and vertical alignment
        - Cross-Sections (XS): Typical and detailed cross-sections
        - Detail Sheets (DT): Construction details
        - Traffic Control Plan (TCP): Temporary traffic control
        - Signing and Pavement Markings (SPM): Sign and marking plans
        - Drainage (DR): Drainage structures and details
        - Utility (UT): Utility relocations and coordination
        
        Args:
            results: Document processing results containing OCR text
        
        Returns:
            Dictionary with identified sheet information
        """
        sheet_info = {
            "sheet_type": None,
            "sheet_number": None,
            "project_number": None,
            "sheet_title": None,
            "confidence": 0.0,
            "identified_headers": []
        }
        
        text = results.get("ocr_text", "")
        if not isinstance(text, str):
            return sheet_info
        
        text_upper = text.upper()
        
        # INDOT sheet type patterns
        sheet_patterns = {
            "Title Sheet": [
                r"TITLE\s+SHEET",
                r"T\.S\.",
                r"TS\s*[-]?\s*\d*",
                r"PROJECT\s+INDEX"
            ],
            "General Notes": [
                r"GENERAL\s+NOTES",
                r"G\.N\.",
                r"GN\s*[-]?\s*\d*",
                r"STANDARD\s+NOTES"
            ],
            "Plan and Profile": [
                r"PLAN\s+AND\s+PROFILE",
                r"PLAN\s*[&/]\s*PROFILE",
                r"P\.P\.",
                r"PP\s*[-]?\s*\d*"
            ],
            "Cross-Section": [
                r"CROSS\s*[-]?\s*SECTION",
                r"TYPICAL\s+SECTION",
                r"X\.S\.",
                r"XS\s*[-]?\s*\d*"
            ],
            "Detail Sheet": [
                r"DETAIL\s+SHEET",
                r"CONSTRUCTION\s+DETAILS",
                r"D\.T\.",
                r"DT\s*[-]?\s*\d*"
            ],
            "Traffic Control Plan": [
                r"TRAFFIC\s+CONTROL\s+PLAN",
                r"MAINTENANCE\s+OF\s+TRAFFIC",
                r"T\.C\.P\.",
                r"TCP\s*[-]?\s*\d*",
                r"MOT"
            ],
            "Signing and Pavement Markings": [
                r"SIGNING\s+AND\s+PAVEMENT\s+MARKING",
                r"SIGNS?\s+AND\s+MARK",
                r"S\.P\.M\.",
                r"SPM\s*[-]?\s*\d*"
            ],
            "Drainage": [
                r"DRAINAGE\s+PLAN",
                r"STORM\s+SEWER",
                r"D\.R\.",
                r"DR\s*[-]?\s*\d*"
            ],
            "Utility": [
                r"UTILITY\s+PLAN",
                r"UTILITY\s+COORDINATION",
                r"U\.T\.",
                r"UT\s*[-]?\s*\d*"
            ]
        }
        
        # Search for sheet type
        max_confidence = 0.0
        for sheet_type, patterns in sheet_patterns.items():
            matches = 0
            found_patterns = []
            for pattern in patterns:
                if re.search(pattern, text_upper):
                    matches += 1
                    found_patterns.append(pattern)
            
            if matches > 0:
                confidence = min(matches / len(patterns), 1.0)
                if confidence > max_confidence:
                    max_confidence = confidence
                    sheet_info["sheet_type"] = sheet_type
                    sheet_info["confidence"] = confidence
                    sheet_info["identified_headers"] = found_patterns
        
        # Extract sheet number (common formats: "Sheet 1 of 50", "SH. 10", etc.)
        sheet_number_patterns = [
            r"SHEET\s+(\d+)\s+OF\s+(\d+)",
            r"SH\.\s*(\d+)",
            r"SHEET\s+(?:NO\.\s*)?(\d+)"
        ]
        
        for pattern in sheet_number_patterns:
            match = re.search(pattern, text_upper)
            if match:
                sheet_info["sheet_number"] = match.group(1)
                break
        
        # Extract project number (INDOT format: DES-XXXXXXXX)
        project_patterns = [
            r"DES[-\s]*(\d{7,10})",
            r"PROJECT\s+NO\.?\s*[:.]?\s*([\d-]+)",
            r"DES\s+NO\.?\s*[:.]?\s*(\d{7,10})"
        ]
        
        for pattern in project_patterns:
            match = re.search(pattern, text_upper)
            if match:
                sheet_info["project_number"] = match.group(1)
                break
        
        # Try to extract sheet title (usually near top of sheet)
        lines = text.split('\n')[:10]  # Check first 10 lines
        for line in lines:
            line_stripped = line.strip()
            # Look for lines with substantial text that might be titles
            if 10 < len(line_stripped) < 100 and line_stripped.isupper():
                # Avoid lines that are just sheet numbers or project numbers
                if not re.match(r'^(SHEET|SH\.|PROJECT|DES)', line_stripped):
                    sheet_info["sheet_title"] = line_stripped
                    break
        
        return sheet_info
    
    def save_results(self, results: Dict, output_path: Union[str, Path]):
        """Save processing results to file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to: {output_path}")
