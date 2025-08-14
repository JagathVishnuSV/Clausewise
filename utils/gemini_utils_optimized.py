import os
import base64
import asyncio
import time
from pathlib import Path
from google import genai
from google.genai import types as gtypes
from dotenv import load_dotenv
import logging
import re
import random

load_dotenv()

logger = logging.getLogger(__name__)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GEMINI_TEXT_MODEL = "gemini-2.5-flash"
GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"

class GeminiAnalyzer:
    """Optimized Gemini analyzer with enhanced features and chunking."""
    
    # Rate limiting configuration
    MAX_TOKENS_PER_REQUEST = 30000  # Conservative limit
    CHUNK_SIZE = 3000  # Characters per chunk
    RATE_LIMIT_DELAY = 0.5  # Reduced delay to speed up requests
    MAX_RETRIES = 3 # Increased retries for robustness
    JITTER_MIN = 0.1
    JITTER_MAX = 0.5
    MAX_CONCURRENT = 5  # Allow more parallel requests

    # Global concurrency limit for outbound Gemini calls
    _concurrency = asyncio.Semaphore(MAX_CONCURRENT)
    
    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 3000) -> list:
        """Split text into manageable chunks while preserving sentence boundaries."""
        if chunk_size is None:
            chunk_size = GeminiAnalyzer.CHUNK_SIZE
            
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        # Split by sentences first
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    @staticmethod
    async def _make_rate_limited_request(func, *args, **kwargs):
        """Make a rate-limited request with global serialization, jitter, and retry."""
        last_error: Exception | None = None
        for attempt in range(GeminiAnalyzer.MAX_RETRIES):
            async with GeminiAnalyzer._concurrency:
                # Add spacing + jitter before call to reduce collisions
                await asyncio.sleep(GeminiAnalyzer.RATE_LIMIT_DELAY + random.uniform(GeminiAnalyzer.JITTER_MIN, GeminiAnalyzer.JITTER_MAX))
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        backoff = (attempt + 1) * 4.0
                        logger.warning(f"Rate limit hit, waiting {backoff}s before retry {attempt + 1}")
                        await asyncio.sleep(backoff)
                        continue
                    raise e
        raise Exception("Max retries exceeded") from last_error
    
    @staticmethod
    async def _analyze_chunk(chunk: str, language: str = "english") -> dict:
        """Analyze a single chunk of text."""
        system_instructions = {
            "english": """Analyze this text segment and provide:
1. **Summary**: Brief summary of this segment
2. **Key Points**: 2-3 key points from this segment
3. **Risks**: Any risks mentioned in this segment
4. **Action Items**: Any action items from this segment
5. **Document Type**: Type of document this appears to be""",
            
            "tamil": """இந்த உரை பிரிவை பகுப்பாய்வு செய்து வழங்கவும்:
1. **சுருக்கம்**: இந்த பிரிவின் சுருக்கமான சுருக்கம்
2. **முக்கிய அம்சங்கள்**: இந்த பிரிவிலிருந்து 2-3 முக்கிய புள்ளிகள்
3. **அபாயங்கள்**: இந்த பிரிவில் குறிப்பிடப்பட்ட அபாயங்கள்
4. **செயல் உருப்படிகள்**: இந்த பிரிவிலிருந்து செயல் உருப்படிகள்
5. **ஆவண வகை**: இது தோன்றும் ஆவண வகை"""
        }
        
        schema = gtypes.Schema(
            type=gtypes.Type.OBJECT,
            properties={
                "summary": gtypes.Schema(type=gtypes.Type.STRING),
                "key_points": gtypes.Schema(type=gtypes.Type.ARRAY, items=gtypes.Schema(type=gtypes.Type.STRING)),
                "risks": gtypes.Schema(type=gtypes.Type.ARRAY, items=gtypes.Schema(type=gtypes.Type.STRING)),
                "action_items": gtypes.Schema(type=gtypes.Type.ARRAY, items=gtypes.Schema(type=gtypes.Type.STRING)),
                "document_type": gtypes.Schema(type=gtypes.Type.STRING),
            },
            required=["summary", "key_points", "risks", "action_items", "document_type"],
        )

        async def _make_request():
            res = client.models.generate_content(
                model=GEMINI_TEXT_MODEL,
                config=gtypes.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    system_instruction=system_instructions.get(language, system_instructions["english"])
                ),
                contents=[gtypes.Content(role="user", parts=[gtypes.Part.from_text(text=chunk)])],
            )
            return res.parsed or {}
        
        return await GeminiAnalyzer._make_rate_limited_request(_make_request)
    
    @staticmethod
    async def analyze_document(doc_text: str, language: str = "english") -> dict:
        """Analyze document with chunking to avoid quota limits."""
        
        if not doc_text or not doc_text.strip():
            return {
                "summary": "Empty document",
                "key_points": [],
                "risks": [],
                "action_items": [],
                "detected_language": "unknown",
                "document_type": "Empty"
            }
        
        try:
            # Cap text analyzed for summary to keep calls light
            if len(doc_text) > 10000:
                doc_text = doc_text[:10000]
            # Split text into chunks
            chunks = GeminiAnalyzer._chunk_text(doc_text)
            logger.info(f"Split document into {len(chunks)} chunks")
            
            # Analyze each chunk concurrently
            tasks = []
            for i, chunk in enumerate(chunks):
                logger.info(f"Creating task for chunk {i+1}/{len(chunks)}")
                tasks.append(GeminiAnalyzer._analyze_chunk(chunk, language))
            
            chunk_results = await asyncio.gather(*tasks)
            
            # Combine results
            combined_summary = " ".join([r.get("summary", "") for r in chunk_results])
            combined_key_points = []
            combined_risks = []
            combined_action_items = []
            document_types = []
            
            for result in chunk_results:
                combined_key_points.extend(result.get("key_points", [])[:2])  # Top 2 from each chunk
                combined_risks.extend(result.get("risks", [])[:1])  # Top 1 from each chunk
                combined_action_items.extend(result.get("action_items", [])[:1])  # Top 1 from each chunk
                doc_type = result.get("document_type", "")
                if doc_type and doc_type not in document_types:
                    document_types.append(doc_type)
            
            # Limit final lists
            combined_key_points = combined_key_points[:7]
            combined_risks = combined_risks[:5]
            combined_action_items = combined_action_items[:5]
            
            # Determine final document type
            final_doc_type = document_types[0] if document_types else "General"
            
            return {
                "summary": combined_summary[:500] + "..." if len(combined_summary) > 500 else combined_summary,
                "key_points": combined_key_points,
                "risks": combined_risks,
                "action_items": combined_action_items,
                "detected_language": language,
                "document_type": final_doc_type
            }
            
        except Exception as e:
            logger.error(f"Error in chunked Gemini analysis: {e}")
            return {
                "summary": "Analysis failed due to API limits",
                "key_points": [],
                "risks": [],
                "action_items": [],
                "detected_language": "unknown",
                "document_type": "Unknown"
            }

    @staticmethod
    async def translate_text(text: str, target_language: str, source_language: str = "auto") -> str:
        """Translate text with chunking for large texts."""
        try:
            # For large texts, chunk and translate separately
            if len(text) > 4000:
                chunks = GeminiAnalyzer._chunk_text(text, 4000)
                translated_chunks = []
                
                for chunk in chunks:
                    translated_chunk = await GeminiAnalyzer._translate_chunk(chunk, target_language, source_language)
                    translated_chunks.append(translated_chunk)
                
                return " ".join(translated_chunks)
            else:
                return await GeminiAnalyzer._translate_chunk(text, target_language, source_language)
                
        except Exception as e:
            logger.error(f"Error in translation: {e}")
            return "Translation failed"
    
    @staticmethod
    async def _translate_chunk(chunk: str, target_language: str, source_language: str = "auto") -> str:
        """Translate a single chunk of text."""
        lang_mapping = {
            "tamil": "Tamil",
            "english": "English",
            "spanish": "Spanish",
            "french": "French",
            "german": "German",
            "chinese": "Chinese",
            "japanese": "Japanese"
        }
        
        target_lang = lang_mapping.get(target_language, target_language)
        
        async def _make_request():
            res = client.models.generate_content(
                model=GEMINI_TEXT_MODEL,
                contents=[
                    gtypes.Content(role="user", parts=[gtypes.Part.from_text(
                        f"Translate the following text from {source_language} to {target_lang}:\n\n{chunk}"
                    )])
                ],
            )
            return res.text.strip()
        
        return await GeminiAnalyzer._make_rate_limited_request(_make_request)

    @staticmethod
    async def generate_tts(text: str, language: str = "english", voice_name: str = "Kore") -> str:
        """Generate TTS with chunking for large texts."""
        try:
            # Language-specific voice mapping
            voice_mapping = {
                "english": {
                    "kore": "Kore",
                    "charon": "Charon",
                    "fenrir": "Fenrir"
                },
                "tamil": {
                    "kore": "Kore",  # Use Kore for Tamil as well
                    "charon": "Charon"
                }
            }
            
            selected_voice = voice_mapping.get(language, {}).get(voice_name.lower(), voice_name)
            
            # Ensure text is within limits
            if not text or len(text.strip()) == 0:
                return ""
            
            # For large texts, chunk and generate TTS for each chunk
            max_length = 4000
            if len(text) > max_length:
                chunks = GeminiAnalyzer._chunk_text(text, max_length)
                audio_files = []
                
                for i, chunk in enumerate(chunks):
                    audio_file = await GeminiAnalyzer._generate_chunk_tts(chunk, selected_voice)
                    if audio_file:
                        audio_files.append(audio_file)
                
                # Return the first audio file for now (could be enhanced to concatenate)
                return audio_files[0] if audio_files else ""
            else:
                return await GeminiAnalyzer._generate_chunk_tts(text, selected_voice)
            
        except Exception as e:
            logger.error(f"TTS generation error: {e}")
            return ""
    
    @staticmethod
    async def _generate_chunk_tts(text: str, voice_name: str) -> str:
        """Generate TTS for a single chunk."""
        async def _make_request():
            res = client.models.generate_content(
                model=GEMINI_TTS_MODEL,
                contents=text,
                config=gtypes.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=gtypes.SpeechConfig(
                        voice_config=gtypes.VoiceConfig(
                            prebuilt_voice_config=gtypes.PrebuiltVoiceConfig(voice_name=voice_name)
                        )
                    )
                ),
            )
            return res
        
        try:
            res = await GeminiAnalyzer._make_rate_limited_request(_make_request)
            
            if not res.candidates or not res.candidates[0].content.parts:
                return ""
            
            audio_part = res.candidates[0].content.parts[0]
            if not hasattr(audio_part, 'inline_data') or not audio_part.inline_data:
                return ""
            
            b64 = audio_part.inline_data.data
            pcm = base64.b64decode(b64)
            
            import uuid
            filename = f"tts_{uuid.uuid4().hex}_{voice_name.lower()}.wav"
            outpath = Path("static/audio") / filename
            outpath.parent.mkdir(exist_ok=True)
            
            import wave
            with wave.open(str(outpath), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(pcm)
            
            return f"/static/audio/{filename}"
            
        except Exception as e:
            logger.error(f"Chunk TTS generation error: {e}")
            return ""
    
    @staticmethod
    async def _simple_text_request(prompt: str) -> str:
        """Make a simple text request without structured output."""
        async def _make_request():
            res = client.models.generate_content(
                model=GEMINI_TEXT_MODEL,
                contents=[gtypes.Content(role="user", parts=[gtypes.Part.from_text(text=prompt)])],
            )
            return res.text.strip()
        
        return await GeminiAnalyzer._make_rate_limited_request(_make_request)
    
    @staticmethod
    async def _structured_request(prompt: str, schema: dict) -> dict:
        """Make a structured request with JSON schema."""
        async def _make_request():
            def map_json_type(t: str):
                t = (t or "string").lower()
                if t == "string":
                    return gtypes.Type.STRING
                if t in ("number", "float", "double"): 
                    return gtypes.Type.NUMBER
                if t in ("integer", "int"): 
                    return gtypes.Type.INTEGER
                if t in ("boolean", "bool"):
                    return gtypes.Type.BOOLEAN
                if t == "array":
                    return gtypes.Type.ARRAY
                return gtypes.Type.STRING

            def build_schema(s: dict) -> gtypes.Schema:
                s_type = map_json_type(s.get("type", "object"))
                if s_type == gtypes.Type.OBJECT:
                    props = s.get("properties", {})
                    return gtypes.Schema(
                        type=gtypes.Type.OBJECT,
                        properties={
                            k: build_schema(v) for k, v in props.items()
                        },
                        required=s.get("required", []),
                    )
                if s_type == gtypes.Type.ARRAY:
                    items = s.get("items", {"type": "string"})
                    return gtypes.Schema(
                        type=gtypes.Type.ARRAY,
                        items=build_schema(items),
                    )
                # primitives
                return gtypes.Schema(type=s_type)

            gtypes_schema = build_schema(schema)
            
            res = client.models.generate_content(
                model=GEMINI_TEXT_MODEL,
                config=gtypes.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=gtypes_schema,
                ),
                contents=[gtypes.Content(role="user", parts=[gtypes.Part.from_text(text=prompt)])],
            )
            return res.parsed or {}
        
        return await GeminiAnalyzer._make_rate_limited_request(_make_request)
