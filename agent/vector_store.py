import chromadb
from chromadb.config import Settings
import os
import logging
from typing import List, Dict, Any, Optional
import uuid
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

class VectorStoreManager:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.collection_name = "documents"
        self.client = None
        self.collection = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client with improved error handling and performance."""
        try:
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Enhanced settings for better performance
            settings = Settings(
                persist_directory=self.persist_directory,
                is_persistent=True,
                anonymized_telemetry=False
            )
            
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=settings
            )
            
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                count = self.collection.count()
                logger.info(f"Loaded existing collection '{self.collection_name}' with {count} documents")
            except Exception:
                # Create collection with optimized configuration
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={
                        "hnsw:space": "cosine",
                        "hnsw:search_ef": 100,  # Better search quality
                        "hnsw:M": 16,           # More connections for better recall
                        "description": "Enhanced document collection for Orbuculum.ai"
                    }
                )
                logger.info(f"Created new collection '{self.collection_name}' with enhanced configuration")
            
            logger.info("Vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    def _generate_document_id(self, content: str, metadata: Dict[str, Any]) -> str:
        """Generate a unique, deterministic ID for documents."""
        source = metadata.get('source_file', metadata.get('source', 'unknown'))
        chunk_id = metadata.get('chunk_id', '')
        
        # Create a hash from content and metadata for uniqueness
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
        source_hash = hashlib.md5(str(source).encode('utf-8')).hexdigest()[:8]
        
        return f"{source_hash}_{content_hash}_{chunk_id}"
    
    def _clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Clean and validate metadata for ChromaDB storage."""
        cleaned = {}
        for key, value in metadata.items():
            # Convert all values to strings and handle None values
            if value is not None:
                cleaned[str(key)] = str(value)
            else:
                cleaned[str(key)] = ""
        
        # Add processing timestamp
        cleaned['indexed_at'] = datetime.now().isoformat()
        
        return cleaned
    
    def add_documents(self, documents: List[Any], batch_size: int = 100) -> bool:
        """Add documents to the vector store with improved batching and deduplication."""
        try:
            if not documents:
                logger.warning("No documents provided to add")
                return True
            
            doc_texts, metadatas, ids = [], [], []
            added_count = 0
            skipped_count = 0
            
            # Get existing document IDs for deduplication
            try:
                existing_ids = set(self.collection.get()['ids'])
            except Exception:
                existing_ids = set()
            
            for i, doc in enumerate(documents):
                try:
                    text = doc.page_content if hasattr(doc, 'page_content') else str(doc)
                    metadata = doc.metadata.copy() if hasattr(doc, 'metadata') and isinstance(doc.metadata, dict) else {}
                    
                    # Skip empty documents
                    if not text or len(text.strip()) < 10:
                        logger.debug(f"Skipping empty or very short document {i}")
                        skipped_count += 1
                        continue
                    
                    # Generate unique ID
                    doc_id = self._generate_document_id(text, metadata)
                    
                    # Skip if document already exists
                    if doc_id in existing_ids:
                        logger.debug(f"Document {doc_id} already exists, skipping")
                        skipped_count += 1
                        continue
                    
                    cleaned_metadata = self._clean_metadata(metadata)
                    
                    doc_texts.append(text)
                    metadatas.append(cleaned_metadata)
                    ids.append(doc_id)
                    added_count += 1
                    
                    # Process in batches to avoid memory issues
                    if len(doc_texts) >= batch_size:
                        self._add_batch(doc_texts, metadatas, ids)
                        doc_texts, metadatas, ids = [], [], []
                        
                except Exception as e:
                    logger.error(f"Error processing document {i}: {e}")
                    skipped_count += 1
                    continue
            
            # Add remaining documents
            if doc_texts:
                self._add_batch(doc_texts, metadatas, ids)
            
            logger.info(f"Successfully added {added_count} new documents, skipped {skipped_count}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            return False
    
    def _add_batch(self, doc_texts: List[str], metadatas: List[Dict], ids: List[str]):
        """Add a batch of documents to the collection."""
        try:
            self.collection.add(
                documents=doc_texts,
                metadatas=metadatas,
                ids=ids
            )
            logger.debug(f"Added batch of {len(doc_texts)} documents")
        except Exception as e:
            logger.error(f"Error adding batch: {e}")
            raise
            
    def rebuild_from_documents(self, documents: List[Any]):
        """Clear the collection and rebuild it from a list of documents."""
        logger.info("Starting collection rebuild...")
        self._clear_collection()
        success = self.add_documents(documents)
        if success:
            logger.info("Collection rebuild completed successfully")
        else:
            logger.error("Collection rebuild failed")
        return success
    
    def _clear_collection(self):
        """Clear all documents from the collection efficiently."""
        try:
            # Get all document IDs in batches
            batch_size = 1000
            while True:
                result = self.collection.get(limit=batch_size)
                if not result['ids']:
                    break
                    
                self.collection.delete(ids=result['ids'])
                logger.debug(f"Cleared batch of {len(result['ids'])} documents")
                
                if len(result['ids']) < batch_size:
                    break
                    
            logger.info("Collection cleared successfully")
        except Exception as e:
            logger.warning(f"Error clearing collection: {e}")
    
    def similarity_search(self, query: str, k: int = 4, score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Enhanced similarity search with filtering and better relevance scoring."""
        try:
            if not self.collection:
                logger.error("Collection not initialized")
                return []
            
            # Increase search results to allow for filtering
            search_k = min(k * 2, 20)
            
            results = self.collection.query(
                query_texts=[query], 
                n_results=search_k,
                include=['documents', 'metadatas', 'distances']
            )
            
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc_text in enumerate(results['documents'][0]):
                    distance = results['distances'][0][i] if results['distances'] and results['distances'][0] else 1.0
                    similarity = 1 - distance  # Convert distance to similarity
                    
                    # Filter by relevance threshold
                    if similarity < (1 - score_threshold):
                        continue
                    
                    metadata = results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {}
                    
                    result = {
                        'page_content': doc_text,
                        'metadata': metadata,
                        'score': distance,
                        'similarity': similarity,
                        'relevance_score': self._calculate_relevance_score(doc_text, query, similarity)
                    }
                    formatted_results.append(result)
            
            # Sort by relevance score and limit results
            formatted_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            formatted_results = formatted_results[:k]
            
            logger.info(f"Found {len(formatted_results)} relevant documents for query (threshold: {score_threshold})")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []
    
    def _calculate_relevance_score(self, document: str, query: str, similarity: float) -> float:
        """Calculate enhanced relevance score considering multiple factors."""
        base_score = similarity
        
        # Boost score for exact keyword matches
        query_words = set(query.lower().split())
        doc_words = set(document.lower().split())
        keyword_overlap = len(query_words.intersection(doc_words)) / len(query_words) if query_words else 0
        
        # Boost score for document length (longer documents might be more informative)
        length_factor = min(len(document) / 500, 1.2)  # Cap at 20% boost
        
        # Combine factors
        relevance_score = base_score * (1 + keyword_overlap * 0.3) * length_factor
        
        return min(relevance_score, 1.0)
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get comprehensive information about the collection."""
        try:
            if not self.collection:
                return {'count': 0, 'error': 'Collection not initialized'}
            
            count = self.collection.count()
            
            # Get sample documents to analyze metadata
            sample = self.collection.get(limit=10)
            
            source_types = set()
            source_files = set()
            
            if sample['metadatas']:
                for metadata in sample['metadatas']:
                    source_types.add(metadata.get('source_type', 'unknown'))
                    source_files.add(metadata.get('source_file', metadata.get('source', 'unknown')))
            
            return {
                'count': count,
                'name': self.collection_name,
                'persist_directory': self.persist_directory,
                'source_types': list(source_types),
                'unique_sources': len(source_files),
                'sample_sources': list(source_files)[:5],  # First 5 sources
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {'count': 0, 'error': str(e)}
    
    def delete_by_source(self, source_filename: str) -> bool:
        """Delete documents by source filename with improved efficiency."""
        try:
            if not self.collection:
                return False
            
            # Find documents matching the source
            results = self.collection.get(
                where={"source_file": source_filename},
                include=['ids']
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} documents with source: {source_filename}")
                return True
            else:
                logger.info(f"No documents found with source: {source_filename}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting documents by source: {e}")
            return False
    
    def reset_collection(self):
        """Reset the entire collection with improved error handling."""
        try:
            # Try to delete the collection
            try:
                self.client.delete_collection(name=self.collection_name)
                logger.info("Deleted existing collection")
            except Exception as e:
                logger.warning(f"Could not delete collection (might not exist): {e}")
            
            # Create new collection with enhanced settings
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={
                    "hnsw:space": "cosine",
                    "hnsw:search_ef": 100,
                    "hnsw:M": 16,
                    "description": "Reset enhanced document collection for Orbuculum.ai",
                    "reset_at": datetime.now().isoformat()
                }
            )
            logger.info("Collection reset successfully with enhanced configuration")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
            return False
    
    def search_with_filters(self, query: str, filters: Dict[str, str] = None, k: int = 4) -> List[Dict[str, Any]]:
        """Search with metadata filters for more precise results."""
        try:
            if not self.collection:
                logger.error("Collection not initialized")
                return []
            
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                where=filters or {},
                include=['documents', 'metadatas', 'distances']
            )
            
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc_text in enumerate(results['documents'][0]):
                    distance = results['distances'][0][i] if results['distances'] and results['distances'][0] else 1.0
                    metadata = results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {}
                    
                    result = {
                        'page_content': doc_text,
                        'metadata': metadata,
                        'score': distance,
                        'similarity': 1 - distance
                    }
                    formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} filtered documents for query")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in filtered search: {e}")
            return []
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get detailed statistics about the document collection."""
        try:
            if not self.collection:
                return {'error': 'Collection not initialized'}
            
            # Get all documents (in batches if collection is large)
            all_docs = self.collection.get(include=['metadatas'])
            
            if not all_docs['metadatas']:
                return {'total_documents': 0, 'sources': {}, 'types': {}}
            
            sources = {}
            types = {}
            
            for metadata in all_docs['metadatas']:
                # Count by source
                source = metadata.get('source_file', metadata.get('source', 'unknown'))
                sources[source] = sources.get(source, 0) + 1
                
                # Count by type
                doc_type = metadata.get('source_type', 'unknown')
                types[doc_type] = types.get(doc_type, 0) + 1
            
            return {
                'total_documents': len(all_docs['metadatas']),
                'unique_sources': len(sources),
                'sources': sources,
                'types': types,
                'collection_name': self.collection_name,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting document stats: {e}")
            return {'error': str(e)}