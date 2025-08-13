from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional
import os
from pathlib import Path

# Load env vars
load_dotenv()

from utils.pdf_utils import extract_text_from_pdf
from utils.gemini_utils import (
    gemini_structured_analysis,
    gemini_translate,
    gemini_tts,
)
from utils.granite_utils import granite_simple_doc_type

# FastAPI app setup
app = FastAPI(title="Legal Document Analyzer (Gemini + Granite)")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ----- Response Schema -----
class AnalyzeResponse(BaseModel):
    granite_doc_type: str
    detected_language: Optional[str]
    summary: str
    key_points: List[str]
    risks: List[str]
    action_items: List[str]
    translation: Optional[str] = None
    tts_path: Optional[str] = None

# ----- Routes -----
from fastapi import Request

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/analyze")
async def analyze_get():
    return {
        "message": "This endpoint only accepts POST requests. Use POST with multipart/form-data to upload files.",
        "method": "POST",
        "content_type": "multipart/form-data",
        "parameters": {
            "file": "Required - PDF or text file to analyze",
            "translate_to": "Optional - Target language for translation",
            "tts": "Optional - Boolean to enable text-to-speech",
            "tts_voice": "Optional - Voice name for TTS (Kore, Charon, Fenrir)"
        }
    }

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    file: UploadFile = File(...),
    translate_to: Optional[str] = Form(None),
    tts: Optional[bool] = Form(False),
    tts_voice: Optional[str] = Form("Kore"),
):
    data = await file.read()
    if file.filename.lower().endswith(".pdf"):
        text = extract_text_from_pdf(data)
    else:
        text = data.decode(errors="ignore")

    if not text.strip():
        raise HTTPException(status_code=400, detail="No extractable text.")

    # 1) Granite doc classification
    granite_label = await granite_simple_doc_type(text)

    # 2) Gemini analysis
    analysis = await gemini_structured_analysis(text)
    
    if not analysis:
        raise HTTPException(
            status_code=500, 
            detail="Failed to analyze document. Please check your API configuration."
        )

    # 3) Translation
    translation = None
    if translate_to:
        summary_text = analysis.get("summary", "")
        key_points_text = "\n".join(analysis.get("key_points", []))
        translation = await gemini_translate(
            summary_text + "\n" + key_points_text,
            translate_to,
        )

    # 4) TTS
    tts_path = None
    if tts:
        tts_path = await gemini_tts(analysis["summary"], voice_name=tts_voice)

    return AnalyzeResponse(
        granite_doc_type=granite_label,
        detected_language=analysis.get("detected_language"),
        summary=analysis["summary"],
        key_points=analysis["key_points"],
        risks=analysis["risks"],
        action_items=analysis["action_items"],
        translation=translation,
        tts_path=tts_path,
    )

@app.post("/tts")
async def tts_endpoint(text: str = Form(...), voice: Optional[str] = Form("Kore")):
    path = await gemini_tts(text, voice_name=voice)
    return FileResponse(path, media_type="audio/wav", filename=os.path.basename(path))

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Legal Document Analyzer is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)
