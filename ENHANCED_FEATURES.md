# ClauseWise Enhanced Features

## Overview

ClauseWise has been enhanced with comprehensive legal document analysis capabilities including clause simplification, named entity recognition, document classification, multi-format support, and enhanced audio narration.

## 🚀 New Features

### 1. Clause Simplification
- **Purpose**: Automatically rewrite legal clauses into layman-friendly language
- **Implementation**: Uses Gemini AI for intelligent simplification
- **Output**: Each clause gets both original and simplified versions
- **Languages**: Supports English and Tamil

### 2. Named Entity Recognition (NER)
- **Purpose**: Extract key entities from legal documents
- **Entity Types**:
  - Parties (individuals, companies)
  - Dates
  - Obligations
  - Monetary values
  - Legal terms
- **Implementation**: Uses HuggingFace transformers (dslim/bert-base-NER) + custom regex patterns
- **Output**: Structured entity data with confidence scores

### 3. Clause Extraction and Breakdown
- **Purpose**: Split documents into individual clauses
- **Patterns Supported**:
  - Numbered clauses (1., 2., etc.)
  - Roman numerals (I., II., etc.)
  - Lettered clauses (a., b., etc.)
  - Paragraph-based splitting (fallback)
- **Output**: Mapped clause_number → clause_text

### 4. Document Type Classification
- **Purpose**: Automatically detect contract type
- **Types Supported**:
  - NDA (Non-Disclosure Agreement)
  - Employment Contract
  - Service Agreement
  - Lease Agreement
  - Purchase Agreement
  - Partnership Agreement
  - License Agreement
  - Settlement Agreement
  - Terms of Service
  - Privacy Policy
- **Implementation**: Gemini AI classifier with confidence scoring

### 5. Multi-format Document Support
- **Formats Supported**:
  - PDF (using PyPDF2)
  - DOCX (using python-docx)
  - TXT (simple text reading)
- **Features**: Metadata extraction, text processing, format detection

### 6. Enhanced Audio Narration
- **Purpose**: Generate high-quality speech for document summaries
- **Technology**: edge-tts (replacing gTTS)
- **Features**:
  - Multiple voice options per language
  - Per-clause audio generation
  - Cached audio files
  - Multiple language support

## 📊 Output Schema

```json
{
  "doc_type": "NDA",
  "doc_subtype": "Confidentiality Agreement",
  "confidence": 0.95,
  "entities": [
    {
      "type": "Party",
      "value": "ABC Corp",
      "confidence": 0.9,
      "start": 150,
      "end": 158
    },
    {
      "type": "Date",
      "value": "2025-08-10",
      "confidence": 0.95,
      "start": 200,
      "end": 210
    },
    {
      "type": "Obligation",
      "value": "Maintain confidentiality",
      "confidence": 0.8,
      "start": 300,
      "end": 320
    },
    {
      "type": "Monetary Value",
      "value": "$50,000",
      "confidence": 0.9,
      "start": 400,
      "end": 408
    }
  ],
  "clauses": [
    {
      "clause_number": 1,
      "original_text": "The party agrees to maintain confidentiality...",
      "simplified_text": "You must keep all information secret."
    }
  ],
  "clause_entities": {
    1: [
      {
        "type": "Obligation",
        "value": "maintain confidentiality",
        "confidence": 0.8
      }
    ]
  },
  "tts_paths": {
    1: "/static/audio/tts_abc123_kore.wav",
    "summary": "/static/audio/tts_summary_kore.wav"
  },
  "metadata": {
    "filename": "contract.pdf",
    "language": "english",
    "total_clauses": 5,
    "total_entities": 12
  }
}
```

## 🛠️ New Modules

### utils/ner_utils.py
- Named entity recognition using HuggingFace transformers
- Custom regex patterns for legal entities
- Entity type mapping and confidence scoring

### utils/simplify_utils.py
- Clause simplification using Gemini AI
- Language-specific prompts
- Batch processing capabilities

### utils/doc_type_classifier.py
- Document type classification using Gemini AI
- Confidence scoring and subtype detection
- Fallback keyword-based classification

### utils/docx_utils.py
- DOCX file processing using python-docx
- Text extraction from paragraphs and tables
- Metadata extraction

### utils/tts_utils.py
- Enhanced TTS using edge-tts
- Multiple voice support per language
- Audio file caching and management

### utils/document_processor.py
- Unified document processing pipeline
- Multi-format support
- Integration of all enhanced features

## 🔧 API Endpoints

### Enhanced /analyze Endpoint
```http
POST /analyze
Content-Type: multipart/form-data

Parameters:
- file: Document file (PDF/DOCX/TXT)
- translate_to: Target language (optional)
- tts: Enable TTS (true/false)
- tts_voice: Voice selection (kore/charon/fenrir)
- language: Document language (english/tamil)
```

### New Endpoints

#### GET /voices
Returns available TTS voices for different languages.

#### POST /analyze-clauses
Analyze specific clauses with detailed breakdown.

#### POST /tts (Enhanced)
Generate TTS using edge-tts with multiple voice options.

## 🎨 Frontend Enhancements

### New UI Sections
1. **Document Type**: Shows classification with confidence
2. **Extracted Entities**: Grouped by entity type
3. **Document Clauses**: Original + simplified text
4. **Enhanced Audio**: Multiple audio players for clauses

### Features
- Entity visualization with type grouping
- Clause-by-clause display with entities
- Multiple audio players for different sections
- Responsive design for all screen sizes

## 🚀 Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Variables
```bash
GEMINI_API_KEY=your_gemini_api_key
```

### 3. Run the Application
```bash
python app_final.py
```

### 4. Test Enhanced Features
```bash
python test_enhanced_features.py
```

## 📈 Performance Considerations

### Optimization Features
- **Chunked Processing**: Large documents processed in chunks
- **Caching**: TTS audio files cached for reuse
- **Async Processing**: Non-blocking operations
- **Error Handling**: Graceful fallbacks for all features

### Memory Management
- Text length limits for TTS generation
- Streaming processing for large documents
- Efficient entity extraction with confidence filtering

## 🔍 Testing

### Test Script
Run `test_enhanced_features.py` to verify all features work correctly.

### Test Coverage
- Document type classification
- Entity extraction
- Clause simplification
- TTS generation
- Full document processing pipeline

## 🎯 Use Cases

### Legal Professionals
- Quick contract analysis
- Entity extraction for due diligence
- Clause simplification for client communication

### Business Users
- Understanding complex legal documents
- Audio summaries for accessibility
- Multi-language support

### Developers
- Extensible architecture
- API integration capabilities
- Custom entity extraction

## 🔮 Future Enhancements

### Planned Features
- Custom NER model training
- More document formats (RTF, ODT)
- Advanced clause analysis
- Contract comparison tools
- Integration with legal databases

### Performance Improvements
- GPU acceleration for NER
- Distributed processing
- Advanced caching strategies
- Real-time collaboration features

## 📝 License

This enhanced version maintains the original license while adding significant new capabilities for legal document analysis and processing.
