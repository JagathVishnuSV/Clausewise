#!/usr/bin/env python3
"""
Test script for enhanced ClauseWise features
"""

import asyncio
import os
from pathlib import Path

# Add the project root to Python path
import sys
sys.path.append(str(Path(__file__).parent))

from utils.document_processor import DocumentProcessor
from utils.ner_utils import ner_extractor
from utils.simplify_utils import ClauseSimplifier
from utils.doc_type_classifier import DocumentTypeClassifier
from utils.tts_utils import EnhancedTTS

async def test_enhanced_features():
    """Test all enhanced features."""
    print("🧪 Testing Enhanced ClauseWise Features")
    print("=" * 50)
    
    # Sample legal text for testing
    sample_text = """
    NON-DISCLOSURE AGREEMENT
    
    1. CONFIDENTIALITY OBLIGATIONS
    The receiving party shall maintain the confidentiality of all proprietary information disclosed by the disclosing party and shall not disclose such information to any third party without prior written consent.
    
    2. TERM AND TERMINATION
    This agreement shall remain in effect for a period of 5 years from the effective date of January 15, 2024. Either party may terminate this agreement with 30 days written notice.
    
    3. LIABILITY AND DAMAGES
    In the event of a breach of this agreement, the breaching party shall be liable for damages up to $50,000 USD. The parties agree to resolve disputes through binding arbitration in New York, NY.
    
    4. GOVERNING LAW
    This agreement shall be governed by the laws of the State of New York and any disputes shall be subject to the exclusive jurisdiction of the courts in New York County.
    """
    
    print("📄 Sample Legal Document:")
    print(sample_text)
    print("\n" + "=" * 50)
    
    # Test 1: Document Type Classification
    print("\n🔍 Test 1: Document Type Classification")
    try:
        doc_classification = await DocumentTypeClassifier.classify_document(sample_text)
        print(f"✅ Document Type: {doc_classification['doc_type']}")
        print(f"✅ Subtype: {doc_classification['subtype']}")
        print(f"✅ Confidence: {doc_classification['confidence']:.2%}")
    except Exception as e:
        print(f"❌ Document classification failed: {e}")
    
    # Test 2: Entity Extraction
    print("\n🏷️ Test 2: Named Entity Recognition")
    try:
        entities = ner_extractor.extract_entities(sample_text)
        print(f"✅ Found {len(entities)} entities:")
        for entity in entities[:10]:  # Show first 10
            print(f"   - {entity['type']}: {entity['value']}")
    except Exception as e:
        print(f"❌ Entity extraction failed: {e}")
    
    # Test 3: Clause Extraction and Simplification
    print("\n📝 Test 3: Clause Extraction and Simplification")
    try:
        from utils.pdf_utils_optimized import PDFProcessor
        clauses = PDFProcessor.extract_clauses(sample_text)
        print(f"✅ Extracted {len(clauses)} clauses")
        
        if clauses:
            simplified_clauses = await ClauseSimplifier.simplify_clauses(clauses[:2])  # Test first 2
            print("✅ Simplified clauses:")
            for clause in simplified_clauses:
                print(f"   Clause {clause['clause_number']}:")
                print(f"     Original: {clause['original_text'][:100]}...")
                print(f"     Simplified: {clause['simplified_text'][:100]}...")
    except Exception as e:
        print(f"❌ Clause processing failed: {e}")
    
    # Test 4: TTS Generation
    print("\n🔊 Test 4: Text-to-Speech Generation")
    try:
        # Test with a short text to avoid long generation times
        test_text = "This is a test of the enhanced TTS system."
        tts_path = await EnhancedTTS.generate_tts(test_text, "english", "kore")
        if tts_path:
            print(f"✅ TTS generated: {tts_path}")
        else:
            print("❌ TTS generation failed")
    except Exception as e:
        print(f"❌ TTS generation failed: {e}")
    
    # Test 5: Full Document Processing
    print("\n🔄 Test 5: Full Document Processing")
    try:
        # Create a mock file bytes object
        file_bytes = sample_text.encode('utf-8')
        
        result = await DocumentProcessor.process_document(
            file_bytes=file_bytes,
            filename="test_nda.txt",
            language="english",
            generate_tts=False  # Skip TTS for faster testing
        )
        
        print(f"✅ Document processed successfully")
        print(f"   - Document Type: {result['doc_type']}")
        print(f"   - Total Entities: {len(result['entities'])}")
        print(f"   - Total Clauses: {len(result['clauses'])}")
        print(f"   - Confidence: {result['confidence']:.2%}")
        
    except Exception as e:
        print(f"❌ Full document processing failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Enhanced features test completed!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_features())
