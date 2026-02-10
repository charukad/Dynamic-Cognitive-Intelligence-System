"""
Integration Tests for RLHF API

Tests API endpoints for feedback submission and retrieval.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


class TestRLHFAPI:
    """Integration tests for RLHF API endpoints."""
    
    def test_submit_thumbs_up_feedback(self):
        """Test submitting thumbs up feedback via API."""
        payload = {
            'session_id': 'test-session',
            'message_id': 'msg-123',
            'agent_id': 'agent-1',
            'feedback_type': 'thumbs_up',
            'user_query': 'What is AI?',
            'agent_response': 'AI is artificial intelligence...',
            'rating': 1.0,
        }
        
        response = client.post('/api/v1/rlhf/feedback', json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'feedback_id' in data
    
    def test_submit_thumbs_down_feedback(self):
        """Test submitting thumbs down feedback via API."""
        payload = {
            'session_id': 'test-session',
            'message_id': 'msg-456',
            'agent_id': 'agent-1',
            'feedback_type': 'thumbs_down',
            'user_query': 'Test query',
            'agent_response': 'Test response',
            'rating': 0.0,
        }
        
        response = client.post('/api/v1/rlhf/feedback', json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
    
    def test_submit_rating_feedback(self):
        """Test submitting star rating feedback."""
        payload = {
            'session_id': 'test-session',
            'message_id': 'msg-789',
            'agent_id': 'agent-2',
            'feedback_type': 'rating',
            'rating': 4.5,
            'user_query': 'Question',
            'agent_response': 'Answer',
        }
        
        response = client.post('/api/v1/rlhf/feedback', json=payload)
        
        assert response.status_code == 200
    
    def test_submit_feedback_with_categories(self):
        """Test submitting feedback with categories."""
        payload = {
            'session_id': 'test-session',
            'message_id': 'msg-cat',
            'agent_id': 'agent-3',
            'feedback_type': 'thumbs_up',
            'categories': ['accuracy', 'helpfulness'],
            'user_query': 'Test',
            'agent_response': 'Response',
        }
        
        response = client.post('/api/v1/rlhf/feedback', json=payload)
        
        assert response.status_code == 200
    
    def test_submit_invalid_feedback_type(self):
        """Test submitting invalid feedback type returns error."""
        payload = {
            'session_id': 'test',
            'message_id': 'msg',
            'agent_id': 'agent',
            'feedback_type': 'invalid_type',
            'user_query': 'Test',
            'agent_response': 'Response',
        }
        
        response = client.post('/api/v1/rlhf/feedback', json=payload)
        
        assert response.status_code == 400
    
    def test_get_agent_feedback_summary(self):
        """Test getting feedback summary for agent."""
        # First submit some feedback
        for i in range(3):
            client.post('/api/v1/rlhf/feedback', json={
                'session_id': 'test',
                'message_id': f'msg-{i}',
                'agent_id': 'test-agent',
                'feedback_type': 'thumbs_up',
                'user_query': 'Test',
                'agent_response': 'Response',
            })
        
        # Get summary
        response = client.get('/api/v1/rlhf/feedback/agent/test-agent')
        
        assert response.status_code == 200
        data = response.json()
        assert 'total_feedback' in data
        assert 'thumbs_up' in data
        assert 'approval_rate' in data
    
    def test_get_top_rated_agents(self):
        """Test getting top-rated agents."""
        response = client.get('/api/v1/rlhf/feedback/top-agents?limit=5')
        
        assert response.status_code == 200
        data = response.json()
        assert 'top_agents' in data
        assert isinstance(data['top_agents'], list)
    
    def test_get_feedback_trends(self):
        """Test getting feedback trends."""
        response = client.get('/api/v1/rlhf/feedback/trends?days=7')
        
        assert response.status_code == 200
        data = response.json()
        assert 'total_feedback' in data
        assert 'trend' in data
        assert 'daily_average' in data
    
    def test_get_reward_score(self):
        """Test getting predicted reward score."""
        response = client.get(
            '/api/v1/rlhf/reward-score',
            params={
                'agent_id': 'agent-1',
                'response': 'This is a test response',
                'query': 'Test query',
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'predicted_score' in data
        assert 0.0 <= data['predicted_score'] <= 1.0
    
    def test_get_rlhf_stats(self):
        """Test getting RLHF statistics."""
        response = client.get('/api/v1/rlhf/stats')
        
        assert response.status_code == 200
        data = response.json()
        assert 'total_feedback' in data
        assert 'avg_rating_overall' in data
        assert 'approval_rate' in data
    
    def test_rlhf_health_check(self):
        """Test RLHF system health check."""
        response = client.get('/api/v1/rlhf/health')
        
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert data['status'] in ['healthy', 'no_data']


class TestAnalyticsAPI:
    """Integration tests for Unified Analytics API."""
    
    def test_get_unified_dashboard(self):
        """Test getting unified dashboard data."""
        response = client.get('/api/v1/analytics/unified-dashboard')
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all subsystems are present
        assert 'rlhf' in data
        assert 'performance' in data
        assert 'cache' in data
        assert 'system_health' in data
        
        # Check RLHF data structure
        assert 'total_feedback' in data['rlhf']
        assert 'approval_rate' in data['rlhf']
        
        # Check performance data
        assert 'avg_latency_ms' in data['performance']
        assert 'total_requests' in data['performance']
    
    def test_get_top_performers(self):
        """Test getting top performers."""
        response = client.get('/api/v1/analytics/top-performers')
        
        assert response.status_code == 200
        data = response.json()
        assert 'top_rated_agents' in data
        assert isinstance(data['top_rated_agents'], list)
    
    def test_analytics_health_check(self):
        """Test analytics system health check."""
        response = client.get('/api/v1/analytics/health')
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'status' in data
        assert 'health_score' in data
        assert 'subsystems' in data
        assert data['status'] in ['healthy', 'degraded', 'warning']


class TestMonitoringAPI:
    """Integration tests for Monitoring API."""
    
    def test_get_metrics(self):
        """Test getting monitoring metrics."""
        response = client.get('/api/v1/monitoring/metrics')
        
        assert response.status_code == 200
        data = response.json()
        assert 'counters' in data or 'gauges' in data
    
    def test_health_check(self):
        """Test monitoring health check."""
        response = client.get('/api/v1/monitoring/health')
        
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
