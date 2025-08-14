from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import logging

load_dotenv()

from utils.document_processor import DocumentProcessor
from utils.gemini_utils_optimized import GeminiAnalyzer
from utils.tts_utils import EnhancedTTS
from utils.gemini_chatbot import ChatbotHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Legal Document Analyzer (Optimized)", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class EntityItem(BaseModel):
    type: str
    value: str


class ClauseItem(BaseModel):
    clause_number: int
    original_text: str
    simplified_text: Optional[str] = None


class AnalyzeResponse(BaseModel):
    doc_type: str
    doc_subtype: str
    confidence: float
    entities: List[EntityItem]
    clauses: List[ClauseItem]
    clause_entities: Dict[int, List[EntityItem]]
    tts_paths: Dict[str, str]
    metadata: Dict[str, Any]
    summary: Optional[str] = None
    key_points: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    action_items: Optional[List[str]] = None
    translation: Optional[str] = None
    error: Optional[str] = None


class ChatRequest(BaseModel):
    query: str
    analysis_data: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    status: str = "success"


# Initialize global chatbot instance
chatbot = ChatbotHandler()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    file: UploadFile = File(...),
    translate_to: Optional[str] = Form(None),
    tts: Optional[bool] = Form(False),
    tts_voice: Optional[str] = Form("kore"),
    language: Optional[str] = Form("english"),
    include_summary: Optional[bool] = Form(True),
):
    try:
        data = await file.read()
        
        # Extract once to reuse and avoid duplication
        extracted_text = await DocumentProcessor._extract_text(data, file.filename)

        # Normalize voice
        if isinstance(tts_voice, str):
            tts_voice = tts_voice.lower()

        # Process document with enhanced features
        result = await DocumentProcessor.process_document(
            file_bytes=data,
            filename=file.filename,
            language=language,
            generate_tts=tts,
            tts_voice=tts_voice,
            pre_extracted_text=extracted_text,
        )
        
        # Check for errors
        if "error" in result and result["error"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Get additional analysis from Gemini if needed
        summary = None
        key_points = None
        risks = None
        action_items = None
        if include_summary:
            gemini_analysis = await GeminiAnalyzer.analyze_document(extracted_text, language)
            summary = gemini_analysis.get("summary")
            key_points = gemini_analysis.get("key_points")
            risks = gemini_analysis.get("risks")
            action_items = gemini_analysis.get("action_items")
        
        # Handle translation
        translation = None
        if translate_to and include_summary:
            translation = await GeminiAnalyzer.translate_text(
                (summary or "") + "\n" + "\n".join(key_points or []),
                translate_to
            )
        
        return AnalyzeResponse(
            doc_type=result["doc_type"],
            doc_subtype=result["doc_subtype"],
            confidence=result["confidence"],
            entities=result["entities"],
            clauses=result["clauses"],
            clause_entities=result["clause_entities"],
            tts_paths=result["tts_paths"],
            metadata=result["metadata"],
            summary=summary,
            key_points=key_points,
            risks=risks,
            action_items=action_items,
            translation=translation
        )
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Handle chat queries using Gemini Flash 1.5"""
    try:
        response = await chatbot.get_response(
            user_query=request.query,
            analysis_data=request.analysis_data
        )
        return ChatResponse(response=response, status="success")
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return ChatResponse(
            response="I apologize, but I'm having trouble processing your request right now. Please try again later.",
            status="error"
        )


@app.post("/tts")
async def tts_endpoint(
    text: str = Form(...), 
    voice: Optional[str] = Form("kore"), 
    language: Optional[str] = Form("english")
):
    try:
        path = await EnhancedTTS.generate_tts(text, language, voice)
        if path:
            return FileResponse(path, media_type="audio/wav", filename=os.path.basename(path))
        else:
            raise HTTPException(status_code=500, detail="TTS generation failed")
    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/voices")
async def get_available_voices():
    """Get available TTS voices."""
    try:
        voices = await EnhancedTTS.get_available_voices()
        return {"voices": voices}
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-clauses")
async def analyze_clauses(
    clause_text: str = Form(...),
    language: Optional[str] = Form("english")
):
    """Analyze specific clauses with detailed breakdown."""
    try:
        result = await DocumentProcessor.analyze_clause_specific(clause_text, language)
        return result
    except Exception as e:
        logger.error(f"Clause analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


## (Removed duplicate /chat endpoint above)


@app.post("/chat/clear")
async def clear_chat_history():
    """Clear the chat history"""
    try:
        chatbot.clear_chat_history()
        return {"message": "Chat history cleared", "status": "success"}
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        return {"message": f"Error clearing history: {e}", "status": "error"}


@app.get("/chat/history")
async def get_chat_history():
    """Get the current chat history"""
    try:
        history = chatbot.get_chat_history()
        return {"history": history, "status": "success"}
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return {"history": [], "status": "error", "message": str(e)}


@app.get("/chat/status")
async def get_chatbot_status():
    """Get chatbot status and configuration"""
    try:
        status = chatbot.get_status()
        return {"chatbot": status, "status": "success"}
    except Exception as e:
        logger.error(f"Error getting chatbot status: {e}")
        return {"chatbot": {"status": "error"}, "status": "error", "message": str(e)}


@app.get("/health")
async def health_check():
    """Health check endpoint with chatbot status"""
    try:
        chatbot_status = chatbot.get_status()
        return {
            "status": "healthy",
            "message": "Legal Document Analyzer is running!",
            "chatbot": chatbot_status
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "healthy",
            "message": "Legal Document Analyzer is running!",
            "chatbot": {"status": "error", "error": str(e)}
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)