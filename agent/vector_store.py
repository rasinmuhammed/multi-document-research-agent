from typing import List, Dict, Any, Optional
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
import logging

logger = logging.getLogger(__name__)

class VectorStoreManager:
    def __init__(self, persist_directory: str = "./data/chroma_db"):
        self.persist_directory = persist_directory
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        self.vectorstore = None
        self._initialize_vectorstore()
    
    def _initialize_vectorstore(self):
        """Initialize or load existing vector store."""
        try:
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            logger.info("Vector store initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            raise
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to the vector store."""
        if not documents:
            return []
        
        try:
            ids = self.vectorstore.add_documents(documents)
            self.vectorstore.persist()
            logger.info(f"Added {len(documents)} documents to vector store")
            return ids
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return []
    
    def similarity_search(self, query: str, k: int = 5, filter_dict: Optional[Dict] = None) -> List[Document]:
        """Search for similar documents."""
        try:
            results = self.vectorstore.similarity_search(
                query=query,
                k=k,
                filter=filter_dict
            )
            logger.info(f"Retrieved {len(results)} similar documents")
            return results
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []
    
    def similarity_search_with_score(self, query: str, k: int = 5) -> List[tuple]:
        """Search with relevance scores."""
        try:
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=k
            )
            return results
        except Exception as e:
            logger.error(f"Error in similarity search with score: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the current collection."""
        try:
            collection = self.vectorstore._collection
            return {
                'count': collection.count(),
                'name': collection.name
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}