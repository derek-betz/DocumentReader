# DocumentReader - Document AI Agent

A specialized Document AI Agent for reading and interpreting difficult documents like photocopied road engineering plans and complex PDFs. This system combines advanced OCR, vision-language models, and layout detection to extract information from low-legibility documents.

## 🎯 Core Mission

Reading and interpreting challenging documents including:
- Photocopied engineering plans
- Technical drawings and blueprints
- Low-legibility scanned documents
- Complex multi-page PDFs
- Road engineering specifications
- Construction documents

## ✨ Features

### Advanced OCR
- **Tesseract OCR**: High-quality open-source OCR with customizable parameters
- **PaddleOCR**: State-of-the-art multilingual OCR particularly effective for low-quality documents
- Image preprocessing for enhanced OCR accuracy (contrast enhancement, denoising, deskewing)

### Vision-Language Models
- **GPT-4o**: OpenAI's vision model for document interpretation
- **Claude**: Anthropic's vision model for detailed document analysis
- Context-aware interpretation combining OCR and visual understanding

### Layout Detection
- Automatic detection of text regions, tables, figures, and other document elements
- Support for multiple layout analysis models (LayoutParser, Detectron2)
- Structured extraction of document components

### Specialized Processing
- Engineering plan processing with measurement and annotation extraction
- Batch processing capabilities
- PDF to image conversion
- Configurable processing pipelines

## 📁 Project Structure

```
DocumentReader/
├── src/
│   └── document_reader/
│       ├── __init__.py
│       ├── document_processor.py      # Main processing pipeline
│       ├── ocr/
│       │   ├── tesseract_reader.py    # Tesseract OCR wrapper
│       │   └── paddle_reader.py       # PaddleOCR wrapper
│       ├── vision/
│       │   └── vl_model.py            # Vision-language models
│       ├── layout/
│       │   └── detector.py            # Layout detection
│       └── utils/
│           ├── file_utils.py          # File operations
│           └── image_utils.py         # Image preprocessing
├── scripts/
│   ├── process_documents.py           # General document processing
│   └── process_engineering_plans.py   # Engineering-specific processing
├── data/
│   ├── input/                         # Input documents
│   ├── output/                        # Processing results
│   ├── models/                        # Model weights
│   └── samples/                       # Sample documents
├── tests/                             # Unit tests
├── requirements.txt                   # Python dependencies
├── setup.py                           # Package installation
├── config.yaml                        # Configuration file
└── README.md                          # This file
```

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- Tesseract OCR (for Tesseract engine)
- Poppler (for PDF processing)

#### Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr poppler-utils
```

**macOS:**
```bash
brew install tesseract poppler
```

**Windows:**
- Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
- Download Poppler from: https://blog.alivate.com.au/poppler-windows/

### Python Dependencies

```bash
# Clone the repository
git clone https://github.com/derek-betz/DocumentReader.git
cd DocumentReader

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

### Optional: Detectron2 for Advanced Layout Detection

```bash
python -m pip install 'git+https://github.com/facebookresearch/detectron2.git'
```

## 🔧 Configuration

Create a `config.yaml` file or use environment variables for API keys:

```yaml
# config.yaml
ocr:
  engine: "tesseract"  # or "paddleocr"
  tesseract:
    language: "eng"
    psm: 3
    enhance_contrast: true
    denoise: true
    deskew: true
  paddleocr:
    language: "en"
    use_angle_cls: true

vision:
  enabled: false
  model: "gpt-4o"  # or "claude"
  openai_api_key: "your-api-key-here"
  anthropic_api_key: "your-api-key-here"

layout:
  enabled: true
  model_type: "layoutparser"
  confidence_threshold: 0.5
```

Or use environment variables:
```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

## 📖 Usage

### Basic Usage

#### Processing a Single Document

```python
from document_reader import DocumentProcessor

# Initialize processor
processor = DocumentProcessor(
    ocr_engine="tesseract",
    use_vision_model=False,
    detect_layout=True
)

# Process document
results = processor.process_document("path/to/document.png")

# Save results
processor.save_results(results, "output/results.json")
```

#### Processing with Vision-Language Model

```python
processor = DocumentProcessor(
    ocr_engine="paddleocr",
    use_vision_model=True,
    vision_model="gpt-4o",
    detect_layout=True,
    config={"vision": {"openai_api_key": "your-key"}}
)

results = processor.process_document("path/to/document.pdf")
```

### Command-Line Interface

#### Process General Documents

```bash
# Process a single document
python scripts/process_documents.py input.png -o output/

# Process with PaddleOCR
python scripts/process_documents.py input.pdf --ocr paddleocr -o output/

# Process with vision model
python scripts/process_documents.py input.png --vision --vision-model gpt-4o -o output/

# Batch process all files in a directory
python scripts/process_documents.py input_dir/ --batch -o output/
```

#### Process Engineering Plans

```bash
# Process an engineering plan with all features
python scripts/process_engineering_plans.py plan.png -o output/engineering/

# Process with specific OCR engine
python scripts/process_engineering_plans.py plan.pdf --ocr tesseract

# Disable vision model
python scripts/process_engineering_plans.py plan.png --no-vision

# Skip measurement extraction
python scripts/process_engineering_plans.py plan.png --no-measurements
```

## 🔄 Processing Pipeline

### For Low-Legibility Engineering Scans

1. **Preprocessing**
   - Load document (image or PDF)
   - Convert PDF to images if needed
   - Enhance contrast and remove noise
   - Deskew rotated images

2. **Layout Detection**
   - Identify text regions, tables, figures
   - Extract bounding boxes and region types
   - Order regions by reading flow

3. **OCR Extraction**
   - Apply OCR to each region
   - Extract text with confidence scores
   - Handle multiple languages if needed

4. **Vision-Language Interpretation** (Optional)
   - Send image to GPT-4o or Claude
   - Get semantic understanding
   - Extract structured information

5. **Engineering-Specific Extraction**
   - Extract measurements and dimensions
   - Identify technical annotations
   - Detect symbols and specifications
   - Extract metadata (scale, units, etc.)

6. **Output Generation**
   - Structured JSON with all extracted data
   - Human-readable summary
   - Annotated images (optional)

### Example Pipeline Flow

```
Low-Legibility Engineering Scan
         ↓
   Preprocessing
   (Enhance, Denoise, Deskew)
         ↓
   Layout Detection
   (Identify Regions)
         ↓
   Advanced OCR
   (Tesseract/PaddleOCR)
         ↓
   Vision Model (Optional)
   (GPT-4o/Claude)
         ↓
   Data Extraction
   (Measurements, Annotations)
         ↓
   Structured Output
   (JSON + Summary)
```

## 📊 Output Format

### JSON Structure

```json
{
  "document_path": "path/to/document.png",
  "ocr_text": "Extracted text content...",
  "layout_analysis": {
    "regions": [
      {
        "type": "text",
        "bbox": [x1, y1, x2, y2],
        "confidence": 0.95
      }
    ],
    "num_regions": 10
  },
  "vision_interpretation": {
    "model": "gpt-4o",
    "interpretation": "This is a road engineering plan showing..."
  },
  "engineering_data": {
    "measurements": [
      {"value": "10.5m", "position": [100, 200]}
    ],
    "annotations": [...],
    "symbols": [...]
  },
  "extracted_data": {
    "text_blocks": [...],
    "tables": [...],
    "headers": [...]
  }
}
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_ocr.py
```

## 🔍 Advanced Features

### Custom OCR Configuration

```python
config = {
    "tesseract": {
        "language": "eng+fra",  # Multiple languages
        "psm": 6,              # Assume uniform block
        "oem": 3,              # LSTM neural network
        "enhance_contrast": True,
        "denoise": True,
        "deskew": True
    }
}

processor = DocumentProcessor(ocr_engine="tesseract", config=config)
```

### Image Preprocessing

```python
from document_reader.utils import enhance_image_for_ocr, deskew_image

# Enhance image before processing
enhanced = enhance_image_for_ocr("input.png", "enhanced.png")

# Deskew rotated images
deskewed = deskew_image("input.png", "deskewed.png")
```

### Batch Processing with Progress

```python
from pathlib import Path
from document_reader import DocumentProcessor

processor = DocumentProcessor()
input_dir = Path("data/input")
output_dir = Path("data/output")

for i, file_path in enumerate(input_dir.glob("*.png")):
    print(f"Processing {i+1}: {file_path.name}")
    results = processor.process_document(file_path)
    processor.save_results(results, output_dir / f"{file_path.stem}.json")
```

## 🛠️ Development

### Code Style

```bash
# Format code
black src/ scripts/ tests/

# Check style
flake8 src/ scripts/ tests/

# Type checking
mypy src/
```

### Adding New Features

1. Fork the repository
2. Create a feature branch
3. Add your changes with tests
4. Ensure all tests pass
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or support, please open an issue on GitHub.

## 🙏 Acknowledgments

- Tesseract OCR project
- PaddleOCR team
- OpenAI and Anthropic for vision-language models
- LayoutParser project
- Detectron2 framework

## 📚 References

- [Tesseract OCR Documentation](https://github.com/tesseract-ocr/tesseract)
- [PaddleOCR Documentation](https://github.com/PaddlePaddle/PaddleOCR)
- [LayoutParser Paper](https://arxiv.org/abs/2103.15348)
- [GPT-4 Vision Documentation](https://platform.openai.com/docs/guides/vision)
- [Claude Vision Documentation](https://docs.anthropic.com/claude/docs)
