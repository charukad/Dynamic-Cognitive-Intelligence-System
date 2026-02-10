"""
Causal Reasoning Tests

Tests for causal graphs, do-calculus, and counterfactuals.
"""

import pytest
from src.services.advanced.causal import (
    CausalGraphBuilder,
    CausalGraph,
    DoCalculus,
    CounterfactualEngine,
    CausalService,
)


# Fixtures
@pytest.fixture
def sample_causal_rules():
    """Sample causal rules for testing"""
    return [
        {'cause': 'rain', 'effect': 'wet_ground'},
        {'cause': 'wet_ground', 'effect': 'slippery'},
        {'cause': 'fertilizer', 'effect': 'plant_growth'},
    ]


@pytest.fixture
def simple_graph():
    """Simple causal graph"""
    graph = CausalGraph()
    graph.add_edge('X', 'Y')
    graph.add_edge('Y', 'Z')
    return graph


# CausalGraph Tests
class TestCausalGraph:
    """Test causal graph structure"""
    
    def test_add_node(self):
        """Test adding nodes"""
        graph = CausalGraph()
        graph.add_node('A')
        
        assert 'A' in graph.nodes
        assert len(graph.nodes) == 1
    
    def test_add_edge(self):
        """Test adding edges"""
        graph = CausalGraph()
        graph.add_edge('A', 'B')
        
        assert ('A', 'B') in graph.edges
        assert 'B' in graph.get_children('A')
        assert 'A' in graph.get_parents('B')
    
    def test_get_ancestors(self, simple_graph):
        """Test ancestor traversal"""
        ancestors = simple_graph.get_ancestors('Z')
        
        assert 'Y' in ancestors
        assert 'X' in ancestors
    
    def test_get_descendants(self, simple_graph):
        """Test descendant traversal"""
        descendants = simple_graph.get_descendants('X')
        
        assert 'Y' in descendants
        assert 'Z' in descendants
    
    def test_is_ancestor(self, simple_graph):
        """Test ancestor relationship"""
        assert simple_graph.is_ancestor('X', 'Z') is True
        assert simple_graph.is_ancestor('Z', 'X') is False
    
    def test_is_acyclic(self):
        """Test DAG property (no cycles)"""
        # Valid DAG
        graph = CausalGraph()
        graph.add_edge('A', 'B')
        graph.add_edge('B', 'C')
        
        assert graph.is_acyclic() is True
        
        # Create cycle
        graph.add_edge('C', 'A')
        
        assert graph.is_acyclic() is False
    
    def test_to_dict(self, simple_graph):
        """Test graph serialization"""
        data = simple_graph.to_dict()
        
        assert 'nodes' in data
        assert 'edges' in data
        assert 'is_acyclic' in data
        assert data['is_acyclic'] is True


# CausalGraphBuilder Tests
class TestCausalGraphBuilder:
    """Test causal graph construction"""
    
    def test_build_from_rules(self, sample_causal_rules):
        """Test building graph from expert rules"""
        builder = CausalGraphBuilder()
        graph = builder.build_from_rules(sample_causal_rules)
        
        assert len(graph.nodes) > 0
        assert len(graph.edges) == len(sample_causal_rules)
        assert graph.is_acyclic() is True
    
    def test_build_from_temporal_data(self):
        """Test building from temporal events"""
        builder = CausalGraphBuilder()
        
        events = [
            {'variable': 'A', 'timestamp': 1.0, 'value': True},
            {'variable': 'B', 'timestamp': 2.0, 'value': True},
            {'variable': 'A', 'timestamp': 3.0, 'value': True},
            {'variable': 'B', 'timestamp': 4.0, 'value': True},
        ]
        
        graph = builder.build_from_temporal_data(events)
        
        assert len(graph.nodes) > 0
    
    def test_build_from_correlations(self):
        """Test building from correlation data"""
        builder = CausalGraphBuilder()
        
        correlations = {
            ('X', 'Y'): 0.8,
            ('Y', 'Z'): 0.75,
        }
        
        graph = builder.build_from_correlations(correlations, threshold=0.7)
        
        assert len(graph.edges) > 0
    
    def test_validate_graph(self, simple_graph):
        """Test graph validation"""
        builder = CausalGraphBuilder()
        validation = builder.validate_graph(simple_graph)
        
        assert 'is_valid' in validation
        assert 'issues' in validation
        assert validation['is_valid'] is True


# DoCalculus Tests
class TestDoCalculus:
    """Test do-calculus interventions"""
    
    def test_intervene(self, simple_graph):
        """Test basic intervention"""
        do_calc = DoCalculus()
        
        result = do_calc.intervene(simple_graph, 'Y', value=1)
        
        assert 'intervention' in result
        assert result['intervention']['variable'] == 'Y'
        assert 'mutilated_graph' in result
        assert 'affected_variables' in result
    
    def test_estimate_causal_effect(self, simple_graph):
        """Test causal effect estimation"""
        do_calc = DoCalculus()
        
        result = do_calc.estimate_causal_effect(
            simple_graph,
            treatment='X',
            outcome='Z'
        )
        
        assert 'is_identifiable' in result
        assert 'treatment' in result
        assert 'outcome' in result
    
    def test_backdoor_criterion(self, simple_graph):
        """Test backdoor criterion checking"""
        do_calc = DoCalculus()
        
        result = do_calc.check_backdoor_criterion(
            simple_graph,
            treatment='X',
            outcome='Z',
            adjustment_set=[]
        )
        
        assert 'satisfies_criterion' in result
        assert 'adjustment_set' in result


# CounterfactualEngine Tests
class TestCounterfactualEngine:
    """Test counterfactual reasoning"""
    
    def test_answer_counterfactual(self, simple_graph):
        """Test counterfactual query"""
        engine = CounterfactualEngine()
        
        actual = {'X': 0, 'Y': 0, 'Z': 0}
        counterfactual = {'X': 1}
        
        result = engine.answer_counterfactual(
            simple_graph,
            actual_observations=actual,
            counterfactual_intervention=counterfactual,
            query_variable='Z'
        )
        
        assert 'actual_world' in result
        assert 'counterfactual_world' in result
        assert 'predicted_outcome' in result
    
    def test_compare_scenarios(self, simple_graph):
        """Test multi-scenario comparison"""
        engine = CounterfactualEngine()
        
        base = {'X': 0, 'Y': 0, 'Z': 0}
        alternatives = [
            {'X': 1},
            {'Y': 1},
        ]
        
        result = engine.compare_scenarios(
            simple_graph,
            base_scenario=base,
            alternative_scenarios=alternatives,
            outcome_variable='Z'
        )
        
        assert 'base_scenario' in result
        assert 'alternative_scenarios' in result
        assert len(result['alternative_scenarios']) == 2
    
    def test_explain_causal_path(self, simple_graph):
        """Test causal path explanation"""
        engine = CounterfactualEngine()
        
        result = engine.explain_c ausal_path(simple_graph, 'X', 'Z')
        
        assert 'has_causal_path' in result
        assert result['has_causal_path'] is True
    
    def test_assess_counterfactual_dependency(self, simple_graph):
        """Test dependency assessment"""
        engine = CounterfactualEngine()
        
        actual = {'X': 1, 'Y': 1, 'Z': 1}
        
        result = engine.assess_counterfactual_dependency(
            simple_graph,
            actual=actual,
            variable_of_interest='Z'
        )
        
        assert 'dependencies' in result
        assert 'total_ancestors' in result


# CausalService Tests
class TestCausalService:
    """Test causal service integration"""
    
    @pytest.mark.asyncio
    async def test_create_graph(self, sample_causal_rules):
        """Test graph creation via service"""
        service = CausalService()
        
        result = await service.create_graph(
            'test_graph',
            rules=sample_causal_rules
        )
        
        assert result['success'] is True
        assert 'graph' in result
        assert result['validation']['is_valid'] is True
    
    @pytest.mark.asyncio
    async def test_get_graph(self, sample_causal_rules):
        """Test graph retrieval"""
        service = CausalService()
        
        # Create graph first
        await service.create_graph('test_graph', rules=sample_causal_rules)
        
        # Retrieve it
        graph = await service.get_graph('test_graph')
        
        assert graph is not None
        assert 'nodes' in graph
    
    @pytest.mark.asyncio
    async def test_perform_intervention(self, sample_causal_rules):
        """Test intervention via service"""
        service = CausalService()
        
        await service.create_graph('test_graph', rules=sample_causal_rules)
        
        result = await service.perform_intervention(
            'test_graph',
            variable='rain',
            value=True
        )
        
        assert 'intervention' in result
        assert 'affected_variables' in result
    
    @pytest.mark.asyncio
    async def test_answer_counterfactual(self, sample_causal_rules):
        """Test counterfactual via service"""
        service = CausalService()
        
        await service.create_graph('test_graph', rules=sample_causal_rules)
        
        result = await service.answer_counterfactual(
            'test_graph',
            actual_observations={'rain': False, 'wet_ground': False},
            counterfactual_intervention={'rain': True},
            query_variable='wet_ground'
        )
        
        assert 'actual_world' in result
        assert 'counterfactual_world' in result
    
    @pytest.mark.asyncio
    async def test_delete_graph(self, sample_causal_rules):
        """Test graph deletion"""
        service = CausalService()
        
        await service.create_graph('test_graph', rules=sample_causal_rules)
        
        success = await service.delete_graph('test_graph')
        
        assert success is True
        
        # Verify deleted
        graph = await service.get_graph('test_graph')
        assert graph is None
    
    @pytest.mark.asyncio
    async def test_list_graphs(self, sample_causal_rules):
        """Test listing all graphs"""
        service = CausalService()
        
        await service.create_graph('graph1', rules=sample_causal_rules)
        await service.create_graph('graph2', rules=sample_causal_rules[:2])
        
        graphs = await service.list_graphs()
        
        assert len(graphs) >= 2


# Integration Tests
class TestCausalIntegration:
    """Integration tests for causal reasoning"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_causal_flow(self):
        """Test complete causal reasoning workflow"""
        service = CausalService()
        
        # 1. Create causal graph
        rules = [
            {'cause': 'study', 'effect': 'knowledge'},
            {'cause': 'knowledge', 'effect': 'performance'},
        ]
        
        result = await service.create_graph('education_graph', rules=rules)
        assert result['success'] is True
        
        # 2. Perform intervention
        intervention = await service.perform_intervention(
            'education_graph',
            variable='study',
            value='intensive'
        )
        
        assert 'affected_variables' in intervention
        assert 'performance' in intervention['affected_variables']
        
        # 3. Answer counterfactual
        cf = await service.answer_counterfactual(
            'education_graph',
            actual_observations={'study': 'minimal', 'performance': 'low'},
            counterfactual_intervention={'study': 'intensive'},
            query_variable='performance'
        )
        
        assert 'predicted_outcome' in cf
        
        # 4. Cleanup
        await service.delete_graph('education_graph')
