"""
Agentic RAG Service
- Implements the complete RAG architecture with agentic capabilities
- Dynamic document analysis and role detection
- Automatic action execution when required
- Configurable model selection
- Comprehensive error handling
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .document_prompts import get_dynamic_document_prompt, get_generic_prompt
from .dynamic_action_handler import execute_document_actions, detect_document_actions
from .openai_services import OpenAICompletionService, OpenAIEmbeddingService
from .pinecone_services import PineconeService
from config import config

logger = logging.getLogger(__name__)

class DocumentAnalyzer:
    """Analyzes documents to determine type, domain, and required actions."""
    
    def __init__(self):
        self.role_keywords = {
            'medical': ['medical', 'health', 'hospital', 'doctor', 'patient', 'treatment', 'diagnosis', 'medicine', 'surgery', 'insurance', 'policy'],
            'legal': ['legal', 'law', 'contract', 'agreement', 'terms', 'conditions', 'clause', 'section', 'article', 'regulation', 'compliance'],
            'financial': ['financial', 'finance', 'banking', 'investment', 'loan', 'credit', 'insurance', 'policy', 'premium', 'claim', 'coverage'],
            'technical': ['technical', 'specification', 'manual', 'guide', 'procedure', 'protocol', 'system', 'configuration', 'installation', 'maintenance'],
            'educational': ['educational', 'academic', 'course', 'curriculum', 'learning', 'training', 'instruction', 'syllabus', 'assignment'],
            'news': ['news', 'article', 'report', 'announcement', 'press', 'media', 'journalism', 'coverage', 'story'],
            'travel': ['travel', 'trip', 'journey', 'destination', 'itinerary', 'booking', 'reservation', 'flight', 'hotel', 'tour'],
            'policy': ['policy', 'procedure', 'guideline', 'rule', 'regulation', 'standard', 'protocol', 'framework', 'methodology']
        }
    
    def analyze_document(self, content: str, metadata: Dict = None) -> Dict[str, Any]:
        """
        Analyze document to determine characteristics and requirements.
        
        Args:
            content: Document content
            metadata: Document metadata
            
        Returns:
            Analysis results
        """
        analysis = {
            'document_type': self._detect_document_type(content, metadata),
            'domain': self._detect_domain(content),
            'complexity': self._assess_complexity(content),
            'language': self._detect_language(content),
            'has_structured_data': self._detect_structured_data(content),
            'has_mathematical_content': self._detect_mathematical_content(content),
            'requires_actions': self._detect_required_actions(content),
            'estimated_tokens': self._estimate_tokens(content),
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Document analysis completed: {analysis}")
        return analysis
    
    def _detect_document_type(self, content: str, metadata: Dict = None) -> str:
        """Detect document type based on content and metadata."""
        if metadata and 'file_type' in metadata:
            file_type = metadata['file_type'].lower()
            if file_type in ['.pdf', '.docx', '.doc']:
                return 'document'
            elif file_type in ['.txt', '.md']:
                return 'text'
            elif file_type in ['.json', '.csv', '.xlsx']:
                return 'data'
            elif file_type in ['.html']:
                return 'web'
        
        # Content-based detection
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ['mission', 'challenge', 'execute', 'steps']):
            return 'mission_brief'
        elif any(keyword in content_lower for keyword in ['news', 'announcement', 'press']):
            return 'news_article'
        elif any(keyword in content_lower for keyword in ['policy', 'insurance', 'coverage']):
            return 'policy_document'
        elif any(keyword in content_lower for keyword in ['constitution', 'article', 'amendment']):
            return 'legal_document'
        elif any(keyword in content_lower for keyword in ['principia', 'newton', 'physics']):
            return 'academic_document'
        elif any(keyword in content_lower for keyword in ['token', 'secret', 'key']):
            return 'token_document'
        
        return 'general_document'
    
    def _detect_domain(self, content: str) -> str:
        """Detect document domain."""
        content_lower = content.lower()
        
        for domain, keywords in self.role_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                return domain
        
        return 'general'
    
    def _assess_complexity(self, content: str) -> str:
        """Assess document complexity."""
        word_count = len(content.split())
        sentence_count = len([s for s in content.split('.') if s.strip()])
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        if avg_sentence_length > 25 or word_count > 5000:
            return 'high'
        elif avg_sentence_length > 15 or word_count > 2000:
            return 'medium'
        else:
            return 'low'
    
    def _detect_language(self, content: str) -> str:
        """Detect document language."""
        # Simple language detection
        if any(char in content for char in 'അആഇഈഉഊഋഌഎഏഐഒഓ'):
            return 'malayalam'
        elif any(char in content for char in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'):
            return 'russian'
        elif any(char in content for char in '一乙二十丁厂七卜人入八九几儿了力乃刀又'):
            return 'chinese'
        else:
            return 'english'
    
    def _detect_structured_data(self, content: str) -> bool:
        """Detect if document contains structured data."""
        structured_patterns = [
            r'\d+\.\s+',  # Numbered lists
            r'[A-Z]\.\s+',  # Lettered lists
            r'Table\s+\d+',  # Tables
            r'Figure\s+\d+',  # Figures
            r'Section\s+\d+',  # Sections
            r'Article\s+\d+',  # Articles
        ]
        
        import re
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in structured_patterns)
    
    def _detect_mathematical_content(self, content: str) -> bool:
        """Detect if document contains mathematical content."""
        math_patterns = [
            r'\d+\s*[+\-*/]\s*\d+',  # Basic arithmetic
            r'[a-zA-Z]\s*=\s*[a-zA-Z0-9+\-*/()]+',  # Equations
            r'formula',  # Formula mentions
            r'equation',  # Equation mentions
            r'calculate',  # Calculation mentions
        ]
        
        import re
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in math_patterns)
    
    def _detect_required_actions(self, content: str) -> List[str]:
        """Detect actions required by document."""
        actions = []
        
        # Use the action detector from dynamic_action_handler
        detected_actions = detect_document_actions(content)
        for action in detected_actions:
            actions.append(action['type'])
        
        return list(set(actions))
    
    def _estimate_tokens(self, content: str) -> int:
        """Estimate token count for content."""
        # Rough estimation: 1 token ≈ 4 characters
        return len(content) // 4

class AgenticRAGService:
    """Main agentic RAG service implementing the complete architecture."""
    
    def __init__(self):
        self.document_analyzer = DocumentAnalyzer()
        self.completion_service = OpenAICompletionService()
        self.embedding_service = OpenAIEmbeddingService()
        self.vector_store = PineconeService()
        
        # Configuration
        self.chunk_size = config.CHUNK_SIZE
        self.chunk_overlap = config.CHUNK_OVERLAP
        self.top_k = config.TOP_K_RESULTS
        self.similarity_threshold = config.SIMILARITY_THRESHOLD
        self.max_context_length = config.MAX_CONTEXT_LENGTH
        
        logger.info("Agentic RAG Service initialized")
    
    def process_document(self, content: str, metadata: Dict = None, document_url: str = None) -> Dict[str, Any]:
        """
        Process a document through the complete RAG pipeline.
        
        Args:
            content: Document content
            metadata: Document metadata
            document_url: Document URL
            
        Returns:
            Processing results
        """
        try:
            # Step 1: Document Analysis
            analysis = self.document_analyzer.analyze_document(content, metadata)
            
            # Step 2: Text Extraction & Cleaning
            cleaned_content = self._clean_content(content)
            
            # Step 3: Chunking
            chunks = self._create_chunks(cleaned_content)
            
            # Step 4: Embedding Generation
            embeddings = self._generate_embeddings(chunks)
            
            # Step 5: Vector Store Insertion
            vector_results = self._store_vectors(chunks, embeddings, analysis, metadata)
            
            # Step 6: Role Detection (Agentic Layer)
            role_info = self._detect_role(analysis)
            
            return {
                'status': 'success',
                'analysis': analysis,
                'chunks_created': len(chunks),
                'vectors_stored': vector_results['vectors_stored'],
                'role_detected': role_info,
                'document_id': vector_results.get('document_id'),
                'processing_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'processing_timestamp': datetime.now().isoformat()
            }
    
    def query_document(self, query: str, document_id: str = None, document_url: str = None) -> Dict[str, Any]:
        """
        Query a document using the agentic RAG system.
        
        Args:
            query: User query
            document_id: Document ID to query
            document_url: Document URL for context
            
        Returns:
            Query results with agentic actions if required
        """
        try:
            # Step 1: Query Embedding
            query_embedding = self._generate_query_embedding(query)
            
            # Step 2: Vector Search
            search_results = self._search_vectors(query_embedding, document_id)
            
            if not search_results['documents']:
                return {
                    'status': 'no_results',
                    'query': query,
                    'message': 'No relevant documents found'
                }
            
            # Step 3: Context Assembly
            context = self._assemble_context(search_results, query)
            
            # Step 4: Action Detection & Execution
            actions_result = self._handle_actions(context, query, document_url)
            
            # Step 5: LLM Generation
            response = self._generate_response(query, context, actions_result, document_url)
            
            return {
                'status': 'success',
                'query': query,
                'response': response,
                'context_used': context['summary'],
                'actions_executed': actions_result.get('actions_executed', []),
                'sources': search_results.get('sources', []),
                'query_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error querying document: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'query': query,
                'query_timestamp': datetime.now().isoformat()
            }
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize document content."""
        # Remove extra whitespace
        cleaned = ' '.join(content.split())
        
        # Remove special characters that might interfere with processing
        import re
        cleaned = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\{\}]', ' ', cleaned)
        
        # Normalize spacing
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()
    
    def _create_chunks(self, content: str) -> List[str]:
        """Create overlapping chunks from content."""
        chunks = []
        words = content.split()
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk = ' '.join(words[i:i + self.chunk_size])
            if chunk.strip():
                chunks.append(chunk.strip())
        
        return chunks
    
    def _generate_embeddings(self, chunks: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks."""
        try:
            embeddings = []
            for chunk in chunks:
                embedding = self.embedding_service.get_embedding(chunk)
                if embedding:
                    embeddings.append(embedding)
                else:
                    logger.warning(f"Failed to generate embedding for chunk: {chunk[:100]}...")
                    # Use zero vector as fallback
                    embeddings.append([0.0] * config.EMBEDDING_DIMENSION)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def _store_vectors(self, chunks: List[str], embeddings: List[List[float]], 
                       analysis: Dict, metadata: Dict) -> Dict[str, Any]:
        """Store vectors in the vector database."""
        try:
            # Prepare metadata for each chunk
            chunk_metadata = []
            for i, chunk in enumerate(chunks):
                chunk_meta = {
                    'chunk_index': i,
                    'chunk_size': len(chunk),
                    'document_type': analysis['document_type'],
                    'domain': analysis['domain'],
                    'complexity': analysis['complexity'],
                    'language': analysis['language'],
                    'has_structured_data': analysis['has_structured_data'],
                    'has_mathematical_content': analysis['has_mathematical_content'],
                    'requires_actions': analysis['requires_actions'],
                    'timestamp': datetime.now().isoformat()
                }
                
                # Add original metadata
                if metadata:
                    chunk_meta.update(metadata)
                
                chunk_metadata.append(chunk_meta)
            
            # Store in vector database
            results = self.vector_store.upsert_vectors(
                texts=chunks,
                embeddings=embeddings,
                metadata=chunk_metadata
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error storing vectors: {e}")
            raise
    
    def _detect_role(self, analysis: Dict) -> Dict[str, Any]:
        """Detect document role and specialization."""
        role_info = {
            'primary_role': analysis['domain'],
            'specialization': analysis['document_type'],
            'complexity_level': analysis['complexity'],
            'language_support': analysis['language'],
            'capabilities': []
        }
        
        # Add role-specific capabilities
        if analysis['domain'] == 'medical':
            role_info['capabilities'].extend(['medical_terminology', 'treatment_guidance', 'safety_compliance'])
        elif analysis['domain'] == 'legal':
            role_info['capabilities'].extend(['legal_analysis', 'compliance_checking', 'contract_review'])
        elif analysis['domain'] == 'financial':
            role_info['capabilities'].extend(['financial_analysis', 'policy_guidance', 'calculation_support'])
        elif analysis['domain'] == 'technical':
            role_info['capabilities'].extend(['technical_specifications', 'procedural_guidance', 'troubleshooting'])
        
        # Add general capabilities
        if analysis['has_structured_data']:
            role_info['capabilities'].append('structured_data_analysis')
        if analysis['has_mathematical_content']:
            role_info['capabilities'].append('mathematical_processing')
        if analysis['requires_actions']:
            role_info['capabilities'].append('action_execution')
        
        return role_info
    
    def _generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for user query."""
        try:
            embedding = self.embedding_service.get_embedding(query)
            if not embedding:
                raise ValueError("Failed to generate query embedding")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise
    
    def _search_vectors(self, query_embedding: List[float], document_id: str = None) -> Dict[str, Any]:
        """Search for relevant vectors."""
        try:
            search_params = {
                'vector': query_embedding,
                'top_k': self.top_k,
                'include_metadata': True
            }
            
            if document_id:
                search_params['filter'] = {'document_id': document_id}
            
            results = self.vector_store.search_vectors(**search_params)
            return results
            
        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            raise
    
    def _assemble_context(self, search_results: Dict, query: str) -> Dict[str, Any]:
        """Assemble context from search results."""
        try:
            documents = search_results.get('documents', [])
            metadata = search_results.get('metadata', [])
            
            if not documents:
                return {'summary': '', 'sources': [], 'total_length': 0}
            
            # Combine document content
            combined_content = '\n\n'.join(documents)
            
            # Truncate if too long
            if len(combined_content) > self.max_context_length:
                combined_content = combined_content[:self.max_context_length] + '...'
            
            # Extract source information
            sources = []
            for meta in metadata:
                if meta:
                    source_info = {
                        'chunk_index': meta.get('chunk_index', 'unknown'),
                        'document_type': meta.get('document_type', 'unknown'),
                        'domain': meta.get('domain', 'unknown'),
                        'timestamp': meta.get('timestamp', 'unknown')
                    }
                    sources.append(source_info)
            
            return {
                'summary': combined_content,
                'sources': sources,
                'total_length': len(combined_content),
                'chunk_count': len(documents)
            }
            
        except Exception as e:
            logger.error(f"Error assembling context: {e}")
            raise
    
    def _handle_actions(self, context: Dict, query: str, document_url: str = None) -> Dict[str, Any]:
        """Handle actions required by the document."""
        try:
            if not config.ENABLE_ACTION_DETECTION:
                return {'actions_executed': [], 'status': 'disabled'}
            
            # Execute actions if required
            actions_result = execute_document_actions(
                content=context['summary'],
                query=query,
                document_url=document_url
            )
            
            return actions_result
            
        except Exception as e:
            logger.error(f"Error handling actions: {e}")
            return {
                'actions_executed': [],
                'status': 'error',
                'error': str(e)
            }
    
    def _generate_response(self, query: str, context: Dict, actions_result: Dict, 
                          document_url: str = None) -> str:
        """Generate response using LLM."""
        try:
            # Build the prompt
            if actions_result.get('actions_executed'):
                # Include action results in the prompt
                action_summary = self._format_action_results(actions_result)
                enhanced_context = f"{context['summary']}\n\nAction Results:\n{action_summary}"
            else:
                enhanced_context = context['summary']
            
            # Generate dynamic prompt
            system_prompt = get_dynamic_document_prompt(
                content=enhanced_context,
                document_url=document_url,
                query=query
            )
            
            # Create completion request
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Question: {query}\n\nContext: {enhanced_context}"}
            ]
            
            # Get completion
            response = self.completion_service.get_completion(
                messages=messages,
                model=get_completion_model(),
                max_tokens=2000,
                temperature=0.1
            )
            
            if not response:
                raise ValueError("Failed to generate response")
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def _format_action_results(self, actions_result: Dict) -> str:
        """Format action results for inclusion in prompt."""
        try:
            if not actions_result.get('actions_executed'):
                return "No actions were executed."
            
            formatted_results = []
            for action_info in actions_result['actions_executed']:
                action = action_info.get('action', {})
                result = action_info.get('result', {})
                
                action_type = action.get('type', 'unknown')
                action_desc = action.get('description', 'No description')
                status = result.get('status', 'unknown')
                
                if status == 'success':
                    if action_type == 'mission_execution':
                        # Format mission execution results
                        if 'trace_info' in result:
                            trace = result['trace_info']
                            formatted_results.append(
                                f"Mission Execution Completed:\n"
                                f"- City: {trace.get('city', 'N/A')}\n"
                                f"- Landmark: {trace.get('landmark', 'N/A')}\n"
                                f"- Flight Number: {trace.get('flight_number', 'N/A')}\n"
                                f"- Endpoint Used: {trace.get('endpoint', 'N/A')}\n"
                                f"- Steps: {', '.join(trace.get('steps_completed', []))}"
                            )
                        else:
                            formatted_results.append(f"Action '{action_desc}' completed successfully: {result}")
                    else:
                        formatted_results.append(f"Action '{action_desc}' completed successfully: {result}")
                else:
                    formatted_results.append(f"Action '{action_desc}' failed: {result.get('error', 'Unknown error')}")
            
            return '\n\n'.join(formatted_results)
            
        except Exception as e:
            logger.error(f"Error formatting action results: {e}")
            return "Error formatting action results"

# Global instance
agentic_rag_service = AgenticRAGService()

def process_document_with_rag(content: str, metadata: Dict = None, document_url: str = None) -> Dict[str, Any]:
    """Process document through the agentic RAG system."""
    return agentic_rag_service.process_document(content, metadata, document_url)

def query_document_with_rag(query: str, document_id: str = None, document_url: str = None) -> Dict[str, Any]:
    """Query document using the agentic RAG system."""
    return agentic_rag_service.query_document(query, document_id, document_url)
