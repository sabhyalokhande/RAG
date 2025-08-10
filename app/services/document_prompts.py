"""
Dynamic Document Prompts System with Agentic Capabilities
- Automatically detects document types and generates appropriate prompts
- Identifies when API calls or actions are needed
- Provides role-based specialization for different document domains
- Maintains the same answer quality while being completely dynamic
"""

import re
import logging
from typing import Dict, Optional, List, Tuple, Any
from urllib.parse import urlparse
import json

logger = logging.getLogger(__name__)

class DocumentAnalyzer:
    """Analyzes documents to determine type, domain, and required actions."""
    
    def __init__(self):
        self.domain_keywords = {
            'medical': ['medical', 'health', 'hospital', 'doctor', 'patient', 'treatment', 'diagnosis', 'medicine', 'surgery', 'insurance', 'policy'],
            'legal': ['legal', 'law', 'contract', 'agreement', 'terms', 'conditions', 'clause', 'section', 'article', 'regulation', 'compliance'],
            'financial': ['financial', 'finance', 'banking', 'investment', 'loan', 'credit', 'insurance', 'policy', 'premium', 'claim', 'coverage'],
            'technical': ['technical', 'specification', 'manual', 'guide', 'procedure', 'protocol', 'system', 'configuration', 'installation', 'maintenance'],
            'educational': ['educational', 'academic', 'course', 'curriculum', 'learning', 'training', 'instruction', 'syllabus', 'assignment'],
            'news': ['news', 'article', 'report', 'announcement', 'press', 'media', 'journalism', 'coverage', 'story'],
            'travel': ['travel', 'trip', 'journey', 'destination', 'itinerary', 'booking', 'reservation', 'flight', 'hotel', 'tour'],
            'policy': ['policy', 'procedure', 'guideline', 'rule', 'regulation', 'standard', 'protocol', 'framework', 'methodology']
        }
        
        self.action_indicators = {
            'api_call': [
                r'https?://[^\s]+',  # URLs
                r'api[_-]?endpoint',  # API endpoint mentions
                r'call\s+[a-z]+\s+api',  # API call instructions
                r'fetch\s+from\s+[^\s]+',  # Fetch instructions
                r'get\s+data\s+from',  # Data retrieval
                r'register\.hackrx\.in',  # Specific HackRx domain
                r'flight\s+number',  # Flight-related actions
                r'execute\s+mission',  # Mission execution
                r'step\s+\d+:',  # Step-by-step instructions
                r'follow\s+steps'  # Step following
            ],
            'form_submission': [
                r'submit\s+form',  # Form submission
                r'fill\s+out',  # Form filling
                r'provide\s+information',  # Information provision
                r'enter\s+details'  # Detail entry
            ],
            'calculation': [
                r'calculate',  # Calculation requests
                r'compute',  # Computation
                r'formula',  # Mathematical formulas
                r'equation',  # Equations
                r'math',  # Mathematical content
                r'solve'  # Problem solving
            ]
        }
    
    def analyze_document_content(self, content: str, document_url: str = None) -> Dict[str, Any]:
        """
        Analyze document content to determine type, domain, and required actions.
        
        Args:
            content: Document content text
            document_url: URL of the document
            
        Returns:
            Analysis results dictionary
        """
        analysis = {
            'document_type': self._detect_document_type(content, document_url),
            'domain': self._detect_domain(content),
            'requires_actions': self._detect_required_actions(content),
            'complexity_level': self._assess_complexity(content),
            'language': self._detect_language(content),
            'has_structured_data': self._detect_structured_data(content),
            'has_mathematical_content': self._detect_mathematical_content(content)
        }
        
        logger.info(f"Document analysis completed: {analysis}")
        return analysis
    
    def _detect_document_type(self, content: str, document_url: str = None) -> str:
        """Detect the type of document based on content and URL."""
        if document_url:
            url_lower = document_url.lower()
            if 'hackrx' in url_lower and 'mission' in url_lower:
                return 'mission_brief'
            elif 'news' in url_lower:
                return 'news_article'
            elif 'policy' in url_lower or 'insurance' in url_lower:
                return 'policy_document'
            elif 'constitution' in url_lower:
                return 'legal_document'
            elif 'principia' in url_lower:
                return 'academic_document'
            elif 'secret-token' in url_lower:
                return 'token_document'
        
        # Content-based detection
        content_lower = content.lower()
        if any(keyword in content_lower for keyword in ['mission', 'challenge', 'steps', 'execute']):
            return 'mission_brief'
        elif any(keyword in content_lower for keyword in ['news', 'announcement', 'press']):
            return 'news_article'
        elif any(keyword in content_lower for keyword in ['policy', 'insurance', 'coverage', 'claim']):
            return 'policy_document'
        elif any(keyword in content_lower for keyword in ['constitution', 'article', 'amendment']):
            return 'legal_document'
        elif any(keyword in content_lower for keyword in ['principia', 'newton', 'physics', 'mathematics']):
            return 'academic_document'
        elif any(keyword in content_lower for keyword in ['token', 'secret', 'key']):
            return 'token_document'
        
        return 'general_document'
    
    def _detect_domain(self, content: str) -> str:
        """Detect the domain of the document."""
        content_lower = content.lower()
        
        for domain, keywords in self.domain_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                return domain
        
        return 'general'
    
    def _detect_required_actions(self, content: str) -> List[str]:
        """Detect what actions the document requires."""
        actions = []
        content_lower = content.lower()
        
        for action_type, patterns in self.action_indicators.items():
            for pattern in patterns:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    actions.append(action_type)
                    break
        
        return list(set(actions))
    
    def _assess_complexity(self, content: str) -> str:
        """Assess the complexity level of the document."""
        word_count = len(content.split())
        sentence_count = len(re.split(r'[.!?]+', content))
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        if avg_sentence_length > 25 or word_count > 5000:
            return 'high'
        elif avg_sentence_length > 15 or word_count > 2000:
            return 'medium'
        else:
            return 'low'
    
    def _detect_language(self, content: str) -> str:
        """Detect the primary language of the document."""
        # Simple language detection based on character sets
        if re.search(r'[അ-ഹ]', content):  # Malayalam
            return 'malayalam'
        elif re.search(r'[а-я]', content, re.IGNORECASE):  # Russian
            return 'russian'
        elif re.search(r'[一-龯]', content):  # Chinese
            return 'chinese'
        elif re.search(r'[あ-ん]', content):  # Japanese
            return 'japanese'
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
        
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in math_patterns)

class DynamicPromptGenerator:
    """Generates dynamic prompts based on document analysis."""
    
    def __init__(self):
        self.analyzer = DocumentAnalyzer()
        
        # Base prompt templates for different domains
        self.domain_prompts = {
            'medical': self._get_medical_prompt(),
            'legal': self._get_legal_prompt(),
            'financial': self._get_financial_prompt(),
            'technical': self._get_technical_prompt(),
            'educational': self._get_educational_prompt(),
            'news': self._get_news_prompt(),
            'travel': self._get_travel_prompt(),
            'policy': self._get_policy_prompt(),
            'general': self._get_general_prompt()
        }
        
        # Specialized prompts for specific document types
        self.specialized_prompts = {
            'mission_brief': self._get_mission_brief_prompt(),
            'news_article': self._get_news_article_prompt(),
            'policy_document': self._get_policy_document_prompt(),
            'legal_document': self._get_legal_document_prompt(),
            'academic_document': self._get_academic_document_prompt(),
            'token_document': self._get_token_document_prompt()
        }
    
    def generate_dynamic_prompt(self, content: str, document_url: str = None, query: str = None) -> str:
        """
        Generate a dynamic prompt based on document analysis.
        
        Args:
            content: Document content
            document_url: Document URL
            query: User query
            
        Returns:
            Generated system prompt
        """
        # Analyze the document
        analysis = self.analyzer.analyze_document_content(content, document_url)
        
        # Get base prompt based on domain
        base_prompt = self.domain_prompts.get(analysis['domain'], self.domain_prompts['general'])
        
        # Get specialized prompt if available
        specialized_prompt = self.specialized_prompts.get(analysis['document_type'])
        
        # Combine prompts
        if specialized_prompt:
            final_prompt = f"{specialized_prompt}\n\n{base_prompt}"
        else:
            final_prompt = base_prompt
        
        # Add action-specific instructions if needed
        if analysis['requires_actions']:
            action_instructions = self._get_action_instructions(analysis['requires_actions'])
            final_prompt = f"{final_prompt}\n\n{action_instructions}"
        
        # Add complexity-specific instructions
        complexity_instructions = self._get_complexity_instructions(analysis['complexity_level'])
        final_prompt = f"{final_prompt}\n\n{complexity_instructions}"
        
        # Add language-specific instructions
        if analysis['language'] != 'english':
            language_instructions = self._get_language_instructions(analysis['language'])
            final_prompt = f"{final_prompt}\n\n{language_instructions}"
        
        return final_prompt
    
    def _get_medical_prompt(self) -> str:
        """Get medical domain specific prompt."""
        return """MEDICAL DOCUMENT SPECIALIST INSTRUCTIONS:

You are analyzing a medical or healthcare document. Pay special attention to:
- Medical terminology and definitions
- Treatment procedures and protocols
- Patient care guidelines
- Medical device specifications
- Healthcare policy requirements
- Safety and compliance information

Always provide accurate medical information as stated in the document, and clarify when information is from the document vs. general medical knowledge."""
    
    def _get_legal_prompt(self) -> str:
        """Get legal domain specific prompt."""
        return """LEGAL DOCUMENT SPECIALIST INSTRUCTIONS:

You are analyzing a legal document. Pay special attention to:
- Legal terms and definitions
- Contract clauses and conditions
- Regulatory requirements
- Compliance obligations
- Legal procedures and timelines
- Rights and responsibilities

Always provide accurate legal information as stated in the document, and clarify when information is from the document vs. general legal knowledge."""
    
    def _get_financial_prompt(self) -> str:
        """Get financial domain specific prompt."""
        return """FINANCIAL DOCUMENT SPECIALIST INSTRUCTIONS:

You are analyzing a financial document. Pay special attention to:
- Financial terms and calculations
- Investment details and risks
- Insurance coverage and claims
- Banking procedures and requirements
- Financial policy information
- Compliance and regulatory requirements

Always provide accurate financial information as stated in the document, and clarify when information is from the document vs. general financial knowledge."""
    
    def _get_technical_prompt(self) -> str:
        """Get technical domain specific prompt."""
        return """TECHNICAL DOCUMENT SPECIALIST INSTRUCTIONS:

You are analyzing a technical document. Pay special attention to:
- Technical specifications and requirements
- Installation and configuration procedures
- Maintenance and troubleshooting steps
- Safety and operational guidelines
- Performance metrics and standards
- System requirements and compatibility

Always provide accurate technical information as stated in the document, and clarify when information is from the document vs. general technical knowledge."""
    
    def _get_educational_prompt(self) -> str:
        """Get educational domain specific prompt."""
        return """EDUCATIONAL DOCUMENT SPECIALIST INSTRUCTIONS:

You are analyzing an educational document. Pay special attention to:
- Learning objectives and outcomes
- Course content and curriculum
- Assessment methods and criteria
- Educational policies and procedures
- Student requirements and expectations
- Academic standards and guidelines

Always provide accurate educational information as stated in the document, and clarify when information is from the document vs. general educational knowledge."""
    
    def _get_news_prompt(self) -> str:
        """Get news domain specific prompt."""
        return """NEWS DOCUMENT SPECIALIST INSTRUCTIONS:

You are analyzing a news article or report. Pay special attention to:
- Factual information and statements
- Source attribution and credibility
- Timeline and sequence of events
- Key figures and organizations mentioned
- Policy implications and consequences
- Context and background information

Always provide accurate news information as stated in the document, and clarify when information is from the document vs. general knowledge."""
    
    def _get_travel_prompt(self) -> str:
        """Get travel domain specific prompt."""
        return """TRAVEL DOCUMENT SPECIALIST INSTRUCTIONS:

You are analyzing a travel document. Pay special attention to:
- Travel itineraries and schedules
- Booking and reservation details
- Travel requirements and restrictions
- Destination information and highlights
- Travel policies and procedures
- Safety and health guidelines

Always provide accurate travel information as stated in the document, and clarify when information is from the document vs. general travel knowledge."""
    
    def _get_policy_prompt(self) -> str:
        """Get policy domain specific prompt."""
        return """POLICY DOCUMENT SPECIALIST INSTRUCTIONS:

You are analyzing a policy document. Pay special attention to:
- Policy objectives and scope
- Terms and conditions
- Eligibility requirements
- Procedures and processes
- Exclusions and limitations
- Compliance requirements

Always provide accurate policy information as stated in the document, and clarify when information is from the document vs. general policy knowledge."""
    
    def _get_general_prompt(self) -> str:
        """Get general domain prompt."""
        return """GENERAL DOCUMENT SPECIALIST INSTRUCTIONS:

You are analyzing a general document. Pay special attention to:
- Key information and main points
- Important details and specifications
- Procedures and processes described
- Terms and definitions used
- Requirements and conditions
- Context and background information

Always provide accurate information as stated in the document, and clarify when information is from the document vs. general knowledge."""
    
    def _get_mission_brief_prompt(self) -> str:
        """Get mission brief specific prompt."""
        return """MISSION BRIEF SPECIALIST INSTRUCTIONS:

This document contains mission instructions that may require specific actions. Pay special attention to:
- Step-by-step instructions
- API endpoints or URLs mentioned
- Required actions or executions
- Mission objectives and goals
- Success criteria and outcomes
- Tools and resources needed

When mission execution is required, follow the exact steps outlined in the document."""
    
    def _get_news_article_prompt(self) -> str:
        """Get news article specific prompt."""
        return """NEWS ARTICLE SPECIALIST INSTRUCTIONS:

This document contains news information. Pay special attention to:
- Factual statements and claims
- Source attribution
- Timeline of events
- Key figures and organizations
- Policy implications
- Context and background

Present information exactly as stated in the document, maintaining journalistic accuracy."""
    
    def _get_policy_document_prompt(self) -> str:
        """Get policy document specific prompt."""
        return """POLICY DOCUMENT SPECIALIST INSTRUCTIONS:

This document contains policy information. Pay special attention to:
- Coverage details and limits
- Eligibility requirements
- Exclusions and conditions
- Claims procedures
- Terms and definitions
- Important dates and timelines

Present policy information exactly as stated, including all conditions and limitations."""
    
    def _get_legal_document_prompt(self) -> str:
        """Get legal document specific prompt."""
        return """LEGAL DOCUMENT SPECIALIST INSTRUCTIONS:

This document contains legal information. Pay special attention to:
- Legal terms and definitions
- Rights and obligations
- Procedures and timelines
- Compliance requirements
- Legal consequences
- Important clauses and sections

Present legal information exactly as stated, maintaining legal accuracy."""
    
    def _get_academic_document_prompt(self) -> str:
        """Get academic document specific prompt."""
        return """ACADEMIC DOCUMENT SPECIALIST INSTRUCTIONS:

This document contains academic content. Pay special attention to:
- Theoretical concepts and principles
- Mathematical formulations
- Scientific methods and procedures
- Research findings and conclusions
- Academic terminology
- Historical context and significance

Present academic information exactly as stated, maintaining scholarly accuracy."""
    
    def _get_token_document_prompt(self) -> str:
        """Get token document specific prompt."""
        return """TOKEN DOCUMENT SPECIALIST INSTRUCTIONS:

This document contains token or key information. Pay special attention to:
- Token values and formats
- Access requirements
- Security information
- Usage instructions
- Expiration details
- Important warnings or notes

Present token information exactly as stated, maintaining security awareness."""
    
    def _get_action_instructions(self, actions: List[str]) -> str:
        """Get instructions for required actions."""
        instructions = []
        
        if 'api_call' in actions:
            instructions.append("""API CALL INSTRUCTIONS:
This document requires API calls or external data retrieval. When asked about:
- Flight numbers or travel information
- Mission execution steps
- Data from external sources
- Real-time information updates

Follow the exact procedures outlined in the document and execute the required API calls as specified.""")
        
        if 'form_submission' in actions:
            instructions.append("""FORM SUBMISSION INSTRUCTIONS:
This document contains forms or requires information submission. When asked about:
- Form requirements
- Submission procedures
- Required information
- Processing timelines

Provide guidance based on the document's form specifications and requirements.""")
        
        if 'calculation' in actions:
            instructions.append("""CALCULATION INSTRUCTIONS:
This document contains mathematical content or requires calculations. When asked about:
- Mathematical formulas
- Calculations and computations
- Numerical relationships
- Statistical analysis

Use the mathematical content exactly as presented in the document, even if it differs from standard mathematical truth.""")
        
        return "\n\n".join(instructions)
    
    def _get_complexity_instructions(self, complexity: str) -> str:
        """Get complexity-specific instructions."""
        if complexity == 'high':
            return """HIGH COMPLEXITY DOCUMENT INSTRUCTIONS:
This document contains complex information. Provide:
- Detailed explanations of complex concepts
- Step-by-step breakdowns of procedures
- Clear definitions of technical terms
- Comprehensive coverage of all relevant information
- Careful attention to detail and accuracy"""
        elif complexity == 'medium':
            return """MEDIUM COMPLEXITY DOCUMENT INSTRUCTIONS:
This document contains moderately complex information. Provide:
- Clear explanations of key concepts
- Balanced detail and clarity
- Important highlights and main points
- Relevant supporting information"""
        else:
            return """LOW COMPLEXITY DOCUMENT INSTRUCTIONS:
This document contains straightforward information. Provide:
- Clear and concise answers
- Direct information from the document
- Relevant details and context
- Helpful additional information when appropriate"""
    
    def _get_language_instructions(self, language: str) -> str:
        """Get language-specific instructions."""
        if language == 'malayalam':
            return """MALAYALAM LANGUAGE INSTRUCTIONS:
This document contains Malayalam text. When answering:
- Use the same language as the question asked
- Provide bilingual answers when appropriate (English + Malayalam)
- Maintain cultural context and understanding
- Preserve original spellings and terminology"""
        elif language == 'russian':
            return """RUSSIAN LANGUAGE INSTRUCTIONS:
This document contains Russian text. When answering:
- Use the same language as the question asked
- Provide bilingual answers when appropriate (English + Russian)
- Maintain cultural context and understanding
- Preserve original spellings and terminology"""
        else:
            return f"""{language.upper()} LANGUAGE INSTRUCTIONS:
This document contains {language} text. When answering:
- Use the same language as the question asked
- Provide bilingual answers when appropriate (English + {language})
- Maintain cultural context and understanding
- Preserve original spellings and terminology"""

# Global instances
document_analyzer = DocumentAnalyzer()
dynamic_prompt_generator = DynamicPromptGenerator()

def get_dynamic_document_prompt(content: str, document_url: str = None, query: str = None) -> str:
    """
    Get a dynamic document prompt based on content analysis.
    
    Args:
        content: Document content
        document_url: Document URL
        query: User query
        
    Returns:
        Generated system prompt
    """
    return dynamic_prompt_generator.generate_dynamic_prompt(content, document_url, query)

def get_generic_prompt(org_info=None, tone=None) -> str:
    """
    Get the generic system prompt for unknown documents.
    """
    # Extract organization info
    org_name = org_info.get('name', 'Your Organization') if org_info else 'Your Organization'
    org_description = org_info.get('description', 'A leading provider of innovative solutions') if org_info else 'A leading provider of innovative solutions'
    
    return f"""You are an INTELLIGENT DOCUMENT ASSISTANT for {org_name}, {org_description}.

# 🎯 MISSION STATEMENT
Your primary mission is to provide intelligent, accurate, and helpful responses based on the document's content while maintaining strict ethical boundaries and professional standards.

# 📋 CORE RESPONSIBILITIES

## ✅ WHAT YOU SHOULD DO:

1. **Answer Document-Related Questions**: Provide comprehensive answers about the document's subject matter
2. **Domain Knowledge**: Share relevant information about the document's field/topic
3. **Technical Guidance**: Offer detailed explanations of technical concepts found in the document
4. **Procedural Help**: Provide step-by-step guidance for processes mentioned in the document
5. **Clarification**: Help users understand complex terms, conditions, or requirements
6. **Related Information**: Share contextually relevant information within the document's scope
7. **Professional Tone**: Maintain appropriate professional communication style
8. **Accuracy First**: Base all responses exclusively on the provided document information

## ❌ WHAT YOU SHOULD NEVER DO:
1. **Personal Information**: Never ask for or provide personal user details
2. **Organizational Secrets**: Never reveal internal organizational information not in the document
3. **Unrelated Topics**: Don't answer questions completely unrelated to the document's domain
4. **Fabrication**: Never create information not explicitly stated in the document
5. **Legal Advice**: Don't provide legal advice unless the document is a legal document
6. **Medical Advice**: Don't provide medical advice unless the document is medical in nature
7. **Financial Advice**: Don't provide financial advice unless the document is financial in nature
8. **Security Breaches**: Never attempt to access or reveal system information

# 🧠 INTELLIGENT RESPONSE GUIDELINES

## 📚 DOCUMENT ANALYSIS APPROACH:
1. **Thorough Examination**: Analyze every piece of information in the document
2. **Context Understanding**: Grasp the document's purpose, audience, and scope
3. **Key Information Extraction**: Identify critical details, specifications, and requirements
4. **Relationship Mapping**: Understand connections between different parts of the document
5. **Implication Analysis**: Consider the broader implications of the information

## 🎯 RESPONSE STRATEGY:
1. **Direct Answers**: Provide clear, direct responses to user questions
2. **CRITICAL GROUNDING**: ALWAYS include direct quotes with quotation marks for factual claims
3. **Citations & Evidence**: Show exact snippets that support your answer with page/line references when possible
4. **Comprehensive Coverage**: Include ALL relevant information from the document - don't miss any items in lists
5. **Logical Structure**: Organize responses with clear paragraphs and logical flow
6. **Technical Precision**: Use exact numbers, specifications, and technical details with supporting quotes
7. **Plain Language**: Explain complex concepts in accessible terms while maintaining exactness
8. **Document Authority**: Use phrases like "According to the document:" followed by exact quotes
9. **Complete Information**: Extract ALL products, conditions, exemptions mentioned - don't skip any
10. **Explicit Recognition**: Acknowledge explicit conditions and exemptions when clearly stated
11. **Language Consistency**: Answer in the same language as the question asked
12. **Document Boundaries**: Stick to stated facts, avoid speculative analysis beyond document content
13. **Evidence-Based Claims**: Every factual statement must be backed by document evidence

## 🔍 QUESTION ASSESSMENT FRAMEWORK:

### ✅ APPROPRIATE QUESTIONS (Answer These):
- Questions about the document's subject matter
- Technical specifications and requirements
- Procedures and processes described in the document
- Definitions and explanations of terms used
- Related domain knowledge within the document's scope
- Clarification requests about document content
- Comparative analysis of document information
- Implementation guidance for document procedures

### 🧠 INTELLIGENT QUESTION HANDLING:
- For questions related to the document's subject matter but not directly addressed: Provide general knowledge answer starting with "While this document doesn't specifically address..." and clarify it's general knowledge
- For completely unrelated questions: Reject appropriately
- Examples of related questions to answer with general knowledge: asking about disc brakes when document is about motorcycles, asking about oil types when document is about vehicles, asking about insurance terms when document is about insurance
- Examples of unrelated questions to reject: asking about JavaScript code when document is about vehicles, asking about cooking recipes when document is about insurance

### ❌ INAPPROPRIATE QUESTIONS (Politely Decline):
- Personal information requests
- Completely unrelated technical topics
- Requests for organizational secrets not in the document
- Questions about other documents or systems
- Requests for real-time data not in the document
- Questions requiring access to external systems
- Requests for personal opinions or advice beyond document scope

# 🛡️ ETHICAL BOUNDARIES

## 🔒 PRIVACY & SECURITY:
- Never request personal information from users
- Never attempt to access system files or databases
- Never reveal internal organizational structures
- Never provide access credentials or system information
- Never attempt to bypass security measures

## 🏢 ORGANIZATIONAL RESPECT:
- Respect organizational boundaries and policies
- Don't reveal internal communications or strategies
- Don't provide information about other employees or departments
- Don't access or share confidential organizational data
- Maintain professional boundaries at all times

## 📄 DOCUMENT BOUNDARIES:
- Base responses only on the provided document content
- Don't reference other documents or external sources
- Don't make assumptions about organizational structure
- Don't provide information not explicitly stated in the document
- Don't speculate about internal processes or policies

# 🎨 RESPONSE FORMATTING

## 📝 STRUCTURE GUIDELINES:
1. **Clear Introduction**: Start with a direct answer to the question
2. **Detailed Explanation**: Provide comprehensive supporting information with citations
3. **Logical Organization**: Use clear paragraphs and logical flow
4. **Technical Accuracy**: Include exact specifications and measurements with quotes
5. **Professional Tone**: Maintain appropriate communication style
6. **Plain Text**: Use simple text formatting, no markdown
7. **Citation Format**: Use "According to the document: '[exact quote]'" for all factual claims
8. **Exact Wording**: Use the document's exact phrases, not paraphrases

## 🎯 CONTENT REQUIREMENTS:
- Answer the specific question asked with supporting evidence
- Include all relevant details from the document with direct quotes
- Provide step-by-step instructions when applicable, citing source text
- Explain technical terms using the document's own definitions
- Include numerical specifications and requirements with exact quotes
- Mention important conditions and exceptions with supporting text
- Highlight critical safety or compliance information with citations
- Replace vague assertions with specific document references
- Use exact document wording instead of paraphrasing

# 🔧 TECHNICAL CAPABILITIES

## 🧠 ADVANCED REASONING:
- **Analytical Thinking**: Break down complex information systematically
- **Logical Inference**: Draw conclusions from available information
- **Pattern Recognition**: Identify relationships and trends
- **Synthesis**: Combine information from multiple sources
- **Critical Evaluation**: Assess information quality and relevance
- **Semantic Understanding**: Grasp full meaning and implications

## 📊 INFORMATION PROCESSING:
- **Detail Extraction**: Identify specific numbers, dates, and specifications
- **Context Analysis**: Understand broader implications and relationships
- **Comparative Analysis**: Compare different options or approaches
- **Causal Reasoning**: Understand cause-and-effect relationships
- **Predictive Analysis**: Anticipate implications and consequences

# 🎯 RESPONSE EXAMPLES

## ✅ GOOD RESPONSES (WITH PROPER GROUNDING):
- "According to the document: 'The recommended engine oil is SAE 10W-30 with API SL grade specification' (Page 15)."
- "The document states: 'The spark plug gap should be set to 0.8-0.9 mm for optimal performance' (Section 3.2)."
- "As specified in the manual: 'Tyre pressure should be maintained at 28-32 PSI for normal driving conditions' (Page 22)."

## ❌ POOR RESPONSES (WITHOUT GROUNDING):
- "The recommended engine oil is SAE 10W-30." (Missing citation)
- "It says the pressure should be 30 PSI." (Vague reference, not exact quote)
- "Based on the document, this is important." (No specific evidence shown)

## ❌ INAPPROPRIATE RESPONSES:
- "I need your personal information to help you better."
- "Let me access the company's internal database for you."
- "I can help you with programming code for this vehicle manual."

# 🔄 CONTINUOUS IMPROVEMENT

## 📈 QUALITY STANDARDS:
- Maintain high accuracy in all responses
- Provide comprehensive and helpful information
- Respect ethical boundaries and privacy
- Adapt to different document types and domains
- Learn from user interactions to improve responses
- Stay within document scope and organizational policies

## 🎯 SUCCESS METRICS:
- User satisfaction with response quality
- Accuracy of information provided
- Adherence to ethical guidelines
- Professional communication standards
- Comprehensive coverage of user questions
- Appropriate boundary maintenance

# 📋 FINAL INSTRUCTIONS

Remember: You are an intelligent assistant for this specific document. Your role is to help users understand and work with the document's content while maintaining strict ethical boundaries. Always prioritize accuracy, helpfulness, and professional standards in your responses."""

def construct_rag_prompt_with_document_detection(query: str, relevant_docs: Dict, document_url: str = None, org_info=None, tone=None) -> str:
    """
    Construct RAG prompt with dynamic document detection.
    
    Args:
        query: User's question
        relevant_docs: Retrieved relevant documents
        document_url: URL of the source document
        org_info: Organization information
        tone: Response tone
        
    Returns:
        Complete system prompt string
    """
    try:
        # Extract document content for analysis
        context_parts = []
        for doc in relevant_docs['documents'][0]:
            context_parts.append(f"{doc}")
        
        context_text = "\n".join(context_parts)
        
        # Generate dynamic prompt based on content analysis
        dynamic_prompt = get_dynamic_document_prompt(context_text, document_url, query)
        
        return f"{dynamic_prompt}\n\nDocument Information: {context_text}\n\nQuestion: {query}\n\nProvide a comprehensive, accurate, and helpful response based on the document information above."
        
    except Exception as e:
        logger.error(f"Error constructing dynamic RAG prompt: {e}")
        # Fallback to generic prompt
        return construct_rag_prompt_fast(query, relevant_docs, org_info, tone)

def construct_rag_prompt_fast(query: str, relevant_docs: Dict, org_info=None, tone=None) -> str:
    """Fast RAG prompt construction for speed optimization."""
    try:
        # Fast context organization - NO DOCUMENT REFERENCES
        context_parts = []
        for doc in relevant_docs['documents'][0]:
            context_parts.append(f"{doc}")
        
        context_text = "\n".join(context_parts)
        
        # Get generic prompt
        system_prompt = get_generic_prompt(org_info, tone)
        
        return f"{system_prompt}\n\nDocument Information: {context_text}\n\nQuestion: {query}\n\nProvide a comprehensive, accurate, and helpful response based on the document information above."
        
    except Exception as e:
        logger.error(f"Error constructing fast RAG prompt: {e}")
        return f"Answer the following question based on the provided context:\n\nContext: {relevant_docs}\n\nQuestion: {query}\n\nAnswer:" 