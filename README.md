# ClauseWise - Enhanced Legal Document Analyzer

## Overview

ClauseWise is a comprehensive legal document analysis platform that leverages advanced AI models to extract, analyze, and provide insights from legal documents. The enhanced version includes clause simplification, named entity recognition, document classification, multi-format support, and enhanced audio narration capabilities through an intuitive web interface.

## 🚀 Features

### Core Analysis
- **AI-Powered Document Analysis**: Extract and analyze legal documents using state-of-the-art language models
- **Document Type Classification**: Automatically detect contract types (NDA, Employment, Lease, Service Agreement, etc.)
- **Named Entity Recognition**: Extract Parties, Dates, Monetary Values, Obligations, Legal Terms/Keywords, and Legal Context (e.g., governing law, jurisdiction)
- **Clause Extraction & Simplification**: Split into clauses and rewrite each into layman-friendly language (batched, chunked, rate-limited)
- **Multi-format Support**: PDF, DOCX, and TXT document processing

### Enhanced Capabilities
- **Clause Extraction**: Intelligent breakdown of documents into numbered clauses or paragraphs
- **Entity Mapping**: Link entities to specific clauses for detailed analysis
- **Audio Narration**: High-quality TTS for document summaries and individual clauses (Edge TTS)
- **Multi-language Support**: English and Tamil with extensible architecture

### Advanced Processing
- **Confidence Scoring**: AI-powered classification with confidence levels
- **Structured Output**: Comprehensive JSON schema compatible with UI & audio pipeline
- **Rate-Limit Resilience**: Gemini calls are chunked, globally serialized with jitter, retried with backoff, and capped; circuit breaker with heuristic fallback
- **Granite/Keyword Fallback**: Uses IBM Granite or keyword rules for classification to reduce LLM pressure
- **Caching System**: Efficient audio file management and reuse
- **Error Handling**: Graceful fallbacks and robust error management

## 📁 Project Structure

```
ClauseWise/
├── app.py                 # Main Flask application (development version)
├── app_final.py          # Production-ready FastAPI application with optimizations
├── app_optimized.py      # Performance-optimized version
├── requirements.txt      # Python dependencies
├── HF_TOKEN_SETUP.md   # Hugging Face token configuration guide
├── README.md          # This documentation file
│
├── data/               # Sample data directory
│   └── sample_contract.pdf  # Example contract for testing
│
├── static/            # Static web assets
│   ├── audio/        # Generated TTS audio files
│   │   └── *.wav     
│   └── js/           # JavaScript files
│       ├── app.js    # Main application JavaScript
│       └── languages.js  # Language configuration
│
├── templates/        # HTML templates
│   └── index.html    # Main web interface
│
└── utils/            # Utility modules
    ├── async_client.py         # Async HTTP client utilities
    ├── gemini_utils_optimized.py  # Google Gemini API integration
    ├── gemini_utils.py         # Google Gemini API integration
    ├── granite_utils.py        # IBM Granite model utilities
    ├── hf_auth_utils.py        # Hugging Face authentication
    ├── pdf_utils_optimized.py   # Optimized PDF processing
    ├── pdf_utils.py          # PDF processing utilities
    ├── ner_utils.py           # Named Entity Recognition
    ├── simplify_utils.py      # Clause simplification
    ├── doc_type_classifier.py # Document type classification
    ├── docx_utils.py          # DOCX file processing
    ├── tts_utils.py           # Enhanced TTS utilities
    └── document_processor.py  # Unified document processor
```

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern, fast Python web framework for APIs
- **Google Gemini API**: Primary AI model for contract analysis
- **IBM Granite**: Alternative AI model option
- **PyPDF2**: PDF text extraction and processing
- **AsyncIO**: Asynchronous processing for improved performance

### Frontend
- **HTML5/CSS3**: Modern web standards
- **JavaScript (ES6+)**: Interactive frontend functionality
- **Responsive Design**: Mobile-friendly interface

### Audio Processing
- **Edge TTS**: High-quality speech synthesis with multiple voices
- **WAV Audio Format**: High-quality audio output saved under `static/audio/`

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git (for version control)

### 1. Clone the Repository
```bash
git clone [repository-url]
cd ClauseWise
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Keys
Follow the instructions in `HF_TOKEN_SETUP.md` to set up your API keys:
- Google Gemini API key
- Hugging Face token (if using Granite models)

### 4. Run the Application

#### Development Mode (Flask)
```bash
python app.py
```

#### Production Mode (FastAPI)
```bash
python -m uvicorn app_final:app --host 0.0.0.0 --port 8000
```

#### Optimized Mode
```bash
python app_optimized.py
```

The application will be available at `http://localhost:8000`.

## 📖 Usage Guide

### 1. Upload Contract
- Navigate to the web interface at `http://localhost:8000`
- Upload a PDF contract file using the file upload button
- Supported formats: PDF

### 2. Analyze Contract
- Click "Analyze Contract" to process the uploaded document
- The AI will extract and analyze key clauses
- Results appear in real-time as the analysis progresses

### 3. Audio Narration
- Click "Play Summary" to hear an audio narration of the analysis
- Audio is generated in Korean language
- Multiple audio files are cached for quick playback

### 4. Interactive Features
- View detailed clause analysis
- Get risk assessments for different contract sections
- Export analysis results

## 🔍 API Endpoints

### Core Endpoints
- `POST /upload`: Upload PDF contract file
- `POST /analyze`: Analyze uploaded contract
- `GET /audio/<filename>`: Retrieve generated audio files
- `GET /`: Serve main web interface
- `GET /health`: Health check endpoint

## 🎯 Key Components

### 1. PDF Processing (`utils/pdf_utils_optimized.py`)
- Extracts text from PDF documents
- Handles various PDF formats and structures
- Optimized for legal document processing
- Chunked processing for large documents

### 2. AI Analysis (`utils/gemini_utils_optimized.py`)
- Integrates with Google Gemini API (gemini-2.0-flash-lite)
- Chunked requests with global serialization, jitter, and backoff retry
- Limits large-document summary to first 10k characters
- Translation and TTS helpers

### 3. Audio Generation (`utils/tts_utils.py`)
- Uses Edge TTS with retries and file verification
- Caches audio files under `static/audio` and exposes URLs for playback
- Configurable voice options mapped by language

### 4. Web Interface (`templates/index.html`)
- Clean, intuitive user interface
- Real-time progress updates
- Responsive design for all devices
- JavaScript-based file upload and progress tracking

## 🚀 Performance Optimizations

### In `app_optimized.py`:
- **Async Processing**: Non-blocking I/O operations
- **Connection Pooling**: Efficient API connections
- **Caching**: Audio file and analysis result caching
- **Error Handling**: Robust error recovery mechanisms

### In `app_final.py`:
- **Production Ready**: Optimized for deployment
- **Security Enhancements**: Input validation and sanitization
- **Logging**: Comprehensive application logging
- **Monitoring**: Performance metrics collection
- **Typed Responses**: Pydantic models for entities and clauses prevent schema errors

## 🔐 Security Features

- Input validation for all file uploads
- API key protection and secure storage
- XSS prevention in web interface
- Rate limiting for API endpoints

## 🐛 Troubleshooting

### Common Issues

1. **API Key Errors**
   - Ensure API keys are correctly set in environment variables
   - Check `HF_TOKEN_SETUP.md` for configuration steps

2. **PDF/DOCX Processing Issues**
   - Verify PDF is not password protected
   - Ensure PDF contains selectable text (not scanned images)
   - For DOCX, ensure the file is not corrupted; DOCX parsing is synchronous

3. **Audio Generation Failures**
   - Check internet connectivity; Edge TTS requires network access
   - Retry; the module has built-in retries and file-size verification

### Handling Rate Limits (Gemini)
- Use the default settings (flash-lite, chunk size 3k, spacing ~3.5s with jitter)
- Clause simplification batches of 1 with long delays (8–12s)
- Cap simplified clauses per document (default 16)
- Circuit breaker switches to heuristic simplification on repeated failures

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google for Gemini API
- IBM for Granite models
- FastAPI community for the modern web framework
- Contributors and testers

## 📞 Support

For support, email [support-email] or create an issue in the GitHub repository.
