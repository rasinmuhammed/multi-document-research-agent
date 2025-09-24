import chromadb
from chromadb.config import Settings
import os
import logging
from typing import List, Dict, Any, Optional
import uuid

logger = logging.getLogger(__name__)

class ImprovedVectorStore:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.collection_name = "documents"
        self.client = None
        self.collection = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client with proper error handling."""
        try:
            # Ensure directory exists
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Initialize ChromaDB client with new API
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"Loaded existing collection '{self.collection_name}'")
            except Exception:
                # Collection doesn't exist, create it
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}  # Use cosine similarity
                )
                logger.info(f"Created new collection '{self.collection_name}'")
            
            logger.info("Vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    def add_documents(self, documents: List[Any]) -> bool:
        """Add documents to the vector store."""
        try:
            if not documents:
                logger.warning("No documents provided to add")
                return True
            
            # Clear existing documents first (for fresh indexing)
            self._clear_collection()
            
            # Prepare data for ChromaDB
            doc_texts = []
            metadatas = []
            ids = []
            
            for i, doc in enumerate(documents):
                # Extract text content
                if hasattr(doc, 'page_content'):
                    text = doc.page_content
                elif hasattr(doc, 'content'):
                    text = doc.content
                else:
                    text = str(doc)
                
                # Extract metadata
                if hasattr(doc, 'metadata') and isinstance(doc.metadata, dict):
                    metadata = doc.metadata.copy()
                else:
                    metadata = {}
                
                # Ensure metadata values are strings or numbers
                cleaned_metadata = {}
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        cleaned_metadata[key] = str(value)
                    elif isinstance(value, list):
                        cleaned_metadata[key] = str(value)
                    else:
                        cleaned_metadata[key] = str(value)
                
                doc_texts.append(text)
                metadatas.append(cleaned_metadata)
                ids.append(f"doc_{i}_{uuid.uuid4().hex[:8]}")
            
            # Add to collection
            if doc_texts:
                self.collection.add(
                    documents=doc_texts,
                    metadatas=metadatas,
                    ids=ids
                )
                
                logger.info(f"Successfully added {len(doc_texts)} documents to vector store")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            return False
    
    def _clear_collection(self):
        """Clear all documents from the collection."""
        try:
            # Get all IDs and delete them
            result = self.collection.get()
            if result['ids']:
                self.collection.delete(ids=result['ids'])
                logger.info(f"Cleared {len(result['ids'])} existing documents")
        except Exception as e:
            logger.warning(f"Error clearing collection: {e}")
    
    def similarity_search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        try:
            if not self.collection:
                logger.error("Collection not initialized")
                return []
            
            # Query the collection
            results = self.collection.query(
                query_texts=[query],
                n_results=min(k, 10)  # Limit results
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc_text in enumerate(results['documents'][0]):
                    result = {
                        'page_content': doc_text,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {},
                        'score': results['distances'][0][i] if results['distances'] and results['distances'][0] else 0.0
                    }
                    formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} similar documents for query")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            if not self.collection:
                return {'count': 0, 'error': 'Collection not initialized'}
            
            # Get collection count
            result = self.collection.get()
            count = len(result['ids']) if result['ids'] else 0
            
            return {
                'count': count,
                'name': self.collection_name,
                'persist_directory': self.persist_directory
            }
            
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {'count': 0, 'error': str(e)}
    
    def delete_by_source(self, source_filename: str) -> bool:
        """Delete documents by source filename."""
        try:
            if not self.collection:
                return False
            
            # Get all documents
            result = self.collection.get()
            
            if not result['ids']:
                return True
            
            # Find IDs to delete based on source metadata
            ids_to_delete = []
            for i, metadata in enumerate(result['metadatas']):
                if metadata and metadata.get('source', '').endswith(source_filename):
                    ids_to_delete.append(result['ids'][i])
            
            # Delete matching documents
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                logger.info(f"Deleted {len(ids_to_delete)} documents with source: {source_filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting documents by source: {e}")
            return False
    
    def reset_collection(self):
        """Reset the entire collection."""
        try:
            # Delete the collection
            self.client.delete_collection(name=self.collection_name)
            
            # Recreate it
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info("Collection reset successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
            return False