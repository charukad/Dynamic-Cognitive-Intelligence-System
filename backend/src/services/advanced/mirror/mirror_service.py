"""
Mirror Service - Main orchestrator for Digital Twin system

Creates and manages digital twins of users based on interaction history.
"""

from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime
from dataclasses import dataclass, asdict

from .persona_extractor import PersonaExtractor
from .style_transfer import StyleTransfer
from .personality_model import PersonalityModel


@dataclass
class DigitalTwin:
    """Digital twin data model"""
    user_id: str
    persona_profile: Dict[str, Any]
    style_signature: Dict[str, Any]
    personality_ocean: Dict[str, float]
    personality_interpretation: Dict[str, str]
    knowledge_domains: List[str]
    interaction_count: int
    confidence_score: float
    created_at: datetime
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert datetime to ISO format
        data['created_at'] = self.created_at.isoformat()
        data['last_updated'] = self.last_updated.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DigitalTwin':
        """Create from dictionary"""
        # Convert ISO strings back to datetime
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)


class MirrorService:
    """
    Main service for creating and managing digital twins.
    
    Orchestrates persona extraction, style transfer, and personality modeling
    to build comprehensive user profiles.
    """
    
    def __init__(self):
        """Initialize mirror service with component extractors"""
        self.persona_extractor = PersonaExtractor()
        self.style_transfer = StyleTransfer()
        self.personality_model = PersonalityModel()
        
        # In-memory storage (in production, use database)
        self._twins: Dict[str, DigitalTwin] = {}
    
    async def create_twin(
        self,
        user_id: str,
        messages: List[Dict[str, Any]],
    ) -> DigitalTwin:
        """
        Create a digital twin from user's message history.
        
        Args:
            user_id: Unique user identifier
            messages: List of messages with 'content', 'timestamp', 'role'
        
        Returns:
            DigitalTwin instance
        """
        # Extract components
        persona = self.persona_extractor.extract_persona(messages)
        style = self.style_transfer.extract_style(messages)
        ocean = self.personality_model.build_ocean_profile(messages, persona, style)
        interpretation = self.personality_model.interpret_ocean(ocean)
        
        # Extract top knowledge domains
        domains = [
            domain['domain'] 
            for domain in persona.get('knowledge_domains', [])[:5]
        ]
        
        # Create twin
        twin = DigitalTwin(
            user_id=user_id,
            persona_profile=persona,
            style_signature=style,
            personality_ocean=ocean,
            personality_interpretation=interpretation,
            knowledge_domains=domains,
            interaction_count=len([m for m in messages if m.get('role') in ['user', 'human']]),
            confidence_score=persona.get('confidence', 0.0),
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
        )
        
        # Store twin
        self._twins[user_id] = twin
        
        return twin
    
    async def get_twin(self, user_id: str) -> Optional[DigitalTwin]:
        """Get existing digital twin"""
        return self._twins.get(user_id)
    
    async def update_twin(
        self,
        user_id: str,
        new_messages: List[Dict[str, Any]],
    ) -> Optional[DigitalTwin]:
        """
        Update digital twin with new interaction data.
        
        Args:
            user_id: User identifier
            new_messages: New messages to incorporate
        
        Returns:
            Updated DigitalTwin or None if not found
        """
        existing_twin = self._twins.get(user_id)
        
        if not existing_twin:
            return None
        
        # Re-extract with new messages
        # In production, would append to history and re-analyze
        updated_twin = await self.create_twin(user_id, new_messages)
        
        return updated_twin
    
    async def delete_twin(self, user_id: str) -> bool:
        """Delete digital twin (privacy compliance)"""
        if user_id in self._twins:
            del self._twins[user_id]
            return True
        return False
    
    async def simulate_response(
        self,
        user_id: str,
        context: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Simulate how the user would respond to a given context.
        
        This is for testing twin accuracy, NOT for impersonation.
        
        Args:
            user_id: User identifier
            context:Ситуational context
        
        Returns:
            Simulated response characteristics
        """
        twin = self._twins.get(user_id)
        
        if not twin:
            return None
        
        # Return predicted response characteristics based on twin
        style = twin.style_signature
        persona = twin.persona_profile
        ocean = twin.personality_ocean
        
        return {
            'predicted_length_words': style.get('length_distribution', {}).get(
                'avg_words_per_message', 0
            ),
            'predicted_formality': persona.get('communication_style', {}).get(
                'formality', 0
            ),
            'predicted_sentiment': persona.get('emotional_pattern', {}).get(
                'sentiment_balance', 0
            ),
            'likely_topics': twin.knowledge_domains,
            'personality_influence': {
                'openness': ocean.get('openness', 0.5),
                'conscientiousness': ocean.get('conscientiousness', 0.5),
                'extraversion': ocean.get('extraversion', 0.5),
            },
            'note': 'This is a probabilistic prediction, not actual user response',
        }
    
    async def get_twin_accuracy_metrics(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get confidence metrics for twin accuracy.
        
        Args:
            user_id: User identifier
        
        Returns:
            Accuracy metrics
        """
        twin = self._twins.get(user_id)
        
        if not twin:
            return None
        
        return {
            'overall_confidence': twin.confidence_score,
            'interaction_count': twin.interaction_count,
            'data_quality': {
                'sufficient_messages': twin.interaction_count >= 50,
                'diverse_domains': len(twin.knowledge_domains) >= 2,
                'clear_personality': max(twin.personality_ocean.values()) > 0.6,
            },
            'recommended_actions': self._recommend_improvements(twin),
        }
    
    def _recommend_improvements(self, twin: DigitalTwin) -> List[str]:
        """Recommend steps to improve twin accuracy"""
        recommendations = []
        
        if twin.interaction_count < 50:
            recommendations.append(
                f"Collect {50 - twin.interaction_count} more messages for higher confidence"
            )
        
        if len(twin.knowledge_domains) < 2:
            recommendations.append(
                "Encourage discussions across multiple topics for better domain modeling"
            )
        
        if twin.confidence_score < 0.7:
            recommendations.append(
                "Continue interactions to improve overall confidence"
            )
        
        # Check for extreme neutral personality (no clear traits)
        neutral_traits = sum(
            1 for score in twin.personality_ocean.values()
            if 0.4 <= score <= 0.6
        )
        if neutral_traits >= 4:
            recommendations.append(
                "Personality traits are unclear; varied interactions needed"
            )
        
        if not recommendations:
            recommendations.append("Twin model is well-calibrated")
        
        return recommendations
    
    async def list_twins(self) -> List[Dict[str, Any]]:
        """List all digital twins (for admin)"""
        return [
            {
                'user_id': twin.user_id,
                'confidence': twin.confidence_score,
                'interaction_count': twin.interaction_count,
                'last_updated': twin.last_updated.isoformat(),
            }
            for twin in self._twins.values()
        ]


# Singleton instance
mirror_service = MirrorService()
