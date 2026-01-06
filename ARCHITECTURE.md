# Architecture Overview

## System Architecture

The Document AI Agent is designed with a modular architecture that separates concerns and allows for flexible configuration and extension.

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
│  (CLI Scripts: process_documents.py, process_engineering_plans.py) │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   DocumentProcessor                          │
│              (Main Processing Pipeline)                      │
│  - Orchestrates all components                              │
│  - Manages processing flow                                  │
│  - Handles configuration                                    │
└─────┬────────────┬─────────────┬──────────────┬────────────┘
      │            │             │              │
      ▼            ▼             ▼              ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│   OCR    │ │  Vision  │ │  Layout  │ │  Utilities   │
│  Engine  │ │  Models  │ │ Detector │ │  (file,      │
│          │ │          │ │          │ │   image)     │
└──────────┘ └──────────┘ └──────────┘ └──────────────┘
```

## Core Components

### 1. DocumentProcessor
**Location:** `src/document_reader/document_processor.py`

The main orchestrator that coordinates all document processing operations.

**Responsibilities:**
- Initialize and configure all sub-components
- Execute processing pipeline
- Coordinate data flow between components
- Handle errors and logging
- Generate structured output

**Key Methods:**
- `process_document()` - General document processing
- `process_engineering_plan()` - Specialized engineering plan processing
- `_extract_structured_data()` - Extract structured information
- `_extract_measurements()` - Extract measurements from technical documents

### 2. OCR Module
**Location:** `src/document_reader/ocr/`

Handles optical character recognition with support for multiple engines.

#### TesseractOCR (`tesseract_reader.py`)
- Wrapper for Tesseract OCR engine
- Image preprocessing (enhance, denoise, deskew)
- Configurable PSM and OEM modes
- Multilingual support

#### PaddleOCRReader (`paddle_reader.py`)
- Wrapper for PaddleOCR engine
- Better performance on low-quality documents
- Multilingual support with angle classification
- Table structure recognition

**Features:**
- Image enhancement for low-legibility documents
- Automatic deskewing
- Noise reduction
- Contrast enhancement

### 3. Vision Module
**Location:** `src/document_reader/vision/`

Integrates vision-language models for semantic understanding.

#### VisionLanguageModel (`vl_model.py`)
- GPT-4o integration (OpenAI)
- Claude integration (Anthropic)
- Context-aware interpretation
- Specialized prompts for engineering documents

**Features:**
- Document type identification
- Semantic information extraction
- Visual understanding beyond OCR
- Customizable prompts

### 4. Layout Module
**Location:** `src/document_reader/layout/`

Detects and analyzes document layout structure.

#### LayoutDetector (`detector.py`)
- Basic OpenCV-based detection
- LayoutParser integration (optional)
- Detectron2 support (optional)

**Detected Elements:**
- Text regions
- Tables
- Figures/images
- Headers and titles
- Columns

### 5. Utilities Module
**Location:** `src/document_reader/utils/`

Provides helper functions for file and image operations.

#### FileUtils (`file_utils.py`)
- File type detection
- PDF to image conversion
- Configuration loading/saving
- Directory management

#### ImageUtils (`image_utils.py`)
- Image enhancement
- Deskewing
- Binarization
- Noise removal
- Resizing

## Processing Pipeline

### General Document Processing Flow

```
1. Input Validation
   ├─ Check file exists
   ├─ Detect file type (image/PDF)
   └─ Load configuration

2. Preprocessing
   ├─ Convert PDF to images (if needed)
   ├─ Enhance image quality
   ├─ Deskew rotated images
   └─ Normalize dimensions

3. Layout Detection (Optional)
   ├─ Identify document regions
   ├─ Classify region types
   └─ Extract bounding boxes

4. OCR Extraction
   ├─ Apply OCR to each region
   ├─ Extract text with confidence
   └─ Preserve spatial information

5. Vision Model (Optional)
   ├─ Encode image to base64
   ├─ Send to vision model
   ├─ Get semantic interpretation
   └─ Extract structured data

6. Post-processing
   ├─ Combine all results
   ├─ Extract structured data
   ├─ Generate metadata
   └─ Format output

7. Output Generation
   ├─ Create JSON with all data
   ├─ Generate summary (optional)
   └─ Save to disk
```

### Engineering Plan Processing Flow

```
1. Load Engineering Document
   └─ Validate file format

2. Enhanced Preprocessing
   ├─ Aggressive contrast enhancement
   ├─ Advanced denoising
   ├─ Deskewing
   └─ Edge detection

3. Layout Analysis
   ├─ Identify drawing regions
   ├─ Locate text annotations
   ├─ Find measurement labels
   └─ Detect symbols

4. Specialized OCR
   ├─ Use optimized PSM mode
   ├─ Extract technical text
   └─ Preserve formatting

5. Measurement Extraction
   ├─ Regex pattern matching
   ├─ Unit detection
   ├─ Dimension parsing
   └─ Scale extraction

6. Annotation Extraction
   ├─ Identify text notes
   ├─ Extract labels
   └─ Parse specifications

7. Vision Model Analysis
   ├─ Understand drawing context
   ├─ Identify drawing type
   └─ Extract technical details

8. Engineering Report
   ├─ Compile all data
   ├─ Generate structured output
   ├─ Create human-readable summary
   └─ Save results
```

## Data Flow

```
Input Document
     │
     ▼
[File Validator]
     │
     ▼
[Preprocessor] ─────► Enhanced Image
     │
     ▼
[Layout Detector] ──► Layout Data
     │
     ▼
[OCR Engine] ───────► Text + Confidence
     │
     ▼
[Vision Model] ─────► Semantic Data
     │
     ▼
[Data Extractor] ───► Structured Data
     │
     ▼
[Output Generator] ─► JSON + Summary
     │
     ▼
Output Files
```

## Configuration System

### Configuration Hierarchy

1. **Default Configuration** (`config.yaml`)
   - System-wide defaults
   - Default model parameters

2. **Runtime Configuration** (passed to constructor)
   - Override defaults
   - Specific processing requirements

3. **Environment Variables**
   - API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY)
   - System paths

### Configuration Structure

```yaml
ocr:
  engine: tesseract
  tesseract: {language, psm, oem, ...}
  paddleocr: {language, use_angle_cls, ...}

vision:
  enabled: false
  model: gpt-4o
  api_keys: ...

layout:
  enabled: true
  model_type: basic_opencv
  confidence_threshold: 0.5

processing:
  pdf: {dpi, format}
  output: {save_intermediate, ...}
  batch: {parallel, max_workers}

engineering:
  extract_measurements: true
  extract_annotations: true
  measurement_patterns: [...]
```

## Extensibility Points

### Adding New OCR Engine

1. Create new file in `src/document_reader/ocr/`
2. Implement `extract_text()` and `extract_data()` methods
3. Add to `DocumentProcessor` initialization
4. Update documentation

### Adding New Vision Model

1. Extend `VisionLanguageModel` class
2. Implement model-specific initialization
3. Add interpretation method
4. Update configuration

### Adding Custom Layout Detector

1. Create detector class in `src/document_reader/layout/`
2. Implement `detect_layout()` method
3. Register in `LayoutDetector`
4. Update configuration options

## Error Handling

### Error Strategy

1. **Graceful Degradation**
   - If vision model fails, continue with OCR only
   - If layout detection fails, use basic text extraction
   - Log warnings but don't halt processing

2. **Detailed Logging**
   - All errors logged with context
   - Warning level for recoverable issues
   - Error level for critical failures

3. **Structured Error Responses**
   - Return error information in results
   - Include error type and message
   - Preserve partial results when possible

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading**
   - Models loaded only when needed
   - Defer heavy imports

2. **Caching**
   - Cache preprocessed images
   - Reuse OCR results when possible

3. **Batch Processing**
   - Process multiple documents efficiently
   - Optional parallel processing

4. **Resource Management**
   - Clean up temporary files
   - Release model memory when done

### Performance Tips

- Use PaddleOCR for batch processing (faster)
- Enable GPU for large batches (if available)
- Adjust image DPI based on quality needs
- Disable vision models for simple documents

## Security Considerations

1. **API Keys**
   - Never commit API keys
   - Use environment variables
   - Support secure configuration files

2. **Input Validation**
   - Validate file types
   - Check file sizes
   - Sanitize file paths

3. **Output Security**
   - Secure temporary file handling
   - Safe output path construction
   - No sensitive data in logs

## Testing Strategy

### Test Levels

1. **Unit Tests**
   - Individual component testing
   - Mock external dependencies
   - Test edge cases

2. **Integration Tests**
   - Component interaction
   - End-to-end processing
   - Configuration validation

3. **System Tests**
   - Real document processing
   - Performance benchmarks
   - Error handling verification

### Test Coverage

- Core functionality: OCR, layout, vision
- Error handling and edge cases
- Configuration parsing
- File I/O operations

## Future Enhancements

### Planned Features

1. **Table Extraction**
   - Advanced table recognition
   - Structure preservation
   - Cell content extraction

2. **Form Processing**
   - Form field detection
   - Checkbox recognition
   - Signature area identification

3. **Multi-page Document Handling**
   - Page relationship detection
   - Cross-page reference resolution
   - Document assembly

4. **Real-time Processing**
   - Streaming API
   - Progressive results
   - Live preview

5. **Advanced Analytics**
   - Document classification
   - Similarity detection
   - Automated summarization

## Dependencies

### Core Dependencies
- numpy: Numerical operations
- Pillow: Image handling
- opencv-python: Computer vision
- pytesseract: Tesseract wrapper
- PyYAML: Configuration

### Optional Dependencies
- paddleocr: Advanced OCR
- openai: GPT-4o integration
- anthropic: Claude integration
- layoutparser: Advanced layout
- torch: Deep learning backend

## Deployment

### Deployment Options

1. **Local Installation**
   - Install as Python package
   - Use command-line scripts
   - Ideal for development

2. **Docker Container**
   - Containerized deployment
   - Includes all dependencies
   - Reproducible environment

3. **Cloud Deployment**
   - Serverless functions
   - API endpoints
   - Scalable processing

4. **Batch Processing**
   - Job queue system
   - Distributed processing
   - Result aggregation

## Monitoring and Logging

### Logging Levels

- DEBUG: Detailed processing information
- INFO: General progress updates
- WARNING: Recoverable issues
- ERROR: Critical failures
- CRITICAL: System failures

### Metrics to Monitor

- Processing time per document
- OCR confidence scores
- API usage and costs
- Error rates by type
- Resource utilization

## License and Attribution

This project is open source under the MIT License. It builds upon several excellent open source projects:

- Tesseract OCR
- PaddleOCR
- LayoutParser
- Detectron2
- OpenCV

See the [LICENSE](LICENSE) file for details.
