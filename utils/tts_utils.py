import asyncio
import edge_tts
import uuid
from pathlib import Path
import logging
from typing import Optional, Dict, Any
import time

logger = logging.getLogger(__name__)

class EnhancedTTS:
    """Enhanced TTS using edge-tts for high-quality speech generation."""
    
    # Voice mappings for different languages
    VOICE_MAPPING = {
        "english": {
            "kore": "en-US-KoreNeural",
            "charon": "en-US-CharonNeural",
            "fenrir": "en-US-FenrirNeural",
            "jenny": "en-US-JennyNeural",
            "guy": "en-US-GuyNeural"
        },
        "tamil": {
            "kore": "ta-IN-PallaviNeural",
            "charon": "ta-IN-ValluvarNeural"
        },
        "spanish": {
            "kore": "es-ES-ElviraNeural",
            "charon": "es-ES-AlvaroNeural"
        },
        "french": {
            "kore": "fr-FR-DeniseNeural",
            "charon": "fr-FR-HenriNeural"
        },
        "german": {
            "kore": "de-DE-KatjaNeural",
            "charon": "de-DE-ConradNeural"
        },
        "hindi": {
            "kore": "hi-IN-SwaraNeural",
            "charon": "hi-IN-MadhurNeural"
        }
    }
    
    @staticmethod
    async def generate_tts(
        text: str, 
        language: str = "english", 
        voice_name: str = "kore",
        rate: str = "+0%",
        volume: str = "+0%"
    ) -> str:
        """Generate TTS audio using edge-tts with retry logic."""
        try:
            if not text or not text.strip():
                return ""
            
            # Get voice for the specified language and voice name
            voices = EnhancedTTS.VOICE_MAPPING.get(language, EnhancedTTS.VOICE_MAPPING["english"])
            voice = voices.get(voice_name.lower(), voices.get("kore", "en-US-KoreNeural"))
            
            # Limit text length to prevent issues
            max_length = 3000
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            # Generate unique filename
            filename = f"tts_{uuid.uuid4().hex}_{voice_name.lower()}.wav"
            output_path = Path("static/audio") / filename
            output_path.parent.mkdir(exist_ok=True)
            
            # Retry logic for TTS generation
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Generate TTS
                    communicate = edge_tts.Communicate(
                        text, 
                        voice,
                        rate=rate,
                        volume=volume
                    )
                    
                    await communicate.save(str(output_path))
                    
                    # Verify file was created and has content
                    if output_path.exists() and output_path.stat().st_size > 0:
                        return f"/static/audio/{filename}"
                    else:
                        logger.warning(f"TTS file created but empty, attempt {attempt + 1}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1)
                            continue
                        else:
                            return ""
                            
                except Exception as e:
                    logger.warning(f"TTS generation attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)  # Wait before retry
                        continue
                    else:
                        raise e
            
            return ""
            
        except Exception as e:
            logger.error(f"TTS generation error after all retries: {e}")
            return ""
    
    @staticmethod
    async def generate_clause_audio(
        clauses: list, 
        language: str = "english", 
        voice_name: str = "kore"
    ) -> Dict[int, str]:
        """Generate TTS audio for each clause with rate limiting."""
        clause_audio = {}
        
        for i, clause in enumerate(clauses):
            clause_num = clause.get('clause_number', 0)
            simplified_text = clause.get('simplified_text', '')
            
            if simplified_text:
                try:
                    audio_path = await EnhancedTTS.generate_tts(
                        simplified_text, 
                        language, 
                        voice_name
                    )
                    if audio_path:
                        clause_audio[clause_num] = audio_path
                    
                    # Rate limiting between clause audio generation
                    if i < len(clauses) - 1:
                        await asyncio.sleep(0.5)
                        
                except Exception as e:
                    logger.error(f"Error generating audio for clause {clause_num}: {e}")
                    continue
        
        return clause_audio
    
    @staticmethod
    async def generate_summary_audio(
        summary: str, 
        language: str = "english", 
        voice_name: str = "kore"
    ) -> str:
        """Generate TTS audio for document summary."""
        return await EnhancedTTS.generate_tts(summary, language, voice_name)
    
    @staticmethod
    async def get_available_voices() -> Dict[str, Dict[str, str]]:
        """Get available voices for different languages."""
        return EnhancedTTS.VOICE_MAPPING
    
    @staticmethod
    async def list_voices() -> list:
        """List all available edge-tts voices."""
        try:
            voices = await edge_tts.list_voices()
            return voices
        except Exception as e:
            logger.error(f"Error listing voices: {e}")
            return []
    
    @staticmethod
    async def test_voice_availability() -> bool:
        """Test if edge-tts is working properly."""
        try:
            test_text = "Hello, this is a test."
            test_voice = "en-US-KoreNeural"
            
            communicate = edge_tts.Communicate(test_text, test_voice)
            
            # Try to get audio data without saving
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            return len(audio_data) > 0
            
        except Exception as e:
            logger.error(f"Voice availability test failed: {e}")
            return False
