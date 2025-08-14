import os
import asyncio
from typing import Dict, Any, List, Optional
from utils.pdf_utils_optimized import PDFProcessor
from utils.docx_utils import DOCXProcessor
from utils.ner_utils import ner_extractor
from utils.simplify_utils import ClauseSimplifier
from utils.doc_type_classifier import DocumentTypeClassifier
from utils.granite_utils import granite_simple_doc_type
from utils.tts_utils import EnhancedTTS
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Unified document processor for multiple formats with enhanced features and chunking."""
    
    # Rate limiting configuration
    PROCESSING_DELAY = 1.0  # Seconds between major processing steps
    MAX_SIMPLIFIED_CLAUSES = 48  # Allow more clauses to be simplified for speed perception
    
    @staticmethod
    async def process_document(
        file_bytes: bytes,
        filename: str,
        language: str = "english",
        generate_tts: bool = False,
        tts_voice: str = "kore",
        pre_extracted_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process document and return comprehensive analysis with chunking."""
        try:
            logger.info(f"Starting document processing for {filename}")
            
            # Extract text based on file type (skip if provided)
            text = pre_extracted_text if (pre_extracted_text is not None and pre_extracted_text.strip()) else await DocumentProcessor._extract_text(file_bytes, filename)
            
            if not text or not text.strip():
                return {
                    "error": "No extractable text found in document",
                    "doc_type": "Unknown",
                    "entities": [],
                    "clauses": [],
                    "summary": "",
                    "key_points": [],
                    "risks": [],
                    "action_items": []
                }
            
            logger.info(f"Extracted {len(text)} characters of text")
            
            # Extract clauses
            clauses = PDFProcessor.extract_clauses(text)
            logger.info(f"Extracted {len(clauses)} clauses")
            
            # Classify document type (prefer Granite/keywords to avoid Gemini limits)
            # Removed PROCESSING_DELAY
            try:
                granite_label = await granite_simple_doc_type(text)
                doc_classification = {
                    "doc_type": granite_label or "General",
                    "subtype": "General",
                    "confidence": 0.6 if granite_label else 0.3
                }
            except Exception:
                # Fallback to keyword-only classification (no external calls)
                doc_classification = DocumentTypeClassifier.classify_by_keywords(text)
            logger.info(f"Document classified as: {doc_classification['doc_type']}")
            
            # Extract entities from full document
            entities = ner_extractor.extract_entities(text)
            logger.info(f"Extracted {len(entities)} entities")
            
            # Extract entities by clause
            clause_entities = ner_extractor.extract_entities_by_clause(clauses)
            logger.info(f"Extracted entities for {len(clause_entities)} clauses")
            
            # Simplify clauses with prioritization: first N clauses + any clause under 160 chars (fast) 
            priority: List[Dict[str, Any]] = []
            fallback_tail: List[Dict[str, Any]] = []
            for idx, c in enumerate(clauses):
                text = c.get('original_text', '') or ''
                if idx < DocumentProcessor.MAX_SIMPLIFIED_CLAUSES or len(text) <= 160:
                    priority.append(c)
                else:
                    c_copy = dict(c)
                    c_copy['simplified_text'] = ClauseSimplifier._heuristic_plainify(text)
                    fallback_tail.append(c_copy)
            head = await ClauseSimplifier.simplify_clauses(priority, language)
            simplified_clauses = head + fallback_tail
            logger.info(f"Simplified {len(simplified_clauses)} clauses")
            
            # Generate TTS if requested
            tts_paths = {}
            if generate_tts:
                logger.info("Generating TTS audio...")
                try:
                    # Generate audio for each clause
                    clause_audio = await EnhancedTTS.generate_clause_audio(
                        simplified_clauses, language, tts_voice
                    )
                    tts_paths.update(clause_audio)
                    logger.info(f"Generated audio for {len(clause_audio)} clauses")
                    
                    # Generate audio for summary
                    summary_audio = await EnhancedTTS.generate_summary_audio(
                        "Document analysis complete", language, tts_voice
                    )
                    if summary_audio:
                        tts_paths["summary"] = summary_audio
                        logger.info("Generated summary audio")
                        
                except Exception as e:
                    logger.error(f"TTS generation failed: {e}")
                    # Continue without TTS if it fails
            
            # Prepare response
            result = {
                "doc_type": doc_classification.get("doc_type", "Unknown"),
                "doc_subtype": doc_classification.get("subtype", "Unknown"),
                "confidence": doc_classification.get("confidence", 0.0),
                "entities": entities,
                "clauses": simplified_clauses,
                "clause_entities": clause_entities,
                "tts_paths": tts_paths if generate_tts else {},
                "metadata": {
                    "filename": filename,
                    "language": language,
                    "total_clauses": len(clauses),
                    "total_entities": len(entities),
                    "processing_time": "completed"
                }
            }
            
            logger.info("Document processing completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return {
                "error": str(e),
                "doc_type": "Unknown",
                "entities": [],
                "clauses": [],
                "summary": "",
                "key_points": [],
                "risks": [],
                "action_items": []
            }
    
    @staticmethod
    async def _extract_text(file_bytes: bytes, filename: str) -> str:
        """Extract text from different file formats."""
        try:
            if filename.lower().endswith('.pdf'):
                return await PDFProcessor.extract_text_chunked(file_bytes)
            elif filename.lower().endswith('.docx'):
                return DOCXProcessor.extract_text(file_bytes)
            elif filename.lower().endswith('.txt'):
                return file_bytes.decode('utf-8', errors='ignore')
            else:
                # Try to decode as text
                return file_bytes.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {e}")
            return ""
    
    @staticmethod
    async def get_document_info(file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Get basic document information."""
        try:
            if filename.lower().endswith('.pdf'):
                return PDFProcessor.get_document_info(file_bytes)
            elif filename.lower().endswith('.docx'):
                return DOCXProcessor.get_document_info(file_bytes)
            else:
                return {
                    "filename": filename,
                    "file_type": "Unknown",
                    "page_count": 1,
                    "file_size": len(file_bytes)
                }
        except Exception as e:
            logger.error(f"Error getting document info: {e}")
            return {
                "filename": filename,
                "file_type": "Unknown",
                "page_count": 0,
                "file_size": len(file_bytes)
            }
    
    @staticmethod
    async def analyze_clause_specific(
        clause_text: str,
        language: str = "english"
    ) -> Dict[str, Any]:
        """Analyze a specific clause in detail."""
        try:
            # Extract entities from the clause
            entities = ner_extractor.extract_entities(clause_text)
            
            # Simplify the clause
            simplified_text = await ClauseSimplifier.simplify_clause(clause_text, language)
            
            return {
                "original_text": clause_text,
                "simplified_text": simplified_text,
                "entities": entities,
                "language": language
            }
            
        except Exception as e:
            logger.error(f"Error analyzing clause: {e}")
            return {
                "original_text": clause_text,
                "simplified_text": clause_text,
                "entities": [],
                "language": language,
                "error": str(e)
            }
