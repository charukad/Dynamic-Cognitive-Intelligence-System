"""
Consistency Checker - Verify knowledge coherence

Validates consistency across:
- Memory systems (episodic, semantic, procedural)
- Agent responses over time
- Knowledge graph relationships

Metrics:
- Consistency score (0-1)
- Number of conflicts detected
- Knowledge drift rate
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict


class ConsistencyChecker:
    """Check consistency across knowledge systems"""
    
    def __init__(self):
        """Initialize consistency checker"""
        self.consistency_threshold = 0.7  # Below this = inconsistent
        self.drift_threshold = 0.15  # 15% drift is concerning
    
    def check_consistency(
        self,
        statements: List[Dict[str, Any]],
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Check consistency of statements over time.
        
        Args:
            statements: List of dicts with 'content', 'timestamp', 'source'
            time_window: Optional time window to analyze
        
        Returns:
            Consistency analysis
        """
        if not statements:
            return self._empty_result()
        
        # Filter by time window if specified
        if time_window:
            cutoff = datetime.utcnow() - time_window
            statements = [
                s for s in statements
                if self._parse_timestamp(s.get('timestamp')) >= cutoff
            ]
        
        # Group by topic/concept
        topics = self._group_by_topic(statements)
        
        # Check each topic for consistency
        topic_consistency = {}
        conflicts = []
        
        for topic, topic_statements in topics.items():
            result = self._check_topic_consistency(topic, topic_statements)
            topic_consistency[topic] = result['consistency_score']
            conflicts.extend(result['conflicts'])
        
        # Calculate overall metrics
        overall_score = (
            sum(topic_consistency.values()) / len(topic_consistency)
            if topic_consistency else 1.0
        )
        
        # Detect knowledge drift
        drift_rate = self._calculate_drift_rate(statements)
        
        return {
            'overall_consistency': round(overall_score, 3),
            'is_consistent': overall_score >= self.consistency_threshold,
            'topic_consistency': topic_consistency,
            'conflicts_detected': len(conflicts),
            'conflicts': conflicts,
            'knowledge_drift_rate': round(drift_rate, 3),
            'is_drifting': drift_rate > self.drift_threshold,
            'total_statements': len(statements),
            'topics_analyzed': len(topics),
        }
    
    def check_agent_response_consistency(
        self,
        responses: List[Dict[str, Any]],
        query: str
    ) -> Dict[str, Any]:
        """
        Check if agent responses are consistent for similar queries.
        
        Args:
            responses: List of agent responses with 'query', 'response', 'timestamp'
            query: Current query to check against
        
        Returns:
            Consistency analysis
        """
        if not responses:
            return {'is_consistent': True, 'consistency_score': 1.0}
        
        # Find similar past queries
        similar_responses = self._find_similar_queries(query, responses)
        
        if not similar_responses:
            return {'is_consistent': True, 'consistency_score': 1.0, 'note': 'No similar past queries'}
        
        # Check if responses are consistent
        response_texts = [r['response'] for r in similar_responses]
        
        # Simple consistency check: Are main points similar?
        consistency_score = self._calculate_response_similarity(response_texts)
        
        return {
            'is_consistent': consistency_score >= self.consistency_threshold,
            'consistency_score': round(consistency_score, 3),
            'similar_queries_found': len(similar_responses),
            'past_responses': similar_responses[:3],  # Show top 3
        }
    
    def check_knowledge_graph_consistency(
        self,
        relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check consistency of knowledge graph relationships.
        
        Args:
            relationships: List of (subject, predicate, object) triples
        
        Returns:
            Consistency analysis
        """
        if not relationships:
            return self._empty_result()
        
        conflicts = []
        
        # Check for inverse relationship conflicts
        # E.g., "A is_parent_of B" vs "B is_parent_of A"
        for i, rel1 in enumerate(relationships):
            for rel2 in relationships[i+1:]:
                if self._are_inverse_conflicts(rel1, rel2):
                    conflicts.append({
                        'type': 'inverse_conflict',
                        'relationship1': rel1,
                        'relationship2': rel2,
                    })
        
        # Check for transitivity violations
        # E.g., "A > B", "B > C", "C > A" (cycle)
        cycles = self._detect_cycles(relationships)
        for cycle in cycles:
            conflicts.append({
                'type': 'transitivity_violation',
                'cycle': cycle,
            })
        
        consistency_score = 1.0 - (len(conflicts) / max(len(relationships), 1))
        
        return {
            'overall_consistency': round(max(0, consistency_score), 3),
            'is_consistent': consistency_score >= self.consistency_threshold,
            'conflicts_detected': len(conflicts),
            'conflicts': conflicts,
            'relationships_analyzed': len(relationships),
        }
    
    def _group_by_topic(self, statements: List[Dict]) -> Dict[str, List[Dict]]:
        """Group statements by topic (simplified keyword-based)"""
        topics = defaultdict(list)
        
        # Simple keyword extraction (would use NER/topic modeling in production)
        for statement in statements:
            content = statement.get('content', '').lower()
            
            # Extract potential topics (nouns)
            words = content.split()
            # Simplified: use longest words as topics
            topic_words = [w for w in words if len(w) > 5]
            
            if topic_words:
                topic = topic_words[0]  # Use first significant word as topic
            else:
                topic = 'general'
            
            topics[topic].append(statement)
        
        return dict(topics)
    
    def _check_topic_consistency(
        self,
        topic: str,
        statements: List[Dict]
    ) -> Dict[str, Any]:
        """Check consistency of statements about same topic"""
        if len(statements) < 2:
            return {'consistency_score': 1.0, 'conflicts': []}
        
        # Import here to avoid circular dependency
        from .contradiction_detector import ContradictionDetector
        detector = ContradictionDetector()
        
        conflicts = []
        contents = [s.get('content', '') for s in statements]
        
        # Check pairwise for contradictions
        for i in range(len(contents)):
            for j in range(i + 1, len(contents)):
                result = detector.detect_contradiction(contents[i], contents[j])
                
                if result['is_contradiction']:
                    conflicts.append({
                        'topic': topic,
                        'statement1': contents[i],
                        'statement2': contents[j],
                        'contradiction_type': result['contradiction_type'],
                        'confidence': result['confidence'],
                    })
        
        # Consistency score: 1 - (conflicts / possible_pairs)
        possible_pairs = (len(statements) * (len(statements) - 1)) / 2
        consistency_score = 1.0 - (len(conflicts) / possible_pairs)
        
        return {
            'consistency_score': max(0, consistency_score),
            'conflicts': conflicts,
        }
    
    def _calculate_drift_rate(self, statements: List[Dict]) -> float:
        """Calculate rate of knowledge drift over time"""
        if len(statements) < 10:
            return 0.0  # Not enough data
        
        # Sort by timestamp
        sorted_statements = sorted(
            statements,
            key=lambda s: self._parse_timestamp(s.get('timestamp'))
        )
        
        # Split into early vs. recent
        mid = len(sorted_statements) // 2
        early_statements = sorted_statements[:mid]
        recent_statements = sorted_statements[mid:]
        
        # Compare consistency between periods
        early_check = self.check_consistency(early_statements)
        recent_check = self.check_consistency(recent_statements)
        
        # Drift = decrease in consistency
        drift = early_check['overall_consistency'] - recent_check['overall_consistency']
        
        return max(0, drift)
    
    def _find_similar_queries(
        self,
        query: str,
        responses: List[Dict]
    ) -> List[Dict]:
        """Find responses to similar queries"""
        # Simple keyword overlap similarity
        query_words = set(query.lower().split())
        
        similar = []
        for response in responses:
            past_query = response.get('query', '').lower()
            past_words = set(past_query.split())
            
            # Calculate Jaccard similarity
            overlap = len(query_words & past_words)
            union = len(query_words | past_words)
            similarity = overlap / union if union > 0 else 0
            
            if similarity > 0.5:  # 50% similarity threshold
                similar.append({
                    **response,
                    'similarity': similarity,
                })
        
        # Sort by similarity descending
        similar.sort(key=lambda x: x['similarity'], reverse=True)
        
        return similar
    
    def _calculate_response_similarity(self, responses: List[str]) -> float:
        """Calculate similarity between multiple responses"""
        if len(responses) < 2:
            return 1.0
        
        # Calculate pairwise similarity
        similarities = []
        for i in range(len(responses)):
            for j in range(i + 1, len(responses)):
                r1_words = set(responses[i].lower().split())
                r2_words = set(responses[j].lower().split())
                
                overlap = len(r1_words & r2_words)
                union = len(r1_words | r2_words)
                
                sim = overlap / union if union > 0 else 0
                similarities.append(sim)
        
        # Average similarity
        return sum(similarities) / len(similarities) if similarities else 1.0
    
    def _are_inverse_conflicts(self, rel1: Dict, rel2: Dict) -> bool:
        """Check if two relationships are inverse conflicts"""
        # E.g., "A parent_of B" vs "B parent_of A"
        return (
            rel1.get('subject') == rel2.get('object') and
            rel1.get('object') == rel2.get('subject') and
            rel1.get('predicate') == rel2.get('predicate')
        )
    
    def _detect_cycles(self, relationships: List[Dict]) -> List[List[Dict]]:
        """Detect cycles in relationships (simplified)"""
        # Build adjacency list
        graph = defaultdict(list)
        for rel in relationships:
            if rel.get('predicate') in ['greater_than', 'before', 'causes']:
                # Directed relationship
                graph[rel['subject']].append(rel['object'])
        
        # Simple cycle detection (would use proper DFS in production)
        cycles = []
        
        # For simplicity, just check 3-node cycles
        for start in graph:
            for mid in graph[start]:
                for end in graph.get(mid, []):
                    if end in graph and start in graph[end]:
                        cycles.append([start, mid, end, start])
        
        return cycles
    
    def _parse_timestamp(self, timestamp: Any) -> datetime:
        """Parse timestamp string or return default"""
        if isinstance(timestamp, datetime):
            return timestamp
        
        if isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                pass
        
        return datetime.utcnow()
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty consistency result"""
        return {
            'overall_consistency': 1.0,
            'is_consistent': True,
            'conflicts_detected': 0,
            'conflicts': [],
            'total_statements': 0,
        }
