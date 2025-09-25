from typing import List, Dict, Any
from langchain_community.tools import DuckDuckGoSearchResults
from langchain.schema import Document
import requests
from bs4 import BeautifulSoup
import logging
import json
import re

logger = logging.getLogger(__name__)

class WebSearcher:
    def __init__(self):
        self.search_tool = DuckDuckGoSearchResults()

    def search_web(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Search the web and return structured results."""
        try:
            results_str = self.search_tool.run(query)
            logger.info(f"Raw search results: {results_str}")

            # Use regex to parse the string into a list of dictionaries
            results = []
            for item in re.findall(r'snippet: (.*?),\s*title: (.*?),\s*link: (.*?)(?:,|$)', results_str):
                results.append({
                    "snippet": item[0],
                    "title": item[1],
                    "link": item[2]
                })

            search_results = []
            for item in results[:num_results]:
                search_results.append({
                    'content': item.get('snippet', 'No snippet available.'),
                    'source': item.get('link', 'No link available'),
                    'title': item.get('title', 'No title'),
                    'query': query
                })

            logger.info(f"Found {len(search_results)} web search results")
            return search_results

        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return []


    def fetch_webpage_content(self, url: str) -> str:
        """Fetch and extract text content from a webpage."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text content
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            return text[:5000]  # Limit content length

        except Exception as e:
            logger.error(f"Error fetching webpage {url}: {e}")
            return ""

    def search_and_extract(self, query: str, num_results: int = 3) -> List[Document]:
        """Search web and return as Document objects."""
        search_results = self.search_web(query, num_results)
        documents = []

        for i, result in enumerate(search_results):
            doc = Document(
                page_content=result['content'],
                metadata={
                    'source': result['source'],
                    'source_type': 'web_search',
                    'title': result['title'],
                    'query': query,
                    'chunk_id': f"web_{hash(query)}_{i}"
                }
            )
            documents.append(doc)

        return documents