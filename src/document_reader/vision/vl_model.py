"""
Vision-Language Model integration for document interpretation.
Supports GPT-4o and Claude for advanced document understanding.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Union
import base64

logger = logging.getLogger(__name__)


class VisionLanguageModel:
    """
    Wrapper for vision-language models (GPT-4o, Claude) to interpret document images.
    """
    
    def __init__(self, model_name: str = "gpt-4o", config: Optional[Dict] = None):
        """
        Initialize vision-language model.
        
        Args:
            model_name: Model to use ('gpt-4o' or 'claude')
            config: Configuration dictionary including API keys
        """
        self.model_name = model_name
        self.config = config or {}
        self.api_key = self.config.get('api_key')
        
        self.client = None
        self._initialize_client()
        
        logger.info(f"VisionLanguageModel initialized with model={model_name}")
    
    def _initialize_client(self):
        """Initialize the API client based on model type."""
        if self.model_name.startswith("gpt"):
            self._initialize_openai()
        elif self.model_name == "claude":
            self._initialize_anthropic()
        else:
            logger.warning(f"Unknown model: {self.model_name}, initialization skipped")
    
    def _initialize_openai(self):
        """Initialize OpenAI client for GPT-4o."""
        try:
            import openai
            
            api_key = self.api_key or self.config.get('openai_api_key')
            if api_key:
                openai.api_key = api_key
                self.client = openai
                logger.info("OpenAI client initialized")
            else:
                logger.warning("No OpenAI API key provided")
                
        except ImportError:
            logger.error("openai package not installed. Install with: pip install openai")
    
    def _initialize_anthropic(self):
        """Initialize Anthropic client for Claude."""
        try:
            import anthropic
            
            api_key = self.api_key or self.config.get('anthropic_api_key')
            if api_key:
                self.client = anthropic.Anthropic(api_key=api_key)
                logger.info("Anthropic client initialized")
            else:
                logger.warning("No Anthropic API key provided")
                
        except ImportError:
            logger.error("anthropic package not installed. Install with: pip install anthropic")
    
    def interpret_document(
        self,
        image_path: Union[str, Path],
        prompt: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict:
        """
        Interpret a document image using vision-language model.
        
        Args:
            image_path: Path to the document image
            prompt: Custom prompt for interpretation
            context: Additional context (e.g., OCR text) to aid interpretation
        
        Returns:
            Dictionary with interpretation results
        """
        image_path = Path(image_path)
        logger.info(f"Interpreting document: {image_path}")
        
        if not prompt:
            prompt = self._get_default_prompt(context)
        
        try:
            if self.model_name.startswith("gpt"):
                return self._interpret_with_gpt(image_path, prompt)
            elif self.model_name == "claude":
                return self._interpret_with_claude(image_path, prompt)
            else:
                logger.error(f"Unsupported model: {self.model_name}")
                return {"error": f"Unsupported model: {self.model_name}"}
                
        except Exception as e:
            logger.error(f"Error during interpretation: {str(e)}")
            return {"error": str(e)}
    
    def _interpret_with_gpt(self, image_path: Path, prompt: str) -> Dict:
        """Interpret document using GPT-4o."""
        try:
            # Encode image
            image_data = self._encode_image(image_path)
            
            if not self.client:
                return {
                    "error": "OpenAI client not initialized. Provide API key in config."
                }
            
            # Call GPT-4o API
            response = self.client.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000
            )
            
            interpretation = response.choices[0].message.content
            
            return {
                "model": self.model_name,
                "interpretation": interpretation,
                "usage": response.usage._asdict() if hasattr(response, 'usage') else {}
            }
            
        except Exception as e:
            logger.error(f"GPT interpretation error: {str(e)}")
            return {"error": str(e)}
    
    def _interpret_with_claude(self, image_path: Path, prompt: str) -> Dict:
        """Interpret document using Claude."""
        try:
            # Encode image
            image_data = self._encode_image(image_path)
            
            if not self.client:
                return {
                    "error": "Anthropic client not initialized. Provide API key in config."
                }
            
            # Determine image media type
            suffix = image_path.suffix.lower()
            media_type = "image/jpeg" if suffix in ['.jpg', '.jpeg'] else "image/png"
            
            # Call Claude API
            message = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )
            
            interpretation = message.content[0].text if message.content else ""
            
            return {
                "model": "claude",
                "interpretation": interpretation,
                "usage": {
                    "input_tokens": message.usage.input_tokens if hasattr(message, 'usage') else 0,
                    "output_tokens": message.usage.output_tokens if hasattr(message, 'usage') else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Claude interpretation error: {str(e)}")
            return {"error": str(e)}
    
    def _encode_image(self, image_path: Path) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _get_default_prompt(self, context: Optional[str] = None) -> str:
        """Generate default interpretation prompt."""
        base_prompt = """Analyze this document image and provide a detailed interpretation. 
        Focus on:
        1. Document type and purpose
        2. Key information and data points
        3. Structure and layout
        4. Any measurements, dimensions, or technical specifications
        5. Quality issues or areas that may be difficult to read
        
        If this is an engineering plan or technical drawing, pay special attention to:
        - Dimensions and measurements
        - Symbols and annotations
        - Scale and units
        - Material specifications
        """
        
        if context:
            base_prompt += f"\n\nAdditional context from OCR:\n{context[:500]}"
        
        return base_prompt
    
    def extract_specific_data(
        self,
        image_path: Union[str, Path],
        data_type: str,
        fields: Optional[list] = None
    ) -> Dict:
        """
        Extract specific types of data from document.
        
        Args:
            image_path: Path to document image
            data_type: Type of data to extract ('measurements', 'tables', 'forms', etc.)
            fields: Specific fields to extract
        
        Returns:
            Dictionary with extracted data
        """
        prompt = self._get_extraction_prompt(data_type, fields)
        return self.interpret_document(image_path, prompt=prompt)
    
    def _get_extraction_prompt(self, data_type: str, fields: Optional[list]) -> str:
        """Generate prompt for specific data extraction."""
        prompts = {
            "measurements": "Extract all measurements, dimensions, and units from this document. Provide them in a structured format.",
            "tables": "Identify and extract all tables from this document. Preserve the table structure and content.",
            "forms": "Extract all form fields and their values from this document.",
            "annotations": "Identify and extract all text annotations, notes, and labels from this document.",
        }
        
        prompt = prompts.get(data_type, f"Extract {data_type} from this document.")
        
        if fields:
            prompt += f"\n\nSpecifically look for these fields: {', '.join(fields)}"
        
        return prompt
