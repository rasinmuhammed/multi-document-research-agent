import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import re

from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from langchain.tools import StructuredTool

from .document_processor import DocumentProcessor
from .vector_store import VectorStoreManager
from .web_searcher import WebSearcher

logger = logging.getLogger(__name__)

# -----------------------------
ic Schem/*************  ✨ Windsurf Command ⭐  *************/
        """
        Initialize the ResearchAgent.

        Args:
            groq_api_key (str): The API key for the Groq LLM.
            documents_dir (str, optional): The directory containing the initial documents to load. Defaults to "./documents".
        """
/*******  443af45d-9c6d-4c1c-a5b2-4eb74d2e6e84  *******/as for Tools
# -----------------------------
class LocalDocInput(BaseModel):
    query: str = Field(description="The search query for local documents.")

class WebSearchInput(BaseModel):
    query: str = Field(description="The search query for web resources.")


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
            model_name="llama-3.1-8b-instant",
            temperature=0.1,
            max_tokens=4000
        )
        
        # Load documents
        self._load_initial_documents()
        
        # Create agent
        self.agent_executor = self._create_agent()
    
    def _load_initial_documents(self):
        """Load and index initial documents."""
        if os.path.exists(self.documents_dir):
            documents = self.doc_processor.load_documents(self.documents_dir)
            if documents:
                self.vector_store.add_documents(documents)
                logger.info(f"Indexed {len(documents)} document chunks")
    
    # -----------------------------
    # Tool Functions
    # -----------------------------
    def _search_local_documents(self, query: str) -> str:
        """Search through local documents for relevant information."""
        try:
            results = self.vector_store.similarity_search_with_score(query, k=5)
            if not results:
                return "No relevant local documents found."
            
            formatted_results = []
            for i, (doc, score) in enumerate(results):
                source = doc.metadata.get('source_file', 'unknown')
                chunk_id = doc.metadata.get('chunk_id', f'chunk_{i}')
                formatted_results.append(
                    f"[LOCAL-{chunk_id}] Source: {source} (Relevance: {1-score:.3f})\n"
                    f"Content: {doc.page_content[:500]}...\n"
                )
            return "\n".join(formatted_results)
        except Exception as e:
            logger.error(f"Error searching local documents: {e}")
            return f"Error searching local documents: {str(e)}"

    def _search_web_resources(self, query: str) -> str:
        """Search web resources for current information and reliable sources."""
        try:
            web_docs = self.web_searcher.search_and_extract(query, num_results=3)
            if not web_docs:
                return "No relevant web resources found."
            
            self.vector_store.add_documents(web_docs)
            
            formatted_results = []
            for doc in web_docs:
                chunk_id = doc.metadata.get('chunk_id', 'web_unknown')
                formatted_results.append(
                    f"[WEB-{chunk_id}] Source: Web Search\n"
                    f"Content: {doc.page_content[:500]}...\n"
                )
            return "\n".join(formatted_results)
        except Exception as e:
            logger.error(f"Error searching web: {e}")
            return f"Error searching web resources: {str(e)}"

    # -----------------------------
    # Agent Creation
    # -----------------------------
    def _create_agent(self) -> AgentExecutor:
        """Create the research agent with tools."""
        
        tools = [
            StructuredTool.from_function(
                func=self._search_local_documents,
                name="search_local_documents",
                description="Search through local PDF and Markdown documents for relevant information. Use this for domain-specific knowledge, research papers, or internal documentation.",
                args_schema=LocalDocInput
            ),
            StructuredTool.from_function(
                func=self._search_web_resources,
                name="search_web_resources", 
                description="Search web resources including Wikipedia, arXiv, and other reliable sources. Use this for current information, general knowledge, or when local documents don't have sufficient information.",
                args_schema=WebSearchInput
            )
        ]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert research assistant that helps users answer complex questions by searching through both local documents and web resources.

Your approach should be:
1. **Plan**: Break down the user's question into specific search queries
2. **Search**: Use both local documents and web resources strategically
3. **Synthesize**: Combine information from multiple sources
4. **Cite**: Always provide clear citations and traceability

When generating responses:
- Always cite sources using format [SOURCE-ID] 
- Provide bullet points for key findings
- Include a summary with actionable insights
- Maintain objectivity and acknowledge limitations
- If information conflicts between sources, note the discrepancy

For complex questions, search multiple times with different query formulations to ensure comprehensive coverage."""),
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
            max_iterations=5,
            return_intermediate_steps=True
        )
    
    # -----------------------------
    # Research Workflow
    # -----------------------------
    def research(self, question: str) -> Dict[str, Any]:
        """Conduct research and return structured results."""
        try:
            logger.info(f"Starting research for question: {question}")
            
            result = self.agent_executor.invoke({"input": question})
            
            # Handle both possible keys
            answer = result.get("output") or result.get("output_text", "")
            
            structured_response = {
                "question": question,
                "timestamp": datetime.now().isoformat(),
                "answer": answer,
                "intermediate_steps": result.get("intermediate_steps", []),
                "sources_used": self._extract_sources_from_steps(result.get("intermediate_steps", [])),
                "confidence_level": "high" if len(result.get("intermediate_steps", [])) >= 2 else "medium"
            }
            
            return structured_response
            
        except Exception as e:
            logger.error(f"Error in research: {e}")
            return {
                "question": question,
                "timestamp": datetime.now().isoformat(),
                "answer": f"Error occurred during research: {str(e)}",
                "intermediate_steps": [],
                "sources_used": [],
                "confidence_level": "low"
            }
    
    def _extract_sources_from_steps(self, steps: List[tuple]) -> List[str]:
        """Extract unique sources from intermediate steps."""
        sources = set()
        for step in steps:
            if len(step) >= 2:
                observation = str(step[1])
                matches = re.findall(r'\[([^\]]+)\]', observation)
                sources.update(matches)
        return list(sources)
    
    # -----------------------------
    # Report Generation
    # -----------------------------
    def generate_report(self, research_result: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """Generate a formatted research report."""
        
        report = f"""# Research Report

## Question
{research_result['question']}

## Executive Summary
{research_result['answer']}

## Research Process
- **Timestamp**: {research_result['timestamp']}
- **Confidence Level**: {research_result['confidence_level']}
- **Sources Consulted**: {len(research_result['sources_used'])}

## Sources Used
"""
        for i, source in enumerate(research_result['sources_used'], 1):
            report += f"{i}. {source}\n"
        
        report += f"""
## Research Steps
Total research iterations: {len(research_result['intermediate_steps'])}

"""
        for i, step in enumerate(research_result['intermediate_steps'], 1):
            if len(step) >= 2:
                action = step[0]
                observation = step[1]
                report += f"### Step {i}: {action.tool if hasattr(action, 'tool') else 'Unknown'}\n"
                report += f"**Query**: {action.tool_input if hasattr(action, 'tool_input') else 'N/A'}\n"
                report += f"**Result**: {str(observation)[:500]}...\n\n"
        
        report += """
---
*Generated by Multi-Document Research Agent*
"""
        
        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Report saved to {output_file}")
        
        return report
