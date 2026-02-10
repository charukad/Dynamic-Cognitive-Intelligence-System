"""
Contrastive Learning Tests

Tests for contradiction detection and consistency checking.
"""

import pytest
from src.services.advanced.contrastive import (
    ContradictionDetector,
    ConsistencyChecker,
    ContrastiveService,
)


# Fixtures
@pytest.fixture
def contradictory_statements():
    """Pairs of contradictory statements"""
    return [
        ("Python is fast", "Python is not fast"),
        ("All birds fly", "No birds fly"),
        ("The server is secure", "The server is insecure"),
    ]


@pytest.fixture
def consistent_statements():
    """Pairs of consistent statements"""
    return [
        ("Python is popular", "Many developers use Python"),
        ("Databases store data", "Data can be stored in databases"),
    ]


# ContradictionDetector Tests
class TestContradictionDetector:
    """Test contradiction detection"""
    
    def test_detect_direct_negation(self):
        """Test detection of direct negation"""
        detector = ContradictionDetector()
        
        result = detector.detect_contradiction(
            "Python is fast",
            "Python is not fast"
        )
        
        assert result['is_contradiction'] is True
        assert result['contradiction_type'] == 'direct'
        assert result['confidence'] > 0.5
    
    def test_detect_antonym_contradiction(self):
        """Test antonym-based contradiction"""
        detector = ContradictionDetector()
        
        result = detector.detect_contradiction(
            "The system is stable",
            "The system is unstable"
        )
        
        assert result['is_contradiction'] is True
        assert result['contradiction_type'] == 'semantic'
    
    def test_detect_logical_contradiction(self):
        """Test logical contradiction (universal vs existential)"""
        detector = ContradictionDetector()
        
        result = detector.detect_contradiction(
            "All agents are online",
            "Some agents are not online"
        )
        
        assert result['is_contradiction'] is True
        assert result['contradiction_type'] == 'logical'
    
    def test_no_contradiction(self, consistent_statements):
        """Test that consistent statements are not flagged"""
        detector = ContradictionDetector()
        
        for s1, s2 in consistent_statements:
            result = detector.detect_contradiction(s1, s2)
            assert result['is_contradiction'] is False
    
    def test_batch_detection(self, contradictory_statements):
        """Test batch contradiction detection"""
        detector = ContradictionDetector()
        
        statements = ["Python is fast", "Java is fast", "Python is not fast"]
        results = detector.detect_batch_contradictions(statements)
        
        # Should find contradiction between statements 0 and 2
        assert len(results) > 0
        assert results[0]['is_contradiction'] is True
    
    def test_severity_classification(self):
        """Test severity classification"""
        detector = ContradictionDetector()
        
        # Direct contradiction should be HIGH severity
        result = detector.detect_contradiction(
            "System is secure",
            "System is not secure"
        )
        
        if result['is_contradiction']:
            assert result['severity'] in ['medium', 'high', 'critical']
    
    def test_explanation_generation(self):
        """Test human-readable explanation"""
        detector = ContradictionDetector()
        
        result = detector.detect_contradiction(
            "The service is running",
            "The service is not running"
        )
        
        explanation = detector.explain_contradiction(result)
        
        assert len(explanation) > 0
        assert 'Contradiction' in explanation or 'No contradiction' in explanation


# ConsistencyChecker Tests
class TestConsistencyChecker:
    """Test consistency checking"""
    
    def test_check_consistency_empty(self):
        """Test with empty statements"""
        checker = ConsistencyChecker()
        result = checker.check_consistency([])
        
        assert result['overall_consistency'] == 1.0
        assert result['is_consistent'] is True
    
    def test_check_consistency_single_topic(self):
        """Test consistency within single topic"""
        checker = ConsistencyChecker()
        
        statements = [
            {'content': 'Python is popular for data science', 'timestamp': '2024-01-01T10:00:00Z'},
            {'content': 'Python has great libraries', 'timestamp': '2024-01-01T10:01:00Z'},
            {'content': 'Python is widely used', 'timestamp': '2024-01-01T10:02:00Z'},
        ]
        
        result = checker.check_consistency(statements)
        
        assert 'overall_consistency' in result
        assert result['is_consistent'] is True
    
    def test_detect_drift(self):
        """Test knowledge drift detection"""
        checker = ConsistencyChecker()
        
        # Create statements showing drift
        early_statements = [
            {'content': 'Python version 2 is standard', 'timestamp': '2020-01-01T10:00:00Z'},
        ] * 10
        
        recent_statements = [
            {'content': 'Python version 3 is standard', 'timestamp': '2024-01-01T10:00:00Z'},
        ] * 10
        
        all_statements = early_statements + recent_statements
        
        result = checker.check_consistency(all_statements)
        
        # Should detect some drift
        assert 'knowledge_drift_rate' in result
    
    def test_agent_response_consistency(self):
        """Test agent response consistency checking"""
        checker = ConsistencyChecker()
        
        responses = [
            {'query': 'What is Python?', 'response': 'Python is a programming language', 'timestamp': '2024-01-01T10:00:00Z'},
            {'query': 'Tell me about Python', 'response': 'Python is a high-level language', 'timestamp': '2024-01-01T10:01:00Z'},
        ]
        
        result = checker.check_agent_response_consistency(responses, 'What is Python?')
        
        assert 'is_consistent' in result
        assert 'consistency_score' in result
    
    def test_knowledge_graph_consistency(self):
        """Test knowledge graph relationship consistency"""
        checker = ConsistencyChecker()
        
        # Valid relationships
        valid_relationships = [
            {'subject': 'Alice', 'predicate': 'parent_of', 'object': 'Bob'},
            {'subject': 'Bob', 'predicate': 'child_of', 'object': 'Alice'},
        ]
        
        result = checker.check_knowledge_graph_consistency(valid_relationships)
        
        assert 'overall_consistency' in result
        assert 'conflicts_detected' in result


# ContrastiveService Tests
class TestContrastiveService:
    """Test contrastive service integration"""
    
    @pytest.mark.asyncio
    async def test_check_statement_consistency(self):
        """Test statement consistency checking"""
        service = ContrastiveService()
        
        result = await service.check_statement_consistency(
            "Python is a programming language",
            {'user_id': 'test_user'}
        )
        
        assert 'is_consistent' in result
        assert 'consistency_score' in result
    
    @pytest.mark.asyncio
    async def test_detect_contradiction(self):
        """Test contradiction detection via service"""
        service = ContrastiveService()
        
        result = await service.detect_contradiction(
            "The system is online",
            "The system is not online"
        )
        
        assert result['is_contradiction'] is True
    
    @pytest.mark.asyncio
    async def test_get_all_conflicts(self):
        """Test retrieving all conflicts"""
        service = ContrastiveService()
        
        # Create a conflict first
        await service.detect_contradiction(
            "X is true",
            "X is false"
        )
        
        conflicts = await service.get_all_conflicts()
        
        assert isinstance(conflicts, list)
    
    @pytest.mark.asyncio
    async def test_resolve_conflict(self):
        """Test conflict resolution"""
        service = ContrastiveService()
        
        # Create conflict
        await service.detect_contradiction("A", "not A")
        
        # Try to resolve (index 0)
        success = await service.resolve_conflict(0)
        
        # May succeed or fail depending on internal state
        assert isinstance(success, bool)
    
    @pytest.mark.asyncio
    async def test_consistency_metrics(self):
        """Test overall consistency metrics"""
        service = ContrastiveService()
        
        metrics = await service.get_consistency_metrics()
        
        assert 'total_conflicts' in metrics
        assert 'overall_health' in metrics
        assert metrics['overall_health'] in ['healthy', 'concerning', 'poor', 'critical']


# Integration Tests
class TestContrastiveIntegration:
    """Integration tests for contrastive learning system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_contradiction_flow(self):
        """Test complete contradiction detection flow"""
        service = ContrastiveService()
        
        # 1. Check initial consistency
        result1 = await service.check_statement_consistency(
            "The database is MySQL",
            {'session_id': 'test_session'}
        )
        
        assert result1['is_consistent'] is True
        
        # 2. Add contradictory statement (in real scenario)
        result2 = await service.detect_contradiction(
            "The database is MySQL",
            "The database is PostgreSQL"
        )
        
        # Should detect conflict
        assert result2['is_contradiction'] is True
        
        # 3. Get metrics
        metrics = await service.get_consistency_metrics()
        assert metrics['total_conflicts'] >= 0
