"""
PyQt5-based desktop GUI for Roadway-Doc-Engine.

Provides a drag-and-drop interface for processing roadway construction plans locally.
"""

import sys
import os
from pathlib import Path
from typing import Optional

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QTextEdit, QFileDialog, QCheckBox,
        QComboBox, QGroupBox, QProgressBar, QSplitter, QMessageBox
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal
    from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFont
except ImportError:
    print("PyQt5 not installed. Install with: pip install PyQt5")
    sys.exit(1)

from document_reader import DocumentProcessor


class ProcessingThread(QThread):
    """Thread for processing documents without blocking the UI."""
    
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, file_path: str, options: dict):
        super().__init__()
        self.file_path = file_path
        self.options = options
    
    def run(self):
        """Process the document in a separate thread."""
        try:
            self.progress.emit("Initializing processor...")
            
            processor = DocumentProcessor(
                ocr_engine=self.options.get('ocr_engine', 'tesseract'),
                use_vision_model=self.options.get('use_vision_model', False),
                vision_model=self.options.get('vision_model', 'gpt-4o'),
                detect_layout=self.options.get('detect_layout', True)
            )
            
            self.progress.emit("Processing document...")
            
            if self.options.get('extract_measurements', True):
                results = processor.process_engineering_plan(
                    self.file_path,
                    extract_measurements=True,
                    extract_annotations=self.options.get('extract_annotations', True)
                )
            else:
                results = processor.process_document(self.file_path)
            
            if self.options.get('identify_sheet_type', True):
                self.progress.emit("Identifying sheet type...")
                sheet_info = processor.identify_indot_sheet_headers(results)
                results['indot_sheet_info'] = sheet_info
            
            self.progress.emit("Processing complete!")
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(str(e))


class RoadwayDocEngineGUI(QMainWindow):
    """Main window for the Roadway-Doc-Engine desktop application."""
    
    def __init__(self):
        super().__init__()
        self.current_file: Optional[str] = None
        self.processing_thread: Optional[ProcessingThread] = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Roadway-Doc-Engine - Desktop GUI")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("🚧 Roadway-Doc-Engine")
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)
        
        subtitle = QLabel("Specialized Document Processing for Roadway Construction Plans")
        subtitle.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle)
        
        # Create splitter for options and results
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Options and controls
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel: Results display
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([400, 800])
        main_layout.addWidget(splitter)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Enable drag and drop
        self.setAcceptDrops(True)
    
    def create_left_panel(self) -> QWidget:
        """Create the left panel with options and controls."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # File selection
        file_group = QGroupBox("Document")
        file_layout = QVBoxLayout()
        
        self.file_label = QLabel("No file selected")
        self.file_label.setWordWrap(True)
        file_layout.addWidget(self.file_label)
        
        select_btn = QPushButton("Select File...")
        select_btn.clicked.connect(self.select_file)
        file_layout.addWidget(select_btn)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Processing options
        options_group = QGroupBox("Processing Options")
        options_layout = QVBoxLayout()
        
        # OCR Engine
        ocr_layout = QHBoxLayout()
        ocr_layout.addWidget(QLabel("OCR Engine:"))
        self.ocr_combo = QComboBox()
        self.ocr_combo.addItems(["tesseract", "paddleocr"])
        ocr_layout.addWidget(self.ocr_combo)
        options_layout.addLayout(ocr_layout)
        
        # Checkboxes
        self.detect_layout_cb = QCheckBox("Detect Layout")
        self.detect_layout_cb.setChecked(True)
        options_layout.addWidget(self.detect_layout_cb)
        
        self.extract_measurements_cb = QCheckBox("Extract Measurements")
        self.extract_measurements_cb.setChecked(True)
        options_layout.addWidget(self.extract_measurements_cb)
        
        self.extract_annotations_cb = QCheckBox("Extract Annotations")
        self.extract_annotations_cb.setChecked(True)
        options_layout.addWidget(self.extract_annotations_cb)
        
        self.identify_sheet_cb = QCheckBox("Identify INDOT Sheet Type")
        self.identify_sheet_cb.setChecked(True)
        options_layout.addWidget(self.identify_sheet_cb)
        
        self.use_vision_cb = QCheckBox("Use Vision-Language Model")
        self.use_vision_cb.setChecked(False)
        options_layout.addWidget(self.use_vision_cb)
        
        # Vision model selection
        vision_layout = QHBoxLayout()
        vision_layout.addWidget(QLabel("Vision Model:"))
        self.vision_combo = QComboBox()
        self.vision_combo.addItems(["gpt-4o", "claude"])
        self.vision_combo.setEnabled(False)
        vision_layout.addWidget(self.vision_combo)
        options_layout.addLayout(vision_layout)
        
        self.use_vision_cb.stateChanged.connect(
            lambda: self.vision_combo.setEnabled(self.use_vision_cb.isChecked())
        )
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Process button
        self.process_btn = QPushButton("Process Document")
        self.process_btn.clicked.connect(self.process_document)
        self.process_btn.setEnabled(False)
        layout.addWidget(self.process_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create the right panel for results display."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Results display
        results_label = QLabel("Processing Results")
        results_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(results_label)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Results will appear here after processing...")
        layout.addWidget(self.results_text)
        
        # Save results button
        save_btn = QPushButton("Save Results to File...")
        save_btn.clicked.connect(self.save_results)
        save_btn.setEnabled(False)
        self.save_btn = save_btn
        layout.addWidget(save_btn)
        
        return panel
    
    def select_file(self):
        """Open file dialog to select a document."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Document",
            "",
            "All Supported (*.pdf *.png *.jpg *.jpeg *.tiff *.bmp);;PDF Files (*.pdf);;Image Files (*.png *.jpg *.jpeg *.tiff *.bmp)"
        )
        
        if file_path:
            self.current_file = file_path
            self.file_label.setText(f"Selected: {Path(file_path).name}")
            self.process_btn.setEnabled(True)
            self.statusBar().showMessage(f"File selected: {Path(file_path).name}")
    
    def process_document(self):
        """Process the selected document."""
        if not self.current_file:
            return
        
        # Prepare options
        options = {
            'ocr_engine': self.ocr_combo.currentText(),
            'detect_layout': self.detect_layout_cb.isChecked(),
            'extract_measurements': self.extract_measurements_cb.isChecked(),
            'extract_annotations': self.extract_annotations_cb.isChecked(),
            'identify_sheet_type': self.identify_sheet_cb.isChecked(),
            'use_vision_model': self.use_vision_cb.isChecked(),
            'vision_model': self.vision_combo.currentText()
        }
        
        # Disable controls during processing
        self.process_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.results_text.clear()
        
        # Start processing thread
        self.processing_thread = ProcessingThread(self.current_file, options)
        self.processing_thread.finished.connect(self.on_processing_finished)
        self.processing_thread.error.connect(self.on_processing_error)
        self.processing_thread.progress.connect(self.on_processing_progress)
        self.processing_thread.start()
    
    def on_processing_progress(self, message: str):
        """Handle progress updates."""
        self.statusBar().showMessage(message)
    
    def on_processing_finished(self, results: dict):
        """Handle processing completion."""
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        
        # Format and display results
        output = self.format_results(results)
        self.results_text.setPlainText(output)
        
        self.statusBar().showMessage("Processing complete!")
        self.last_results = results
    
    def on_processing_error(self, error_message: str):
        """Handle processing errors."""
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        
        self.results_text.setPlainText(f"Error during processing:\n\n{error_message}")
        self.statusBar().showMessage("Processing failed!")
        
        QMessageBox.critical(self, "Processing Error", f"An error occurred:\n\n{error_message}")
    
    def format_results(self, results: dict) -> str:
        """Format results for display."""
        output = []
        output.append("=" * 60)
        output.append("ROADWAY-DOC-ENGINE PROCESSING RESULTS")
        output.append("=" * 60)
        output.append("")
        
        # INDOT Sheet Info
        if 'indot_sheet_info' in results:
            sheet_info = results['indot_sheet_info']
            output.append("INDOT SHEET INFORMATION")
            output.append("-" * 60)
            output.append(f"Sheet Type: {sheet_info.get('sheet_type', 'Unknown')}")
            output.append(f"Confidence: {sheet_info.get('confidence', 0) * 100:.1f}%")
            if sheet_info.get('sheet_number'):
                output.append(f"Sheet Number: {sheet_info['sheet_number']}")
            if sheet_info.get('project_number'):
                output.append(f"Project Number: {sheet_info['project_number']}")
            if sheet_info.get('sheet_title'):
                output.append(f"Sheet Title: {sheet_info['sheet_title']}")
            output.append("")
        
        # OCR Text (preview)
        if results.get('ocr_text'):
            output.append("EXTRACTED TEXT (Preview)")
            output.append("-" * 60)
            text_preview = results['ocr_text'][:500] + "..." if len(results['ocr_text']) > 500 else results['ocr_text']
            output.append(text_preview)
            output.append("")
        
        # Engineering Data
        if 'engineering_data' in results:
            eng_data = results['engineering_data']
            if eng_data.get('measurements'):
                output.append(f"MEASUREMENTS FOUND: {len(eng_data['measurements'])}")
                output.append("-" * 60)
                for i, measurement in enumerate(eng_data['measurements'][:5], 1):
                    output.append(f"{i}. {measurement.get('value', 'N/A')}")
                if len(eng_data['measurements']) > 5:
                    output.append(f"... and {len(eng_data['measurements']) - 5} more")
                output.append("")
        
        return "\n".join(output)
    
    def save_results(self):
        """Save processing results to a file."""
        if not hasattr(self, 'last_results'):
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Results",
            "",
            "JSON Files (*.json);;Text Files (*.txt)"
        )
        
        if file_path:
            try:
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    if file_path.endswith('.json'):
                        json.dump(self.last_results, f, indent=2, ensure_ascii=False)
                    else:
                        f.write(self.results_text.toPlainText())
                
                self.statusBar().showMessage(f"Results saved to: {Path(file_path).name}")
                QMessageBox.information(self, "Success", f"Results saved successfully to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save results:\n\n{str(e)}")
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if Path(file_path).suffix.lower() in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                    self.current_file = file_path
                    self.file_label.setText(f"Selected: {Path(file_path).name}")
                    self.process_btn.setEnabled(True)
                    self.statusBar().showMessage(f"File dropped: {Path(file_path).name}")
                else:
                    QMessageBox.warning(self, "Invalid File", "Please drop a supported file type (PDF or image)")


def main():
    """Entry point for the desktop GUI application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Roadway-Doc-Engine")
    app.setOrganizationName("DocumentReader")
    
    window = RoadwayDocEngineGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
