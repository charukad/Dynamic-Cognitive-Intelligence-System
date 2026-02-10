"""
Personality Model - Build Big Five (OCEAN) personality profile

Models personality using the Five-Factor Model:
- Openness: Curiosity, creativity, unconventional thinking
- Conscientiousness: Organization, dependability, discipline
- Extraversion: Sociability, assertiveness, energy
- Agreeableness: Compassion, cooperation, trust
- Neuroticism: Anxiety, moodiness, emotional stability

Each trait scored 0.0 (low) to 1.0 (high)
"""

from typing import Dict, List, Any
from collections import Counter


class PersonalityModel:
    """Build OCEAN personality model from user interactions"""
    
    def __init__(self):
        """Initialize with trait indicator keywords"""
        # Openness indicators
        self.openness_high = {
            'creative', 'idea', 'imagine', 'curious', 'explore', 'innovative',
            'artistic', 'novel', 'unconventional', 'experiment', 'wonder',
        }
        
        self.openness_low = {
            'traditional', 'conventional', 'practical', 'realistic', 'standard',
        }
        
        # Conscientiousness indicators
        self.conscientiousness_high = {
            'plan', 'organize', 'schedule', 'detail', 'careful', 'thorough',
            'complete', 'finish', 'systematic', 'methodical', 'precise',
        }
        
        self.conscientiousness_low = {
            'spontaneous', 'flexible', 'casual', 'relaxed',
        }
        
        # Extraversion indicators
        self.extraversion_high = {
            'social', 'outgoing', 'talk', 'people', 'group', 'party',
            'energetic', 'active', 'assertive', 'confident',
        }
        
        self.extraversion_low = {
            'quiet', 'reserved', 'alone', 'solitary', 'introverted', 'shy',
        }
        
        # Agreeableness indicators
        self.agreeableness_high = {
            'help', 'kind', 'friendly', 'cooperate', 'trust', 'empathy',
            'compassion', 'understanding', 'supportive', 'generous',
        }
        
        self.agreeableness_low = {
            'compete', 'challenge', 'critical', 'skeptical', 'suspicious',
        }
        
        # Neuroticism indicators  
        self.neuroticism_high = {
            'worry', 'anxious', 'stress', 'nervous', 'fear', 'concerned',
            'tense', 'frustrated', 'upset', 'overwhelmed',
        }
        
        self.neuroticism_low = {
            'calm', 'relaxed', 'stable', 'confident', 'secure', 'comfortable',
        }
    
    def build_ocean_profile(
        self,
        messages: List[Dict[str, Any]],
        persona: Dict[str, Any],
        style: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Build OCEAN personality profile.
        
        Args:
            messages: User message history
            persona: Persona profile from PersonaExtractor
            style: Style profile from StyleTransfer
        
        Returns:
            OCEAN scores (each 0.0 to 1.0)
        """
        if not messages:
            return self._neutral_ocean()
        
        user_messages = [
            msg for msg in messages 
            if msg.get('role') in ['user', 'human']
        ]
        
        if not user_messages:
            return self._neutral_ocean()
        
        # Calculate each trait
        openness = self._calculate_openness(user_messages, persona, style)
        conscientiousness = self._calculate_conscientiousness(user_messages, persona, style)
        extraversion = self._calculate_extraversion(user_messages, persona, style)
        agreeableness = self._calculate_agreeableness(user_messages, persona, style)
        neuroticism = self._calculate_neuroticism(user_messages, persona, style)
        
        return {
            'openness': round(openness, 3),
            'conscientiousness': round(conscientiousness, 3),
            'extraversion': round(extraversion, 3),
            'agreeableness': round(agreeableness, 3),
            'neuroticism': round(neuroticism, 3),
        }
    
    def _calculate_openness(
        self,
        messages: List[Dict],
        persona: Dict,
        style: Dict
    ) -> float:
        """Calculate Openness score (curiosity, creativity)"""
        score = 0.5  # Start neutral
        
        # Count indicators
        high_count, low_count = self._count_trait_markers(
            messages, self.openness_high, self.openness_low
        )
        
        # Adjust based on markers
        if high_count + low_count > 0:
            marker_score = high_count / (high_count + low_count)
            score = score * 0.3 + marker_score * 0.7
        
        # Adjust based on knowledge domains (diverse = high openness)
        domains = persona.get('knowledge_domains', [])
        if len(domains) >= 3:
            score += 0.1
        
        # Adjust based on vocabulary richness
        vocab_richness = style.get('vocabulary', {}).get('vocab_richness', 0.5)
        score = score * 0.7 + vocab_richness * 0.3
        
        return min(1.0, max(0.0, score))
    
    def _calculate_conscientiousness(
        self,
        messages: List[Dict],
        persona: Dict,
        style: Dict
    ) -> float:
        """Calculate Conscientiousness score (organization, discipline)"""
        score = 0.5
        
        high_count, low_count = self._count_trait_markers(
            messages, self.conscientiousness_high, self.conscientiousness_low
        )
        
        if high_count + low_count > 0:
            marker_score = high_count / (high_count + low_count)
            score = score * 0.4 + marker_score * 0.6
        
        # Formal communication suggests higher conscientiousness
        formality = persona.get('communication_style', {}).get('formality', 0)
        score += formality * 0.1
        
        # Consistent punctuation suggests attention to detail
        punct_density = style.get('punctuation', {}).get('punctuation_density', 0)
        if punct_density > 0.05:  # Above average punctuation use
            score += 0.05
        
        return min(1.0, max(0.0, score))
    
    def _calculate_extraversion(
        self,
        messages: List[Dict],
        persona: Dict,
        style: Dict
    ) -> float:
        """Calculate Extraversion score (sociability, assertiveness)"""
        score = 0.5
        
        high_count, low_count = self._count_trait_markers(
            messages, self.extraversion_high, self.extraversion_low
        )
        
        if high_count + low_count > 0:
            marker_score = high_count / (high_count + low_count)
            score = score * 0.4 + marker_score * 0.6
        
        # Verbose, enthusiastic communication suggests extraversion
        verbosity = persona.get('communication_style', {}).get('verbosity', 0.5)
        score += verbosity * 0.1
        
        # Exclamation marks suggest expressiveness
        exclaim_ratio = style.get('sentence_structure', {}).get('exclamation_ratio', 0)
        score += exclaim_ratio * 0.2
        
        return min(1.0, max(0.0, score))
    
    def _calculate_agreeableness(
        self,
        messages: List[Dict],
        persona: Dict,
        style: Dict
    ) -> float:
        """Calculate Agreeableness score (compassion, cooperation)"""
        score = 0.5
        
        high_count, low_count = self._count_trait_markers(
            messages, self.agreeableness_high, self.agreeableness_low
        )
        
        if high_count + low_count > 0:
            marker_score = high_count / (high_count + low_count)
            score = score * 0.5 + marker_score * 0.5
        
        # Positive emotional tone suggests agreeableness
        positivity = persona.get('emotional_pattern', {}).get('positivity', 0.5)
        score += positivity * 0.15
        
        # Polite, formal language correlates with agreeableness
        formality = persona.get('communication_style', {}).get('formality', 0)
        if formality > 0:
            score += formality * 0.1
        
        return min(1.0, max(0.0, score))
    
    def _calculate_neuroticism(
        self,
        messages: List[Dict],
        persona: Dict,
        style: Dict
    ) -> float:
        """Calculate Neuroticism score (anxiety, mood stability)"""
        score = 0.5
        
        high_count, low_count = self._count_trait_markers(
            messages, self.neuroticism_high, self.neuroticism_low
        )
        
        if high_count + low_count > 0:
            marker_score = high_count / (high_count + low_count)
            score = score * 0.5 + marker_score * 0.5
        
        # Negative emotional tone suggests higher neuroticism
        negativity = persona.get('emotional_pattern', {}).get('negativity', 0)
        score += negativity * 0.2
        
        # Excessive punctuation (!!!, ???) may indicate anxiety
        question_count = style.get('punctuation', {}).get('question_count', 0)
        exclaim_count = style.get('punctuation', {}).get('exclamation_count', 0)
        total_msg = len(messages)
        if total_msg > 0:
            intense_punct = (question_count + exclaim_count) / total_msg
            if intense_punct > 2:  # More than 2 per message
                score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def _count_trait_markers(
        self,
        messages: List[Dict],
        high_markers: set,
        low_markers: set
    ) -> tuple:
        """Count high and low trait indicator words"""
        high_count = 0
        low_count = 0
        
        for msg in messages:
            content = msg.get('content', '').lower()
            words = content.split()
            
            high_count += sum(1 for word in words if word in high_markers)
            low_count += sum(1 for word in words if word in low_markers)
        
        return high_count, low_count
    
    def _neutral_ocean(self) -> Dict[str, float]:
        """Return neutral OCEAN profile (all traits at 0.5)"""
        return {
            'openness': 0.5,
            'conscientiousness': 0.5,
            'extraversion': 0.5,
            'agreeableness': 0.5,
            'neuroticism': 0.5,
        }
    
    def interpret_ocean(self, ocean: Dict[str, float]) -> Dict[str, str]:
        """
        Provide human-readable interpretation of OCEAN scores.
        
        Args:
            ocean: OCEAN scores dict
        
        Returns:
            Interpretations for each trait
        """
        def interpret_score(score: float, trait: str) -> str:
            if score < 0.3:
                interpretations = {
                    'openness': 'Prefers familiar, traditional approaches',
                    'conscientiousness': 'Spontaneous, flexible with plans',
                    'extraversion': 'Reserved, prefers solitary activities',
                    'agreeableness': 'Direct, competitive, challenges others',
                    'neuroticism': 'Calm, emotionally stable, resilient',
                }
                return interpretations.get(trait, 'Low')
            elif score > 0.7:
                interpretations = {
                    'openness': 'Creative, curious, loves new experiences',
                    'conscientiousness': 'Organized, disciplined, detail-oriented',
                    'extraversion': 'Sociable, energetic, assertive',
                    'agreeableness': 'Cooperative, empathetic, trusting',
                    'neuroticism': 'Prone to worry, stress-sensitive',
                }
                return interpretations.get(trait, 'High')
            else:
                return 'Moderate, balanced trait expression'
        
        return {
            trait: interpret_score(score, trait)
            for trait, score in ocean.items()
        }
