"""
Reinforcement Learning from Human Feedback (RLHF)

Human-in-the-loop learning system:
- Collect user feedback on agent responses
- Build reward models from preferences
- Track response quality over time
- Enable continuous agent improvement
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from src.core import get_logger

logger = get_logger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class FeedbackType(Enum):
    """Types of user feedback."""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    RATING = "rating"  # 1-5 stars
    TEXT_FEEDBACK = "text_feedback"


class FeedbackCategory(Enum):
    """Feedback categories."""
    ACCURACY = "accuracy"
    HELPFULNESS = "helpfulness"
    CLARITY = "clarity"
    RELEVANCE = "relevance"
    COMPLETENESS = "completeness"


@dataclass
class UserFeedback:
    """Single piece of user feedback."""
    
    id: UUID
    session_id: str
    message_id: str  # ID of the message being rated
    agent_id: str
    
    # Feedback content
    feedback_type: FeedbackType
    rating: Optional[float] = None  # 0-1 normalized (or 1-5 stars)
    text_feedback: Optional[str] = None
    categories: List[FeedbackCategory] = field(default_factory=list)
    
    # Context
    user_query: str = ""
    agent_response: str = ""
    model_version: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'session_id': self.session_id,
            'message_id': self.message_id,
            'agent_id': self.agent_id,
            'feedback_type': self.feedback_type.value,
            'rating': self.rating,
            'text_feedback': self.text_feedback,
            'categories': [c.value for c in self.categories],
            'user_query': self.user_query,
            'agent_response': self.agent_response,
            'model_version': self.model_version,
            'created_at': self.created_at.isoformat(),
            'user_id': self.user_id,
            'metadata': self.metadata,
        }


@dataclass
class RewardModel:
    """Learned reward model for agent behavior."""
    
    id: UUID
    agent_id: str
    name: str
    
    # Model parameters
    positive_samples: int = 0
    negative_samples: int = 0
    total_ratings: int = 0
    avg_rating: float = 0.0
    
    # Feature weights (learned from feedback)
    feature_weights: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'agent_id': self.agent_id,
            'name': self.name,
            'positive_samples': self.positive_samples,
            'negative_samples': self.negative_samples,
            'total_ratings': self.total_ratings,
            'avg_rating': self.avg_rating,
            'feature_weights': self.feature_weights,
            'accuracy': self.accuracy,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
        }
    
    @property
    def accuracy(self) -> float:
        """Calculate model accuracy (% of positive feedback)."""
        if self.total_ratings == 0:
            return 0.0
        return self.positive_samples / self.total_ratings


# ============================================================================
# Feedback Manager
# ============================================================================

class FeedbackManager:
    """
    Manage user feedback and reward models.
    
    Collects feedback, trains reward models, and provides
    quality scores for agent responses.
    """
    
    def __init__(self):
        """Initialize feedback manager."""
        self.feedback_history: List[UserFeedback] = []
        self.reward_models: Dict[str, RewardModel] = {}  # agent_id -> model
        
        logger.info("Initialized FeedbackManager")
    
    def collect_feedback(
        self,
        session_id: str,
        message_id: str,
        agent_id: str,
        feedback_type: FeedbackType,
        user_query: str = "",
        agent_response: str = "",
        rating: Optional[float] = None,
        text_feedback: Optional[str] = None,
        categories: Optional[List[FeedbackCategory]] = None,
        user_id: Optional[str] = None,
        model_version: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UserFeedback:
        """
        Collect user feedback on agent response.
        
        Args:
            session_id: Session identifier
            message_id: Message being rated
            agent_id: Agent that generated response
            feedback_type: Type of feedback
            user_query: Original user query
            agent_response: Agent's response
            rating: Optional numeric rating (0-1 or 1-5)
            text_feedback: Optional text feedback
            categories: Optional feedback categories
            user_id: Optional user identifier
            model_version: Optional model version
            metadata: Optional additional metadata
            
        Returns:
            UserFeedback object
        """
        feedback = UserFeedback(
            id=uuid4(),
            session_id=session_id,
            message_id=message_id,
            agent_id=agent_id,
            feedback_type=feedback_type,
            rating=rating,
            text_feedback=text_feedback,
            categories=categories or [],
            user_query=user_query,
            agent_response=agent_response,
            model_version=model_version,
            user_id=user_id,
            metadata=metadata or {},
        )
        
        self.feedback_history.append(feedback)
        
        # Update reward model
        self._update_reward_model(agent_id, feedback)
        
        logger.info(
            f"Collected {feedback_type.value} feedback for agent {agent_id} "
            f"(message: {message_id})"
        )
        
        return feedback
    
    def _update_reward_model(self, agent_id: str, feedback: UserFeedback):
        """Update reward model with new feedback."""
        # Create model if doesn't exist
        if agent_id not in self.reward_models:
            self.reward_models[agent_id] = RewardModel(
                id=uuid4(),
                agent_id=agent_id,
                name=f"Reward Model - {agent_id}",
            )
        
        model = self.reward_models[agent_id]
        
        # Update counts
        model.total_ratings += 1
        model.last_updated = datetime.now()
        
        # Process feedback
        if feedback.feedback_type == FeedbackType.THUMBS_UP:
            model.positive_samples += 1
            feedback_value = 1.0
        elif feedback.feedback_type == FeedbackType.THUMBS_DOWN:
            model.negative_samples += 1
            feedback_value = 0.0
        elif feedback.feedback_type == FeedbackType.RATING and feedback.rating is not None:
            # Normalize rating to 0-1
            if feedback.rating <= 1.0:
                feedback_value = feedback.rating
            else:
                feedback_value = feedback.rating / 5.0  # Assume 1-5 scale
            
            if feedback_value >= 0.6:
                model.positive_samples += 1
            else:
                model.negative_samples += 1
        else:
            feedback_value = 0.5  # Neutral
        
        # Update running average rating
        n = model.total_ratings
        model.avg_rating = (model.avg_rating * (n - 1) + feedback_value) / n
        
        # Update feature weights (simple approach)
        for category in feedback.categories:
            if category.value not in model.feature_weights:
                model.feature_weights[category.value] = 0.0
            
            # Update weight with exponential moving average
            alpha = 0.1  # Learning rate
            current_weight = model.feature_weights[category.value]
            model.feature_weights[category.value] = (
                (1 - alpha) * current_weight + alpha * feedback_value
            )
    
    def get_reward_score(
        self,
        agent_id: str,
        response: str,
        query: str = "",
    ) -> float:
        """
        Calculate predicted reward score for a response.
        
        Args:
            agent_id: Agent identifier
            response: Agent response to score
            query: User query
            
        Returns:
            Predicted reward score (0-1)
        """
        if agent_id not in self.reward_models:
            return 0.5  # Neutral score for unknown agents
        
        model = self.reward_models[agent_id]
        
        # Simple heuristic-based scoring
        # In production, this would use ML model
        score = model.avg_rating
        
        # Adjust based on response length (prefer detailed responses)
        response_length = len(response.split())
        if 50 <= response_length <= 300:
            score += 0.1
        elif response_length < 20:
            score -= 0.1
        
        # Adjust based on query similarity (simple check)
        if query and query.lower() in response.lower():
            score += 0.05
        
        return max(0.0, min(1.0, score))
    
    def get_agent_feedback_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get feedback summary for an agent."""
        agent_feedback = [f for f in self.feedback_history if f.agent_id == agent_id]
        
        if not agent_feedback:
            return {
                'agent_id': agent_id,
                'total_feedback': 0,
                'avg_rating': 0.0,
                'thumbs_up': 0,
                'thumbs_down': 0,
                'feedback_distribution': {},
            }
        
        thumbs_up = len([f for f in agent_feedback if f.feedback_type == FeedbackType.THUMBS_UP])
        thumbs_down = len([f for f in agent_feedback if f.feedback_type == FeedbackType.THUMBS_DOWN])
        
        # Calculate average rating
        ratings = [
            f.rating for f in agent_feedback
            if f.rating is not None
        ]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
        
        # Category distribution
        category_counts = {}
        for feedback in agent_feedback:
            for category in feedback.categories:
                category_counts[category.value] = category_counts.get(category.value, 0) + 1
        
        return {
            'agent_id': agent_id,
            'total_feedback': len(agent_feedback),
            'avg_rating': avg_rating,
            'thumbs_up': thumbs_up,
            'thumbs_down': thumbs_down,
            'approval_rate': thumbs_up / (thumbs_up + thumbs_down) if (thumbs_up + thumbs_down) > 0 else 0.0,
            'feedback_distribution': category_counts,
            'recent_feedback': [f.to_dict() for f in agent_feedback[-10:]],
        }
    
    def get_top_rated_agents(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top-rated agents based on feedback."""
        agent_ratings = []
        
        for agent_id, model in self.reward_models.items():
            if model.total_ratings >= 5:  # Minimum feedback threshold
                agent_ratings.append({
                    'agent_id': agent_id,
                    'avg_rating': model.avg_rating,
                    'accuracy': model.accuracy,
                    'total_ratings': model.total_ratings,
                })
        
        # Sort by average rating
        agent_ratings.sort(key=lambda x: x['avg_rating'], reverse=True)
        
        return agent_ratings[:limit]
    
    def get_feedback_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get feedback trends over time."""
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_feedback = [
            f for f in self.feedback_history
            if f.created_at >= cutoff_date
        ]
        
        if not recent_feedback:
            return {
                'period_days': days,
                'total_feedback': 0,
                'daily_average': 0.0,
                'trend': 'stable',
            }
        
        # Group by day
        daily_counts = {}
        daily_ratings = {}
        
        for feedback in recent_feedback:
            day = feedback.created_at.date().isoformat()
            daily_counts[day] = daily_counts.get(day, 0) + 1
            
            if feedback.rating:
                if day not in daily_ratings:
                    daily_ratings[day] = []
                daily_ratings[day].append(feedback.rating)
        
        # Calculate trend
        avg_ratings_by_day = {
            day: sum(ratings) / len(ratings)
            for day, ratings in daily_ratings.items()
        }
        
        if len(avg_ratings_by_day) >= 2:
            days_sorted = sorted(avg_ratings_by_day.keys())
            first_half_avg = sum(
                avg_ratings_by_day[d] for d in days_sorted[:len(days_sorted)//2]
            ) / (len(days_sorted) // 2)
            second_half_avg = sum(
                avg_ratings_by_day[d] for d in days_sorted[len(days_sorted)//2:]
            ) / (len(days_sorted) - len(days_sorted) // 2)
            
            if second_half_avg > first_half_avg + 0.1:
                trend = 'improving'
            elif second_half_avg < first_half_avg - 0.1:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'period_days': days,
            'total_feedback': len(recent_feedback),
            'daily_average': len(recent_feedback) / days,
            'daily_counts': daily_counts,
            'trend': trend,
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall feedback statistics."""
        total_feedback = len(self.feedback_history)
        
        if total_feedback == 0:
            return {
                'total_feedback': 0,
                'total_agents_with_models': 0,
                'avg_rating_overall': 0.0,
            }
        
        # Overall statistics
        all_ratings = [f.rating for f in self.feedback_history if f.rating is not None]
        avg_rating = sum(all_ratings) / len(all_ratings) if all_ratings else 0.0
        
        thumbs_up_count = len([
            f for f in self.feedback_history
            if f.feedback_type == FeedbackType.THUMBS_UP
        ])
        
        thumbs_down_count = len([
            f for f in self.feedback_history
            if f.feedback_type == FeedbackType.THUMBS_DOWN
        ])
        
        return {
            'total_feedback': total_feedback,
            'total_agents_with_models': len(self.reward_models),
            'avg_rating_overall': avg_rating,
            'thumbs_up_count': thumbs_up_count,
            'thumbs_down_count': thumbs_down_count,
            'approval_rate': (
                thumbs_up_count / (thumbs_up_count + thumbs_down_count)
                if (thumbs_up_count + thumbs_down_count) > 0 else 0.0
            ),
        }


# ============================================================================
# Singleton Instance
# ============================================================================

feedback_manager = FeedbackManager()
