# Roadway-Doc-Engine (DocumentReader)

A specialized document processing system designed to parse roadway construction plans (PDFs and CAD exports). This system combines advanced OCR, vision-language models, and layout detection to extract information from engineering documents, with specialized support for INDOT (Indiana Department of Transportation) standard sheet types.

## 🎯 Core Mission

Processing and interpreting roadway construction documents including:
- INDOT-standard engineering plans (Title Sheets, Plan & Profile, Cross-Sections)
- Photocopied road engineering plans  
- Technical drawings and blueprints
- Low-legibility scanned documents
- Complex multi-page PDFs

## ✨ Key Features

### 🔍 Specialized Document Processing
- **INDOT Sheet Type Identification**: Automatically identifies standard INDOT sheet types (Title Sheet, Plan & Profile, Cross-Sections, etc.)
- **Measurement Extraction**: Extracts dimensions, measurements, and annotations from engineering plans
- **Advanced OCR**: Tesseract and PaddleOCR support for high-quality text extraction
- **Layout Detection**: Identifies text regions, tables, figures, and document structure
- **Vision-Language Models**: Optional GPT-4o or Claude integration for semantic understanding

### 🌐 Dual-Interface Architecture

#### REST API (FastAPI)
- Production-ready API endpoints for document processing
- Integration-ready for other roadway task tools (quantity takeoff, utility coordination)
- Supports batch processing and async operations
- CORS-enabled for web integration

#### Web UI (React)
- Browser-based dashboard for document uploads
- Drag-and-drop interface
- Real-time processing status
- Interactive results display with INDOT sheet information

#### Desktop GUI (PyQt5)
- Lightweight local application
- High-speed drag-and-drop processing
- Offline processing capabilities
- Results export to JSON or text

### 🤖 Automated Maintenance
- Weekly GitHub Actions workflow to check for ML model updates
- Automatic issue creation when new versions are available
- Tracks updates for LayoutLMv3, PaddleOCR, Tesseract, and related models

## 📁 Project Structure

```
DocumentReader/
├── src/
│   ├── document_reader/        # Core document processing library
│   │   ├── __init__.py
│   │   ├── document_processor.py  # Main processor with INDOT support
│   │   ├── ocr/                # OCR engines (Tesseract, PaddleOCR)
│   │   ├── vision/             # Vision-language models
│   │   ├── layout/             # Layout detection
│   │   └── utils/              # Utilities
│   └── api/                    # FastAPI REST API layer
│       ├── __init__.py
│       └── main.py             # API endpoints
├── web-ui/                     # React web interface
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
├── desktop-gui/                # PyQt5 desktop application
│   ├── __init__.py
│   └── main.py
├── scripts/                    # Processing scripts
├── tests/                      # Unit and integration tests
├── .github/
│   ├── workflows/              # GitHub Actions
│   └── scripts/                # Automation scripts
├── pyproject.toml              # Modern Python packaging
├── requirements.txt
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Tesseract OCR (for Tesseract engine)
- Poppler (for PDF processing)
- Node.js 18+ (for web UI)

### Installation

#### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr poppler-utils
```

**macOS:**
```bash
brew install tesseract poppler
```

#### 2. Install Python Package

```bash
# Clone the repository
git clone https://github.com/derek-betz/DocumentReader.git
cd DocumentReader

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with all features
pip install -e ".[all]"

# Or install with specific features
pip install -e ".[dev,layout]"  # Development + Layout detection
```

### Using the REST API

#### Start the API Server

```bash
# Using the command
roadway-doc-engine-api

# Or directly with uvicorn
uvicorn src.api.main:app --reload
```

The API will be available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for interactive API documentation.

#### Example API Usage

```python
import requests

# Process a roadway plan
with open('plan.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/process',
        files={'file': f},
        params={
            'ocr_engine': 'tesseract',
            'identify_sheet_type': True,
            'extract_measurements': True
        }
    )

results = response.json()
print(f"Sheet Type: {results['results']['indot_sheet_info']['sheet_type']}")
```

### Using the Web UI

```bash
cd web-ui
npm install
npm run dev
```

Visit `http://localhost:3000` to access the web interface.

### Using the Desktop GUI

```bash
# Install PyQt5
pip install PyQt5

# Run the desktop application
python desktop-gui/main.py
```

### Using as a Python Library

```python
from document_reader import DocumentProcessor

# Initialize processor
processor = DocumentProcessor(
    ocr_engine="tesseract",
    detect_layout=True
)

# Process an engineering plan
results = processor.process_engineering_plan(
    "path/to/plan.pdf",
    extract_measurements=True
)

# Identify INDOT sheet type
sheet_info = processor.identify_indot_sheet_headers(results)
print(f"Sheet Type: {sheet_info['sheet_type']}")
print(f"Confidence: {sheet_info['confidence']:.2%}")
print(f"Project Number: {sheet_info['project_number']}")

# Save results
processor.save_results(results, "output/results.json")
```

### Using the Document Expert Pipeline

```python
from document_reader import DocumentExpert

expert = DocumentExpert(
    ocr_engine="tesseract",
    detect_layout=True
)

results = expert.analyze(
    "path/to/document.pdf",
    tasks=["classify", "quality", "tables", "measurements", "key_values"]
)

print(results.document_type.type)
print(results.ocr_text[:200])
```

```bash
process-expert path/to/document.pdf --tasks classify,quality,tables
```

## 📖 API Endpoints

### Core Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /process` - Process any document with full options
- `POST /process/engineering-plan` - Specialized engineering plan processing
- `POST /identify-sheet-type` - Quick INDOT sheet type identification
- `POST /process/expert` - Generalized expert pipeline with structured output

### Example Request

```bash
curl -X POST "http://localhost:8000/process/engineering-plan" \
  -F "file=@plan.pdf" \
  -F "ocr_engine=tesseract"
```

## 🔧 Configuration

### Environment Variables

```bash
# API Keys for vision models (optional)
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"

# API Server Configuration
export HOST="0.0.0.0"
export PORT="8000"
```

### Configuration File (config.yaml)

```yaml
ocr:
  engine: "tesseract"
  tesseract:
    language: "eng"
    psm: 3
    enhance_contrast: true

vision:
  enabled: false
  model: "gpt-4o"

layout:
  enabled: true
  confidence_threshold: 0.5
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_indot_identification.py -v
pytest tests/test_api.py -v

# Run with coverage
pytest --cov=src tests/
```

## 🛠️ Development

### Code Quality

```bash
# Format code
black src/ tests/ desktop-gui/

# Lint
flake8 src/ tests/ desktop-gui/

# Type checking
mypy src/
```

### Building for Distribution

```bash
# Build Python package
python -m build

# Build web UI
cd web-ui && npm run build
```

## 📊 INDOT Sheet Types Supported

The system can identify the following INDOT standard sheet types:

- **Title Sheet (TS)**: Project overview and index
- **General Notes (GN)**: Project-wide notes and specifications  
- **Plan and Profile (PP)**: Horizontal and vertical alignment
- **Cross-Sections (XS)**: Typical and detailed cross-sections
- **Detail Sheets (DT)**: Construction details
- **Traffic Control Plan (TCP)**: Temporary traffic control
- **Signing and Pavement Markings (SPM)**: Sign and marking plans
- **Drainage (DR)**: Drainage structures and details
- **Utility (UT)**: Utility relocations and coordination

## 🤝 Integration with Other Tools

The REST API layer enables integration with other roadway engineering tools:

```python
# Example: Integrate with quantity takeoff system
import requests

# Process plans and extract data
response = requests.post(
    'http://roadway-doc-engine:8000/process/engineering-plan',
    files={'file': open('plan.pdf', 'rb')}
)

# Use extracted measurements in your tool
measurements = response.json()['results']['engineering_data']['measurements']
# ... process measurements for quantity takeoff
```

## 🔄 Automated Model Updates

The system includes a weekly GitHub Action that:
1. Checks PyPI for new versions of ML dependencies
2. Checks Hugging Face for model updates
3. Creates GitHub issues when updates are available
4. Provides upgrade recommendations

Manual trigger:
```bash
# Go to Actions tab in GitHub
# Select "Weekly ML Model Update Check"
# Click "Run workflow"
```

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Tesseract OCR project
- PaddleOCR team  
- OpenAI and Anthropic for vision-language models
- LayoutParser project
- INDOT for roadway engineering standards

## 📧 Support

For questions or issues:
- Open an issue on GitHub
- Check the [documentation](ARCHITECTURE.md)
- Review [QUICKSTART.md](QUICKSTART.md)

## 🚀 Future Enhancements

- [ ] Support for more state DOT standards (TDOT, ODOT, etc.)
- [ ] Advanced table extraction from quantity sheets
- [ ] CAD file format support (DWG, DXF)
- [ ] Batch processing improvements
- [ ] Real-time streaming API
- [ ] Mobile application
- [ ] Cloud deployment templates (AWS, Azure, GCP)

---

**Built for roadway engineers, by engineers. Making construction document processing intelligent and efficient.**
