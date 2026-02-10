"""ChromaDB embedding generation and storage."""

import hashlib
from typing import Dict, List, Optional

import httpx

from src.core import get_logger

logger = get_logger(__name__)


class EmbeddingPipeline:
    """
    Pipeline for generating embeddings and storing in ChromaDB.
    
    Handles text chunking, embedding generation, and vector storage.
    """

    def __init__(
        self,
        chromadb_client,
        llm_client,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        """
        Initialize embedding pipeline.
        
        Args:
            chromadb_client: ChromaDB client for storage
            llm_client: LLM client for generating embeddings
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks
        """
        self.chroma_client = chromadb_client
        self.llm_client = llm_client
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > self.chunk_size // 2:
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - self.chunk_overlap
        
        return chunks

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            # Use LLM client to generate embeddings
            embedding = await self.llm_client.get_embedding(text)
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * 384  # Default embedding dimension

    async def store_document(
        self,
        collection_name: str,
        document: str,
        metadata: Optional[Dict] = None,
        document_id: Optional[str] = None,
    ) -> str:
        """
        Store document with embeddings in ChromaDB.
        
        Args:
            collection_name: Collection to store in
            document: Document text
            metadata: Optional metadata
            document_id: Optional document ID
            
        Returns:
            Document ID
        """
        # Chunk the document
        chunks = self.chunk_text(document)
        
        # Generate ID if not provided
        if not document_id:
            document_id = hashlib.md5(document.encode()).hexdigest()
        
        # Store each chunk
        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk_{i}"
            
            # Generate embedding
            embedding = await self.generate_embedding(chunk)
            
            # Prepare metadata
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                "document_id": document_id,
                "chunk_index": i,
                "total_chunks": len(chunks),
            })
            
            # Store in ChromaDB
            await self.chroma_client.add_documents(
                collection_name=collection_name,
                documents=[chunk],
                embeddings=[embedding],
                metadatas=[chunk_metadata],
                ids=[chunk_id],
            )
            
            logger.debug(f"Stored chunk {i+1}/{len(chunks)} for document {document_id}")
        
        return document_id

    async def search_similar(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Search for similar documents using semantic search.
        
        Args:
            collection_name: Collection to search
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of matching documents with scores
        """
        # Generate query embedding
        query_embedding = await self.generate_embedding(query)
        
        # Search ChromaDB
        results = await self.chroma_client.query_documents(
            collection_name=collection_name,
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata,
        )
        
        return results

    async def build_rag_context(
        self,
        collection_name: str,
        query: str,
        max_chunks: int = 5,
    ) -> str:
        """
        Build RAG context from relevant documents.
        
        Args:
            collection_name: Collection to search
            query: User query
            max_chunks: Maximum chunks to include
            
        Returns:
            Concatenated context string
        """
        # Search for relevant chunks
        results = await self.search_similar(
            collection_name=collection_name,
            query=query,
            n_results=max_chunks,
        )
        
        # Extract and deduplicate
        context_chunks = []
        seen_content = set()
        
        for result in results:
            content = result.get("content", "")
            if content and content not in seen_content:
                context_chunks.append(content)
                seen_content.add(content)
        
        # Concatenate with separators
        context = "\n\n---\n\n".join(context_chunks)
        
        logger.info(f"Built RAG context with {len(context_chunks)} chunks ({len(context)} chars)")
        
        return context

    async def delete_document(
        self,
        collection_name: str,
        document_id: str,
    ) -> bool:
        """
        Delete all chunks of a document.
        
        Args:
            collection_name: Collection name
            document_id: Document ID to delete
            
        Returns:
            Success status
        """
        try:
            # Query for all chunks of this document
            results = await self.chroma_client.query_documents(
                collection_name=collection_name,
                query_embeddings=[[0.0] * 384],  # Dummy embedding
                n_results=1000,
                where={"document_id": document_id},
            )
            
            # Delete each chunk
            chunk_ids = [r["id"] for r in results]
            
            for chunk_id in chunk_ids:
                await self.chroma_client.delete_documents(
                    collection_name=collection_name,
                    ids=[chunk_id],
                )
            
            logger.info(f"Deleted {len(chunk_ids)} chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False


# Global instance - will be initialized by memory/__init__.py
# This avoids circular imports
embedding_pipeline: Optional[EmbeddingPipeline] = None


def get_embedding_pipeline() -> Optional[EmbeddingPipeline]:
    """
    Get the global embedding pipeline instance.
    
    Returns:
        Embedding pipeline or None if not initialized
    """
    return embedding_pipeline


def set_embedding_pipeline(pipeline: EmbeddingPipeline) -> None:
    """
    Set the global embedding pipeline instance.
    
    Args:
        pipeline: Embedding pipeline to set
    """
    global embedding_pipeline
    embedding_pipeline = pipeline
