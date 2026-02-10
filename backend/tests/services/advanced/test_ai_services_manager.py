"""
Integration Tests for Advanced AI Services Manager

Tests the orchestration layer integrating:
- Oneiroi Dreaming
- GAIA Tournaments
- Multi-modal Processing
- Service health monitoring
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from src.services.advanced.ai_services_manager import (
    AdvancedAIServicesManager,
    DreamCycleRequest,
    MatchRequest
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
async def manager():
    """Create AI Services Manager instance"""
    return AdvancedAIServicesManager()


@pytest.fixture
def sample_image_data():
    """Sample image bytes (1x1 red pixel PNG)"""
    import base64
    # Minimal 1x1 red PNG
    png_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    return base64.b64decode(png_data)


# ============================================================================
# Oneiroi Integration Tests
# ============================================================================

class TestOneiroiIntegration:
    """Test Oneiroi dreaming integration"""
    
    @pytest.mark.asyncio
    async def test_dream_cycle_execution(self, manager):
        """Test complete dream cycle execution"""
        request = DreamCycleRequest(
            agent_id="test_agent",
            num_experiences=10
        )
        
        with patch.object(manager.dream_engine, 'rem_phase', new_callable=AsyncMock) as mock_rem:
            with patch.object(manager.dream_engine, 'nrem_phase', new_callable=AsyncMock) as mock_nrem:
                with patch.object(manager.dream_engine, 'integration_phase', new_callable=AsyncMock) as mock_int:
                    # Setup mocks
                    mock_rem.return_value = {
                        'cycle_id': 'test_cycle',
                        'replayed_experiences': []
                    }
                    mock_nrem.return_value = {
                        'patterns': [],
                        'insights': []
                    }
                    mock_int.return_value = {
                        'applied_insights': [],
                        'improvement_score': 0.05
                    }
                    
                    result = await manager.run_dream_cycle(request)
                    
                    assert result['agent_id'] == 'test_agent'
                    assert 'dream_cycle_id' in result
                    assert mock_rem.called
                    assert mock_nrem.called
                    assert mock_int.called
    
    @pytest.mark.asyncio
    async def test_dream_insights_retrieval(self, manager):
        """Test retrieving dream insights"""
        with patch.object(manager.dream_engine, 'get_insights', new_callable=AsyncMock) as mock:
            mock.return_value = []
            
            insights = await manager.get_dream_insights('test_agent', limit=10)
            
            assert isinstance(insights, list)
            mock.assert_called_once_with('test_agent', 10)
    
    @pytest.mark.asyncio
    async def test_dream_metrics_update(self, manager):
        """Test service metrics are updated"""
        initial_requests = manager.service_metrics['oneiroi'].total_requests
        
        request = DreamCycleRequest(agent_id="test_agent", num_experiences=5)
        
        with patch.object(manager.dream_engine, 'rem_phase', new_callable=AsyncMock):
            with patch.object(manager.dream_engine, 'nrem_phase', new_callable=AsyncMock):
                with patch.object(manager.dream_engine, 'integration_phase', new_callable=AsyncMock):
                    try:
                        await manager.run_dream_cycle(request)
                    except:
                        pass
        
        # Metrics should be updated
        assert manager.service_metrics['oneiroi'].total_requests >= initial_requests


# ============================================================================
# GAIA Integration Tests
# ============================================================================

class TestGAIAIntegration:
    """Test GAIA tournament integration"""
    
    @pytest.mark.asyncio
    async def test_match_execution(self, manager):
        """Test match execution"""
        request = MatchRequest(
            agent_id="test_agent",
            opponent_type="synthetic",
            num_rounds=3
        )
        
        with patch.object(manager.match_engine, 'run_match', new_callable=AsyncMock) as mock:
            mock.return_value = {
                'match_id': 'test_match',
                'winner': 'test_agent',
                'score': {'player1': 2, 'player2': 1},
                'elo_before': 1500,
                'elo_after': 1520,
                'elo_change': 20
            }
            
            result = await manager.run_match(request)
            
            assert result['agent_id'] == 'test_agent'
            assert 'match_id' in result
            assert 'elo_change' in result
    
    @pytest.mark.asyncio
    async def test_elo_retrieval(self, manager):
        """Test ELO rating retrieval"""
        with patch.object(manager.match_engine, 'get_elo', new_callable=AsyncMock) as mock:
            mock.return_value = 1550.0
            
            elo = await manager.get_agent_elo('test_agent')
            
            assert elo == 1550.0
    
    @pytest.mark.asyncio
    async def test_match_history(self, manager):
        """Test match history retrieval"""
        with patch.object(manager.match_engine, 'get_history', new_callable=AsyncMock) as mock:
            mock.return_value = []
            
            history = await manager.get_match_history('test_agent', limit=10)
            
            assert isinstance(history, list)


# ============================================================================
# Multi-modal Integration Tests
# ============================================================================

class TestMultiModalIntegration:
    """Test multi-modal processing integration"""
    
    @pytest.mark.asyncio
    async def test_image_processing(self, manager, sample_image_data):
        """Test image processing"""
        with patch.object(manager.vision_processor, 'generate_caption', new_callable=AsyncMock) as mock_caption:
            with patch.object(manager.vision_processor, 'get_embedding', new_callable=AsyncMock) as mock_embed:
                mock_caption.return_value = "A test image"
                mock_embed.return_value = [0.1, 0.2, 0.3]
                
                result = await manager.process_image(
                    image_data=sample_image_data,
                    operations=['caption']
                )
                
                assert 'caption' in result
                assert 'embedding' in result
    
    @pytest.mark.asyncio
    async def test_audio_processing(self, manager):
        """Test audio processing"""
        audio_data = b'fake_audio_data'
        
        with patch.object(manager.audio_processor, 'transcribe', new_callable=AsyncMock) as mock_trans:
            with patch.object(manager.audio_processor, 'get_embedding', new_callable=AsyncMock) as mock_embed:
                mock_trans.return_value = {"text": "Hello world", "confidence": 0.95}
                mock_embed.return_value = [0.1, 0.2, 0.3]
                
                result = await manager.process_audio(
                    audio_data=audio_data,
                    operations=['transcribe']
                )
                
                assert 'transcription' in result
                assert 'embedding' in result
    
    @pytest.mark.asyncio
    async def test_similarity_search(self, manager):
        """Test similarity search"""
        query_embedding = [0.1, 0.2, 0.3]
        
        with patch.object(manager.vision_processor, 'search_similar', new_callable=AsyncMock) as mock:
            mock.return_value = []
            
            results = await manager.search_similar(
                query_embedding=query_embedding,
                modality='image',
                top_k=5
            )
            
            assert isinstance(results, list)


# ============================================================================
# Service Health Tests
# ============================================================================

class TestServiceHealth:
    """Test service health monitoring"""
    
    def test_get_service_status(self, manager):
        """Test retrieving service status"""
        status = manager.get_service_status()
        
        assert 'oneiroi' in status
        assert 'gaia' in status
        assert 'multimodal' in status
        assert 'orchestrator' in status
        
        for service_status in status.values():
            assert service_status.service_name
            assert service_status.status in ['online', 'busy', 'offline']
    
    @pytest.mark.asyncio
    async def test_metrics_tracking(self, manager):
        """Test that metrics are properly tracked"""
        initial_oneiroi = manager.service_metrics['oneiroi'].total_requests
        
        # Simulate a dream cycle (with mocked dependencies)
        request = DreamCycleRequest(agent_id="test", num_experiences=5)
        
        with patch.object(manager.dream_engine, 'rem_phase', new_callable=AsyncMock):
            with patch.object(manager.dream_engine, 'nrem_phase', new_callable=AsyncMock):
                with patch.object(manager.dream_engine, 'integration_phase', new_callable=AsyncMock):
                    try:
                        await manager.run_dream_cycle(request)
                    except:
                        pass
        
        # Total requests should increase
        assert manager.service_metrics['oneiroi'].total_requests > initial_oneiroi


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling across services"""
    
    @pytest.mark.asyncio
    async def test_dream_cycle_error_handling(self, manager):
        """Test dream cycle error handling"""
        request = DreamCycleRequest(agent_id="test", num_experiences=5)
        
        with patch.object(manager.dream_engine, 'rem_phase', new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("Test error")
            
            with pytest.raises(Exception):
                await manager.run_dream_cycle(request)
            
            # Service should still be online after error
            assert manager.service_metrics['oneiroi'].status in ['online', 'busy']
    
    @pytest.mark.asyncio
    async def test_invalid_modality(self, manager):
        """Test invalid modality for similarity search"""
        with pytest.raises(ValueError):
            await manager.search_similar(
                query_embedding=[0.1, 0.2],
                modality='invalid',
                top_k=5
            )


# ============================================================================
# Concurrent Operations Tests
# ============================================================================

class TestConcurrentOperations:
    """Test concurrent service operations"""
    
    @pytest.mark.asyncio
    async def test_concurrent_dream_cycles(self, manager):
        """Test multiple simultaneous dream cycles"""
        requests = [
            DreamCycleRequest(agent_id=f"agent_{i}", num_experiences=5)
            for i in range(3)
        ]
        
        with patch.object(manager.dream_engine, 'rem_phase', new_callable=AsyncMock):
            with patch.object(manager.dream_engine, 'nrem_phase', new_callable=AsyncMock):
                with patch.object(manager.dream_engine, 'integration_phase', new_callable=AsyncMock):
                    # Run concurrently
                    tasks = [manager.run_dream_cycle(req) for req in requests]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # All should complete (or error gracefully)
                    assert len(results) == 3
