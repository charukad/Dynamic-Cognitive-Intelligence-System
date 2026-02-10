"""
Persona Extractor - Extract user traits from conversation history

Analyzes communication patterns to identify:
- Communication style (formal/casual, verbose/concise)
- Knowledge domains (topics of expertise)
- Emotional patterns (optimistic/pessimistic, etc.)
- Decision-making style (analytical/intuitive)
"""

from typing import Dict, List, Any
from collections import Counter, defaultdict
import re
from datetime import datetime


class PersonaExtractor:
    """Extract user persona from conversation history"""
    
    def __init__(self):
        """Initialize persona extractor with linguistic patterns"""
        self.formal_indicators = {
            'please', 'thank you', 'kindly', 'appreciate', 'regards',
            'sincerely', 'furthermore', 'moreover', 'nevertheless'
        }
        
        self.casual_indicators = {
            'yeah', 'nope', 'gonna', 'wanna', 'kinda', 'sorta',
            'cool', 'awesome', 'hey', 'okay', 'ok'
        }
        
        self.question_words = {
            'what', 'why', 'how', 'when', 'where', 'who', 'which'
        }
        
        self.emotion_positive = {
            'happy', 'great', 'excellent', 'wonderful', 'amazing',
            'love', 'enjoy', 'exciting', 'fantastic', 'perfect'
        }
        
        self.emotion_negative = {
            'bad', 'terrible', 'awful', 'hate', 'dislike', 
            'frustrating', 'annoying', 'difficult', 'problem', 'issue'
        }
    
    def extract_persona(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract persona profile from message history.
        
        Args:
            messages: List of message dicts with 'content', 'timestamp', 'role'
        
        Returns:
            Persona profile with traits and scores
        """
        if not messages:
            return self._empty_persona()
        
        # Filter user messages only
        user_messages = [
            msg for msg in messages 
            if msg.get('role') in ['user', 'human']
        ]
        
        if not user_messages:
            return self._empty_persona()
        
        return {
            'communication_style': self._analyze_communication_style(user_messages),
            'knowledge_domains': self._extract_knowledge_domains(user_messages),
            'emotional_pattern': self._analyze_emotional_pattern(user_messages),
            'decision_style': self._analyze_decision_style(user_messages),
            'interaction_stats': self._compute_interaction_stats(user_messages),
            'confidence': self._compute_confidence(len(user_messages)),
        }
    
    def _analyze_communication_style(self, messages: List[Dict]) -> Dict[str, float]:
        """Analyze how the user communicates"""
        total_words = 0
        total_messages = len(messages)
        formal_count = 0
        casual_count = 0
        question_count = 0
        
        for msg in messages:
            content = msg.get('content', '').lower()
            words = content.split()
            total_words += len(words)
            
            # Count formal vs casual markers
            formal_count += sum(1 for word in words if word in self.formal_indicators)
            casual_count += sum(1 for word in words if word in self.casual_indicators)
            
            # Count questions
            if any(q in content for q in self.question_words):
                question_count += 1
        
        avg_words_per_message = total_words / total_messages if total_messages > 0 else 0
        
        # Formality: -1 (very casual) to +1 (very formal)
        formality = 0.0
        if formal_count + casual_count > 0:
            formality = (formal_count - casual_count) / (formal_count + casual_count)
        
        # Verbosity: 0 (concise) to 1 (verbose)
        # Average message length: <10 words = concise, >50 words = verbose
        verbosity = min(1.0, avg_words_per_message / 50.0)
        
        # Inquisitiveness: ratio of questions
        inquisitiveness = question_count / total_messages if total_messages > 0 else 0
        
        return {
            'formality': round(formality, 3),  # -1 to +1
            'verbosity': round(verbosity, 3),   # 0 to 1
            'inquisitiveness': round(inquisitiveness, 3),  # 0 to 1
            'avg_message_length': round(avg_words_per_message, 1),
        }
    
    def _extract_knowledge_domains(self, messages: List[Dict]) -> List[Dict[str, Any]]:
        """Extract topics the user discusses frequently"""
        # Domain keywords (simplified - in production would use topic modeling)
        domain_keywords = {
            'programming': ['code', 'python', 'javascript', 'function', 'algorithm', 
                          'programming', 'software', 'debug', 'api', 'database'],
            'data_science': ['data', 'model', 'machine learning', 'ai', 'neural',
                           'training', 'dataset', 'prediction', 'classification'],
            'business': ['business', 'strategy', 'market', 'customer', 'revenue',
                        'growth', 'sales', 'management', 'startup'],
            'creative': ['design', 'art', 'creative', 'writing', 'story', 
                        'music', 'visual', 'aesthetic', 'style'],
            'science': ['research', 'study', 'theory', 'experiment', 'hypothesis',
                       'analysis', 'scientific', 'evidence'],
        }
        
        domain_counts = defaultdict(int)
        total_words = 0
        
        for msg in messages:
            content = msg.get('content', '').lower()
            words = set(content.split())
            total_words += len(words)
            
            for domain, keywords in domain_keywords.items():
                matches = sum(1 for kw in keywords if kw in content)
                domain_counts[domain] += matches
        
        # Convert to list with scores
        domains = []
        for domain, count in domain_counts.items():
            if count > 0:
                # Score based on frequency
                score = count / total_words if total_words > 0 else 0
                domains.append({
                    'domain': domain,
                    'mentions': count,
                    'score': round(score * 1000, 3),  # Scale up for readability
                })
        
        # Sort by score descending
        domains.sort(key=lambda x: x['score'], reverse=True)
        
        return domains[:5]  # Top 5 domains
    
    def _analyze_emotional_pattern(self, messages: List[Dict]) -> Dict[str, float]:
        """Analyze emotional tone"""
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for msg in messages:
            content = msg.get('content', '').lower()
            words = set(content.split())
            
            pos = sum(1 for word in words if word in self.emotion_positive)
            neg = sum(1 for word in words if word in self.emotion_negative)
            
            if pos > neg:
                positive_count += 1
            elif neg > pos:
                negative_count += 1
            else:
                neutral_count += 1
        
        total = len(messages)
        
        return {
            'positivity': round(positive_count / total, 3) if total > 0 else 0,
            'negativity': round(negative_count / total, 3) if total > 0 else 0,
            'neutrality': round(neutral_count / total, 3) if total > 0 else 0,
            'sentiment_balance': round(
                (positive_count - negative_count) / total, 3
            ) if total > 0 else 0,
        }
    
    def _analyze_decision_style(self, messages: List[Dict]) -> Dict[str, float]:
        """Analyze decision-making patterns"""
        analytical_markers = {
            'analyze', 'data', 'evidence', 'proof', 'logical', 'reason',
            'compare', 'evaluate', 'metrics', 'statistics'
        }
        
        intuitive_markers = {
            'feel', 'think', 'seems', 'believe', 'intuition', 'gut',
            'sense', 'impression', 'instinct'
        }
        
        analytical_count = 0
        intuitive_count = 0
        
        for msg in messages:
            content = msg.get('content', '').lower()
            words = content.split()
            
            analytical_count += sum(1 for word in words if word in analytical_markers)
            intuitive_count += sum(1 for word in words if word in intuitive_markers)
        
        total = analytical_count + intuitive_count
        
        # -1 (intuitive) to +1 (analytical)
        analytical_score = 0.0
        if total > 0:
            analytical_score = (analytical_count - intuitive_count) / total
        
        return {
            'analytical_score': round(analytical_score, 3),
            'analytical_markers': analytical_count,
            'intuitive_markers': intuitive_count,
        }
    
    def _compute_interaction_stats(self, messages: List[Dict]) -> Dict[str, Any]:
        """Compute interaction statistics"""
        if not messages:
            return {}
        
        # Get timestamps if available
        timestamps = [
            msg.get('timestamp') for msg in messages 
            if msg.get('timestamp')
        ]
        
        stats = {
            'total_messages': len(messages),
            'total_words': sum(len(msg.get('content', '').split()) for msg in messages),
        }
        
        if timestamps and len(timestamps) > 1:
            # Simple time span calculation
            stats['interaction_span_days'] = 'N/A'  # Would need proper datetime parsing
        
        return stats
    
    def _compute_confidence(self, message_count: int) -> float:
        """
        Compute confidence score based on data volume.
        More messages = higher confidence in persona accuracy.
        """
        # Logarithmic scale: 10 messages = 0.3, 50 = 0.6, 100 = 0.75, 500+ = 0.95
        if message_count < 10:
            return round(message_count * 0.03, 2)
        elif message_count < 50:
            return round(0.3 + (message_count - 10) * 0.0075, 2)
        elif message_count < 100:
            return round(0.6 + (message_count - 50) * 0.003, 2)
        elif message_count < 500:
            return round(0.75 + (message_count - 100) * 0.0005, 2)
        else:
            return 0.95
    
    def _empty_persona(self) -> Dict[str, Any]:
        """Return empty persona profile"""
        return {
            'communication_style': {
                'formality': 0.0,
                'verbosity': 0.0,
                'inquisitiveness': 0.0,
                'avg_message_length': 0.0,
            },
            'knowledge_domains': [],
            'emotional_pattern': {
                'positivity': 0.0,
                'negativity': 0.0,
                'neutrality': 1.0,
                'sentiment_balance': 0.0,
            },
            'decision_style': {
                'analytical_score': 0.0,
                'analytical_markers': 0,
                'intuitive_markers': 0,
            },
            'interaction_stats': {
                'total_messages': 0,
                'total_words': 0,
            },
            'confidence': 0.0,
        }
