"""
Contracts for the generalized document expert service.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


DEFAULT_TASKS = [
    "classify",
    "quality",
    "tables",
    "measurements",
    "key_values",
]


class BoundingBox(BaseModel):
    x1: int = Field(..., description="Left coordinate")
    y1: int = Field(..., description="Top coordinate")
    x2: int = Field(..., description="Right coordinate")
    y2: int = Field(..., description="Bottom coordinate")


class LayoutRegion(BaseModel):
    type: str = Field(..., description="Region type")
    bbox: BoundingBox = Field(..., description="Bounding box")
    confidence: Optional[float] = Field(None, description="Detection confidence")
    text: Optional[str] = Field(None, description="Region text if available")


class TableRegion(BaseModel):
    page_number: int = Field(..., description="Page index (1-based)")
    bbox: BoundingBox = Field(..., description="Table bounding box")
    confidence: Optional[float] = Field(None, description="Detection confidence")
    method: str = Field(..., description="Detection method")


class Measurement(BaseModel):
    page_number: int = Field(..., description="Page index (1-based)")
    value: str = Field(..., description="Measurement text")
    span: Optional[List[int]] = Field(None, description="Span in OCR text")


class KeyValue(BaseModel):
    page_number: int = Field(..., description="Page index (1-based)")
    key: str = Field(..., description="Key label")
    value: str = Field(..., description="Extracted value")
    line: Optional[str] = Field(None, description="Source line")


class QualityMetrics(BaseModel):
    width: int = Field(..., description="Image width")
    height: int = Field(..., description="Image height")
    blur_score: float = Field(..., description="Variance of Laplacian")
    contrast_score: float = Field(..., description="Standard deviation of grayscale")
    skew_angle: float = Field(..., description="Estimated skew angle in degrees")
    mean_brightness: float = Field(..., description="Average grayscale brightness")
    flags: List[str] = Field(default_factory=list, description="Quality warnings")


class DocumentTypeResult(BaseModel):
    type: Optional[str] = Field(None, description="Document type classification")
    confidence: float = Field(0.0, description="Classification confidence")
    candidates: Dict[str, float] = Field(default_factory=dict, description="Candidate scores")


class PageResult(BaseModel):
    page_number: int = Field(..., description="Page index (1-based)")
    ocr_text: str = Field("", description="OCR text for the page")
    layout: List[LayoutRegion] = Field(default_factory=list, description="Layout regions")
    quality: Optional[QualityMetrics] = Field(None, description="Quality metrics")
    tables: List[TableRegion] = Field(default_factory=list, description="Detected tables")
    key_values: List[KeyValue] = Field(default_factory=list, description="Key-value pairs")
    measurements: List[Measurement] = Field(default_factory=list, description="Measurements")
    vision_interpretation: Optional[Dict[str, Any]] = Field(
        None, description="Vision-language model output"
    )
    warnings: List[str] = Field(default_factory=list, description="Page-specific warnings")


class DocumentResult(BaseModel):
    document_path: str = Field(..., description="Input document path")
    document_type: DocumentTypeResult = Field(
        default_factory=DocumentTypeResult, description="Document classification"
    )
    summary: Optional[str] = Field(None, description="High-level summary")
    language: Optional[str] = Field(None, description="Detected language")
    ocr_text: str = Field("", description="Combined OCR text")
    pages: List[PageResult] = Field(default_factory=list, description="Per-page results")
    tables: List[TableRegion] = Field(default_factory=list, description="All detected tables")
    key_values: List[KeyValue] = Field(default_factory=list, description="All key-values")
    measurements: List[Measurement] = Field(default_factory=list, description="All measurements")
    warnings: List[str] = Field(default_factory=list, description="Document-level warnings")


class ExpertProcessingOptions(BaseModel):
    ocr_engine: str = Field(default="tesseract", description="OCR engine")
    use_vision_model: bool = Field(default=False, description="Enable vision-language model")
    vision_model: str = Field(default="gpt-4o", description="Vision model to use")
    detect_layout: bool = Field(default=True, description="Enable layout detection")
    tasks: List[str] = Field(default_factory=lambda: list(DEFAULT_TASKS))
    preprocess: bool = Field(default=True, description="Enable image preprocessing")


class ExpertProcessingResponse(BaseModel):
    status: str = Field(..., description="Processing status")
    results: Optional[DocumentResult] = Field(None, description="Processing results")
    error: Optional[str] = Field(None, description="Error message, if any")
