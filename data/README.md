# Data Directory

This directory contains data used by the Document AI Agent.

## Structure

- `input/` - Place your input documents here for processing
- `output/` - Processed results will be saved here
- `models/` - Store downloaded model weights here
- `samples/` - Sample documents for testing and examples

## Usage

### Input Documents

Place your documents (images or PDFs) in the `input/` directory:

```
data/input/
├── engineering_plan_1.png
├── scanned_document.pdf
└── blueprint.tiff
```

### Output Results

Processing results are saved to `output/` in JSON format:

```
data/output/
├── engineering_plan_1_results.json
├── engineering_plan_1_summary.txt
└── scanned_document_results.json
```

### Models

Download and store model weights in `models/`:

```
data/models/
├── layoutparser_model.pth
└── custom_ocr_model.pkl
```

## Sample Documents

The `samples/` directory can contain example documents for testing:

- Low-quality scanned documents
- Engineering plans
- Technical drawings
- Complex PDFs

## File Formats Supported

### Input Formats
- Images: PNG, JPEG, TIFF, BMP
- Documents: PDF (automatically converted to images)

### Output Formats
- JSON: Structured data with all extracted information
- TXT: Human-readable summaries (for engineering plans)

## Notes

- Large files (>100MB) should be processed in batch mode
- For best results with engineering plans, use 300 DPI or higher resolution
- Model files are excluded from git by default (see .gitignore)
