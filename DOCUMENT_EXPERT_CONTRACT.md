# Document Expert Contract

This contract defines how other repos/agents should call the generalized document expert service and what to expect in the response.

## Entry Points

- Python API: `document_reader.expert.DocumentExpert.analyze(path, tasks=...)`
- REST API: `POST /process/expert` (see `src/api/main.py`)

## Request Options

### ExpertProcessingOptions
- `ocr_engine`: `tesseract` or `paddleocr`
- `use_vision_model`: `true|false` (requires API keys)
- `vision_model`: `gpt-4o` or `claude`
- `detect_layout`: `true|false`
- `tasks`: list of tasks
  - `classify`, `quality`, `tables`, `measurements`, `key_values`, `summary`
- `preprocess`: `true|false`

## Response Shape (DocumentResult)

```json
{
  "document_path": "path/original.pdf",
  "document_type": {
    "type": "engineering_plan",
    "confidence": 0.6,
    "candidates": {
      "engineering_plan": 0.6,
      "construction_detail": 0.2
    }
  },
  "summary": "Optional high-level summary",
  "language": null,
  "ocr_text": "Full OCR text",
  "pages": [
    {
      "page_number": 1,
      "ocr_text": "Page OCR text",
      "layout": [
        {
          "type": "Text",
          "bbox": {"x1": 0, "y1": 0, "x2": 100, "y2": 50},
          "confidence": 0.9,
          "text": null
        }
      ],
      "quality": {
        "width": 2550,
        "height": 3300,
        "blur_score": 145.2,
        "contrast_score": 32.8,
        "skew_angle": -0.6,
        "mean_brightness": 180.4,
        "flags": []
      },
      "tables": [],
      "key_values": [],
      "measurements": [],
      "vision_interpretation": null,
      "warnings": []
    }
  ],
  "tables": [],
  "key_values": [],
  "measurements": [],
  "warnings": []
}
```

## Notes

- `summary` requires a vision model; otherwise it is `null` and a warning is added.
- `tables`, `key_values`, and `measurements` are aggregated across pages.
- If `processing.output.save_intermediate=true`, intermediate artifacts are written under `processing.output.artifacts_dir` (default `output/document_expert`).
