import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import './App.css';

interface ProcessingOptions {
  ocr_engine: string;
  use_vision_model: boolean;
  vision_model: string;
  detect_layout: boolean;
  extract_measurements: boolean;
  extract_annotations: boolean;
  identify_sheet_type: boolean;
}

interface SheetInfo {
  sheet_type: string | null;
  sheet_number: string | null;
  project_number: string | null;
  sheet_title: string | null;
  confidence: number;
  identified_headers: string[];
}

interface ProcessingResult {
  status: string;
  document_path: string;
  results?: {
    ocr_text?: string;
    indot_sheet_info?: SheetInfo;
    engineering_data?: unknown;
  };
  error?: string;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<ProcessingResult | null>(null);
  const [options, setOptions] = useState<ProcessingOptions>({
    ocr_engine: 'tesseract',
    use_vision_model: false,
    vision_model: 'gpt-4o',
    detect_layout: true,
    extract_measurements: true,
    extract_annotations: true,
    identify_sheet_type: true,
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setResult(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']
    },
    multiple: false
  });

  const handleProcess = async () => {
    if (!file) return;

    setProcessing(true);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post<ProcessingResult>(
        `${API_BASE_URL}/process`,
        formData,
        {
          params: options,
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setResult(response.data);
    } catch (error) {
      console.error('Error processing document:', error);
      setResult({
        status: 'error',
        document_path: file.name,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      });
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🚧 Roadway-Doc-Engine</h1>
        <p>Specialized Document Processing for Roadway Construction Plans</p>
      </header>

      <main className="App-main">
        <div className="upload-section">
          <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
            <input {...getInputProps()} />
            {file ? (
              <p>Selected: <strong>{file.name}</strong></p>
            ) : isDragActive ? (
              <p>Drop the file here...</p>
            ) : (
              <p>Drag & drop a document here, or click to select<br />
                <small>Supports PDF, PNG, JPG, TIFF</small>
              </p>
            )}
          </div>

          {file && (
            <div className="options-section">
              <h3>Processing Options</h3>
              
              <label>
                <span>OCR Engine:</span>
                <select 
                  value={options.ocr_engine} 
                  onChange={(e) => setOptions({...options, ocr_engine: e.target.value})}
                >
                  <option value="tesseract">Tesseract</option>
                  <option value="paddleocr">PaddleOCR</option>
                </select>
              </label>

              <label>
                <input
                  type="checkbox"
                  checked={options.detect_layout}
                  onChange={(e) => setOptions({...options, detect_layout: e.target.checked})}
                />
                Detect Layout
              </label>

              <label>
                <input
                  type="checkbox"
                  checked={options.extract_measurements}
                  onChange={(e) => setOptions({...options, extract_measurements: e.target.checked})}
                />
                Extract Measurements
              </label>

              <label>
                <input
                  type="checkbox"
                  checked={options.extract_annotations}
                  onChange={(e) => setOptions({...options, extract_annotations: e.target.checked})}
                />
                Extract Annotations
              </label>

              <label>
                <input
                  type="checkbox"
                  checked={options.identify_sheet_type}
                  onChange={(e) => setOptions({...options, identify_sheet_type: e.target.checked})}
                />
                Identify INDOT Sheet Type
              </label>

              <label>
                <input
                  type="checkbox"
                  checked={options.use_vision_model}
                  onChange={(e) => setOptions({...options, use_vision_model: e.target.checked})}
                />
                Use Vision-Language Model
              </label>

              {options.use_vision_model && (
                <label>
                  <span>Vision Model:</span>
                  <select 
                    value={options.vision_model} 
                    onChange={(e) => setOptions({...options, vision_model: e.target.value})}
                  >
                    <option value="gpt-4o">GPT-4o</option>
                    <option value="claude">Claude</option>
                  </select>
                </label>
              )}

              <button 
                onClick={handleProcess} 
                disabled={processing}
                className="process-button"
              >
                {processing ? 'Processing...' : 'Process Document'}
              </button>
            </div>
          )}
        </div>

        {result && (
          <div className="results-section">
            <h3>Processing Results</h3>
            
            {result.status === 'error' ? (
              <div className="error">
                <p><strong>Error:</strong> {result.error}</p>
              </div>
            ) : (
              <>
                {result.results?.indot_sheet_info && (
                  <div className="sheet-info">
                    <h4>INDOT Sheet Information</h4>
                    <div className="info-grid">
                      <div>
                        <strong>Sheet Type:</strong> 
                        <span className="highlight">
                          {result.results.indot_sheet_info.sheet_type || 'Unknown'}
                        </span>
                      </div>
                      <div>
                        <strong>Confidence:</strong> 
                        <span>{(result.results.indot_sheet_info.confidence * 100).toFixed(1)}%</span>
                      </div>
                      {result.results.indot_sheet_info.sheet_number && (
                        <div>
                          <strong>Sheet Number:</strong> 
                          <span>{result.results.indot_sheet_info.sheet_number}</span>
                        </div>
                      )}
                      {result.results.indot_sheet_info.project_number && (
                        <div>
                          <strong>Project Number:</strong> 
                          <span>{result.results.indot_sheet_info.project_number}</span>
                        </div>
                      )}
                      {result.results.indot_sheet_info.sheet_title && (
                        <div>
                          <strong>Sheet Title:</strong> 
                          <span>{result.results.indot_sheet_info.sheet_title}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {result.results?.ocr_text && (
                  <div className="ocr-text">
                    <h4>Extracted Text (preview)</h4>
                    <pre>{result.results.ocr_text.substring(0, 500)}...</pre>
                  </div>
                )}

                <details className="full-results">
                  <summary>View Full Results (JSON)</summary>
                  <pre>{JSON.stringify(result.results, null, 2)}</pre>
                </details>
              </>
            )}
          </div>
        )}
      </main>

      <footer className="App-footer">
        <p>Roadway-Doc-Engine v0.1.0 | Specialized for INDOT roadway construction plans</p>
      </footer>
    </div>
  );
}

export default App;
