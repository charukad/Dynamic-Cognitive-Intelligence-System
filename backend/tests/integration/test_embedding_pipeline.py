"""Tests for embedding pipeline and ChromaDB integration."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.services.memory.embedding_pipeline import EmbeddingPipeline


@pytest.mark.integration
@pytest.mark.asyncio
class TestEmbeddingPipeline:
    """Test suite for embedding pipeline."""

    async def test_chunking(self, mock_chroma_client, mock_llm_client):
        """Test text chunking."""
        pipeline = EmbeddingPipeline(
            chromadb_client=mock_chroma_client,
            llm_client=mock_llm_client,
            chunk_size=100,
            chunk_overlap=20,
        )
        
        text = "A" * 250  # Long text
        chunks = pipeline.chunk_text(text)
        
        assert len(chunks) > 1
        # Check overlap
        assert len(chunks[0]) <= 100

    async def test_small_text_no_chunking(self, mock_chroma_client, mock_llm_client):
        """Test that small text is not chunked."""
        pipeline = EmbeddingPipeline(
            chromadb_client=mock_chroma_client,
            llm_client=mock_llm_client,
        )
        
        text = "Short text"
        chunks = pipeline.chunk_text(text)
        
        assert len(chunks) == 1
        assert chunks[0] == text

    async def test_embedding_generation(self, mock_chroma_client, mock_llm_client):
        """Test embedding generation."""
        pipeline = EmbeddingPipeline(
            chromadb_client=mock_chroma_client,
            llm_client=mock_llm_client,
        )
        
        # Mock embedding
        mock_llm_client.get_embedding.return_value = [0.1] * 384
        
        embedding = await pipeline.generate_embedding("test text")
        
        assert len(embedding) == 384
        mock_llm_client.get_embedding.assert_called_once()

    async def test_store_document(self, mock_chroma_client, mock_llm_client):
        """Test storing document with embeddings."""
        pipeline = EmbeddingPipeline(
            chromadb_client=mock_chroma_client,
            llm_client=mock_llm_client,
            chunk_size=100,
        )
        
        # Mock embedding
        mock_llm_client.get_embedding.return_value = [0.1] * 384
        
        doc_id = await pipeline.store_document(
            collection_name="test_collection",
            document="This is a test document with some content.",
            metadata={"source": "test"},
        )
        
        assert doc_id is not None
        assert mock_chroma_client.add_documents.called

    async def test_semantic_search(self, mock_chroma_client, mock_llm_client):
        """Test semantic search."""
        pipeline = EmbeddingPipeline(
            chromadb_client=mock_chroma_client,
            llm_client=mock_llm_client,
        )
        
        # Mock embedding and results
        mock_llm_client.get_embedding.return_value = [0.1] * 384
        mock_chroma_client.query_documents.return_value = [
            {"content": "Result 1", "score": 0.9},
            {"content": "Result 2", "score": 0.8},
        ]
        
        results = await pipeline.search_similar(
            collection_name="test_collection",
            query="test query",
            n_results=5,
        )
        
        assert len(results) == 2
        assert results[0]["content"] == "Result 1"

    async def test_rag_context_building(self, mock_chroma_client, mock_llm_client):
        """Test RAG context building."""
        pipeline = EmbeddingPipeline(
            chromadb_client=mock_chroma_client,
            llm_client=mock_llm_client,
        )
        
        # Mock
        mock_llm_client.get_embedding.return_value = [0.1] * 384
        mock_chroma_client.query_documents.return_value = [
            {"content": "Chunk 1", "score": 0.9},
            {"content": "Chunk 2", "score": 0.8},
            {"content": "Chunk 1", "score": 0.7},  # Duplicate
        ]
        
        context = await pipeline.build_rag_context(
            collection_name="test_collection",
            query="test query",
            max_chunks=5,
        )
        
        assert "Chunk 1" in context
        assert "Chunk 2" in context
        # Should deduplicate
        assert context.count("Chunk 1") == 1

    async def test_delete_document(self, mock_chroma_client, mock_llm_client):
        """Test document deletion."""
        pipeline = EmbeddingPipeline(
            chromadb_client=mock_chroma_client,
            llm_client=mock_llm_client,
        )
        
        # Mock chunks found
        mock_chroma_client.query_documents.return_value = [
            {"id": "doc1_chunk_0"},
            {"id": "doc1_chunk_1"},
        ]
        
        success = await pipeline.delete_document(
            collection_name="test_collection",
            document_id="doc1",
        )
        
        assert success is True
        assert mock_chroma_client.delete_documents.called

    async def test_chunking_at_sentence_boundary(self, mock_chroma_client, mock_llm_client):
        """Test that chunking prefers sentence boundaries."""
        pipeline = EmbeddingPipeline(
            chromadb_client=mock_chroma_client,
            llm_client=mock_llm_client,
            chunk_size=100,
            chunk_overlap=10,
        )
        
        text = "First sentence. " * 20 + "Last sentence."
        chunks = pipeline.chunk_text(text)
        
        # Should break at periods
        for chunk in chunks[:-1]:  # All but last
            if len(chunk) > 50:  # Only check substantial chunks
                assert chunk.endswith('.') or chunk.endswith('\n')
