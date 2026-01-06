"""
Integration tests for the Roadway-Doc-Engine REST API.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json
import io

from src.api.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_processor():
    """Create a mock DocumentProcessor."""
    with patch('src.api.main.DocumentProcessor') as mock:
        processor_instance = MagicMock()
        mock.return_value = processor_instance
        
        # Mock process_document method
        processor_instance.process_document.return_value = {
            "document_path": "test.pdf",
            "ocr_text": "Sample OCR text",
            "layout_analysis": None,
            "vision_interpretation": None,
            "extracted_data": {}
        }
        
        # Mock process_engineering_plan method
        processor_instance.process_engineering_plan.return_value = {
            "document_path": "test.pdf",
            "ocr_text": "Sample OCR text",
            "engineering_data": {
                "measurements": [{"value": "10m", "position": [100, 200]}]
            }
        }
        
        # Mock identify_indot_sheet_headers method
        processor_instance.identify_indot_sheet_headers.return_value = {
            "sheet_type": "Title Sheet",
            "sheet_number": "1",
            "project_number": "DES-1234567",
            "confidence": 0.95
        }
        
        yield processor_instance


class TestAPIEndpoints:
    """Tests for API endpoints."""
    
    def test_root_endpoint(self, client):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ok'
        assert 'version' in data
    
    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
    
    def test_process_document_endpoint(self, client, mock_processor):
        """Test the document processing endpoint."""
        # Create a fake PDF file
        fake_file = io.BytesIO(b"fake pdf content")
        
        response = client.post(
            "/process",
            files={"file": ("test.pdf", fake_file, "application/pdf")},
            params={
                "ocr_engine": "tesseract",
                "detect_layout": True,
                "identify_sheet_type": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['document_path'] == 'test.pdf'
        assert 'results' in data
    
    def test_process_engineering_plan_endpoint(self, client, mock_processor):
        """Test the engineering plan processing endpoint."""
        fake_file = io.BytesIO(b"fake pdf content")
        
        response = client.post(
            "/process/engineering-plan",
            files={"file": ("plan.pdf", fake_file, "application/pdf")},
            params={"ocr_engine": "tesseract"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'results' in data
    
    def test_identify_sheet_type_endpoint(self, client, mock_processor):
        """Test the sheet type identification endpoint."""
        fake_file = io.BytesIO(b"fake pdf content")
        
        response = client.post(
            "/identify-sheet-type",
            files={"file": ("sheet.pdf", fake_file, "application/pdf")},
            params={"ocr_engine": "tesseract"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'sheet_info' in data
        assert data['sheet_info']['sheet_type'] == 'Title Sheet'
    
    def test_process_with_vision_model(self, client, mock_processor):
        """Test processing with vision model enabled."""
        fake_file = io.BytesIO(b"fake pdf content")
        
        response = client.post(
            "/process",
            files={"file": ("test.pdf", fake_file, "application/pdf")},
            params={
                "use_vision_model": True,
                "vision_model": "gpt-4o"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
    
    def test_process_with_different_ocr_engine(self, client, mock_processor):
        """Test processing with PaddleOCR."""
        fake_file = io.BytesIO(b"fake pdf content")
        
        response = client.post(
            "/process",
            files={"file": ("test.pdf", fake_file, "application/pdf")},
            params={"ocr_engine": "paddleocr"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
    
    def test_process_without_measurements(self, client, mock_processor):
        """Test processing without measurement extraction."""
        fake_file = io.BytesIO(b"fake pdf content")
        
        response = client.post(
            "/process",
            files={"file": ("test.pdf", fake_file, "application/pdf")},
            params={
                "extract_measurements": False,
                "extract_annotations": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'


class TestAPIErrorHandling:
    """Tests for API error handling."""
    
    def test_missing_file(self, client):
        """Test handling of missing file parameter."""
        response = client.post("/process")
        # FastAPI will return 422 for missing required fields
        assert response.status_code == 422
    
    def test_invalid_file_type(self, client, mock_processor):
        """Test handling of invalid file types."""
        # This test ensures the API accepts the upload
        # File validation happens in the processor
        fake_file = io.BytesIO(b"fake content")
        
        response = client.post(
            "/process",
            files={"file": ("test.txt", fake_file, "text/plain")}
        )
        
        # Should still accept the file (validation is in processor)
        assert response.status_code in [200, 500]


# Run tests with: pytest tests/test_api.py -v
