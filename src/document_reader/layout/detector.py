"""
Layout detection for document structure analysis.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class LayoutDetector:
    """
    Document layout detection for identifying text regions, tables, figures, etc.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize layout detector.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.model_type = self.config.get('model_type', 'detectron2')
        self.confidence_threshold = self.config.get('confidence_threshold', 0.5)
        
        self.model = None
        self._initialize_model()
        
        logger.info(f"LayoutDetector initialized with model={self.model_type}")
    
    def _initialize_model(self):
        """Initialize the layout detection model."""
        if self.model_type == 'detectron2':
            self._initialize_detectron2()
        elif self.model_type == 'layoutparser':
            self._initialize_layoutparser()
        else:
            logger.warning(f"Unknown model type: {self.model_type}")
    
    def _initialize_detectron2(self):
        """Initialize Detectron2-based layout model."""
        try:
            # This is a placeholder for Detectron2 initialization
            # In practice, you would load a pre-trained layout detection model
            logger.info("Detectron2 model initialization (placeholder)")
            # from detectron2 import model_zoo
            # from detectron2.config import get_cfg
            # self.model = ...
            
        except ImportError:
            logger.error("Detectron2 not installed. Install with: pip install detectron2")
        except Exception as e:
            logger.error(f"Error initializing Detectron2: {str(e)}")
    
    def _initialize_layoutparser(self):
        """Initialize LayoutParser model."""
        try:
            import layoutparser as lp
            
            # Load pre-trained model for document layout analysis
            model_name = self.config.get('model_name', 'lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config')
            self.model = lp.Detectron2LayoutModel(
                model_name,
                extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", self.confidence_threshold],
                label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
            )
            logger.info("LayoutParser model initialized")
            
        except ImportError:
            logger.error("layoutparser not installed. Install with: pip install layoutparser")
        except Exception as e:
            logger.error(f"Error initializing LayoutParser: {str(e)}")
    
    def detect_layout(self, image_path: Union[str, Path]) -> Dict:
        """
        Detect layout elements in a document image.
        
        Args:
            image_path: Path to the document image
        
        Returns:
            Dictionary containing detected layout elements
        """
        image_path = Path(image_path)
        logger.info(f"Detecting layout for: {image_path}")
        
        try:
            if self.model is None:
                return self._detect_layout_basic(image_path)
            
            if self.model_type == 'layoutparser':
                return self._detect_layout_layoutparser(image_path)
            else:
                return self._detect_layout_basic(image_path)
                
        except Exception as e:
            logger.error(f"Error during layout detection: {str(e)}")
            return {"error": str(e), "regions": []}
    
    def _detect_layout_layoutparser(self, image_path: Path) -> Dict:
        """Detect layout using LayoutParser."""
        try:
            import cv2
            
            # Load image
            image = cv2.imread(str(image_path))
            
            # Detect layout
            layout = self.model.detect(image)
            
            # Convert to dictionary format
            regions = []
            for block in layout:
                # Safely extract coordinates
                coords = block.coordinates
                bbox = [coords[0], coords[1], coords[2], coords[3]] if len(coords) >= 4 else [0, 0, 0, 0]
                
                regions.append({
                    "type": block.type,
                    "bbox": bbox,
                    "confidence": block.score,
                    "text": getattr(block, 'text', None)
                })
            
            return {
                "regions": regions,
                "num_regions": len(regions),
                "image_size": image.shape[:2]
            }
            
        except Exception as e:
            logger.error(f"LayoutParser detection error: {str(e)}")
            return {"error": str(e), "regions": []}
    
    def _detect_layout_basic(self, image_path: Path) -> Dict:
        """
        Basic layout detection using OpenCV when specialized models are not available.
        """
        try:
            import cv2
            import numpy as np
            
            # Load image
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Threshold to binary
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter and classify regions
            regions = []
            height, width = image.shape[:2]
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter small regions
                if w < 20 or h < 20:
                    continue
                
                area = w * h
                aspect_ratio = w / h if h > 0 else 0
                
                # Simple classification based on geometry
                region_type = "text"
                if aspect_ratio > 3:
                    region_type = "title"
                elif area > (width * height * 0.2):
                    region_type = "figure"
                elif aspect_ratio < 0.5 and h > 100:
                    region_type = "column"
                
                regions.append({
                    "type": region_type,
                    "bbox": [int(x), int(y), int(x + w), int(y + h)],
                    "confidence": 0.7,  # Placeholder confidence
                    "area": int(area)
                })
            
            # Sort regions by position (top to bottom, left to right)
            regions.sort(key=lambda r: (r["bbox"][1], r["bbox"][0]))
            
            return {
                "regions": regions,
                "num_regions": len(regions),
                "image_size": [height, width],
                "method": "basic_opencv"
            }
            
        except Exception as e:
            logger.error(f"Basic layout detection error: {str(e)}")
            return {"error": str(e), "regions": []}
    
    def extract_text_regions(self, image_path: Union[str, Path]) -> List[Dict]:
        """
        Extract specifically text regions from document.
        
        Args:
            image_path: Path to document image
        
        Returns:
            List of text regions with bounding boxes
        """
        layout = self.detect_layout(image_path)
        
        text_regions = [
            region for region in layout.get("regions", [])
            if region.get("type") in ["text", "title", "Text", "Title"]
        ]
        
        return text_regions
    
    def extract_tables(self, image_path: Union[str, Path]) -> List[Dict]:
        """
        Extract table regions from document.
        
        Args:
            image_path: Path to document image
        
        Returns:
            List of table regions with bounding boxes
        """
        layout = self.detect_layout(image_path)
        
        table_regions = [
            region for region in layout.get("regions", [])
            if region.get("type") in ["table", "Table"]
        ]
        
        return table_regions
    
    def visualize_layout(
        self,
        image_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None
    ) -> Optional[Path]:
        """
        Visualize detected layout on image.
        
        Args:
            image_path: Path to document image
            output_path: Path to save visualization (if None, returns array)
        
        Returns:
            Path to saved visualization or None
        """
        try:
            import cv2
            import numpy as np
            
            image_path = Path(image_path)
            image = cv2.imread(str(image_path))
            
            layout = self.detect_layout(image_path)
            
            # Draw bounding boxes
            colors = {
                "text": (0, 255, 0),      # Green
                "title": (255, 0, 0),      # Blue
                "table": (0, 0, 255),      # Red
                "figure": (255, 255, 0),   # Cyan
                "list": (255, 0, 255),     # Magenta
            }
            
            for region in layout.get("regions", []):
                bbox = region["bbox"]
                region_type = region.get("type", "text").lower()
                color = colors.get(region_type, (128, 128, 128))
                
                cv2.rectangle(
                    image,
                    (bbox[0], bbox[1]),
                    (bbox[2], bbox[3]),
                    color,
                    2
                )
                
                # Add label
                label = f"{region_type}: {region.get('confidence', 0):.2f}"
                cv2.putText(
                    image,
                    label,
                    (bbox[0], bbox[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    1
                )
            
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(output_path), image)
                logger.info(f"Layout visualization saved to: {output_path}")
                return output_path
            
            return None
            
        except Exception as e:
            logger.error(f"Error visualizing layout: {str(e)}")
            return None
