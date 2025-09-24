import os
from typing import List, Dict, Any
from langchain_community.document_loaders import PyPDFLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def load_documents(self, documents_dir: str) -> List[Document]:
        """Load and process all documents from the directory."""
        documents = []
        
        if not os.path.exists(documents_dir):
            logger.warning(f"Documents directory {documents_dir} does not exist")
            return documents
        
        for filename in os.listdir(documents_dir):
            file_path = os.path.join(documents_dir, filename)
            
            if not os.path.isfile(file_path):
                continue
                
            try:
                if filename.endswith('.pdf'):
                    loader = PyPDFLoader(file_path)
                    docs = loader.load()
                elif filename.endswith('.md'):
                    loader = UnstructuredMarkdownLoader(file_path)
                    docs = loader.load()
                else:
                    logger.warning(f"Unsupported file type: {filename}")
                    continue
                
                # Add metadata
                for doc in docs:
                    doc.metadata.update({
                        'source_file': filename,
                        'source_type': 'local_document'
                    })
                
                documents.extend(docs)
                logger.info(f"Loaded {len(docs)} chunks from {filename}")
                
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
        
        # Split documents into chunks
        chunked_docs = self.text_splitter.split_documents(documents)
        
        # Add chunk IDs
        for i, doc in enumerate(chunked_docs):
            doc.metadata['chunk_id'] = f"doc_{i}"
        
        logger.info(f"Total chunks created: {len(chunked_docs)}")
        return chunked_docs
    
    def process_text(self, text: str, source: str, source_type: str = "web") -> List[Document]:
        """Process raw text into document chunks."""
        doc = Document(
            page_content=text,
            metadata={
                'source': source,
                'source_type': source_type
            }
        )
        
        chunks = self.text_splitter.split_documents([doc])
        for i, chunk in enumerate(chunks):
            chunk.metadata['chunk_id'] = f"{source_type}_{hash(source)}_{i}"
        
        return chunks