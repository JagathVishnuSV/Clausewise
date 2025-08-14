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
GEMINI_MODEL = "gemini-2.0-flash-lite"

class ClauseSimplifier:
    """Clause simplification using Gemini AI with chunking and rate limiting."""
    
    # Rate limiting configuration
    BATCH_SIZE = 48  # Target size for single-request batching
    DELAY_BETWEEN_BATCHES = 0.0  # No extra delay; global rate limiter already spaces calls
    CIRCUIT_FAILS_BEFORE_OPEN = 1
    _consecutive_fail_batches = 0
    BATCH_MAX_CHARS = 9000  # Keep prompt within safe limits for flash-lite
    
    @staticmethod
    async def simplify_clause(clause_text: str, language: str = "english") -> str:
        """Simplify a single clause into layman's terms."""
        try:
            if not clause_text or not clause_text.strip():
                return ""
            
            # Fast-path heuristics for very short headings/phrases to avoid LLM calls
            text_norm = clause_text.strip().strip(':').strip('-').strip()
            if len(text_norm) <= 80 and len(text_norm.split()) <= 12:
                fast = ClauseSimplifier._fast_heuristic(text_norm)
                if fast:
                    return fast
            
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
            
            # Use the chunked approach from GeminiAnalyzer and ensure we get a single concise line
            simplified = await GeminiAnalyzer._make_rate_limited_request(
                lambda: GeminiAnalyzer._simple_text_request(prompt)
            )
            # Post-trim: take first sentence to avoid run-ons
            # Removed aggressive trimming to allow multi-sentence simplified clauses if model produces them
            # if simplified:
            #     simplified = simplified.strip()
            #     # If model echoes the original, shorten to a concise sentence
            #     if simplified.lower().startswith("original"):
            #         simplified = simplified.split("\n")[-1].strip()
            #     first_sentence = simplified.split(". ")[0].strip()
            #     if 8 <= len(first_sentence) <= len(simplified):
            #         simplified = first_sentence if not simplified.endswith('.') else first_sentence + '.'
            
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
            simplified_clauses: List[Dict[str, str]] = []
            
            # Circuit breaker: if repeated batch failures, fall back to heuristic for remaining
            if ClauseSimplifier._consecutive_fail_batches >= ClauseSimplifier.CIRCUIT_FAILS_BEFORE_OPEN:
                for clause in clauses:
                    clause['simplified_text'] = ClauseSimplifier._heuristic_plainify(clause.get('original_text', ''))
                return clauses

            # Pre-fill very short headings via fast heuristic to reduce payload
            need_llm: List[tuple[int, Dict[str, str]]] = []
            for idx, clause in enumerate(clauses):
                text = clause.get('original_text', '') or ''
                text_norm = text.strip().strip(':').strip('-').strip()
                fast = None
                if len(text_norm) <= 80 and len(text_norm.split()) <= 12:
                    fast = ClauseSimplifier._fast_heuristic(text_norm)
                if fast:
                    out = dict(clause)
                    out['simplified_text'] = fast
                    simplified_clauses.append(out)
                else:
                    need_llm.append((idx, clause))

            if not need_llm:
                # Sort back to original order
                simplified_clauses.sort(key=lambda c: c.get('clause_number', 0))
                return simplified_clauses

            # Build a single large batch up to BATCH_SIZE and within char limits
            logger.info(f"Building single-request batch for up to {ClauseSimplifier.BATCH_SIZE} clauses")
            batched_items: List[tuple[int, Dict[str, str]]] = []
            total_chars = 0
            for idx, clause in need_llm[:ClauseSimplifier.BATCH_SIZE]:
                t = (clause.get('original_text', '') or '').strip()
                if not t:
                    continue
                if total_chars + len(t) > ClauseSimplifier.BATCH_MAX_CHARS and batched_items:
                    break
                batched_items.append((idx, clause))
                total_chars += len(t)

            # Prepare and send one structured request for the batched items
            try:
                batch_clauses = [c for _, c in batched_items]
                simplified_list = await ClauseSimplifier._simplify_batch_with_gemini(batch_clauses, language)
                if len(simplified_list) != len(batch_clauses):
                    raise Exception("Batch response size mismatch")
                for (idx, clause), simp in zip(batched_items, simplified_list):
                    out = dict(clause)
                    out['simplified_text'] = (simp or '').strip()
                    simplified_clauses.append(out)
                ClauseSimplifier._consecutive_fail_batches = 0
            except Exception as e:
                logger.error(f"Single-batch simplification failed: {e}")
                ClauseSimplifier._consecutive_fail_batches += 1
                # Fallback: simplify each remaining via per-clause (still uses global limiter)
                for idx, clause in batched_items:
                    try:
                        simp = await ClauseSimplifier.simplify_clause(clause.get('original_text', ''), language)
                    except Exception as e2:
                        logger.error(f"Per-clause fallback error (idx {idx}): {e2}")
                        simp = ClauseSimplifier._heuristic_plainify(clause.get('original_text', ''))
                    out = dict(clause)
                    out['simplified_text'] = simp
                    simplified_clauses.append(out)

            # For any remaining clauses beyond the first batch, use heuristic to keep fast
            remaining = [c for c in need_llm[len(batched_items):]]
            for _, clause in remaining:
                out = dict(clause)
                out['simplified_text'] = ClauseSimplifier._heuristic_plainify(clause.get('original_text', ''))
                simplified_clauses.append(out)

            # Sort back to original clause order
            simplified_clauses.sort(key=lambda c: c.get('clause_number', 0))
            
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
    def _fast_heuristic(text: str) -> str | None:
        """Return a quick simplified phrase for common short headings; otherwise None."""
        t = text.strip().strip(':').strip()
        tl = t.lower()
        rules = [
            (r"second\s+(e-)?opinion.*critical\s+illness", "Second medical opinion for serious (critical) illness"),
            (r"refractory\s+heart\s+failure", "Heart failure that doesn't respond to treatment"),
            (r"contact\s+number\s+of\s+the\s+insured\s+person", "Insured person's phone number"),
            (r"modification\s+of\s+base\s+co[- ]?payment", "Change to the standard amount you pay (base co-payment)"),
            (r"update\s+to\s+family\s+members", "Update information of your family members"),
            (r"excl0?2[:\-]?\s*specified\s+disease/?procedure", "Code Excl02: Listed disease/procedure"),
        ]
        import re
        for pat, out in rules:
            if re.search(pat, tl):
                return out
        # Generic short heading cleanup
        if len(t) <= 60 and not t.endswith('.'):
            return t[0].upper() + t[1:]
        return None

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
