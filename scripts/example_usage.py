#!/usr/bin/env python3
"""
Example usage of the Document AI Agent for processing engineering plans.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.document_reader import DocumentProcessor


def example_basic_usage():
    """Example: Basic document processing."""
    print("Example 1: Basic Document Processing")
    print("-" * 50)
    
    # Initialize processor with Tesseract OCR and layout detection
    processor = DocumentProcessor(
        ocr_engine="tesseract",
        detect_layout=True
    )
    
    # Note: This is a demonstration - replace with actual file path
    document_path = "data/samples/example_document.png"
    
    print(f"Would process: {document_path}")
    print("Features enabled: OCR, Layout Detection")
    print()


def example_engineering_plan():
    """Example: Engineering plan processing."""
    print("Example 2: Engineering Plan Processing")
    print("-" * 50)
    
    # Initialize processor with PaddleOCR and all features
    processor = DocumentProcessor(
        ocr_engine="paddleocr",
        use_vision_model=False,  # Set to True if you have API keys
        detect_layout=True,
        config={
            "paddleocr": {
                "language": "en",
                "use_angle_cls": True
            },
            "layout": {
                "model_type": "basic_opencv",
                "confidence_threshold": 0.6
            }
        }
    )
    
    # Note: This is a demonstration - replace with actual file path
    plan_path = "data/samples/engineering_plan.png"
    
    print(f"Would process: {plan_path}")
    print("Features enabled: PaddleOCR, Layout Detection")
    print("Specialized for: Engineering plans with measurements")
    print()


def example_with_vision_model():
    """Example: Processing with vision-language model."""
    print("Example 3: Processing with Vision-Language Model")
    print("-" * 50)
    
    # Initialize processor with vision model
    # Note: Requires API key in config or environment variable
    processor = DocumentProcessor(
        ocr_engine="tesseract",
        use_vision_model=True,
        vision_model="gpt-4o",
        detect_layout=True,
        config={
            "vision": {
                # Set OPENAI_API_KEY environment variable instead
                "openai_api_key": ""
            }
        }
    )
    
    document_path = "data/samples/complex_document.pdf"
    
    print(f"Would process: {document_path}")
    print("Features enabled: OCR, Vision Model (GPT-4o), Layout Detection")
    print("Note: Requires OPENAI_API_KEY environment variable")
    print()


def example_batch_processing():
    """Example: Batch processing multiple documents."""
    print("Example 4: Batch Processing")
    print("-" * 50)
    
    from pathlib import Path
    
    processor = DocumentProcessor(ocr_engine="tesseract")
    
    input_dir = Path("data/input")
    output_dir = Path("data/output")
    
    print(f"Would process all files in: {input_dir}")
    print(f"Results would be saved to: {output_dir}")
    print()
    
    # Example pattern:
    # for file_path in input_dir.glob("*.png"):
    #     results = processor.process_document(file_path)
    #     processor.save_results(results, output_dir / f"{file_path.stem}.json")


def main():
    """Run all examples."""
    print("=" * 50)
    print("Document AI Agent - Usage Examples")
    print("=" * 50)
    print()
    
    example_basic_usage()
    example_engineering_plan()
    example_with_vision_model()
    example_batch_processing()
    
    print("=" * 50)
    print("To run actual processing:")
    print("1. Place your documents in data/input/")
    print("2. Use scripts/process_documents.py for general processing")
    print("3. Use scripts/process_engineering_plans.py for engineering plans")
    print("=" * 50)


if __name__ == "__main__":
    main()
