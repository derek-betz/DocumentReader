"""
Unit tests for INDOT sheet header identification functionality.
"""

import pytest
from unittest.mock import Mock, patch
from src.document_reader.document_processor import DocumentProcessor


class TestINDOTSheetIdentification:
    """Tests for INDOT sheet header identification."""
    
    def test_identify_title_sheet(self):
        """Test identification of INDOT Title Sheet."""
        with patch('src.document_reader.document_processor.TesseractOCR'):
            with patch('src.document_reader.document_processor.LayoutDetector'):
                processor = DocumentProcessor()
                
                # Mock OCR results for a title sheet
                results = {
                    "ocr_text": """
                    TITLE SHEET
                    PROJECT INDEX
                    DES-1234567
                    SHEET 1 OF 50
                    STATE ROAD 37 IMPROVEMENT PROJECT
                    """
                }
                
                sheet_info = processor.identify_indot_sheet_headers(results)
                
                assert sheet_info['sheet_type'] == 'Title Sheet'
                assert sheet_info['confidence'] > 0
                assert sheet_info['sheet_number'] == '1'
                assert sheet_info['project_number'] == '1234567'
    
    def test_identify_plan_and_profile(self):
        """Test identification of INDOT Plan and Profile sheet."""
        with patch('src.document_reader.document_processor.TesseractOCR'):
            with patch('src.document_reader.document_processor.LayoutDetector'):
                processor = DocumentProcessor()
                
                results = {
                    "ocr_text": """
                    PLAN AND PROFILE
                    STATE ROAD 37
                    SHEET 15 OF 50
                    DES NO. 9876543
                    STATION 10+00 TO 20+00
                    """
                }
                
                sheet_info = processor.identify_indot_sheet_headers(results)
                
                assert sheet_info['sheet_type'] == 'Plan and Profile'
                assert sheet_info['confidence'] > 0
                assert sheet_info['sheet_number'] == '15'
                assert sheet_info['project_number'] == '9876543'
    
    def test_identify_cross_section(self):
        """Test identification of INDOT Cross-Section sheet."""
        with patch('src.document_reader.document_processor.TesseractOCR'):
            with patch('src.document_reader.document_processor.LayoutDetector'):
                processor = DocumentProcessor()
                
                results = {
                    "ocr_text": """
                    TYPICAL SECTION
                    CROSS-SECTION DETAILS
                    SH. 25
                    PROJECT NO: DES-5555555
                    """
                }
                
                sheet_info = processor.identify_indot_sheet_headers(results)
                
                assert sheet_info['sheet_type'] == 'Cross-Section'
                assert sheet_info['confidence'] > 0
                assert sheet_info['sheet_number'] == '25'
    
    def test_identify_traffic_control_plan(self):
        """Test identification of INDOT Traffic Control Plan sheet."""
        with patch('src.document_reader.document_processor.TesseractOCR'):
            with patch('src.document_reader.document_processor.LayoutDetector'):
                processor = DocumentProcessor()
                
                results = {
                    "ocr_text": """
                    TRAFFIC CONTROL PLAN
                    MAINTENANCE OF TRAFFIC
                    TCP-5
                    DES-1111111
                    SHEET 30 OF 50
                    """
                }
                
                sheet_info = processor.identify_indot_sheet_headers(results)
                
                assert sheet_info['sheet_type'] == 'Traffic Control Plan'
                assert sheet_info['confidence'] > 0
    
    def test_identify_drainage_sheet(self):
        """Test identification of INDOT Drainage sheet."""
        with patch('src.document_reader.document_processor.TesseractOCR'):
            with patch('src.document_reader.document_processor.LayoutDetector'):
                processor = DocumentProcessor()
                
                results = {
                    "ocr_text": """
                    DRAINAGE PLAN
                    STORM SEWER DETAILS
                    DR-2
                    SHEET 40
                    """
                }
                
                sheet_info = processor.identify_indot_sheet_headers(results)
                
                assert sheet_info['sheet_type'] == 'Drainage'
                assert sheet_info['confidence'] > 0
    
    def test_identify_unknown_sheet(self):
        """Test handling of unknown sheet types."""
        with patch('src.document_reader.document_processor.TesseractOCR'):
            with patch('src.document_reader.document_processor.LayoutDetector'):
                processor = DocumentProcessor()
                
                results = {
                    "ocr_text": """
                    SOME RANDOM UNRELATED TEXT
                    THIS IS NOT A ROADWAY PLAN
                    JUST SOME ARBITRARY CONTENT
                    """
                }
                
                sheet_info = processor.identify_indot_sheet_headers(results)
                
                # Should either return None or have very low confidence
                assert sheet_info['sheet_type'] is None or sheet_info['confidence'] < 0.5
    
    def test_empty_text(self):
        """Test handling of empty OCR text."""
        with patch('src.document_reader.document_processor.TesseractOCR'):
            with patch('src.document_reader.document_processor.LayoutDetector'):
                processor = DocumentProcessor()
                
                results = {"ocr_text": ""}
                
                sheet_info = processor.identify_indot_sheet_headers(results)
                
                assert sheet_info['sheet_type'] is None
                assert sheet_info['confidence'] == 0.0
    
    def test_multiple_indicators(self):
        """Test sheet identification with multiple indicators."""
        with patch('src.document_reader.document_processor.TesseractOCR'):
            with patch('src.document_reader.document_processor.LayoutDetector'):
                processor = DocumentProcessor()
                
                results = {
                    "ocr_text": """
                    GENERAL NOTES
                    STANDARD NOTES
                    G.N.
                    GN-1
                    """
                }
                
                sheet_info = processor.identify_indot_sheet_headers(results)
                
                assert sheet_info['sheet_type'] == 'General Notes'
                # Should have high confidence with multiple matches
                assert sheet_info['confidence'] > 0.5
                assert len(sheet_info['identified_headers']) > 1


# Run tests with: pytest tests/test_indot_identification.py -v
