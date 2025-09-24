from typing import List, Dict, Any, Optional
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.schema import Document
import requests
from bs4 import BeautifulSoup
import logging
import re
import time
from urllib.parse import urljoin, urlparse
import hashlib

logger = logging.getLogger(__name__)

class EnhancedWebSearcher:
    def __init__(self):
        self.search_tool = DuckDuckGoSearchRun()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.search_cache = {}
        self.content_cache = {}
        
        # Quality sources for different domains
        self.quality_sources = {
            'academic': ['arxiv.org', 'scholar.google.com', 'pubmed.ncbi.nlm.nih.gov', 'ieee.org', 'acm.org'],
            'technical': ['github.com', 'stackoverflow.com', 'medium.com', 'dev.to', 'hackernews.ycombinator.com'],
            'news': ['reuters.com', 'bbc.com', 'apnews.com', 'npr.org'],
            'reference': ['wikipedia.org', 'britannica.com', 'investopedia.com'],
            'official': ['.gov', '.edu', '.org']
        }
    
    def search_web(self, query: str, num_results: int = 5, search_type: str = "general") -> List[Dict[str, str]]:
        """Enhanced web search with intelligent source targeting."""
        try:
            # Check cache first
            cache_key = hashlib.md5(f"{query}_{num_results}_{search_type}".encode()).hexdigest()
            if cache_key in self.search_cache:
                logger.info(f"Using cached search results for: {query}")
                return self.search_cache[cache_key]
            
            # Enhance query based on search type
            enhanced_query = self._enhance_query(query, search_type)
            
            # Perform search
            logger.info(f"Searching web for: {enhanced_query}")
            raw_results = self.search_tool.run(enhanced_query)
            
            # Parse and structure results
            search_results = self._parse_search_results(raw_results, query, num_results)
            
            # Filter and rank results
            filtered_results = self._filter_and_rank_results(search_results, search_type)
            
            # Cache results
            self.search_cache[cache_key] = filtered_results
            
            logger.info(f"Found {len(filtered_results)} quality web search results")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return []
    
    def _enhance_query(self, query: str, search_type: str) -> str:
        """Enhance search query based on type and add relevant site filters."""
        enhanced_query = query
        
        if search_type == "academic":
            enhanced_query = f"{query} (site:arxiv.org OR site:scholar.google.com OR site:pubmed.ncbi.nlm.nih.gov)"
        elif search_type == "technical":
            enhanced_query = f"{query} (site:github.com OR site:stackoverflow.com OR site:medium.com)"
        elif search_type == "news":
            enhanced_query = f"{query} (site:reuters.com OR site:bbc.com OR site:apnews.com)"
        elif search_type == "reference":
            enhanced_query = f"{query} (site:wikipedia.org OR site:britannica.com)"
        elif search_type == "recent":
            # Add time-based keywords for recent information
            enhanced_query = f"{query} 2024 OR 2023 latest recent"
        
        return enhanced_query
    
    def _parse_search_results(self, raw_results: str, original_query: str, num_results: int) -> List[Dict[str, str]]:
        """Parse raw search results into structured format."""
        search_results = []
        
        try:
            # Split results by lines and clean
            lines = [line.strip() for line in raw_results.split('\n') if line.strip()]
            
            current_result = {}
            for line in lines:
                if len(search_results) >= num_results:
                    break
                
                # Try to identify URLs
                url_pattern = r'https?://[^\s]+'
                urls = re.findall(url_pattern, line)
                
                if urls:
                    if current_result:
                        search_results.append(current_result)
                    
                    url = urls[0]
                    current_result = {
                        'url': url,
                        'content': line,
                        'source': self._extract_domain(url),
                        'query': original_query,
                        'relevance_score': 0.5  # Default score
                    }
                elif current_result:
                    # Add to current result's content
                    current_result['content'] += f" {line}"
            
            # Add the last result
            if current_result and len(search_results) < num_results:
                search_results.append(current_result)
            
            # If no URLs found, create generic results from content
            if not search_results:
                content_chunks = [chunk.strip() for chunk in raw_results.split('.') if len(chunk.strip()) > 50]
                for i, chunk in enumerate(content_chunks[:num_results]):
                    search_results.append({
                        'content': chunk,
                        'source': f'web_search_{i}',
                        'query': original_query,
                        'url': None,
                        'relevance_score': 0.4
                    })
            
        except Exception as e:
            logger.error(f"Error parsing search results: {e}")
            # Fallback: create single result from raw content
            search_results = [{
                'content': raw_results[:1000],
                'source': 'web_search_fallback',
                'query': original_query,
                'url': None,
                'relevance_score': 0.3
            }]
        
        return search_results
    
    def _filter_and_rank_results(self, results: List[Dict[str, str]], search_type: str) -> List[Dict[str, str]]:
        """Filter and rank results based on quality indicators."""
        scored_results = []
        
        for result in results:
            score = result.get('relevance_score', 0.5)
            source = result.get('source', '').lower()
            content = result.get('content', '').lower()
            
            # Quality source bonus
            for category, domains in self.quality_sources.items():
                for domain in domains:
                    if domain in source:
                        if category == 'academic' and search_type in ['academic', 'technical']:
                            score += 0.3
                        elif category == 'technical' and search_type == 'technical':
                            score += 0.2
                        elif category == 'reference':
                            score += 0.15
                        elif category == 'official':
                            score += 0.1
                        break
            
            # Content quality indicators
            quality_indicators = [
                'research', 'study', 'analysis', 'data', 'findings',
                'methodology', 'results', 'conclusion', 'evidence'
            ]
            
            quality_score = sum(1 for indicator in quality_indicators if indicator in content)
            score += min(quality_score * 0.05, 0.2)  # Cap bonus at 0.2
            
            # Length penalty for very short content
            if len(result.get('content', '')) < 100:
                score -= 0.1
            
            result['final_score'] = score
            scored_results.append(result)
        
        # Sort by score and return top results
        scored_results.sort(key=lambda x: x['final_score'], reverse=True)
        return scored_results
    
    def fetch_webpage_content(self, url: str, max_length: int = 3000) -> str:
        """Fetch and extract enhanced content from a webpage."""
        try:
            # Check cache
            cache_key = hashlib.md5(url.encode()).hexdigest()
            if cache_key in self.content_cache:
                return self.content_cache[cache_key]
            
            logger.info(f"Fetching content from: {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'ad']):
                element.decompose()
            
            # Extract main content areas
            main_content = ""
            
            # Try to find main content containers
            content_selectors = [
                'main', 'article', '.content', '.main-content', 
                '.article-body', '.post-content', '#content'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    main_content = content_elem.get_text()
                    break
            
            # Fallback to body content
            if not main_content:
                main_content = soup.get_text()
            
            # Clean and format text
            lines = (line.strip() for line in main_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit length
            if len(clean_text) > max_length:
                clean_text = clean_text[:max_length] + "..."
            
            # Cache the result
            self.content_cache[cache_key] = clean_text
            
            return clean_text
            
        except Exception as e:
            logger.error(f"Error fetching webpage {url}: {e}")
            return f"Error fetching content from {url}"
    
    def search_and_extract(self, query: str, num_results: int = 3, search_type: str = "general") -> List[Document]:
        """Enhanced search and extract with intelligent content processing."""
        search_results = self.search_web(query, num_results, search_type)
        documents = []
        
        for i, result in enumerate(search_results):
            # Use existing content or fetch from URL if available
            content = result['content']
            
            if result.get('url') and len(content) < 200:
                # Try to fetch more detailed content
                webpage_content = self.fetch_webpage_content(result['url'])
                if len(webpage_content) > len(content):
                    content = webpage_content
            
            # Enhance content with metadata
            enhanced_content = self._enhance_content(content, result)
            
            doc = Document(
                page_content=enhanced_content,
                metadata={
                    'source': result['source'],
                    'source_type': 'web_search',
                    'search_type': search_type,
                    'query': query,
                    'url': result.get('url'),
                    'relevance_score': result.get('final_score', 0.5),
                    'chunk_id': f"web_{hashlib.md5((query + str(i)).encode()).hexdigest()[:8]}",
                    'content_length': len(content),
                    'fetch_timestamp': time.time()
                }
            )
            documents.append(doc)
        
        return documents
    
    def _enhance_content(self, content: str, result: Dict[str, str]) -> str:
        """Enhance content with context and formatting."""
        enhanced = content
        
        # Add source context
        source = result.get('source', 'Unknown')
        if source != 'Unknown':
            enhanced = f"[Source: {source}]\n{enhanced}"
        
        # Add query context
        query = result.get('query', '')
        if query and query.lower() not in enhanced.lower():
            enhanced = f"[Related to: {query}]\n{enhanced}"
        
        return enhanced
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return 'unknown'
    
    def get_search_suggestions(self, query: str) -> List[str]:
        """Generate search suggestions for better results."""
        suggestions = []
        
        # Add technical variants
        tech_terms = {
            'ai': ['artificial intelligence', 'machine learning', 'neural networks'],
            'ml': ['machine learning', 'predictive modeling', 'algorithms'],
            'crypto': ['cryptocurrency', 'blockchain', 'digital currency'],
            'security': ['cybersecurity', 'information security', 'data protection']
        }
        
        query_lower = query.lower()
        for abbrev, expansions in tech_terms.items():
            if abbrev in query_lower:
                for expansion in expansions:
                    suggestions.append(query.replace(abbrev, expansion))
        
        # Add contextual suggestions
        if 'how' in query_lower:
            suggestions.append(query.replace('how', 'guide to'))
            suggestions.append(query.replace('how', 'tutorial'))
        
        if 'what' in query_lower:
            suggestions.append(query.replace('what is', 'definition of'))
            suggestions.append(query.replace('what are', 'types of'))
        
        return suggestions[:5]

# For backward compatibility
WebSearcher = EnhancedWebSearcher