import os
import base64
import tempfile
from pathlib import Path
from google import genai
from google.genai import types as gtypes
from dotenv import load_dotenv
import wave
import logging

load_dotenv()

logger = logging.getLogger(__name__)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GEMINI_TEXT_MODEL = "gemini-2.5-pro"
GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"

async def gemini_structured_analysis(doc_text: str) -> dict:
    """Async structured analysis of legal documents."""
    schema = gtypes.Schema(
        type=gtypes.Type.OBJECT,
        properties={
            "summary": gtypes.Schema(type=gtypes.Type.STRING),
            "key_points": gtypes.Schema(type=gtypes.Type.ARRAY, items=gtypes.Schema(type=gtypes.Type.STRING)),
            "risks": gtypes.Schema(type=gtypes.Type.ARRAY, items=gtypes.Schema(type=gtypes.Type.STRING)),
            "action_items": gtypes.Schema(type=gtypes.Type.ARRAY, items=gtypes.Schema(type=gtypes.Type.STRING)),
            "detected_language": gtypes.Schema(type=gtypes.Type.STRING),
        },
        required=["summary", "key_points", "risks", "action_items"],
    )

    try:
        res = client.models.generate_content(
            model=GEMINI_TEXT_MODEL,
            config=gtypes.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                system_instruction="""You are an expert legal document analyst. Analyze the provided legal text comprehensively and provide:

1. **Summary**: A clear, concise executive summary (2-3 paragraphs) highlighting the main purpose and key implications
2. **Key Points**: 5-7 bullet points covering critical terms, obligations, rights, and deadlines
3. **Risks**: 3-5 specific legal, financial, or operational risks identified in the document
4. **Action Items**: 3-5 concrete next steps or recommendations for the parties involved
5. **Detected Language**: The primary language of the document

Ensure accuracy, clarity, and practical insights. Focus on actionable intelligence rather than just description."""
            ),
            contents=[gtypes.Content(role="user", parts=[gtypes.Part.from_text(text=doc_text)])],
        )
        return res.parsed
    except Exception as e:
        logger.error(f"Error in Gemini structured analysis: {e}")
        return {
            "summary": "Analysis failed",
            "key_points": [],
            "risks": [],
            "action_items": [],
            "detected_language": "unknown"
        }

async def gemini_translate(text: str, target_language: str) -> str:
    """Async translation using Gemini."""
    try:
        res = client.models.generate_content(
            model=GEMINI_TEXT_MODEL,
            contents=[
                gtypes.Content(role="user", parts=[gtypes.Part.from_text(f"Translate to {target_language}:\n{text}")])
            ],
        )
        return res.text.strip()
    except Exception as e:
        logger.error(f"Error in Gemini translation: {e}")
        return "Translation failed"

async def gemini_tts(text: str, voice_name: str = "Kore") -> str:
    """Async text-to-speech using Gemini with proper content formatting."""
    import uuid

    try:
        if not text.strip():
            logger.error("Empty text provided for TTS")
            return ""

        # Limit to avoid Gemini input size errors
        if len(text) > 4000:
            text = text[:4000] + "..."

        logger.info(f"Generating TTS with voice: {voice_name}")

        res = client.models.generate_content(
            model=GEMINI_TTS_MODEL,
            contents=[
                gtypes.Content(role="user", parts=[gtypes.Part(text=text)])
            ],
            config=gtypes.GenerateContentConfig(
                response_mime_type="audio/wav",  # Request WAV output
                speech_config=gtypes.SpeechConfig(
                    voice_config=gtypes.VoiceConfig(
                        prebuilt_voice_config=gtypes.PrebuiltVoiceConfig(
                            voice_name=voice_name
                        )
                    )
                ),
            ),
        )

        # Check response validity
        if not res.candidates or not res.candidates[0].content.parts:
            logger.error("No audio data returned from Gemini")
            return ""

        audio_part = res.candidates[0].content.parts[0]
        if not hasattr(audio_part, "inline_data") or not getattr(audio_part.inline_data, "data", None):
            logger.error("No inline audio data found")
            return ""

        # Decode base64 audio
        pcm_data = base64.b64decode(audio_part.inline_data.data)

        # Create static audio folder
        audio_dir = Path("static/audio")
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Save audio file
        filename = f"tts_{uuid.uuid4().hex}_{voice_name.lower()}.wav"
        outpath = audio_dir / filename
        with open(outpath, "wb") as f:
            f.write(pcm_data)

        logger.info(f"TTS audio generated successfully: {outpath}")
        return f"/static/audio/{filename}"

    except Exception as e:
        logger.error(f"Error in Gemini TTS: {str(e)}", exc_info=True)
        return ""
