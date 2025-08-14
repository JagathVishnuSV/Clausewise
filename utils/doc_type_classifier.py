import os
import asyncio
import logging
from typing import Dict, Any
from google import genai
from google.genai import types as gtypes
from dotenv import load_dotenv
from utils.gemini_utils_optimized import GeminiAnalyzer

load_dotenv()

logger = logging.getLogger(__name__)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GEMINI_MODEL = "gemini-2.5-pro"

class DocumentTypeClassifier:
    """Document type classification using Gemini AI with chunking and rate limiting."""
    
    @staticmethod
    async def classify_document(text: str, language: str = "english") -> Dict[str, Any]:
        """Classify document type using chunked approach."""
        try:
            if not text or not text.strip():
                return {
                    "doc_type": "Unknown",
                    "subtype": "Unknown",
                    "confidence": 0.0
                }
            
            # For large documents, use first chunk for classification
            if len(text) > 4000:
                chunks = GeminiAnalyzer._chunk_text(text, 4000)
                text = chunks[0]  # Use first chunk for classification
            
            # Language-specific prompts
            prompts = {
                "english": f"""Analyze this document and classify its type. Return a JSON response with:
1. doc_type: Main document type (NDA, Lease, Employment, Service Agreement, etc.)
2. subtype: More specific subtype if applicable
3. confidence: Confidence level (0.0 to 1.0)

Document text: {text[:2000]}...

Classification:""",
                
                "tamil": f"""இந்த ஆவணத்தை பகுப்பாய்வு செய்து அதன் வகையை வகைப்படுத்துங்கள். JSON பதிலுடன் திருப்பி அனுப்புங்கள்:
1. doc_type: முக்கிய ஆவண வகை (NDA, Lease, Employment, Service Agreement, etc.)
2. subtype: பொருந்தினால் மேலும் குறிப்பிட்ட துணை வகை
3. confidence: நம்பிக்கை நிலை (0.0 முதல் 1.0 வரை)

ஆவண உரை: {text[:2000]}...

வகைப்படுத்தல்:"""
            }
            
            prompt = prompts.get(language, prompts["english"])
            
            # Use structured output for classification
            schema = {
                "type": "object",
                "properties": {
                    "doc_type": {"type": "string"},
                    "subtype": {"type": "string"},
                    "confidence": {"type": "number"}
                },
                "required": ["doc_type", "subtype", "confidence"]
            }
            
            # Use the chunked approach from GeminiAnalyzer
            result = await GeminiAnalyzer._make_rate_limited_request(
                lambda: GeminiAnalyzer._structured_request(prompt, schema)
            )
            
            if result:
                return {
                    "doc_type": result.get("doc_type", "Unknown"),
                    "subtype": result.get("subtype", "Unknown"),
                    "confidence": result.get("confidence", 0.0)
                }
            else:
                # Fallback to keyword-based classification
                return DocumentTypeClassifier.classify_by_keywords(text)
                
        except Exception as e:
            logger.error(f"Error in document classification: {e}")
            return {
                "doc_type": "Unknown",
                "subtype": "Unknown",
                "confidence": 0.0
            }
    
    @staticmethod
    def classify_by_keywords(text: str) -> Dict[str, Any]:
        """Fallback keyword-based document classification."""
        text_lower = text.lower()
        
        # Define document type keywords
        doc_types = {
            "NDA": ["confidentiality", "non-disclosure", "nda", "secret", "proprietary"],
            "Lease": ["lease", "rental", "tenant", "landlord", "premises", "property"],
            "Employment": ["employee", "employer", "salary", "termination", "job", "work"],
            "Service Agreement": ["service", "vendor", "client", "deliverables", "scope"],
            "Purchase Agreement": ["purchase", "buy", "seller", "buyer", "payment"],
            "License": ["license", "permission", "rights", "intellectual property"],
            "Partnership": ["partner", "partnership", "joint venture", "collaboration"],
            "Divorce Petition": ["divorce", "petition", "matrimonial", "dissolution", "marriage", "cruelty", "adultery", "custody"],
            "Will": ["will", "testament", "executor", "beneficiary", "estate", "bequeath"],
            "Loan Agreement": ["loan", "borrower", "lender", "interest", "repayment", "credit"],
            "Power of Attorney": ["power of attorney", "attorney-in-fact", "principal", "agent", "legal representative"]
        }
        
        scores = {}
        for doc_type, keywords in doc_types.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[doc_type] = score
        
        if scores:
            best_type = max(scores, key=scores.get)
            # Adjust confidence calculation: higher score for more matches, relative to max possible keywords
            max_keywords = max(len(keywords) for keywords in doc_types.values()) # Get max possible keywords for normalization
            confidence = min(scores[best_type] / max_keywords, 1.0) if max_keywords > 0 else 0.0
            
            return {
                "doc_type": best_type,
                "subtype": "General", # Subtype can be refined with more advanced classification later
                "confidence": confidence
            }
        else:
            return {
                "doc_type": "General",
                "subtype": "Unknown",
                "confidence": 0.1
            }
