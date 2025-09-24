import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
import re
import json

from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from langchain.tools import StructuredTool
from langchain.schema import Document

from .document_processor import DocumentProcessor
from .vector_store import VectorStoreManager
from .web_searcher import WebSearcher

logger = logging.getLogger(__name__)

class LocalDocInput(BaseModel):
    query: str = Field(description="The search query for local documents.")

class WebSearchInput(BaseModel):
    query: str = Field(description="The search query for web resources.")

class AnalysisInput(BaseModel):
    content: str = Field(description="Content to analyze for key insights.")

class EnhancedResearchAgent:
    def __init__(self, groq_api_key: str, documents_dir: str = "./documents"):
        self.groq_api_key = groq_api_key
        self.documents_dir = documents_dir
        
        # Initialize components
        self.doc_processor = DocumentProcessor()
        self.vector_store = VectorStoreManager()
        self.web_searcher = WebSearcher()
        
        # Initialize LLM with enhanced settings
        self.llm = ChatGroq(
            groq_api_key=groq_api_key,
            model_name="llama-3.1-8b-instant",
            temperature=0.1,
            max_tokens=4000,
            max_retries=3
        )
        
        # Research state tracking
        self.current_research_context = {}
        self.search_cache = {}
        
        # Load documents
        self._load_initial_documents()
        
        # Create enhanced agent
        self.agent_executor = self._create_enhanced_agent()
    
    def _load_initial_documents(self):
        """Load and index initial documents with enhanced metadata."""
        if os.path.exists(self.documents_dir):
            documents = self.doc_processor.load_documents(self.documents_dir)
            if documents:
                # Enhance documents with topic analysis
                enhanced_docs = self._enhance_documents_with_topics(documents)
                self.vector_store.add_documents(enhanced_docs)
                logger.info(f"Indexed {len(enhanced_docs)} enhanced document chunks")
    
    def _enhance_documents_with_topics(self, documents: List[Document]) -> List[Document]:
        """Enhance documents with topic extraction and categorization."""
        enhanced_docs = []
        
        for doc in documents:
            # Basic topic extraction using keywords
            content = doc.page_content.lower()
            topics = []
            
            # Technical topics
            tech_keywords = {
                'ai': ['artificial intelligence', 'machine learning', 'neural network', 'deep learning'],
                'cybersecurity': ['security', 'encryption', 'vulnerability', 'threat', 'firewall'],
                'quantum': ['quantum computing', 'qubit', 'quantum', 'superposition'],
                'blockchain': ['blockchain', 'cryptocurrency', 'bitcoin', 'smart contract'],
                'cloud': ['cloud computing', 'aws', 'azure', 'docker', 'kubernetes'],
                'data': ['data science', 'analytics', 'big data', 'database', 'visualization']
            }
            
            for topic, keywords in tech_keywords.items():
                if any(keyword in content for keyword in keywords):
                    topics.append(topic)
            
            # Update metadata
            doc.metadata.update({
                'topics': topics,
                'content_length': len(doc.page_content),
                'enhanced': True
            })
            
            enhanced_docs.append(doc)
        
        return enhanced_docs
    
    def _search_local_documents(self, query: str) -> str:
        """Enhanced local document search with intelligent ranking."""
        try:
            # Check cache first
            cache_key = f"local_{hash(query)}"
            if cache_key in self.search_cache:
                logger.info(f"Using cached local search results for: {query}")
                return self.search_cache[cache_key]
            
            # Multi-level search strategy
            results = []
            
            # 1. Primary search
            primary_results = self.vector_store.similarity_search_with_score(query, k=3)
            results.extend(primary_results)
            
            # 2. Keyword-enhanced search if primary results are limited
            if len(primary_results) < 2:
                keywords = self._extract_keywords(query)
                for keyword in keywords[:2]:
                    keyword_results = self.vector_store.similarity_search_with_score(keyword, k=2)
                    results.extend(keyword_results)
            
            # Remove duplicates and sort by relevance
            unique_results = {}
            for doc, score in results:
                chunk_id = doc.metadata.get('chunk_id', 'unknown')
                if chunk_id not in unique_results or score < unique_results[chunk_id][1]:
                    unique_results[chunk_id] = (doc, score)
            
            final_results = list(unique_results.values())[:5]
            
            if not final_results:
                result = "No relevant local documents found."
            else:
                formatted_results = []
                for i, (doc, score) in enumerate(final_results):
                    source = doc.metadata.get('source_file', 'unknown')
                    chunk_id = doc.metadata.get('chunk_id', f'chunk_{i}')
                    topics = doc.metadata.get('topics', [])
                    relevance = 1 - score
                    
                    formatted_results.append(
                        f"[LOCAL-{chunk_id}] Source: {source} | Topics: {', '.join(topics)} | Relevance: {relevance:.3f}\n"
                        f"Content: {doc.page_content[:600]}...\n"
                    )
                result = "\n".join(formatted_results)
            
            # Cache result
            self.search_cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"Error searching local documents: {e}")
            return f"Error searching local documents: {str(e)}"
    
    def _search_web_resources(self, query: str) -> str:
        """Enhanced web search with intelligent source selection."""
        try:
            # Check cache first
            cache_key = f"web_{hash(query)}"
            if cache_key in self.search_cache:
                logger.info(f"Using cached web search results for: {query}")
                return self.search_cache[cache_key]
            
            # Enhanced web search with multiple strategies
            web_docs = []
            
            # 1. Direct search
            direct_results = self.web_searcher.search_and_extract(query, num_results=3)
            web_docs.extend(direct_results)
            
            # 2. Alternative query formulations for better coverage
            alt_queries = self._generate_alternative_queries(query)
            for alt_query in alt_queries[:2]:
                alt_results = self.web_searcher.search_and_extract(alt_query, num_results=2)
                web_docs.extend(alt_results)
            
            if not web_docs:
                result = "No relevant web resources found."
            else:
                # Add to vector store for future reference
                self.vector_store.add_documents(web_docs)
                
                # Format results with enhanced metadata
                formatted_results = []
                for doc in web_docs[:5]:  # Limit to top 5
                    chunk_id = doc.metadata.get('chunk_id', 'web_unknown')
                    source_query = doc.metadata.get('query', query)
                    
                    formatted_results.append(
                        f"[WEB-{chunk_id}] Query: {source_query}\n"
                        f"Content: {doc.page_content[:600]}...\n"
                    )
                result = "\n".join(formatted_results)
            
            # Cache result
            self.search_cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"Error searching web: {e}")
            return f"Error searching web resources: {str(e)}"
    
    def _analyze_content(self, content: str) -> str:
        """Analyze content for key insights and patterns."""
        try:
            # Extract key entities, topics, and insights
            analysis_prompt = f"""
            Analyze the following content and provide key insights:
            
            Content: {content[:2000]}...
            
            Provide:
            1. Main topics and themes
            2. Key findings or claims
            3. Important entities (people, organizations, technologies)
            4. Potential gaps or areas needing more information
            
            Keep the analysis concise and focused.
            """
            
            response = self.llm.invoke(analysis_prompt)
            return f"[ANALYSIS] {response.content}"
            
        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            return f"Error analyzing content: {str(e)}"
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract key terms from query for enhanced search."""
        # Simple keyword extraction - could be enhanced with NLP libraries
        import re
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'about'}
        
        # Extract meaningful terms
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        
        return keywords[:5]  # Top 5 keywords
    
    def _generate_alternative_queries(self, original_query: str) -> List[str]:
        """Generate alternative query formulations for comprehensive search."""
        keywords = self._extract_keywords(original_query)
        
        alternatives = []
        
        # Keyword combinations
        if len(keywords) >= 2:
            alternatives.append(f"{keywords[0]} {keywords[1]}")
        
        # Add technical variants
        tech_variants = {
            'ai': 'artificial intelligence',
            'ml': 'machine learning',
            'crypto': 'cryptocurrency',
            'tech': 'technology',
            'comp': 'computer'
        }
        
        for abbrev, full in tech_variants.items():
            if abbrev in original_query.lower():
                alternatives.append(original_query.lower().replace(abbrev, full))
        
        return alternatives[:3]
    
    def _create_enhanced_agent(self) -> AgentExecutor:
        """Create an enhanced research agent with intelligent tools."""
        
        tools = [
            StructuredTool.from_function(
                func=self._search_local_documents,
                name="search_local_documents",
                description="Search through local PDF and Markdown documents. Use this first for domain-specific knowledge, research papers, or internal documentation. Provides high-quality, curated information.",
                args_schema=LocalDocInput
            ),
            StructuredTool.from_function(
                func=self._search_web_resources,
                name="search_web_resources", 
                description="Search web resources for current information, general knowledge, or when local documents lack sufficient information. Use after checking local documents or for recent developments.",
                args_schema=WebSearchInput
            ),
            StructuredTool.from_function(
                func=self._analyze_content,
                name="analyze_content",
                description="Analyze gathered content to extract key insights, identify patterns, and highlight important findings. Use this to synthesize information from multiple sources.",
                args_schema=AnalysisInput
            )
        ]
        
        # Enhanced system prompt with better reasoning
        system_prompt = """You are an expert AI research assistant with advanced analytical capabilities. Your goal is to provide comprehensive, accurate, and well-sourced answers to complex questions.

**Research Methodology:**
1. **Question Analysis**: Break down the question to understand what information is needed
2. **Strategic Search**: Start with local documents, then expand to web resources if needed
3. **Information Synthesis**: Combine information from multiple sources intelligently
4. **Quality Assessment**: Evaluate source reliability and information quality
5. **Comprehensive Response**: Provide detailed answers with proper citations

**Search Strategy:**
- Always search local documents FIRST - they contain curated, high-quality information
- Use web search for recent information, current events, or when local sources are insufficient
- Try multiple search queries with different keywords if initial results are limited
- Use content analysis to extract key insights from gathered information

**Response Format:**
- Start with a direct answer to the question
- Provide detailed explanations with supporting evidence
- Use clear source citations: [LOCAL-chunk_id] or [WEB-chunk_id]
- Include confidence assessment and any limitations
- Suggest follow-up questions or related topics when relevant

**Quality Standards:**
- Prioritize accuracy over speed
- Always cite sources for claims
- Acknowledge uncertainties or conflicting information
- Provide balanced perspectives when appropriate
- Focus on actionable insights and practical implications

Remember: Your goal is to be thorough, accurate, and helpful. Take time to search comprehensively and synthesize information thoughtfully."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=8,  # Increased for more thorough research
            return_intermediate_steps=True,
            handle_parsing_errors=True
        )
    
    def research(self, question: str) -> Dict[str, Any]:
        """Conduct enhanced research with intelligent planning."""
        try:
            logger.info(f"Starting enhanced research for: {question}")
            
            # Initialize research context
            self.current_research_context = {
                'question': question,
                'start_time': datetime.now(),
                'search_queries_used': [],
                'sources_found': set()
            }
            
            # Conduct research
            result = self.agent_executor.invoke({"input": question})
            
            # Extract and enhance results
            answer = result.get("output", "No answer generated")
            intermediate_steps = result.get("intermediate_steps", [])
            
            # Enhanced source extraction
            sources_used = self._extract_enhanced_sources(intermediate_steps)
            
            # Calculate research quality metrics
            quality_metrics = self._calculate_research_quality(intermediate_steps, sources_used)
            
            structured_response = {
                "question": question,
                "timestamp": datetime.now().isoformat(),
                "answer": answer,
                "intermediate_steps": intermediate_steps,
                "sources_used": sources_used,
                "confidence_level": quality_metrics['confidence'],
                "research_depth": quality_metrics['depth'],
                "source_diversity": quality_metrics['diversity'],
                "total_research_time": (datetime.now() - self.current_research_context['start_time']).total_seconds()
            }
            
            logger.info(f"Enhanced research completed - Confidence: {quality_metrics['confidence']}, Sources: {len(sources_used)}")
            return structured_response
            
        except Exception as e:
            logger.error(f"Error in enhanced research: {e}")
            return {
                "question": question,
                "timestamp": datetime.now().isoformat(),
                "answer": f"Research error occurred: {str(e)}. Please try rephrasing your question or check the system status.",
                "intermediate_steps": [],
                "sources_used": [],
                "confidence_level": "low",
                "research_depth": "minimal",
                "source_diversity": "none",
                "error": str(e)
            }
    
    def _extract_enhanced_sources(self, steps: List[tuple]) -> List[str]:
        """Extract and categorize sources with enhanced metadata."""
        sources = set()
        
        for step in steps:
            if len(step) >= 2:
                observation = str(step[1])
                
                # Extract source IDs with patterns
                local_matches = re.findall(r'\[LOCAL-([^\]]+)\]', observation)
                web_matches = re.findall(r'\[WEB-([^\]]+)\]', observation)
                analysis_matches = re.findall(r'\[ANALYSIS\]', observation)
                
                # Add categorized sources
                for match in local_matches:
                    sources.add(f"LOCAL-{match}")
                for match in web_matches:
                    sources.add(f"WEB-{match}")
                if analysis_matches:
                    sources.add("ANALYSIS-synthesis")
        
        return sorted(list(sources))
    
    def _calculate_research_quality(self, steps: List[tuple], sources: List[str]) -> Dict[str, str]:
        """Calculate research quality metrics."""
        
        # Confidence based on multiple factors
        num_sources = len(sources)
        num_steps = len(steps)
        has_local_sources = any('LOCAL' in s for s in sources)
        has_web_sources = any('WEB' in s for s in sources)
        has_analysis = any('ANALYSIS' in s for s in sources)
        
        # Calculate confidence
        confidence_score = 0
        if num_sources >= 3: confidence_score += 30
        elif num_sources >= 2: confidence_score += 20
        elif num_sources >= 1: confidence_score += 10
        
        if has_local_sources: confidence_score += 25
        if has_web_sources: confidence_score += 20
        if has_analysis: confidence_score += 15
        if num_steps >= 3: confidence_score += 10
        
        # Map to categorical confidence
        if confidence_score >= 80:
            confidence = "very_high"
        elif confidence_score >= 60:
            confidence = "high"  
        elif confidence_score >= 40:
            confidence = "medium"
        elif confidence_score >= 20:
            confidence = "low"
        else:
            confidence = "very_low"
        
        # Research depth
        if num_steps >= 5:
            depth = "comprehensive"
        elif num_steps >= 3:
            depth = "thorough"
        elif num_steps >= 2:
            depth = "adequate"
        else:
            depth = "minimal"
        
        # Source diversity
        if has_local_sources and has_web_sources and has_analysis:
            diversity = "excellent"
        elif (has_local_sources and has_web_sources) or (num_sources >= 4):
            diversity = "good"
        elif num_sources >= 2:
            diversity = "fair"
        else:
            diversity = "limited"
        
        return {
            'confidence': confidence,
            'depth': depth,
            'diversity': diversity
        }
    
    def generate_report(self, research_result: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """Generate an enhanced research report with quality metrics."""
        
        report = f"""# Enhanced AI Research Report

## Research Question
{research_result['question']}

## Executive Summary
{research_result['answer']}

## Research Quality Assessment
- **Confidence Level**: {research_result.get('confidence_level', 'unknown').replace('_', ' ').title()}
- **Research Depth**: {research_result.get('research_depth', 'unknown').title()}
- **Source Diversity**: {research_result.get('source_diversity', 'unknown').title()}
- **Total Research Time**: {research_result.get('total_research_time', 0):.2f} seconds

## Research Methodology
- **Timestamp**: {research_result['timestamp']}
- **Sources Consulted**: {len(research_result['sources_used'])}
- **Research Iterations**: {len(research_result['intermediate_steps'])}

## Sources and Citations
"""
        # Categorize sources
        local_sources = [s for s in research_result['sources_used'] if s.startswith('LOCAL')]
        web_sources = [s for s in research_result['sources_used'] if s.startswith('WEB')]
        analysis_sources = [s for s in research_result['sources_used'] if s.startswith('ANALYSIS')]
        
        if local_sources:
            report += f"\n### 📚 Local Documents ({len(local_sources)})\n"
            for i, source in enumerate(local_sources, 1):
                report += f"{i}. {source}\n"
        
        if web_sources:
            report += f"\n### 🌐 Web Resources ({len(web_sources)})\n"
            for i, source in enumerate(web_sources, 1):
                report += f"{i}. {source}\n"
        
        if analysis_sources:
            report += f"\n### 🧠 Analysis & Synthesis ({len(analysis_sources)})\n"
            for i, source in enumerate(analysis_sources, 1):
                report += f"{i}. {source}\n"
        
        report += f"""

## Detailed Research Process
"""
        for i, step in enumerate(research_result['intermediate_steps'], 1):
            if len(step) >= 2:
                action = step[0]
                observation = step[1]
                tool_name = action.tool if hasattr(action, 'tool') else 'Unknown'
                tool_input = action.tool_input if hasattr(action, 'tool_input') else 'N/A'
                
                report += f"""
### Step {i}: {tool_name.replace('_', ' ').title()}
**Query**: {tool_input}
**Result**: {str(observation)[:800]}{'...' if len(str(observation)) > 800 else ''}
"""
        
        report += f"""

## Research Summary
This research was conducted using an enhanced AI agent that:
- Searched through {len([s for s in research_result['sources_used'] if s.startswith('LOCAL')])} local document sources
- Consulted {len([s for s in research_result['sources_used'] if s.startswith('WEB')])} web resources  
- Performed {len(research_result['intermediate_steps'])} research iterations
- Achieved {research_result.get('confidence_level', 'unknown').replace('_', ' ')} confidence level

---
*Generated by Enhanced AI Research Agent v2.0*
*Powered by Groq Llama-3.1 • LangChain • ChromaDB*
"""
        
        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Enhanced report saved to {output_file}")
        
        return report

# For backward compatibility
ResearchAgent = EnhancedResearchAgent