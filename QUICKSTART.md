# Roadway-Doc-Engine - Quick Start Guide

This guide will help you get started with Roadway-Doc-Engine in under 10 minutes.

## 🎯 What You'll Learn

- How to install and configure Roadway-Doc-Engine
- How to process your first roadway construction plan
- How to use the REST API, Web UI, and Desktop GUI
- How to identify INDOT sheet types

## Prerequisites

Before starting, ensure you have:
- Python 3.8 or higher
- Tesseract OCR installed
- Poppler (for PDF processing)
- Node.js 18+ (optional, for Web UI)

## Step 1: System Dependencies

### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr poppler-utils python3-pip
```

### macOS
```bash
brew install tesseract poppler python
```

### Windows
1. Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
2. Download Poppler: https://blog.alivate.com.au/poppler-windows/
3. Add both to your PATH

## Step 2: Install Roadway-Doc-Engine

```bash
# Clone the repository
git clone https://github.com/derek-betz/DocumentReader.git
cd DocumentReader

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with all features
pip install -e ".[all,dev]"
```

## Step 3: Quick Test

Let's verify everything works:

```bash
# Run tests
pytest tests/ -v

# Should show: 26 passed
```

## Step 4: Choose Your Interface

### Option A: Python Library (Recommended for Development)

Create a file `test_processing.py`:

```python
from document_reader import DocumentProcessor

# Initialize the processor
processor = DocumentProcessor(
    ocr_engine="tesseract",
    detect_layout=True
)

# Process an engineering plan (use your own PDF)
results = processor.process_engineering_plan(
    "path/to/your/plan.pdf",
    extract_measurements=True,
    extract_annotations=True
)

# Identify INDOT sheet type
sheet_info = processor.identify_indot_sheet_headers(results)

# Display results
print(f"Sheet Type: {sheet_info['sheet_type']}")
print(f"Confidence: {sheet_info['confidence']:.1%}")
print(f"Project Number: {sheet_info.get('project_number', 'N/A')}")
print(f"Sheet Number: {sheet_info.get('sheet_number', 'N/A')}")

# Save results
processor.save_results(results, "output/results.json")
print("Results saved to output/results.json")
```

Run it:
```bash
python test_processing.py
```

### Option B: REST API (Recommended for Integration)

#### Start the API Server

Terminal 1:
```bash
# Start the API
uvicorn src.api.main:app --reload --port 8000
```

#### Use the API

Terminal 2:
```bash
# Process a document
curl -X POST "http://localhost:8000/process/engineering-plan" \
  -F "file=@plan.pdf" \
  -F "ocr_engine=tesseract"

# Or identify sheet type only
curl -X POST "http://localhost:8000/identify-sheet-type" \
  -F "file=@plan.pdf"
```

#### Interactive API Documentation

Visit `http://localhost:8000/docs` in your browser for:
- Interactive API testing
- Complete endpoint documentation
- Request/response examples

#### Python Client Example

```python
import requests

# Process a document
with open('plan.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/process/engineering-plan',
        files={'file': f},
        params={'ocr_engine': 'tesseract'}
    )

results = response.json()
sheet_info = results['results']['indot_sheet_info']

print(f"Sheet Type: {sheet_info['sheet_type']}")
print(f"Confidence: {sheet_info['confidence']:.1%}")
```

### Option C: Web UI (Recommended for End Users)

#### Start the Web UI

Terminal 1 - Start API:
```bash
uvicorn src.api.main:app --port 8000
```

Terminal 2 - Start Web UI:
```bash
cd web-ui
npm install  # First time only
npm run dev
```

Visit `http://localhost:3000` in your browser:
1. Drag and drop a PDF or image file
2. Configure processing options
3. Click "Process Document"
4. View INDOT sheet information and results

### Option D: Desktop GUI (Recommended for Offline Use)

```bash
# Install PyQt5 (if not already installed)
pip install PyQt5

# Run the desktop application
python desktop-gui/main.py
```

Features:
- Drag and drop files directly
- Process without internet connection
- Export results to JSON or text
- Real-time progress indicators

## Step 5: Advanced Features

### Using Vision-Language Models

Set up API keys:
```bash
# Add to .env file or export
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

Use in code:
```python
processor = DocumentProcessor(
    ocr_engine="tesseract",
    use_vision_model=True,
    vision_model="gpt-4o"  # or "claude"
)
```

### Processing Multiple Documents

```python
from pathlib import Path

processor = DocumentProcessor()
input_dir = Path("input_plans")
output_dir = Path("output_results")
output_dir.mkdir(exist_ok=True)

for pdf_file in input_dir.glob("*.pdf"):
    print(f"Processing {pdf_file.name}...")
    
    results = processor.process_engineering_plan(pdf_file)
    sheet_info = processor.identify_indot_sheet_headers(results)
    
    output_file = output_dir / f"{pdf_file.stem}.json"
    processor.save_results(results, output_file)
    
    print(f"  Sheet Type: {sheet_info['sheet_type']}")
    print(f"  Saved to: {output_file}")
```

### Using PaddleOCR (Better for Low-Quality Scans)

```bash
# Install PaddleOCR (optional)
pip install paddleocr paddlepaddle

# Use in code
processor = DocumentProcessor(ocr_engine="paddleocr")
```

## Step 6: Understanding INDOT Sheet Types

Roadway-Doc-Engine can identify these INDOT standard sheets:

| Sheet Type | Abbreviation | Description |
|------------|--------------|-------------|
| Title Sheet | TS | Project overview and index |
| General Notes | GN | Project-wide specifications |
| Plan and Profile | PP | Horizontal and vertical alignment |
| Cross-Section | XS | Typical and detailed sections |
| Detail Sheet | DT | Construction details |
| Traffic Control Plan | TCP/MOT | Temporary traffic control |
| Signing and Pavement Markings | SPM | Sign and marking plans |
| Drainage | DR | Drainage structures |
| Utility | UT | Utility coordination |

Example output:
```json
{
  "sheet_type": "Plan and Profile",
  "sheet_number": "15",
  "project_number": "DES-1234567",
  "confidence": 0.95,
  "sheet_title": "STATE ROAD 37 IMPROVEMENTS"
}
```

## Step 7: Integration with Other Tools

### Integrate with a Quantity Takeoff System

```python
import requests

# Your existing tool's code
def process_plan_for_quantities(plan_file):
    # Send to Roadway-Doc-Engine
    with open(plan_file, 'rb') as f:
        response = requests.post(
            'http://localhost:8000/process/engineering-plan',
            files={'file': f}
        )
    
    data = response.json()
    measurements = data['results']['engineering_data']['measurements']
    
    # Process measurements in your tool
    for measurement in measurements:
        value = measurement['value']
        # ... your quantity calculation logic
        
    return calculated_quantities
```

### Integrate with a Document Management System

```python
# Your DMS integration
def classify_and_store_plan(plan_file, dms_client):
    # Identify sheet type
    with open(plan_file, 'rb') as f:
        response = requests.post(
            'http://localhost:8000/identify-sheet-type',
            files={'file': f}
        )
    
    sheet_info = response.json()['sheet_info']
    
    # Store with metadata
    dms_client.upload_document(
        file=plan_file,
        metadata={
            'sheet_type': sheet_info['sheet_type'],
            'project_number': sheet_info['project_number'],
            'confidence': sheet_info['confidence']
        }
    )
```

## Troubleshooting

### OCR Not Working
```bash
# Verify Tesseract installation
tesseract --version

# If missing, install it
sudo apt-get install tesseract-ocr
```

### PDF Processing Errors
```bash
# Verify Poppler installation
pdftoppm -v

# If missing, install it
sudo apt-get install poppler-utils
```

### Import Errors
```bash
# Reinstall in development mode
pip install -e .

# Or add src to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Low OCR Accuracy
- Try PaddleOCR instead of Tesseract
- Ensure input images are high resolution (300+ DPI)
- Use image preprocessing options
- Consider using vision-language models for difficult documents

## Next Steps

1. **Read the full documentation**: Check `README.md` and `ARCHITECTURE.md`
2. **Explore examples**: Look at scripts in the `scripts/` directory
3. **Run more tests**: `pytest tests/ -v --cov=src`
4. **Customize**: Modify OCR settings in `config.yaml`
5. **Contribute**: Fork the repo and submit pull requests

## Getting Help

- **Issues**: Open an issue on GitHub
- **Documentation**: Read `ARCHITECTURE.md` for design details
- **Examples**: Check `scripts/example_usage.py`
- **Tests**: Look at `tests/` for usage patterns

## Example Workflow

Here's a complete workflow for processing roadway plans:

```bash
# 1. Set up your environment
source venv/bin/activate

# 2. Start the API (Terminal 1)
uvicorn src.api.main:app --port 8000

# 3. Process documents (Terminal 2)
python << 'EOF'
import requests
import json
from pathlib import Path

# Process all PDFs in a directory
for pdf in Path("plans").glob("*.pdf"):
    print(f"\nProcessing: {pdf.name}")
    
    with open(pdf, 'rb') as f:
        response = requests.post(
            'http://localhost:8000/process/engineering-plan',
            files={'file': f}
        )
    
    results = response.json()
    sheet_info = results['results']['indot_sheet_info']
    
    # Display summary
    print(f"  Type: {sheet_info['sheet_type']}")
    print(f"  Confidence: {sheet_info['confidence']:.0%}")
    
    # Save results
    output = Path("output") / f"{pdf.stem}.json"
    output.parent.mkdir(exist_ok=True)
    with open(output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"  Saved: {output}")
EOF
```

---

**You're now ready to process roadway construction plans with Roadway-Doc-Engine!** 🎉

For more information, visit the [full documentation](README.md).
