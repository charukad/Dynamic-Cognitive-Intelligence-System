"""
Contrastive Service - Main orchestrator for contradiction detection and consistency checking

Provides unified interface for:
- Detecting contradictions in statements
- Checking knowledge consistency
- Monitoring cognitive dissonance
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

from .contradiction_detector import ContradictionDetector, ContradictionType, ContradictionSeverity
from .consistency_checker import ConsistencyChecker


@dataclass
class ContradictionResult:
    """Result of contradiction analysis"""
    is_contradiction: bool
    contradiction_type: Optional[str]
    severity: Optional[str]
    confidence: float
    explanation: str
    statement1: str
    statement2: str
    detected_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['detected_at'] = self.detected_at.isoformat()
        return data


class ContrastiveService:
    """
    Main service for contrastive learning operations.
    
    Orchestrates contradiction detection and consistency checking
    across the multi-agent system.
    """
    
    def __init__(self):
        """Initialize contrastive service"""
        self.contradiction_detector = ContradictionDetector()
        self.consistency_checker = ConsistencyChecker()
        
        # Store detected conflicts (in-memory, would use DB in production)
        self._conflicts: List[ContradictionResult] = []
    
    async def check_statement_consistency(
        self,
        statement: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check if a new statement is consistent with existing knowledge.
        
        Args:
            statement: Statement to check
            context: Optional context (user_id, session_id, etc.)
        
        Returns:
            Consistency analysis
        """
        user_id = context.get('user_id') if context else None
        
        # Get past statements for this user/session
        past_statements = self._get_past_statements(user_id)
        
        if not past_statements:
            return {
                'is_consistent': True,
                'consistency_score': 1.0,
                'conflicts': [],
                'note': 'No past statements to compare against'
            }
        
        # Check for contradictions
        conflicts = []
        for past_stmt in past_statements:
            result = self.contradiction_detector.detect_contradiction(
                statement,
                past_stmt['content']
            )
            
            if result['is_contradiction'] and result['confidence'] >= 0.7:
                conflict = ContradictionResult(
                    is_contradiction=True,
                    contradiction_type=result['contradiction_type'],
                    severity=result['severity'],
                    confidence=result['confidence'],
                    explanation=result['explanation'],
                    statement1=statement,
                    statement2=past_stmt['content'],
                    detected_at=datetime.utcnow(),
                )
                conflicts.append(conflict)
                self._conflicts.append(conflict)
        
        consistency_score = 1.0 - (len(conflicts) / max(len(past_statements), 1))
        
        return {
            'is_consistent': len(conflicts) == 0,
            'consistency_score': round(max(0, consistency_score), 3),
            'conflicts_detected': len(conflicts),
            'conflicts': [c.to_dict() for c in conflicts],
        }
    
    async def detect_contradiction(
        self,
        statement1: str,
        statement2: str
    ) -> Dict[str, Any]:
        """
        Detect contradiction between two statements.
        
        Args:
            statement1: First statement
            statement2: Second statement
        
        Returns:
            Contradiction analysis
        """
        result = self.contradiction_detector.detect_contradiction(statement1, statement2)
        
        if result['is_contradiction']:
            # Store conflict
            conflict = ContradictionResult(
                is_contradiction=True,
                contradiction_type=result['contradiction_type'],
                severity=result['severity'],
                confidence=result['confidence'],
                explanation=result['explanation'],
                statement1=statement1,
                statement2=statement2,
                detected_at=datetime.utcnow(),
            )
            self._conflicts.append(conflict)
        
        return result
    
    async def check_agent_consistency(
        self,
        agent_id: str,
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Check consistency of an agent's responses over time.
        
        Args:
            agent_id: Agent identifier
            time_window: Optional time window (default: 24 hours)
        
        Returns:
            Consistency analysis
        """
        if time_window is None:
            time_window = timedelta(hours=24)
        
        # Get agent's recent responses
        responses = self._get_agent_responses(agent_id, time_window)
        
        if len(responses) < 2:
            return {
                'is_consistent': True,
                'consistency_score': 1.0,
                'note': 'Insufficient data for consistency check'
            }
        
        # Convert to format expected by consistency checker
        statements = [
            {
                'content': r.get('response', ''),
                'timestamp': r.get('timestamp'),
                'source': f"agent_{agent_id}"
            }
            for r in responses
        ]
        
        result = self.consistency_checker.check_consistency(statements, time_window)
        
        return result
    
    async def get_all_conflicts(
        self,
        min_severity: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all detected conflicts.
        
        Args:
            min_severity: Minimum severity filter
            limit: Maximum number of results
        
        Returns:
            List of conflicts
        """
        conflicts = self._conflicts
        
        # Filter by severity if specified
        if min_severity:
            severity_order = ['low', 'medium', 'high', 'critical']
            severity_idx = severity_order.index(min_severity)
            
            conflicts = [
                c for c in conflicts
                if c.severity and severity_order.index(c.severity) >= severity_idx
            ]
        
        # Sort by timestamp descending (most recent first)
        conflicts.sort(key=lambda c: c.detected_at, reverse=True)
        
        return [c.to_dict() for c in conflicts[:limit]]
    
    async def resolve_conflict(self, conflict_id: int) -> bool:
        """
        Mark a conflict as resolved.
        
        Args:
            conflict_id: Index of conflict in internal list
        
        Returns:
            Success status
        """
        if 0 <= conflict_id < len(self._conflicts):
            # In production, would update DB record
            # For now, just remove from list
            self._conflicts.pop(conflict_id)
            return True
        
        return False
    
    async def get_consistency_metrics(self) -> Dict[str, Any]:
        """
        Get overall consistency metrics for the system.
        
        Returns:
            System-wide consistency metrics
        """
        if not self._conflicts:
            return {
                'total_conflicts': 0,
                'critical_conflicts': 0,
                'high_conflicts': 0,
                'medium_conflicts': 0,
                'low_conflicts': 0,
                'overall_health': 'healthy',
            }
        
        # Count by severity
        severity_counts = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
        }
        
        for conflict in self._conflicts:
            if conflict.severity:
                severity_counts[conflict.severity] += 1
        
        # Determine health status
        if severity_counts['critical'] > 0:
            health = 'critical'
        elif severity_counts['high'] > 5:
            health = 'poor'
        elif severity_counts['medium'] > 10:
            health = 'concerning'
        else:
            health = 'healthy'
        
        return {
            'total_conflicts': len(self._conflicts),
            'critical_conflicts': severity_counts['critical'],
            'high_conflicts': severity_counts['high'],
            'medium_conflicts': severity_counts['medium'],
            'low_conflicts': severity_counts['low'],
            'overall_health': health,
        }
    
    def _get_past_statements(self, user_id: Optional[str]) -> List[Dict]:
        """Get past statements for user (stub - would query DB)"""
        # In production, query from episodic memory or database
        return []
    
    def _get_agent_responses(self, agent_id: str, time_window: timedelta) -> List[Dict]:
        """Get agent responses within time window (stub - would query DB)"""
        # In production, query from task/response database
        return []


# Singleton instance
contrastive_service = ContrastiveService()
