import os
import asyncio
import logging
from typing import List, Dict, Any
from google import genai
from google.genai import types as gtypes
from dotenv import load_dotenv
from utils.gemini_utils_optimized import GeminiAnalyzer
from utils.granite_utils import granite_simple_doc_type

load_dotenv()

logger = logging.getLogger(__name__)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GEMINI_MODEL = "gemini-2.5-flash-lite"

class ClauseSimplifier:
    """Clause simplification using Gemini AI with chunking and rate limiting."""
    
    # Rate limiting configuration
    BATCH_SIZE = 6  # Larger batch to reduce total API calls
    DELAY_BETWEEN_BATCHES = 3.0  # Slightly longer to respect limits
    CIRCUIT_FAILS_BEFORE_OPEN = 2
    _consecutive_fail_batches = 0
    
    @staticmethod
    async def simplify_clause(clause_text: str, language: str = "english") -> str:
        """Simplify a single clause into layman's terms."""
        try:
            if not clause_text or not clause_text.strip():
                return ""
            
            # Language-specific prompts
            prompts = {
                "english": f"""Simplify this legal clause into clear, simple language that a non-lawyer can understand. 
                Keep the meaning accurate but use everyday words. Remove legal jargon where possible.
                
                Original clause: {clause_text}
                
                Simplified version:""",
                
                "tamil": f"""இந்த சட்ட விதியை எளிய, தெளிவான மொழியில் எளிதாக்குங்கள், சட்டம் படிக்காதவரும் புரிந்துகொள்ளும் வகையில்.
                பொருளை துல்லியமாக வைத்துக்கொண்டு, அன்றாட வார்த்தைகளைப் பயன்படுத்துங்கள். சட்ட வார்த்தைகளை முடிந்தவரை நீக்குங்கள்.
                
                அசல் விதி: {clause_text}
                
                எளிதாக்கப்பட்ட பதிப்பு:"""
            }
            
            prompt = prompts.get(language, prompts["english"])
            
            # Use the chunked approach from GeminiAnalyzer
            simplified = await GeminiAnalyzer._make_rate_limited_request(
                lambda: GeminiAnalyzer._simple_text_request(prompt)
            )
            
            return simplified.strip() if simplified else clause_text
            
        except Exception as e:
            logger.error(f"Error simplifying clause: {e}")
            # Heuristic fallback: shorten and plainify
            fallback = clause_text.strip()
            if len(fallback) > 300:
                fallback = fallback[:300] + "..."
            return fallback
    
    @staticmethod
    async def simplify_clauses(clauses: List[Dict[str, str]], language: str = "english") -> List[Dict[str, str]]:
        """Simplify multiple clauses with batching to avoid rate limits."""
        try:
            simplified_clauses = []
            
            # Circuit breaker: if repeated batch failures, fall back to heuristic for remaining
            if ClauseSimplifier._consecutive_fail_batches >= ClauseSimplifier.CIRCUIT_FAILS_BEFORE_OPEN:
                for clause in clauses:
                    clause['simplified_text'] = ClauseSimplifier._heuristic_plainify(clause.get('original_text', ''))
                return clauses

            # Process clauses in batches
            for i in range(0, len(clauses), ClauseSimplifier.BATCH_SIZE):
                batch = clauses[i:i + ClauseSimplifier.BATCH_SIZE]
                logger.info(f"Processing batch {i//ClauseSimplifier.BATCH_SIZE + 1}")
                
                # Try single batched Gemini call first
                try:
                    batched = await ClauseSimplifier._simplify_batch_with_gemini(batch, language)
                    for clause, simp in zip(batch, batched):
                        clause['simplified_text'] = simp
                        simplified_clauses.append(clause)
                    ClauseSimplifier._consecutive_fail_batches = 0
                except Exception as e:
                    logger.error(f"Batch simplification failed, falling back per-clause: {e}")
                    ClauseSimplifier._consecutive_fail_batches += 1
                    # Process batch concurrently per-clause
                    batch_tasks = []
                    for clause in batch:
                        task = ClauseSimplifier.simplify_clause(
                            clause.get('original_text', ''), 
                            language
                        )
                        batch_tasks.append(task)
                    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                    for j, (clause, simplified_text) in enumerate(zip(batch, batch_results)):
                        if isinstance(simplified_text, Exception):
                            logger.error(f"Error simplifying clause {i+j+1}: {simplified_text}")
                            simplified_text = ClauseSimplifier._heuristic_plainify(clause.get('original_text', ''))
                        clause['simplified_text'] = simplified_text
                        simplified_clauses.append(clause)
                
                # Delay between batches to avoid rate limits
                if i + ClauseSimplifier.BATCH_SIZE < len(clauses):
                    await asyncio.sleep(ClauseSimplifier.DELAY_BETWEEN_BATCHES)
            
            return simplified_clauses
            
        except Exception as e:
            logger.error(f"Error in batch clause simplification: {e}")
            # Return original clauses if simplification fails
            for clause in clauses:
                clause['simplified_text'] = ClauseSimplifier._heuristic_plainify(clause.get('original_text', ''))
            return clauses
    
    @staticmethod
    async def simplify_document_sections(text: str, language: str = "english") -> str:
        """Simplify entire document sections."""
        try:
            # Split into paragraphs and simplify each
            paragraphs = text.split('\n\n')
            simplified_paragraphs = []
            
            for paragraph in paragraphs:
                if paragraph.strip():
                    simplified = await ClauseSimplifier.simplify_clause(paragraph.strip(), language)
                    simplified_paragraphs.append(simplified)
                else:
                    simplified_paragraphs.append(paragraph)
            
            return '\n\n'.join(simplified_paragraphs)
            
        except Exception as e:
            logger.error(f"Error simplifying document sections: {e}")
            return text

    @staticmethod
    def _heuristic_plainify(text: str) -> str:
        """Very simple heuristic fallback: shorten and remove some jargon markers."""
        if not text:
            return ""
        t = text.replace("hereinafter", "").replace("thereof", "").replace("hereto", "")
        t = t.replace("Party", "side").replace("parties", "sides")
        t = t.strip()
        if len(t) > 300:
            t = t[:300] + "..."
        return t

    @staticmethod
    async def _simplify_batch_with_gemini(batch: List[Dict[str, str]], language: str) -> List[str]:
        """Ask Gemini to simplify multiple clauses in one structured call."""
        originals = [c.get('original_text', '') for c in batch]
        if not any(o.strip() for o in originals):
            return [""] * len(batch)
        if language == "tamil":
            prompt = (
                "கீழ்க்காணும் பல சட்ட விதிகளை எளிய தமிழில் மாற்றுங்கள். JSON வரிசையாக மட்டும் பதிலளிக்கவும்; ஒவ்வொரு உருப்படியும் எளிதாக்கப்பட்ட விதி ஆக வேண்டும்.\n\n"
                + "\n\n".join(f"[Clause {i+1}] {o}" for i, o in enumerate(originals))
            )
        else:
            prompt = (
                "Simplify the following multiple legal clauses into plain English. Respond ONLY as a JSON array of strings, where each item is the simplified clause in the same order.\n\n"
                + "\n\n".join(f"[Clause {i+1}] {o}" for i, o in enumerate(originals))
            )

        schema = {
            "type": "array",
            "items": {"type": "string"}
        }

        result = await GeminiAnalyzer._structured_request(prompt, schema)
        # Some SDKs may return python list directly; ensure list of strings
        if isinstance(result, list):
            return [str(x) if x is not None else "" for x in result]
        # If parsed object is missing, fallback to per-clause
        raise Exception("Batch structured response invalid")
