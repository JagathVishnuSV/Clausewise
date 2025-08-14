import google.generativeai as genai
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
import asyncio

logger = logging.getLogger(__name__)

class ChatbotHandler:
    def __init__(self):
        """Initialize the chatbot with Gemini Flash 1.5"""
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables")
            self.model = None
            # Still initialize containers to avoid attribute errors
            self.document_data = None
            self.chat_history = []
            return
        
        try:
            genai.configure(api_key=api_key)
            # Initialize Gemini Flash 1.5 model
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Gemini Flash 1.5 initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Gemini: {e}")
            self.model = None
        
        # Store document data and chat history
        self.document_data = None
        self.chat_history = []
        
    def load_document_data(self, file_path: str = "data") -> bool:
        """Load document data from the data directory"""
        try:
            data_dir = Path(file_path)
            if not data_dir.exists():
                logger.info(f"Data directory {file_path} does not exist")
                return False
            
            # Look for common document files
            document_files = []
            for ext in ['.txt', '.pdf', '.doc', '.docx', '.json']:
                document_files.extend(data_dir.glob(f'*{ext}'))
            
            if document_files:
                # For simplicity, read the first text file found
                for file in document_files:
                    try:
                        if file.suffix == '.txt':
                            with open(file, 'r', encoding='utf-8') as f:
                                content = f.read()
                                self.document_data = {
                                    'filename': file.name,
                                    'content': content,
                                    'file_path': str(file)
                                }
                                logger.info(f"Loaded document: {file.name}")
                                return True
                        elif file.suffix == '.json':
                            with open(file, 'r', encoding='utf-8') as f:
                                self.document_data = json.load(f)
                                logger.info(f"Loaded JSON data: {file.name}")
                                return True
                    except Exception as e:
                        logger.error(f"Error reading file {file}: {e}")
                        continue
            
            logger.info("No readable document files found")
            return False
        except Exception as e:
            logger.error(f"Error loading document data: {e}")
            return False
    
    def create_context_prompt(self, user_query: str, analysis_data: Optional[Dict] = None) -> str:
        """Create a context-aware prompt for the chatbot"""
        
        base_prompt = """You are a helpful legal AI assistant specialized in document analysis. 
        You provide accurate, professional, and conversational responses about legal documents.
        Keep your responses concise but informative.
        
        Current conversation context:
        """
        
        # Add document context if available
        if self.document_data:
            base_prompt += f"\n\nDocument Information:\n"
            base_prompt += f"- Filename: {self.document_data.get('filename', 'Unknown')}\n"
            if isinstance(self.document_data.get('content'), str):
                content_preview = self.document_data['content'][:800] if len(self.document_data['content']) > 800 else self.document_data['content']
                base_prompt += f"- Content: {content_preview}\n"
        
        # Add analysis data if available
        if analysis_data:
            base_prompt += f"\n\nDocument Analysis Results:\n"
            base_prompt += f"- Document Type: {analysis_data.get('doc_type', 'Unknown')}\n"
            base_prompt += f"- Summary: {analysis_data.get('summary', 'Not available')}\n"
            
            if analysis_data.get('key_points'):
                base_prompt += f"- Key Points: {analysis_data['key_points']}\n"
            
            if analysis_data.get('risks'):
                base_prompt += f"- Risks: {analysis_data['risks']}\n"
                
            if analysis_data.get('action_items'):
                base_prompt += f"- Action Items: {analysis_data['action_items']}\n"
        
        # Add recent chat history for context
        if self.chat_history:
            base_prompt += "\n\nRecent conversation:\n"
            for msg in self.chat_history[-6:]:  # Last 6 messages for context
                role = "User" if msg['role'] == 'user' else "Assistant"
                content = msg['content'][:150] + "..." if len(msg['content']) > 150 else msg['content']
                base_prompt += f"- {role}: {content}\n"
        
        base_prompt += f"\n\nUser's current question: {user_query}\n\n"
        base_prompt += """Please provide a helpful response. If the question is about the document, 
        reference specific information when available. Be conversational but professional.
        If you don't have enough information, suggest what the user should do next."""
        
        return base_prompt
    
    async def get_response(self, user_query: str, analysis_data: Optional[Dict] = None) -> str:
        """Get response from Gemini Flash 1.5"""
        if not self.model:
            return "I apologize, but the AI service is not available. Please check the API configuration."
        
        try:
            # Load fresh document data
            self.load_document_data()
            
            # Create context-aware prompt
            prompt = self.create_context_prompt(user_query, analysis_data)
            
            # Generate response using Gemini off the event loop
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            
            if getattr(response, "text", None):
                # Store in chat history
                self.chat_history.append({
                    'role': 'user',
                    'content': user_query
                })
                self.chat_history.append({
                    'role': 'assistant',
                    'content': response.text
                })
                
                # Keep only last 30 messages to manage memory
                if len(self.chat_history) > 30:
                    self.chat_history = self.chat_history[-30:]
                
                return response.text
            else:
                return "I apologize, but I couldn't generate a response. Please try rephrasing your question."
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I encountered an error while processing your request. Please try again or check if the API service is working properly."
    
    def clear_chat_history(self):
        """Clear the chat history"""
        self.chat_history = []
        logger.info("Chat history cleared")
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """Get the current chat history"""
        return self.chat_history.copy()
    
    def is_available(self) -> bool:
        """Check if the chatbot is available"""
        return self.model is not None
    
    def get_status(self) -> Dict[str, str]:
        """Get chatbot status"""
        return {
            "status": "connected" if self.model else "disconnected",
            "model": "gemini-1.5-flash" if self.model else "none",
            "document_loaded": bool(self.document_data),
            "chat_history_length": len(self.chat_history)
        }