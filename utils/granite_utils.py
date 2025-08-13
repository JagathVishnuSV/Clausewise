import os
import asyncio
import logging
from typing import Optional, Dict, Any
from utils.async_client import AsyncHTTPClient
from utils.hf_auth_utils import validate_hf_token, get_hf_headers, check_model_accessibility

logger = logging.getLogger(__name__)

HF_GRANITE_MODEL = "ibm-granite/granite-3.2-2b-instruct"
HF_INFERENCE_URL = f"https://api-inference.huggingface.co/models/{HF_GRANITE_MODEL}"

# Alternative fallback models that might be more accessible
FALLBACK_MODELS = [
    "microsoft/DialoGPT-medium",
    "facebook/blenderbot-400M-distill",
    "google/flan-t5-base"
]

async def granite_simple_doc_type(doc_text: str) -> str:
    """Async document type classification using Granite with improved error handling."""
    
    # Validate token first
    if not validate_hf_token():
        logger.warning("HF_API_TOKEN not configured, using fallback classification")
        return await fallback_classification(doc_text)
    
    headers = get_hf_headers()
    if not headers:
        logger.warning("Could not get HF headers, using fallback")
        return await fallback_classification(doc_text)
    
    # Check if model is accessible
    if not check_model_accessibility(HF_GRANITE_MODEL):
        logger.warning(f"Model {HF_GRANITE_MODEL} not accessible, using fallback")
        return await fallback_classification(doc_text)
    
    prompt = (
        "Classify the document type from: NDA, Lease, Employment Agreement, Purchase Agreement, Policy, Other.\n"
        "Return ONLY the label.\n\nDocument:\n" + doc_text[:6000]
    )
    
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 32, "temperature": 0.1}
    }
    
    try:
        async with AsyncHTTPClient() as client:
            response = await client.post(HF_INFERENCE_URL, headers=headers, json=payload)
            
            if isinstance(response, dict) and "error" in response:
                error_msg = response.get("error", "")
                logger.error(f"API Error: {error_msg}")
                
                # Handle specific error cases
                if any(keyword in error_msg.lower() for keyword in ["authorization", "token", "403", "forbidden"]):
                    logger.error("Authentication issue detected, using fallback")
                    return await fallback_classification(doc_text)
                
                return "Other"
            
            if isinstance(response, list) and response and "generated_text" in response[0]:
                result = response[0]["generated_text"].strip().split("\n")[0][:64]
                return result if result else "Other"
            
            logger.warning("Unexpected response format, using fallback")
            return await fallback_classification(doc_text)
            
    except Exception as e:
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ["403", "forbidden", "authorization", "authentication"]):
            logger.error(f"Authentication/Access issue: {e}")
        else:
            logger.error(f"Network/API Error: {e}")
        
        return await fallback_classification(doc_text)

async def fallback_classification(doc_text: str) -> str:
    """Fallback classification when HF API is not available."""
    logger.info("Using fallback classification method")
    
    # Simple keyword-based classification
    text_lower = doc_text.lower()
    
    # Define keyword patterns for each document type
    patterns = {
        "NDA": ["non-disclosure", "confidential", "nda", "proprietary"],
        "Lease": ["lease", "rental", "tenant", "landlord", "property"],
        "Employment Agreement": ["employment", "salary", "position", "hire", "job"],
        "Purchase Agreement": ["purchase", "sale", "buy", "sell", "transaction"],
        "Policy": ["policy", "guidelines", "procedure", "rules", "regulation"]
    }
    
    # Count matches for each type
    scores = {}
    for doc_type, keywords in patterns.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        scores[doc_type] = score
    
    # Return the type with highest score, or "Other" if no matches
    if scores:
        best_type = max(scores, key=scores.get)
        return best_type if scores[best_type] > 0 else "Other"
    
    return "Other"
