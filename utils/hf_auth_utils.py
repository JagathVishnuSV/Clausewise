import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def validate_hf_token() -> bool:
    """Validate if HF_API_TOKEN is properly configured."""
    token = os.getenv("HF_API_TOKEN")
    if not token:
        logger.error("HF_API_TOKEN environment variable is not set")
        return False
    
    if len(token) < 10:  # Basic validation
        logger.error("HF_API_TOKEN appears to be invalid (too short)")
        return False
    
    return True

def get_hf_headers() -> Optional[Dict[str, str]]:
    """Get properly formatted headers for Hugging Face API."""
    if not validate_hf_token():
        return None
    
    token = os.getenv("HF_API_TOKEN")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def check_model_accessibility(model_id: str) -> bool:
    """Check if the model is accessible with current token."""
    import requests
    
    headers = get_hf_headers()
    if not headers:
        return False
    
    try:
        url = f"https://huggingface.co/api/models/{model_id}"
        response = requests.get(url, headers=headers, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error checking model accessibility: {e}")
        return False
