import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import re
import hashlib

from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from langchain.tools import StructuredTool

from .document_processor import DocumentProcessor
from .vector_store import VectorStoreManager
from .web_searcher import WebSearcher

logger = logging.getLogger(__name__)

class ResearchAgent:
    def __init__(self, groq_api_key: str, documents_dir: str = "./documents"):
        self.groq_api_key = groq_api_key
        self.documents_dir = documents_dir
        
        # Initialize components
        self.doc_processor = DocumentProcessor()
        self.vector_store = VectorStoreManager()
        self.web_searcher = WebSearcher()
        
        # Initialize LLM
        self.llm = ChatGroq(
            groq_api_key=groq_api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=8000
        )
        
        # Citation tracking
        self.citation_counter = 0
        self.source_registry = {}
        
        # Load documents
        self._load_initial_documents()
        
        # Create agent
        self.agent_executor = self._create_agent()
    
    def _load_initial_documents(self):
        """Load and index initial documents."""
        if os.path.exists(self.documents_dir) and os.listdir(self.documents_dir):
            documents = self.doc_processor.load_documents(self.documents_dir)
            if documents:
                self.vector_store.rebuild_from_documents(documents)
                logger.info(f"Indexed {len(documents)} document chunks")
    
    def _generate_source_alias(self, source_info: Dict[str, str]) -> str:
        """Generate a clean alias for sources."""
        source_type = source_info.get('type', 'unknown')
        
        if source_type == 'local':
            # For local documents, use clean filename
            name = source_info.get('name', 'Unknown')
            if '/' in name:
                name = os.path.basename(name)
            # Remove file extension for display
            if '.' in name:
                name = '.'.join(name.split('.')[:-1])
            return f"Doc: {name}"
        
        elif source_type == 'web':
            # For web sources, extract domain
            url = source_info.get('url', '')
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                if domain:
                    # Clean up common prefixes
                    if domain.startswith('www.'):
                        domain = domain[4:]
                    return f"Web: {domain}"
            except:
                pass
            return "Web: External Source"
        
        return f"{source_type.title()}: Source"
    
    def _register_source(self, source_info: Dict[str, str]) -> str:
        """Register a source and return its citation ID."""
        # Create a unique key for the source
        source_key = f"{source_info.get('type', '')}-{source_info.get('name', '')}-{source_info.get('url', '')}"
        source_hash = hashlib.md5(source_key.encode()).hexdigest()[:8]
        
        if source_hash not in self.source_registry:
            self.citation_counter += 1
            self.source_registry[source_hash] = {
                'id': self.citation_counter,
                'alias': self._generate_source_alias(source_info),
                'info': source_info
            }
        
        return f"[{self.source_registry[source_hash]['id']}]"
    
    def _search_local_documents(self, query: str) -> str:
        """Search through local documents with enhanced citation tracking."""
        try:
            results = self.vector_store.similarity_search(query, k=5)
            if not results:
                return "No relevant local documents found."
            
            formatted_results = []
            for i, doc in enumerate(results):
                source_file = doc['metadata'].get('source_file', 'unknown')
                chunk_id = doc['metadata'].get('chunk_id', f'chunk_{i}')
                score = doc.get('score', 0.0)
                relevance = 1 - score
                
                # Register source for citation
                source_info = {
                    'type': 'local',
                    'name': source_file,
                    'url': None
                }
                citation_id = self._register_source(source_info)
                
                formatted_results.append(
                    f"{citation_id} {self._generate_source_alias(source_info)} (Relevance: {relevance:.3f})\n"
                    f"Content: {doc['page_content'][:600]}...\n"
                )
            return "\n".join(formatted_results)
            
        except Exception as e:
            logger.error(f"Error searching local documents: {e}")
            return f"Error searching local documents: {str(e)}"

    def _search_web_resources(self, query: str) -> str:
        """Search web resources with enhanced citation tracking."""
        try:
            web_docs = self.web_searcher.search_and_extract(query, num_results=3)
            if not web_docs:
                return "No relevant web resources found."
            
            formatted_results = []
            for doc in web_docs:
                source_url = doc.metadata.get('source', 'unknown url')
                title = doc.metadata.get('title', 'Unknown Title')
                
                # Register source for citation
                source_info = {
                    'type': 'web',
                    'name': title,
                    'url': source_url
                }
                citation_id = self._register_source(source_info)
                
                formatted_results.append(
                    f"{citation_id} {self._generate_source_alias(source_info)}\n"
                    f"Title: {title}\n"
                    f"Content: {doc.page_content[:600]}...\n"
                )
            return "\n".join(formatted_results)
            
        except Exception as e:
            logger.error(f"Error searching web: {e}")
            return f"Error searching web resources: {str(e)}"

    def _create_agent(self) -> AgentExecutor:
        """Create the research agent with enhanced prompting."""
        
        tools = [
            StructuredTool.from_function(
                func=self._search_local_documents,
                name="search_local_documents",
                description="Search through local PDF and Markdown documents for relevant information. Use this for domain-specific knowledge, research papers, or internal documentation. Returns content with citation IDs.",
            ),
            StructuredTool.from_function(
                func=self._search_web_resources, 
                name="search_web_resources", 
                description="Search web resources including Wikipedia, arXiv, and other reliable sources. Use this for current information, general knowledge, or when local documents don't have sufficient information. Returns content with citation IDs.",
            )
        ]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Orbuculum.ai, an expert research assistant that provides comprehensive, well-cited answers by searching through both local documents and web resources.

**Your approach should be:**
1. **Plan**: Break down complex questions into specific search queries
2. **Search**: Use both local documents and web resources strategically. For comprehensive answers, use multiple targeted searches
3. **Synthesize**: Combine information from multiple sources into a coherent, well-structured response
4. **Cite**: Always include proper citations using the provided citation IDs

**Response formatting guidelines:**
- Provide comprehensive answers (minimum 3 paragraphs for complex topics)
- Use the exact citation IDs provided in search results (e.g., [1], [2], [3])
- Place citations immediately after the relevant information
- Structure your response with clear paragraphs and logical flow
- Include key findings as bullet points when appropriate, each with its own citation
- End with a brief summary or actionable insights when relevant
- Maintain objectivity and acknowledge limitations or conflicting information

**Citation rules:**
- Always use the exact citation format provided in search results: [1], [2], etc.
- Place citations right after the specific claim or information
- Multiple sources can support one claim: [1][2]
- Never make up or modify citation numbers

**Quality standards:**
- Provide detailed, informative responses
- Connect information across sources when relevant
- Highlight key insights and implications
- Be transparent about uncertainty or conflicting information
- Maintain professional, academic tone while being accessible
"""),
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
            max_iterations=6,
            return_intermediate_steps=True
        )
    
    def research(self, question: str) -> Dict[str, Any]:
        """Conduct research with enhanced citation management."""
        try:
            # Reset citation tracking for new research
            self.citation_counter = 0
            self.source_registry = {}
            
            logger.info(f"Starting research for question: {question}")
            
            result = self.agent_executor.invoke({"input": question})
            
            answer = result.get("output") or result.get("output_text", "")
            intermediate_steps = result.get("intermediate_steps", [])
            
            # Compile sources from registry
            sources_used = []
            for source_hash, source_data in self.source_registry.items():
                source_info = source_data['info']
                sources_used.append({
                    "id": source_data['id'],
                    "type": source_info['type'],
                    "name": source_info['name'],
                    "url": source_info.get('url'),
                    "alias": source_data['alias']
                })
            
            # Sort sources by ID
            sources_used.sort(key=lambda x: x['id'])
            
            structured_response = {
                "question": question,
                "timestamp": datetime.now().isoformat(),
                "answer": answer,
                "intermediate_steps": intermediate_steps,
                "sources_used": sources_used,
                "confidence_level": self._assess_confidence(intermediate_steps, len(sources_used))
            }
            
            return structured_response
            
        except Exception as e:
            logger.error(f"Error in research: {e}")
            return {
                "question": question,
                "timestamp": datetime.now().isoformat(),
                "answer": f"I encountered an error while researching: {str(e)}",
                "intermediate_steps": [],
                "sources_used": [],
                "confidence_level": "low"
            }
    
    def _assess_confidence(self, steps: List, num_sources: int) -> str:
        """Assess confidence level based on research depth and source diversity."""
        if len(steps) >= 3 and num_sources >= 3:
            return "high"
        elif len(steps) >= 2 and num_sources >= 2:
            return "medium"
        else:
            return "low"
    
    def generate_report(self, research_result: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """Generate a formatted research report with improved structure."""
        
        timestamp = research_result.get('timestamp', datetime.now().isoformat())
        date_str = timestamp[:10]
        time_str = timestamp[11:19]
        
        report = f"""# Orbuculum.ai Research Report

**Generated on:** {date_str} at {time_str}  
**Confidence Level:** {research_result['confidence_level'].title()}  
**Sources Consulted:** {len(research_result['sources_used'])}  

---

## Research Question
> {research_result['question']}

---

## Executive Summary
{research_result['answer']}

---

## Sources Referenced

"""
        
        for source in research_result['sources_used']:
            source_type_icon = "📄" if source['type'] == 'local' else "🌐"
            report += f"**[{source['id']}]** {source_type_icon} {source['name']}\n"
            if source.get('url'):
                report += f"   - URL: {source['url']}\n"
            report += f"   - Type: {source['type'].title()}\n\n"

        report += """---

## Research Methodology

"""
        
        for i, step in enumerate(research_result['intermediate_steps'], 1):
            if len(step) >= 2:
                action = step[0]
                observation = step[1]
                tool_name = action.tool if hasattr(action, 'tool') else 'Unknown Tool'
                tool_input = action.tool_input if hasattr(action, 'tool_input') else 'N/A'
                
                if isinstance(tool_input, dict):
                    display_input = tool_input.get('query', str(tool_input))
                else:
                    display_input = str(tool_input)

                report += f"### Step {i}: {tool_name}\n"
                report += f"**Query:** {display_input}\n\n"
                
                # Truncate long observations for readability
                obs_text = str(observation)
                if len(obs_text) > 1000:
                    obs_text = obs_text[:1000] + "... [truncated for brevity]"
                
                report += f"**Results:** {obs_text}\n\n"

        report += f"""---

## Report Metadata
- **Generated by:** Orbuculum.ai Research Assistant
- **Total Research Steps:** {len(research_result['intermediate_steps'])}
- **Processing Time:** Research completed at {time_str}
- **Report ID:** {research_result.get('report_id', 'N/A')}

---
*This report was automatically generated by Orbuculum.ai. All sources have been verified and cited appropriately.*
"""
        
        if output_file:
            try:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report)
                logger.info(f"Report saved to {output_file}")
            except Exception as e:
                logger.error(f"Failed to save report to {output_file}: {e}")
        
        return report