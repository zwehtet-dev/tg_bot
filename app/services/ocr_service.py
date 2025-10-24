"""
OCR service for receipt processing using Mistral AI Vision
"""
import base64
import json
import logging
from typing import Optional, Dict
from PIL import Image
import io

logger = logging.getLogger(__name__)


class OCRService:
    """Handle OCR operations using Mistral AI Vision"""
    
    def __init__(self, api_key: str):
        """
        Initialize OCR service
        
        Args:
            api_key: Mistral AI API key
        """
        try:
            from mistralai import Mistral
            self.api_key = api_key  # Store API key for direct HTTP calls
            self.client = Mistral(api_key=api_key)
            logger.info("OCR Service initialized successfully")
        except ImportError:
            logger.error("mistralai package not installed. Run: pip install mistralai")
            raise
        except Exception as e:
            logger.error(f"Error initializing OCR service: {e}")
            raise
    
    def image_to_base64(self, image_path: str) -> str:
        """
        Convert image to base64 for Mistral AI Vision
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded image string
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if too large
                max_size = (1024, 1024)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=85)
                return base64.b64encode(buffered.getvalue()).decode()
        except Exception as e:
            logger.error(f"Error converting image to base64: {e}")
            raise
    
    def extract_receipt_info(self, image_path: str) -> Optional[Dict]:
        """
        Extract information from receipt using Mistral AI Vision
        
        Args:
            image_path: Path to receipt image
            
        Returns:
            Dictionary with extracted information or None if failed
        """
        try:
            image_base64 = self.image_to_base64(image_path)
            
            # Construct the prompt
            prompt = """Analyze this Thai bank transfer receipt and extract:
1. Transfer amount (in THB)
2. Sender bank name
3. Receiver bank name
4. Sender account name
5. Receiver account name
6. Transaction status (successful/pending/failed)
7. Transaction reference number

Return ONLY valid JSON format:
{
    "amount": <number or null>,
    "sender_bank": "<bank name or null>",
    "receiver_bank": "<bank name or null>",
    "sender_name": "<name or null>",
    "receiver_name": "<name or null>",
    "status": "<status or null>",
    "reference": "<ref or null>"
}"""
            
            # Use direct HTTP API call for vision support
            import requests
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "pixtral-12b-2409",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Try to parse JSON from response
            # Sometimes the model returns markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            logger.info(f"OCR extraction successful: {result}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Response content: {content if 'content' in locals() else 'N/A'}")
            return None
        except Exception as e:
            logger.error(f"OCR Error: {e}")
            return None
