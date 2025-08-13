#!/usr/bin/env python3
"""
Test script to verify chunking and TTS fixes work properly.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))

from utils.gemini_utils_optimized import GeminiAnalyzer
from utils.simplify_utils import ClauseSimplifier
from utils.doc_type_classifier import DocumentTypeClassifier
from utils.tts_utils import EnhancedTTS
from utils.ner_utils import ner_extractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_chunking_and_fixes():
    """Test the chunking and TTS fixes."""
    
    # Sample legal text for testing
    sample_text = """
    NON-DISCLOSURE AGREEMENT
    
    This Non-Disclosure Agreement (the "Agreement") is entered into as of January 1, 2024, by and between ABC Corporation, a Delaware corporation with its principal place of business at 123 Main Street, New York, NY 10001 ("Disclosing Party"), and XYZ Company, a California corporation with its principal place of business at 456 Oak Avenue, Los Angeles, CA 90210 ("Receiving Party").
    
    WHEREAS, the parties wish to explore a potential business relationship and may disclose to each other certain confidential and proprietary information;
    
    NOW, THEREFORE, in consideration of the mutual promises and covenants contained herein, the parties agree as follows:
    
    1. CONFIDENTIAL INFORMATION. "Confidential Information" means any information disclosed by the Disclosing Party to the Receiving Party, either directly or indirectly, in writing, orally or by inspection of tangible objects, which is designated as "Confidential," "Proprietary" or some similar designation, or that should reasonably be understood to be confidential given the nature of the information and the circumstances of disclosure.
    
    2. NON-USE AND NON-DISCLOSURE. The Receiving Party agrees not to use any Confidential Information for any purpose except to evaluate and engage in discussions concerning a potential business relationship between the parties. The Receiving Party agrees not to disclose any Confidential Information to third parties or to the Receiving Party's employees, except to those employees who are required to have the information in order to evaluate or engage in discussions concerning the potential business relationship and who have signed confidentiality agreements with the Receiving Party.
    
    3. MAINTENANCE OF CONFIDENTIALITY. The Receiving Party agrees that it shall take reasonable measures to protect the secrecy of and avoid disclosure and unauthorized use of the Confidential Information. Without limiting the foregoing, the Receiving Party shall take at least those measures that it takes to protect its own confidential information of a similar nature.
    
    4. TERM. This Agreement shall remain in effect for a period of three (3) years from the date of this Agreement.
    
    5. RETURN OF MATERIALS. Upon the termination of this Agreement or upon the written request of the Disclosing Party, the Receiving Party shall promptly return to the Disclosing Party all copies of Confidential Information in tangible form or destroy all such copies and certify in writing to the Disclosing Party that such Confidential Information has been destroyed.
    
    IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first above written.
    
    ABC CORPORATION
    By: _________________________
    Name: John Smith
    Title: CEO
    Date: January 1, 2024
    
    XYZ COMPANY
    By: _________________________
    Name: Jane Doe
    Title: President
    Date: January 1, 2024
    """
    
    print("🧪 Testing Chunking and TTS Fixes")
    print("=" * 50)
    
    try:
        # Test 1: Document Type Classification with chunking
        print("\n1️⃣ Testing Document Type Classification...")
        doc_classification = await DocumentTypeClassifier.classify_document(sample_text, "english")
        print(f"✅ Document Type: {doc_classification['doc_type']}")
        print(f"✅ Subtype: {doc_classification['subtype']}")
        print(f"✅ Confidence: {doc_classification['confidence']}")
        
        # Test 2: NER with chunking
        print("\n2️⃣ Testing Named Entity Recognition...")
        entities = ner_extractor.extract_entities(sample_text)
        print(f"✅ Extracted {len(entities)} entities")
        for entity in entities[:5]:  # Show first 5 entities
            print(f"   - {entity['type']}: {entity['value']}")
        
        # Test 3: Clause Simplification with chunking
        print("\n3️⃣ Testing Clause Simplification...")
        clauses = [
            {'clause_number': 1, 'original_text': 'The Receiving Party agrees not to use any Confidential Information for any purpose except to evaluate and engage in discussions concerning a potential business relationship between the parties.'},
            {'clause_number': 2, 'original_text': 'The Receiving Party agrees that it shall take reasonable measures to protect the secrecy of and avoid disclosure and unauthorized use of the Confidential Information.'}
        ]
        simplified_clauses = await ClauseSimplifier.simplify_clauses(clauses, "english")
        print(f"✅ Simplified {len(simplified_clauses)} clauses")
        for clause in simplified_clauses:
            print(f"   - Clause {clause['clause_number']}: {clause['simplified_text'][:100]}...")
        
        # Test 4: TTS Generation
        print("\n4️⃣ Testing TTS Generation...")
        tts_available = await EnhancedTTS.test_voice_availability()
        if tts_available:
            print("✅ TTS service is available")
            
            # Test TTS generation
            audio_path = await EnhancedTTS.generate_tts(
                "This is a test of the TTS system.", 
                "english", 
                "kore"
            )
            if audio_path:
                print(f"✅ TTS generated successfully: {audio_path}")
            else:
                print("❌ TTS generation failed")
        else:
            print("❌ TTS service is not available")
        
        # Test 5: Full Document Analysis with chunking
        print("\n5️⃣ Testing Full Document Analysis...")
        analysis = await GeminiAnalyzer.analyze_document(sample_text, "english")
        print(f"✅ Document Type: {analysis['document_type']}")
        print(f"✅ Summary: {analysis['summary'][:100]}...")
        print(f"✅ Key Points: {len(analysis['key_points'])} points")
        print(f"✅ Risks: {len(analysis['risks'])} risks")
        print(f"✅ Action Items: {len(analysis['action_items'])} items")
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.error(f"Test error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_chunking_and_fixes())
