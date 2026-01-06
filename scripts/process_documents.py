#!/usr/bin/env python3
"""
Process a single document or batch of documents.
"""

import argparse
import json
import logging
from pathlib import Path
import sys

# Add parent directory to path to import document_reader
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.document_reader.document_processor import DocumentProcessor
from src.document_reader.utils.file_utils import is_pdf_file, pdf_to_images, ensure_dir

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_single_document(
    input_path: Path,
    output_dir: Path,
    ocr_engine: str = "tesseract",
    use_vision: bool = False,
    vision_model: str = "gpt-4o"
):
    """Process a single document."""
    logger.info(f"Processing document: {input_path}")
    
    # Initialize processor
    processor = DocumentProcessor(
        ocr_engine=ocr_engine,
        use_vision_model=use_vision,
        vision_model=vision_model,
        detect_layout=True
    )
    
    # Handle PDF files
    if is_pdf_file(input_path):
        logger.info("Converting PDF to images...")
        temp_dir = output_dir / "temp"
        image_paths = pdf_to_images(input_path, temp_dir)
        
        all_results = []
        for i, image_path in enumerate(image_paths):
            logger.info(f"Processing page {i+1}/{len(image_paths)}")
            results = processor.process_document(image_path)
            results["page_number"] = i + 1
            all_results.append(results)
        
        # Save combined results
        output_path = output_dir / f"{input_path.stem}_results.json"
        with open(output_path, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        logger.info(f"Results saved to: {output_path}")
        return all_results
    else:
        # Process image directly
        results = processor.process_document(input_path)
        
        # Save results
        output_path = output_dir / f"{input_path.stem}_results.json"
        processor.save_results(results, output_path)
        
        return results


def process_batch(
    input_dir: Path,
    output_dir: Path,
    ocr_engine: str = "tesseract",
    use_vision: bool = False,
    vision_model: str = "gpt-4o",
    pattern: str = "*.*"
):
    """Process a batch of documents."""
    logger.info(f"Processing batch from: {input_dir}")
    
    ensure_dir(output_dir)
    
    # Find all matching files
    files = list(input_dir.glob(pattern))
    logger.info(f"Found {len(files)} files to process")
    
    results_summary = []
    
    for i, file_path in enumerate(files, 1):
        logger.info(f"Processing file {i}/{len(files)}: {file_path.name}")
        
        try:
            result = process_single_document(
                file_path,
                output_dir,
                ocr_engine,
                use_vision,
                vision_model
            )
            results_summary.append({
                "file": str(file_path),
                "status": "success",
                "output": str(output_dir / f"{file_path.stem}_results.json")
            })
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            results_summary.append({
                "file": str(file_path),
                "status": "error",
                "error": str(e)
            })
    
    # Save summary
    summary_path = output_dir / "batch_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(results_summary, f, indent=2)
    
    logger.info(f"Batch processing complete. Summary saved to: {summary_path}")
    return results_summary


def main():
    parser = argparse.ArgumentParser(
        description="Process documents using Document AI Agent"
    )
    
    parser.add_argument(
        "input",
        type=str,
        help="Input file or directory"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="./output",
        help="Output directory (default: ./output)"
    )
    
    parser.add_argument(
        "--ocr",
        type=str,
        choices=["tesseract", "paddleocr"],
        default="tesseract",
        help="OCR engine to use (default: tesseract)"
    )
    
    parser.add_argument(
        "--vision",
        action="store_true",
        help="Use vision-language model for interpretation"
    )
    
    parser.add_argument(
        "--vision-model",
        type=str,
        choices=["gpt-4o", "claude"],
        default="gpt-4o",
        help="Vision-language model to use (default: gpt-4o)"
    )
    
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process all files in directory"
    )
    
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.*",
        help="File pattern for batch processing (default: *.*)"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_dir = Path(args.output)
    
    ensure_dir(output_dir)
    
    try:
        if args.batch or input_path.is_dir():
            process_batch(
                input_path,
                output_dir,
                args.ocr,
                args.vision,
                args.vision_model,
                args.pattern
            )
        else:
            process_single_document(
                input_path,
                output_dir,
                args.ocr,
                args.vision,
                args.vision_model
            )
        
        logger.info("Processing complete!")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
