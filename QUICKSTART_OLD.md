# Quick Start Guide

Get started with Document AI Agent in minutes!

## 1. Installation

```bash
# Clone the repository
git clone https://github.com/derek-betz/DocumentReader.git
cd DocumentReader

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install basic dependencies
pip install numpy Pillow opencv-python pytesseract PyYAML python-dotenv
```

## 2. Install System Dependencies

### Ubuntu/Debian
```bash
sudo apt-get install tesseract-ocr poppler-utils
```

### macOS
```bash
brew install tesseract poppler
```

## 3. Quick Test

Create a test script `test_quick.py`:

```python
from pathlib import Path
import sys
sys.path.insert(0, 'src')

from document_reader.ocr.tesseract_reader import TesseractOCR

# Initialize OCR
ocr = TesseractOCR()
print("✓ Document AI Agent is ready!")
print(f"OCR engine: {ocr.language}, PSM: {ocr.psm}")
```

Run it:
```bash
python test_quick.py
```

## 4. Process Your First Document

```bash
# Place an image in data/input/
# Then run:
python scripts/process_documents.py data/input/your_image.png -o data/output/
```

## 5. For Engineering Plans

```bash
python scripts/process_engineering_plans.py data/input/plan.png -o data/output/
```

## Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Configure API keys for vision models (optional)
3. Install additional dependencies as needed:
   ```bash
   pip install paddleocr  # For PaddleOCR
   pip install openai anthropic  # For vision models
   pip install layoutparser  # For advanced layout detection
   ```

## Common Issues

### "No module named pytesseract"
```bash
pip install pytesseract
```

### "Tesseract not found"
Install Tesseract OCR system package (see step 2)

### "No module named cv2"
```bash
pip install opencv-python
```

## Documentation

- [Full README](README.md)
- [Configuration Guide](config.yaml)
- [API Documentation](src/document_reader/)
- [Examples](scripts/example_usage.py)

## Support

- Issues: https://github.com/derek-betz/DocumentReader/issues
- Discussions: https://github.com/derek-betz/DocumentReader/discussions
