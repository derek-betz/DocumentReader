"""
FastAPI main application for Roadway-Doc-Engine REST API.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

import sys
from pathlib import Path
# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from document_reader import DocumentProcessor
from document_reader.expert import DocumentExpert
from document_reader.expert.contracts import (
    ExpertProcessingOptions,
    ExpertProcessingResponse,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Roadway-Doc-Engine API",
    description="REST API for processing roadway construction plans and engineering documents",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for web UI integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class ProcessingOptions(BaseModel):
    """Options for document processing."""
    ocr_engine: str = Field(default="tesseract", description="OCR engine: tesseract or paddleocr")
    use_vision_model: bool = Field(default=False, description="Enable vision-language model")
    vision_model: str = Field(default="gpt-4o", description="Vision model: gpt-4o or claude")
    detect_layout: bool = Field(default=True, description="Enable layout detection")
    extract_measurements: bool = Field(default=True, description="Extract measurements from plans")
    extract_annotations: bool = Field(default=True, description="Extract text annotations")
    identify_sheet_type: bool = Field(default=True, description="Identify INDOT sheet type")


class ProcessingResponse(BaseModel):
    """Response model for document processing."""
    status: str = Field(description="Processing status")
    document_path: Optional[str] = Field(None, description="Path to processed document")
    results: Optional[Dict[str, Any]] = Field(None, description="Processing results")
    error: Optional[str] = Field(None, description="Error message if processing failed")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    version: str
    message: str


# Global processor instance (can be configured via environment variables)
_processor: Optional[DocumentProcessor] = None
_expert: Optional[DocumentExpert] = None


def get_processor(options: ProcessingOptions) -> DocumentProcessor:
    """Get or create a DocumentProcessor with specified options."""
    global _processor
    
    # For now, create a new processor for each request
    # In production, consider caching processors with common configurations
    config = {}
    
    # Add API keys from environment if using vision models
    if options.use_vision_model:
        config["vision"] = {}
        if options.vision_model == "gpt-4o":
            config["vision"]["openai_api_key"] = os.getenv("OPENAI_API_KEY")
        elif options.vision_model == "claude":
            config["vision"]["anthropic_api_key"] = os.getenv("ANTHROPIC_API_KEY")
    
    return DocumentProcessor(
        ocr_engine=options.ocr_engine,
        use_vision_model=options.use_vision_model,
        vision_model=options.vision_model,
        detect_layout=options.detect_layout,
        config=config
    )


def get_expert(options: ExpertProcessingOptions) -> DocumentExpert:
    """Get a DocumentExpert with specified options."""
    config = {}

    if options.use_vision_model:
        config["vision"] = {}
        if options.vision_model == "gpt-4o":
            config["vision"]["openai_api_key"] = os.getenv("OPENAI_API_KEY")
        elif options.vision_model == "claude":
            config["vision"]["anthropic_api_key"] = os.getenv("ANTHROPIC_API_KEY")

    return DocumentExpert(
        ocr_engine=options.ocr_engine,
        use_vision_model=options.use_vision_model,
        vision_model=options.vision_model,
        detect_layout=options.detect_layout,
        config=config,
    )


def cleanup_temp_file(file_path: Path):
    """Clean up temporary file after processing."""
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Cleaned up temporary file: {file_path}")
    except Exception as e:
        logger.error(f"Error cleaning up file {file_path}: {e}")


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - API information."""
    return HealthResponse(
        status="ok",
        version="0.1.0",
        message="Roadway-Doc-Engine API is running. Visit /docs for API documentation."
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        message="Service is operational"
    )


@app.post("/process", response_model=ProcessingResponse)
async def process_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Document file (PDF, PNG, JPG, etc.)"),
    ocr_engine: str = "tesseract",
    use_vision_model: bool = False,
    vision_model: str = "gpt-4o",
    detect_layout: bool = True,
    extract_measurements: bool = True,
    extract_annotations: bool = True,
    identify_sheet_type: bool = True
):
    """
    Process a roadway construction plan or engineering document.
    
    Upload a document file and receive extracted information including:
    - OCR text extraction
    - Layout analysis
    - INDOT sheet type identification
    - Measurements and annotations
    - Optional vision-language model interpretation
    """
    temp_file_path = None
    
    try:
        # Create processing options
        options = ProcessingOptions(
            ocr_engine=ocr_engine,
            use_vision_model=use_vision_model,
            vision_model=vision_model,
            detect_layout=detect_layout,
            extract_measurements=extract_measurements,
            extract_annotations=extract_annotations,
            identify_sheet_type=identify_sheet_type
        )
        
        # Save uploaded file to temporary location
        suffix = Path(file.filename).suffix if file.filename else ".tmp"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = Path(temp_file.name)
        
        logger.info(f"Processing uploaded file: {file.filename} (saved to {temp_file_path})")
        
        # Initialize processor
        processor = get_processor(options)
        
        # Process document
        if extract_measurements or extract_annotations:
            # Use engineering plan processing
            results = processor.process_engineering_plan(
                temp_file_path,
                extract_measurements=extract_measurements,
                extract_annotations=extract_annotations
            )
        else:
            # Use general document processing
            results = processor.process_document(temp_file_path)
        
        # Identify INDOT sheet type if requested
        if identify_sheet_type:
            sheet_info = processor.identify_indot_sheet_headers(results)
            results["indot_sheet_info"] = sheet_info
        
        # Schedule cleanup of temporary file
        if temp_file_path:
            background_tasks.add_task(cleanup_temp_file, temp_file_path)
        
        return ProcessingResponse(
            status="success",
            document_path=file.filename,
            results=results
        )
    
    except Exception as e:
        logger.error(f"Error processing document: {e}", exc_info=True)
        
        # Clean up temp file on error
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up temp file: {cleanup_error}")
        
        return ProcessingResponse(
            status="error",
            document_path=file.filename if file.filename else None,
            error=str(e)
        )


@app.post("/process/expert", response_model=ExpertProcessingResponse)
async def process_expert_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Document file (PDF, PNG, JPG, etc.)"),
    ocr_engine: str = "tesseract",
    use_vision_model: bool = False,
    vision_model: str = "gpt-4o",
    detect_layout: bool = True,
    preprocess: bool = True,
    tasks: Optional[List[str]] = Query(None),
):
    """
    Process any document with the generalized expert pipeline.

    This endpoint returns a structured, multi-task result for downstream agents.
    """
    temp_file_path = None

    try:
        options_payload = {
            "ocr_engine": ocr_engine,
            "use_vision_model": use_vision_model,
            "vision_model": vision_model,
            "detect_layout": detect_layout,
            "preprocess": preprocess,
        }
        if tasks:
            options_payload["tasks"] = tasks
        options = ExpertProcessingOptions(**options_payload)

        suffix = Path(file.filename).suffix if file.filename else ".tmp"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = Path(temp_file.name)

        expert = get_expert(options)
        if not options.preprocess:
            expert.processing_config.setdefault("preprocess", {})["enabled"] = False

        results = expert.analyze(temp_file_path, tasks=options.tasks)

        if temp_file_path:
            background_tasks.add_task(cleanup_temp_file, temp_file_path)

        return ExpertProcessingResponse(status="success", results=results)

    except Exception as e:
        logger.error(f"Error processing document (expert): {e}", exc_info=True)

        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up temp file: {cleanup_error}")

        return ExpertProcessingResponse(status="error", error=str(e))


@app.post("/process/engineering-plan", response_model=ProcessingResponse)
async def process_engineering_plan(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Engineering plan file (PDF, PNG, JPG, etc.)"),
    ocr_engine: str = "tesseract",
    use_vision_model: bool = False,
    vision_model: str = "gpt-4o"
):
    """
    Specialized endpoint for processing engineering plans with full feature extraction.
    
    This endpoint is optimized for roadway construction plans and automatically:
    - Extracts measurements and dimensions
    - Identifies text annotations
    - Detects INDOT sheet types
    - Performs layout analysis
    """
    return await process_document(
        background_tasks=background_tasks,
        file=file,
        ocr_engine=ocr_engine,
        use_vision_model=use_vision_model,
        vision_model=vision_model,
        detect_layout=True,
        extract_measurements=True,
        extract_annotations=True,
        identify_sheet_type=True
    )


@app.post("/identify-sheet-type", response_model=Dict[str, Any])
async def identify_sheet_type(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Sheet file to identify"),
    ocr_engine: str = "tesseract"
):
    """
    Quickly identify the INDOT sheet type without full processing.
    
    This is a lightweight endpoint that only performs OCR and sheet type identification,
    useful for batch classification or initial document routing.
    """
    temp_file_path = None
    
    try:
        # Save uploaded file to temporary location
        suffix = Path(file.filename).suffix if file.filename else ".tmp"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = Path(temp_file.name)
        
        logger.info(f"Identifying sheet type for: {file.filename}")
        
        # Initialize minimal processor
        processor = DocumentProcessor(
            ocr_engine=ocr_engine,
            use_vision_model=False,
            detect_layout=False
        )
        
        # Extract text only
        results = processor.process_document(temp_file_path)
        
        # Identify sheet type
        sheet_info = processor.identify_indot_sheet_headers(results)
        
        # Schedule cleanup
        if temp_file_path:
            background_tasks.add_task(cleanup_temp_file, temp_file_path)
        
        return {
            "status": "success",
            "filename": file.filename,
            "sheet_info": sheet_info
        }
    
    except Exception as e:
        logger.error(f"Error identifying sheet type: {e}", exc_info=True)
        
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up temp file: {cleanup_error}")
        
        raise HTTPException(status_code=500, detail=str(e))


def start_server():
    """Entry point for running the API server."""
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting Roadway-Doc-Engine API server on {host}:{port}")
    
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    start_server()
