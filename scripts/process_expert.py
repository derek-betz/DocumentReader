#!/usr/bin/env python3
"""
Process a document with the generalized expert pipeline.
"""

import argparse
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.document_reader.expert.pipeline import DocumentExpert
from src.document_reader.utils.file_utils import ensure_dir

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Document Expert pipeline")
    parser.add_argument("input", type=str, help="Input file (PDF or image)")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="./output/expert",
        help="Output directory (default: ./output/expert)",
    )
    parser.add_argument(
        "--ocr",
        type=str,
        choices=["tesseract", "paddleocr"],
        default="tesseract",
        help="OCR engine to use",
    )
    parser.add_argument("--vision", action="store_true", help="Enable vision model")
    parser.add_argument(
        "--vision-model",
        type=str,
        choices=["gpt-4o", "claude"],
        default="gpt-4o",
        help="Vision model to use",
    )
    parser.add_argument("--no-layout", action="store_true", help="Disable layout detection")
    parser.add_argument("--no-preprocess", action="store_true", help="Disable preprocessing")
    parser.add_argument(
        "--tasks",
        type=str,
        default="",
        help="Comma-separated tasks (classify,quality,tables,measurements,key_values,summary)",
    )

    args = parser.parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output)
    ensure_dir(output_dir)

    if not input_path.exists():
        logger.error(f"File not found: {input_path}")
        return 2

    tasks = [t.strip() for t in args.tasks.split(",") if t.strip()] if args.tasks else None

    expert = DocumentExpert(
        ocr_engine=args.ocr,
        use_vision_model=args.vision,
        vision_model=args.vision_model,
        detect_layout=not args.no_layout,
    )
    if args.no_preprocess:
        expert.processing_config.setdefault("preprocess", {})["enabled"] = False

    results = expert.analyze(input_path, tasks=tasks)

    output_path = output_dir / f"{input_path.stem}_expert.json"
    output_path.write_text(results.model_dump_json(indent=2), encoding="utf-8")
    logger.info(f"Results saved to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
