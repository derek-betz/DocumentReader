"""
Generalized document expert pipeline.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

from ..layout.detector import LayoutDetector
from ..ocr.paddle_reader import PaddleOCRReader
from ..ocr.tesseract_reader import TesseractOCR
from ..utils.file_utils import is_pdf_file, pdf_to_images
from ..vision.vl_model import VisionLanguageModel
from .classification import classify_document
from .contracts import (
    DEFAULT_TASKS,
    DocumentResult,
    PageResult,
    TableRegion,
)
from .extractors import extract_key_values, extract_measurements
from .preprocess import preprocess_image
from .quality import compute_quality
from .tables import detect_tables


class DocumentExpert:
    """
    Generalized document expert pipeline with modular steps and structured output.
    """

    def __init__(
        self,
        ocr_engine: str = "tesseract",
        use_vision_model: bool = False,
        vision_model: str = "gpt-4o",
        detect_layout: bool = True,
        config: Optional[Dict] = None,
    ):
        self.config = config or {}
        self.processing_config = self.config.get("processing", {})
        self.preprocess_config = self.processing_config.get("preprocess", {})
        self.quality_config = self.processing_config.get("quality", {})
        self.output_config = self.processing_config.get("output", {})
        self.extractor_config = self.config.get("extractors", {})
        self.engineering_config = self.config.get("engineering", {})

        if ocr_engine == "tesseract":
            self.ocr = TesseractOCR(self.config.get("tesseract", {}))
        elif ocr_engine == "paddleocr":
            self.ocr = PaddleOCRReader(self.config.get("paddleocr", {}))
        else:
            raise ValueError(f"Unsupported OCR engine: {ocr_engine}")

        self.layout_detector = LayoutDetector(self.config.get("layout", {})) if detect_layout else None

        self.vision_model = None
        if use_vision_model:
            self.vision_model = VisionLanguageModel(
                model_name=vision_model,
                config=self.config.get("vision", {}),
            )

    def analyze(
        self,
        document_path: Union[str, Path],
        tasks: Optional[Sequence[str]] = None,
    ) -> DocumentResult:
        document_path = Path(document_path)
        task_set = {t.lower() for t in (tasks or DEFAULT_TASKS)}

        result = DocumentResult(document_path=str(document_path))
        warnings: List[str] = []

        save_intermediate = bool(self.output_config.get("save_intermediate", False))
        artifacts_root = self.output_config.get("artifacts_dir", "output/document_expert")
        run_dir = None
        if save_intermediate:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            run_dir = Path(artifacts_root) / f"{document_path.stem}_{timestamp}"
            run_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="document_expert_") as temp_dir:
            work_dir = Path(temp_dir)
            page_dir = (run_dir / "pages") if run_dir else (work_dir / "pages")
            preprocess_dir = (run_dir / "preprocessed") if run_dir else (work_dir / "preprocessed")

            image_paths = self._load_images(document_path, page_dir)
            page_results: List[PageResult] = []
            ocr_parts: List[str] = []
            tables: List[TableRegion] = []

            for page_number, image_path in enumerate(image_paths, start=1):
                page_warnings: List[str] = []
                processed_path = image_path

                if self.preprocess_config.get("enabled", True):
                    processed_path, _ = preprocess_image(
                        image_path, preprocess_dir, self.preprocess_config
                    )

                layout_regions = []
                if self.layout_detector:
                    layout_result = self.layout_detector.detect_layout(processed_path)
                    for region in layout_result.get("regions", []):
                        bbox = region.get("bbox") or [0, 0, 0, 0]
                        if len(bbox) < 4:
                            continue
                        layout_regions.append(
                            {
                                "type": region.get("type", "unknown"),
                                "bbox": {
                                    "x1": int(bbox[0]),
                                    "y1": int(bbox[1]),
                                    "x2": int(bbox[2]),
                                    "y2": int(bbox[3]),
                                },
                                "confidence": region.get("confidence"),
                                "text": region.get("text"),
                            }
                        )

                ocr_text = self.ocr.extract_text(processed_path)
                ocr_text = ocr_text or ""
                if ocr_text:
                    ocr_parts.append(ocr_text.strip())

                quality = None
                if "quality" in task_set:
                    try:
                        quality = compute_quality(processed_path, self.quality_config)
                    except Exception as exc:
                        page_warnings.append(f"quality_failed:{exc}")

                page_tables: List[TableRegion] = []
                if "tables" in task_set:
                    page_tables = detect_tables(
                        processed_path,
                        page_number=page_number,
                        config=self.extractor_config.get("tables", {}),
                    )
                    tables.extend(page_tables)

                measurement_patterns = self.engineering_config.get(
                    "measurement_patterns",
                    [
                        r"\d+\.?\d*\s*(?:mm|cm|m|km|in|ft|yd)",
                        r"\d+\'\d+\"",
                        r"\d+\.?\d*\s*x\s*\d+\.?\d*",
                    ],
                )
                measurements = []
                if "measurements" in task_set:
                    measurements = extract_measurements(
                        ocr_text,
                        page_number,
                        measurement_patterns,
                    )

                key_values = []
                if "key_values" in task_set:
                    key_values = extract_key_values(
                        ocr_text,
                        page_number,
                        self.extractor_config.get("key_values", {}),
                    )

                vision_output = None
                if self.vision_model:
                    vision_scope = self.config.get("vision", {}).get("scope", "first_page")
                    if vision_scope == "all_pages" or page_number == 1:
                        vision_output = self.vision_model.interpret_document(
                            processed_path,
                            context=ocr_text,
                        )

                page_results.append(
                    PageResult(
                        page_number=page_number,
                        ocr_text=ocr_text,
                        layout=layout_regions,
                        quality=quality,
                        tables=page_tables,
                        key_values=key_values,
                        measurements=measurements,
                        vision_interpretation=vision_output,
                        warnings=page_warnings,
                    )
                )

            result.pages = page_results
            result.ocr_text = "\n\n".join(ocr_parts)
            result.tables = tables
            result.key_values = [kv for page in page_results for kv in page.key_values]
            result.measurements = [m for page in page_results for m in page.measurements]

            if "classify" in task_set:
                result.document_type = classify_document(result.ocr_text)

            if "summary" in task_set and self.vision_model and page_results:
                summary_prompt = _summary_prompt(result.ocr_text)
                summary_response = self.vision_model.interpret_document(
                    image_paths[0],
                    prompt=summary_prompt,
                    context=result.ocr_text,
                )
                summary_text = summary_response.get("interpretation") if isinstance(summary_response, dict) else None
                result.summary = summary_text
            elif "summary" in task_set:
                warnings.append("summary_unavailable_without_vision_model")

        result.warnings = warnings
        return result

    def _load_images(self, document_path: Path, output_dir: Path) -> List[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        if is_pdf_file(document_path):
            pdf_config = self.processing_config.get("pdf", {})
            dpi = int(pdf_config.get("dpi", 300))
            poppler_path = pdf_config.get("poppler_path")
            return pdf_to_images(
                document_path,
                output_dir=output_dir,
                dpi=dpi,
                poppler_path=poppler_path,
            )
        return [document_path]


def _summary_prompt(ocr_text: str) -> str:
    trimmed = (ocr_text or "")[:800]
    return (
        "Summarize this document for a downstream automation system. "
        "Focus on document type, key fields, and any notable quality issues. "
        f"\n\nOCR context:\n{trimmed}"
    )
