#!/usr/bin/env python3
"""
Specialized script for processing engineering plans and technical drawings.
"""

import argparse
import json
import logging
from pathlib import Path
import sys

# Add parent directory to path to import document_reader
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.document_reader.document_processor import DocumentProcessor
from src.document_reader.utils.file_utils import ensure_dir

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_engineering_plan(
    plan_path: Path,
    output_dir: Path,
    ocr_engine: str = "paddleocr",
    use_vision: bool = True,
    extract_measurements: bool = True,
    extract_annotations: bool = True
):
    """Process an engineering plan with specialized settings."""
    logger.info(f"Processing engineering plan: {plan_path}")
    
    # Initialize processor with optimal settings for engineering plans
    config = {
        "tesseract": {
            "language": "eng",
            "psm": 6,  # Assume uniform block of text
            "enhance_contrast": True,
            "denoise": True,
            "deskew": True
        },
        "paddleocr": {
            "language": "en",
            "use_angle_cls": True
        },
        "layout": {
            "model_type": "layoutparser",
            "confidence_threshold": 0.6
        }
    }
    
    processor = DocumentProcessor(
        ocr_engine=ocr_engine,
        use_vision_model=use_vision,
        vision_model="gpt-4o",
        detect_layout=True,
        config=config
    )
    
    # Process the engineering plan
    results = processor.process_engineering_plan(
        plan_path,
        extract_measurements=extract_measurements,
        extract_annotations=extract_annotations
    )
    
    # Save results
    output_path = output_dir / f"{plan_path.stem}_engineering_analysis.json"
    processor.save_results(results, output_path)
    
    # Generate a summary report
    summary = generate_engineering_summary(results)
    summary_path = output_dir / f"{plan_path.stem}_summary.txt"
    with open(summary_path, 'w') as f:
        f.write(summary)
    
    logger.info(f"Results saved to: {output_path}")
    logger.info(f"Summary saved to: {summary_path}")
    
    return results


def generate_engineering_summary(results: dict) -> str:
    """Generate a human-readable summary of engineering plan analysis."""
    lines = []
    lines.append("=" * 80)
    lines.append("ENGINEERING PLAN ANALYSIS SUMMARY")
    lines.append("=" * 80)
    lines.append("")
    
    # Document info
    lines.append(f"Document: {results.get('document_path', 'Unknown')}")
    lines.append("")
    
    # OCR Results
    ocr_text = results.get('ocr_text', '')
    if ocr_text:
        lines.append(f"OCR Text Length: {len(ocr_text)} characters")
        lines.append("")
    
    # Layout Analysis
    if results.get('layout_analysis'):
        layout = results['layout_analysis']
        lines.append("Layout Analysis:")
        lines.append(f"  - Number of regions detected: {layout.get('num_regions', 0)}")
        if 'regions' in layout:
            region_types = {}
            for region in layout['regions']:
                rtype = region.get('type', 'unknown')
                region_types[rtype] = region_types.get(rtype, 0) + 1
            for rtype, count in region_types.items():
                lines.append(f"  - {rtype}: {count}")
        lines.append("")
    
    # Engineering Data
    if results.get('engineering_data'):
        eng_data = results['engineering_data']
        lines.append("Engineering Data:")
        
        if eng_data.get('measurements'):
            measurements = eng_data['measurements']
            lines.append(f"  - Measurements found: {len(measurements)}")
            for i, m in enumerate(measurements[:5], 1):  # Show first 5
                lines.append(f"    {i}. {m.get('value', 'N/A')}")
            if len(measurements) > 5:
                lines.append(f"    ... and {len(measurements) - 5} more")
        
        if eng_data.get('annotations'):
            annotations = eng_data['annotations']
            lines.append(f"  - Annotations found: {len(annotations)}")
        
        lines.append("")
    
    # Vision Interpretation
    if results.get('vision_interpretation'):
        vision = results['vision_interpretation']
        lines.append("Vision Model Interpretation:")
        interpretation = vision.get('interpretation', '')
        if interpretation:
            # Truncate if too long
            if len(interpretation) > 500:
                lines.append(interpretation[:500] + "...")
            else:
                lines.append(interpretation)
        lines.append("")
    
    lines.append("=" * 80)
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Process engineering plans and technical drawings"
    )
    
    parser.add_argument(
        "input",
        type=str,
        help="Input engineering plan file"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="./output/engineering",
        help="Output directory (default: ./output/engineering)"
    )
    
    parser.add_argument(
        "--ocr",
        type=str,
        choices=["tesseract", "paddleocr"],
        default="paddleocr",
        help="OCR engine to use (default: paddleocr)"
    )
    
    parser.add_argument(
        "--no-vision",
        action="store_true",
        help="Disable vision-language model"
    )
    
    parser.add_argument(
        "--no-measurements",
        action="store_true",
        help="Skip measurement extraction"
    )
    
    parser.add_argument(
        "--no-annotations",
        action="store_true",
        help="Skip annotation extraction"
    )
    
    args = parser.parse_args()
    
    plan_path = Path(args.input)
    output_dir = Path(args.output)
    
    if not plan_path.exists():
        logger.error(f"File not found: {plan_path}")
        sys.exit(1)
    
    ensure_dir(output_dir)
    
    try:
        process_engineering_plan(
            plan_path,
            output_dir,
            args.ocr,
            not args.no_vision,
            not args.no_measurements,
            not args.no_annotations
        )
        
        logger.info("Processing complete!")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
