"""
Unit Tests for RLHF Feedback Manager

Tests reward modeling, feedback collection, and trend analysis.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from src.services.rlhf.feedback_manager import (
    FeedbackManager,
    FeedbackType,
    FeedbackCategory,
    UserFeedback,
    RewardModel,
)


class TestFeedbackManager:
    """Test suite for FeedbackManager."""
    
    @pytest.fixture
    def manager(self):
        """Create fresh FeedbackManager instance."""
        return FeedbackManager()
    
    @pytest.fixture
    def sample_feedback_data(self):
        """Sample feedback data for testing."""
        return {
            'session_id': 'test-session-123',
            'message_id': 'msg-456',
            'agent_id': 'agent-1',
            'user_query': 'What is machine learning?',
            'agent_response': 'Machine learning is a subset of AI...',
        }
    
    # ========================================================================
    # Feedback Collection Tests
    # ========================================================================
    
    def test_collect_thumbs_up_feedback(self, manager, sample_feedback_data):
        """Test collecting thumbs up feedback."""
        feedback = manager.collect_feedback(
            **sample_feedback_data,
            feedback_type=FeedbackType.THUMBS_UP,
        )
        
        assert feedback.feedback_type == FeedbackType.THUMBS_UP
        assert feedback.session_id == sample_feedback_data['session_id']
        assert feedback.message_id == sample_feedback_data['message_id']
        assert len(manager.feedback_history) == 1
    
    def test_collect_thumbs_down_feedback(self, manager, sample_feedback_data):
        """Test collecting thumbs down feedback."""
        feedback = manager.collect_feedback(
            **sample_feedback_data,
            feedback_type=FeedbackType.THUMBS_DOWN,
        )
        
        assert feedback.feedback_type == FeedbackType.THUMBS_DOWN
        assert len(manager.feedback_history) == 1
    
    def test_collect_rating_feedback(self, manager, sample_feedback_data):
        """Test collecting star rating feedback."""
        feedback = manager.collect_feedback(
            **sample_feedback_data,
            feedback_type=FeedbackType.RATING,
            rating=4.5,
        )
        
        assert feedback.feedback_type == FeedbackType.RATING
        assert feedback.rating == 4.5
    
    def test_collect_feedback_with_categories(self, manager, sample_feedback_data):
        """Test feedback with categories."""
        categories = [FeedbackCategory.ACCURACY, FeedbackCategory.HELPFULNESS]
        
        feedback = manager.collect_feedback(
            **sample_feedback_data,
            feedback_type=FeedbackType.THUMBS_UP,
            categories=categories,
        )
        
        assert len(feedback.categories) == 2
        assert FeedbackCategory.ACCURACY in feedback.categories
    
    def test_collect_text_feedback(self, manager, sample_feedback_data):
        """Test text feedback collection."""
        text = "Great explanation, very clear!"
        
        feedback = manager.collect_feedback(
            **sample_feedback_data,
            feedback_type=FeedbackType.TEXT_FEEDBACK,
            text_feedback=text,
        )
        
        assert feedback.text_feedback == text
    
    # ========================================================================
    # Reward Model Tests
    # ========================================================================
    
    def test_reward_model_creation(self, manager, sample_feedback_data):
        """Test reward model is created for new agent."""
        agent_id = sample_feedback_data['agent_id']
        
        # Initially no model
        assert agent_id not in manager.reward_models
        
        # Collect feedback
        manager.collect_feedback(
            **sample_feedback_data,
            feedback_type=FeedbackType.THUMBS_UP,
        )
        
        # Model should be created
        assert agent_id in manager.reward_models
        assert isinstance(manager.reward_models[agent_id], RewardModel)
    
    def test_reward_model_updates_on_positive_feedback(self, manager, sample_feedback_data):
        """Test reward model updates correctly on positive feedback."""
        agent_id = sample_feedback_data['agent_id']
        
        # Collect positive feedback
        manager.collect_feedback(
            **sample_feedback_data,
            feedback_type=FeedbackType.THUMBS_UP,
        )
        
        model = manager.reward_models[agent_id]
        assert model.positive_samples == 1
        assert model.negative_samples == 0
        assert model.total_ratings == 1
        assert model.avg_rating > 0.5
    
    def test_reward_model_updates_on_negative_feedback(self, manager, sample_feedback_data):
        """Test reward model updates correctly on negative feedback."""
        agent_id = sample_feedback_data['agent_id']
        
        # Collect negative feedback
        manager.collect_feedback(
            **sample_feedback_data,
            feedback_type=FeedbackType.THUMBS_DOWN,
        )
        
        model = manager.reward_models[agent_id]
        assert model.positive_samples == 0
        assert model.negative_samples == 1
        assert model.total_ratings == 1
        assert model.avg_rating < 0.5
    
    def test_reward_model_running_average(self, manager, sample_feedback_data):
        """Test reward model calculates running average correctly."""
        agent_id = sample_feedback_data['agent_id']
        
        # Collect mixed feedback
        manager.collect_feedback(**sample_feedback_data, feedback_type=FeedbackType.THUMBS_UP)
        manager.collect_feedback(**sample_feedback_data, feedback_type=FeedbackType.THUMBS_UP)
        manager.collect_feedback(**sample_feedback_data, feedback_type=FeedbackType.THUMBS_DOWN)
        
        model = manager.reward_models[agent_id]
        assert model.total_ratings == 3
        assert model.positive_samples == 2
        assert model.negative_samples == 1
        assert 0.5 < model.avg_rating < 1.0  # Should be around 0.67
    
    def test_reward_model_accuracy(self, manager, sample_feedback_data):
        """Test reward model accuracy calculation."""
        agent_id = sample_feedback_data['agent_id']
        
        # 80% positive feedback
        for _ in range(8):
            manager.collect_feedback(**sample_feedback_data, feedback_type=FeedbackType.THUMBS_UP)
        for _ in range(2):
            manager.collect_feedback(**sample_feedback_data, feedback_type=FeedbackType.THUMBS_DOWN)
        
        model = manager.reward_models[agent_id]
        assert model.accuracy == 0.8
    
    # ========================================================================
    # Reward Score Prediction Tests
    # ========================================================================
    
    def test_get_reward_score_for_unknown_agent(self, manager):
        """Test reward score returns neutral for unknown agent."""
        score = manager.get_reward_score('unknown-agent', 'test response', 'test query')
        assert score == 0.5  # Neutral score
    
    def test_get_reward_score_for_high_rated_agent(self, manager, sample_feedback_data):
        """Test reward score reflects agent's rating history."""
        agent_id = sample_feedback_data['agent_id']
        
        # Give agent high ratings
        for _ in range(10):
            manager.collect_feedback(**sample_feedback_data, feedback_type=FeedbackType.THUMBS_UP)
        
        score = manager.get_reward_score(agent_id, 'Great response here!', 'test query')
        assert score > 0.5  # Should be above neutral
    
    def test_reward_score_considers_response_length(self, manager, sample_feedback_data):
        """Test reward score considers response quality heuristics."""
        agent_id = sample_feedback_data['agent_id']
        
        # Train model
        manager.collect_feedback(**sample_feedback_data, feedback_type=FeedbackType.THUMBS_UP)
        
        # Very short response
        short_score = manager.get_reward_score(agent_id, 'Ok.', 'test')
        
        # Good length response
        good_response = ' '.join(['word'] * 100)  # ~100 words
        good_score = manager.get_reward_score(agent_id, good_response, 'test')
        
        assert good_score > short_score
    
    # ========================================================================
    # Feedback Summary Tests
    # ========================================================================
    
    def test_get_agent_feedback_summary_empty(self, manager):
        """Test feedback summary for agent with no feedback."""
        summary = manager.get_agent_feedback_summary('unknown-agent')
        
        assert summary['total_feedback'] == 0
        assert summary['avg_rating'] == 0.0
        assert summary['thumbs_up'] == 0
        assert summary['thumbs_down'] == 0
    
    def test_get_agent_feedback_summary(self, manager, sample_feedback_data):
        """Test feedback summary calculation."""
        agent_id = sample_feedback_data['agent_id']
        
        # Collect various feedback
        manager.collect_feedback(**sample_feedback_data, feedback_type=FeedbackType.THUMBS_UP)
        manager.collect_feedback(**sample_feedback_data, feedback_type=FeedbackType.THUMBS_UP)
        manager.collect_feedback(**sample_feedback_data, feedback_type=FeedbackType.THUMBS_DOWN)
        
        summary = manager.get_agent_feedback_summary(agent_id)
        
        assert summary['total_feedback'] == 3
        assert summary['thumbs_up'] == 2
        assert summary['thumbs_down'] == 1
        assert summary['approval_rate'] == 2/3
    
    def test_get_agent_feedback_summary_with_categories(self, manager, sample_feedback_data):
        """Test feedback summary includes category distribution."""
        agent_id = sample_feedback_data['agent_id']
        
        manager.collect_feedback(
            **sample_feedback_data,
            feedback_type=FeedbackType.THUMBS_UP,
            categories=[FeedbackCategory.ACCURACY],
        )
        manager.collect_feedback(
            **sample_feedback_data,
            feedback_type=FeedbackType.THUMBS_UP,
            categories=[FeedbackCategory.ACCURACY, FeedbackCategory.HELPFULNESS],
        )
        
        summary = manager.get_agent_feedback_summary(agent_id)
        
        assert 'accuracy' in summary['feedback_distribution']
        assert summary['feedback_distribution']['accuracy'] == 2
        assert summary['feedback_distribution']['helpfulness'] == 1
    
    # ========================================================================
    # Top Agents Tests
    # ========================================================================
    
    def test_get_top_rated_agents_empty(self, manager):
        """Test top agents with no feedback."""
        top_agents = manager.get_top_rated_agents()
        assert len(top_agents) == 0
    
    def test_get_top_rated_agents(self, manager):
        """Test top agents ranking."""
        # Create feedback for multiple agents
        for i in range(3):
            agent_id = f'agent-{i}'
            rating_count = 5 + i * 2  # Different ratings per agent
            
            for _ in range(rating_count):
                manager.collect_feedback(
                    session_id='test',
                    message_id='msg',
                    agent_id=agent_id,
                    feedback_type=FeedbackType.THUMBS_UP,
                    user_query='test',
                    agent_response='test',
                )
        
        top_agents = manager.get_top_rated_agents(limit=2)
        
        assert len(top_agents) <= 2
        assert all('avg_rating' in agent for agent in top_agents)
        assert all('total_ratings' in agent for agent in top_agents)
    
    def test_top_agents_require_minimum_feedback(self, manager, sample_feedback_data):
        """Test top agents only includes agents with sufficient feedback."""
        # Agent with only 2 ratings (below threshold of 5)
        manager.collect_feedback(**sample_feedback_data, feedback_type=FeedbackType.THUMBS_UP)
        manager.collect_feedback(**sample_feedback_data, feedback_type=FeedbackType.THUMBS_UP)
        
        top_agents = manager.get_top_rated_agents()
        
        # Should not include agent with only 2 ratings
        assert len(top_agents) == 0
    
    # ========================================================================
    # Trend Analysis Tests
    # ========================================================================
    
    def test_get_feedback_trends_empty(self, manager):
        """Test trends with no feedback."""
        trends = manager.get_feedback_trends(days=7)
        
        assert trends['total_feedback'] == 0
        assert trends['daily_average'] == 0.0
        assert trends['trend'] == 'insufficient_data'
    
    def test_get_feedback_trends(self, manager, sample_feedback_data):
        """Test feedback trend calculation."""
        # Add some feedback
        for _ in range(10):
            manager.collect_feedback(**sample_feedback_data, feedback_type=FeedbackType.THUMBS_UP)
        
        trends = manager.get_feedback_trends(days=7)
        
        assert trends['total_feedback'] == 10
        assert trends['daily_average'] == 10 / 7
        assert 'daily_counts' in trends
    
    # ========================================================================
    # Statistics Tests
    # ========================================================================
    
    def test_get_statistics_empty(self, manager):
        """Test statistics with no feedback."""
        stats = manager.get_statistics()
        
        assert stats['total_feedback'] == 0
        assert stats['total_agents_with_models'] == 0
        assert stats['avg_rating_overall'] == 0.0
    
    def test_get_statistics(self, manager, sample_feedback_data):
        """Test overall statistics calculation."""
        # Add feedback for multiple agents
        for agent_num in range(2):
            data = {**sample_feedback_data, 'agent_id': f'agent-{agent_num}'}
            manager.collect_feedback(**data, feedback_type=FeedbackType.THUMBS_UP)
            manager.collect_feedback(**data, feedback_type=FeedbackType.THUMBS_DOWN)
        
        stats = manager.get_statistics()
        
        assert stats['total_feedback'] == 4
        assert stats['total_agents_with_models'] == 2
        assert stats['thumbs_up_count'] == 2
        assert stats['thumbs_down_count'] == 2
        assert stats['approval_rate'] == 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
