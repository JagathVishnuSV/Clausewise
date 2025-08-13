import os
import re
from typing import List, Dict, Any
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
import logging

logger = logging.getLogger(__name__)

class LegalNER:
    """Named Entity Recognition for legal documents."""
    
    def __init__(self):
        self.ner_pipeline = None
        self.initialize_models()
    
    def initialize_models(self):
        """Initialize NER models."""
        try:
            # Use a general NER model that works well for legal text
            model_name = "dslim/bert-base-NER"
            self.ner_pipeline = pipeline(
                "ner",
                model=model_name,
                tokenizer=model_name,
                aggregation_strategy="simple"
            )
            logger.info("NER model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize NER model: {e}")
            self.ner_pipeline = None
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from legal text."""
        if not self.ner_pipeline or not text.strip():
            return []
        
        try:
            # Extract entities using the NER pipeline
            entities = self.ner_pipeline(text)
            
            # Map NER labels to our custom categories
            mapped_entities = []
            for entity in entities:
                entity_type = self._map_entity_type(entity['entity_group'])
                if entity_type:
                    mapped_entities.append({
                        "type": entity_type,
                        "value": entity['word'],
                        "confidence": entity['score'],
                        "start": entity['start'],
                        "end": entity['end']
                    })
            
            # Add custom legal entity extraction
            custom_entities = self._extract_custom_entities(text)
            mapped_entities.extend(custom_entities)
            
            return mapped_entities
            
        except Exception as e:
            logger.error(f"Error in entity extraction: {e}")
            return []
    
    def _map_entity_type(self, ner_label: str) -> str:
        """Map NER labels to our custom entity types."""
        mapping = {
            'PERSON': 'Party',
            'ORG': 'Party',
            'MISC': 'Legal Term',
            'LOC': 'Location',
            'DATE': 'Date',
            'TIME': 'Date'
        }
        return mapping.get(ner_label, 'Other')
    
    def _extract_custom_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract custom legal entities using regex patterns."""
        entities = []
        
        # Extract monetary values
        money_patterns = [
            r'\$[\d,]+(?:\.\d{2})?',
            r'[\d,]+(?:\.\d{2})?\s*(?:dollars?|USD|EUR|GBP|INR)',
            r'[\d,]+(?:\.\d{2})?\s*(?:rupees?|₹)'
        ]
        
        for pattern in money_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    "type": "Monetary Value",
                    "value": match.group(),
                    "confidence": 0.9,
                    "start": match.start(),
                    "end": match.end()
                })
        
        # Extract dates
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{4}-\d{2}-\d{2}',
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
            r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}'
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    "type": "Date",
                    "value": match.group(),
                    "confidence": 0.9,
                    "start": match.start(),
                    "end": match.end()
                })
        
        # Extract obligations (common legal phrases)
        obligation_patterns = [
            r'shall\s+\w+',
            r'must\s+\w+',
            r'required\s+to\s+\w+',
            r'obligated\s+to\s+\w+',
            r'responsible\s+for\s+\w+',
            r'liable\s+for\s+\w+'
        ]
        
        for pattern in obligation_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get more context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                
                entities.append({
                    "type": "Obligation",
                    "value": context,
                    "confidence": 0.8,
                    "start": match.start(),
                    "end": match.end()
                })
        
        # Extract legal terms
        legal_terms = [
            'confidentiality', 'non-disclosure', 'breach', 'termination',
            'liability', 'indemnification', 'governing law', 'jurisdiction',
            'arbitration', 'mediation', 'force majeure', 'severability',
            'entire agreement', 'amendment', 'waiver', 'assignment',
            'subcontracting', 'warranty', 'representation', 'covenant'
        ]
        
        for term in legal_terms:
            matches = re.finditer(r'\b' + re.escape(term) + r'\b', text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    "type": "Legal Term",
                    "value": match.group(),
                    "confidence": 0.9,
                    "start": match.start(),
                    "end": match.end()
                })

        # Extract legal context snippets (e.g., governing law, state laws, corporation law)
        context_patterns = [
            r'governing law[^\.;\n]*',
            r'jurisdiction[^\.;\n]*',
            r'laws?\s+of\s+[^\.;\n]*',
            r'(?:state|federal)\s+laws?[^\.;\n]*',
            r'corporation\s+law[^\.;\n]*',
        ]
        for pattern in context_patterns:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                snippet = m.group().strip().strip(' .;')
                if len(snippet) > 0:
                    entities.append({
                        "type": "Legal Context",
                        "value": snippet,
                        "confidence": 0.75,
                        "start": m.start(),
                        "end": m.end()
                    })
        
        return entities
    
    def extract_entities_by_clause(self, clauses: List[Dict[str, str]]) -> Dict[int, List[Dict[str, Any]]]:
        """Extract entities for each clause separately."""
        clause_entities = {}
        
        for clause in clauses:
            clause_num = clause.get('clause_number', 0)
            clause_text = clause.get('original_text', '')
            
            if clause_text:
                entities = self.extract_entities(clause_text)
                clause_entities[clause_num] = entities
        
        return clause_entities

# Global instance
ner_extractor = LegalNER()
