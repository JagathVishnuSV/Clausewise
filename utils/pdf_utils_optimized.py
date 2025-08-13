import io
import asyncio
from typing import List, Dict, Any
from pypdf import PdfReader
import logging

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Optimized PDF processor with chunked processing for large documents."""
    
    @staticmethod
    async def extract_text_chunked(file_bytes: bytes, chunk_size: int = 5, progress_callback=None) -> str:
        """Extract text from PDF with chunked processing and progress tracking."""
        try:
            with io.BytesIO(file_bytes) as buf:
                reader = PdfReader(buf)
                total_pages = len(reader.pages)
                
                if total_pages <= chunk_size:
                    # Small document - process all at once
                    texts = []
                    for page in reader.pages:
                        text = page.extract_text()
                        if text and text.strip():
                            texts.append(text.strip())
                    return "\n\n".join(texts).strip()
                
                # Large document - process in chunks
                texts = []
                for i in range(0, total_pages, chunk_size):
                    chunk_texts = []
                    end_page = min(i + chunk_size, total_pages)
                    
                    for page_num in range(i, end_page):
                        try:
                            page = reader.pages[page_num]
                            text = page.extract_text()
                            if text and text.strip():
                                chunk_texts.append(text.strip())
                        except Exception as e:
                            logger.warning(f"Error on page {page_num + 1}: {e}")
                            continue
                    
                    texts.extend(chunk_texts)
                    
                    # Progress callback
                    if progress_callback:
                        progress = min((i + chunk_size) / total_pages * 100, 100)
                        await progress_callback(progress)
                    
                    # Prevent blocking
                    await asyncio.sleep(0.05)
                
                return "\n\n".join(texts).strip()
                
        except Exception as e:
            logger.error(f"PDF processing error: {e}")
            return ""
    
    @staticmethod
    def get_document_info(file_bytes: bytes) -> Dict[str, Any]:
        """Get PDF metadata."""
        try:
            with io.BytesIO(file_bytes) as buf:
                reader = PdfReader(buf)
                return {
                    "pages": len(reader.pages),
                    "size_kb": len(file_bytes) / 1024,
                    "encrypted": reader.is_encrypted,
                    "metadata": reader.metadata
                }
        except Exception as e:
            logger.error(f"Error getting PDF info: {e}")
            return {"pages": 0, "size_kb": 0, "encrypted": False, "metadata": {}}
    
    @staticmethod
    async def extract_with_metadata(file_bytes: bytes, progress_callback=None) -> Dict[str, Any]:
        """Extract text and metadata together."""
        info = PDFProcessor.get_document_info(file_bytes)
        text = await PDFProcessor.extract_text_chunked(file_bytes, progress_callback=progress_callback)
        
        return {
            "text": text,
            "metadata": info,
            "document_type": PDFProcessor.classify_document_type(text)
        }
    
    @staticmethod
    def classify_document_type(text: str) -> str:
        """Classify document type based on content."""
        text_lower = text.lower()
        
        # English classifications
        if any(word in text_lower for word in ['contract', 'agreement', 'terms']):
            return "Contract/Agreement"
        elif any(word in text_lower for word in ['invoice', 'bill', 'payment']):
            return "Invoice/Bill"
        elif any(word in text_lower for word in ['resume', 'cv', 'curriculum vitae']):
            return "Resume/CV"
        elif any(word in text_lower for word in ['report', 'analysis', 'summary']):
            return "Report/Analysis"
        elif any(word in text_lower for word in ['policy', 'procedure', 'guideline']):
            return "Policy/Procedure"
        
        # Tamil classifications
        elif any(word in text_lower for word in ['ஒப்பந்தம்', 'ஒப்பந்த', 'உடன்படிக்கை']):
            return "ஒப்பந்தம்/உடன்படிக்கை"
        elif any(word in text_lower for word in ['இன்வாய்ஸ்', 'பில்', 'கட்டணம்']):
            return "இன்வாய்ஸ்/பில்"
        elif any(word in text_lower for word in ['ரெசுமே', 'சிவி', 'வேலை விண்ணப்பம்']):
            return "ரெசுமே/சிவி"
        elif any(word in text_lower for word in ['அறிக்கை', 'பகுப்பாய்வு', 'சுருக்கம்']):
            return "அறிக்கை/பகுப்பாய்வு"
        
        return "General Document"
    
    @staticmethod
    def extract_clauses(text: str) -> List[Dict[str, str]]:
        """Extract clauses from legal document text."""
        clauses = []
        
        if not text or not text.strip():
            return clauses
        
        # Split by common clause patterns
        import re
        
        # Pattern 1: Numbered clauses (1., 2., etc.)
        numbered_pattern = r'^\s*(\d+)\.\s*(.+?)(?=^\s*\d+\.|$)'
        numbered_matches = re.findall(numbered_pattern, text, re.MULTILINE | re.DOTALL)
        
        for match in numbered_matches:
            clause_num = int(match[0])
            clause_text = match[1].strip()
            if clause_text and len(clause_text) > 10:  # Minimum length filter
                clauses.append({
                    'clause_number': clause_num,
                    'original_text': clause_text
                })
        
        # Pattern 2: Roman numeral clauses (I., II., etc.)
        roman_pattern = r'^\s*([IVX]+)\.\s*(.+?)(?=^\s*[IVX]+\.|$)'
        roman_matches = re.findall(roman_pattern, text, re.MULTILINE | re.DOTALL)
        
        for i, match in enumerate(roman_matches, start=len(clauses) + 1):
            clause_text = match[1].strip()
            if clause_text and len(clause_text) > 10:
                clauses.append({
                    'clause_number': i,
                    'original_text': clause_text
                })
        
        # Pattern 3: Lettered clauses (a., b., etc.)
        letter_pattern = r'^\s*([a-z])\.\s*(.+?)(?=^\s*[a-z]\.|$)'
        letter_matches = re.findall(letter_pattern, text, re.MULTILINE | re.DOTALL)
        
        for i, match in enumerate(letter_matches, start=len(clauses) + 1):
            clause_text = match[1].strip()
            if clause_text and len(clause_text) > 10:
                clauses.append({
                    'clause_number': i,
                    'original_text': clause_text
                })
        
        # Pattern 4: Paragraph-based splitting (if no numbered clauses found)
        if not clauses:
            paragraphs = text.split('\n\n')
            for i, para in enumerate(paragraphs, 1):
                para = para.strip()
                if para and len(para) > 50:  # Longer paragraphs only
                    clauses.append({
                        'clause_number': i,
                        'original_text': para
                    })
        
        # Sort by clause number
        clauses.sort(key=lambda x: x['clause_number'])
        
        return clauses
