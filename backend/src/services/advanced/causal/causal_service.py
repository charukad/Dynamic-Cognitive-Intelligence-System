"""
Causal Service - Main orchestrator for causal reasoning

Provides unified interface for:
- Building causal graphs
- Performing interventions (do-calculus)
- Answering counterfactual questions
- Analyzing causal effects
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from .graph_builder import CausalGraphBuilder, CausalGraph
from .do_calculus import DoCalculus
from .counterfactual import CounterfactualEngine


@dataclass
class CausalQuery:
    """Causal query specification"""
    query_type: str  # 'intervention', 'counterfactual', 'effect_estimation'
    treatment: Optional[str] = None
    outcome: Optional[str] = None
    intervention: Optional[Dict[str, Any]] = None
    observations: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class CausalService:
    """
    Main service for causal reasoning operations.
    
    Orchestrates graph building, interventions, and counterfactuals.
    """
    
    def __init__(self):
        """Initialize causal service"""
        self.graph_builder = CausalGraphBuilder()
        self.do_calculus = DoCalculus()
        self.counterfactual_engine = CounterfactualEngine()
        
        # Store causal graphs (in-memory, would use DB in production)
        self._graphs: Dict[str, CausalGraph] = {}
    
    async def create_graph(
        self,
        graph_id: str,
        rules: Optional[List[Dict[str, str]]] = None,
        correlations: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create a new causal graph.
        
        Args:
            graph_id: Unique identifier for graph
            rules: Optional expert rules (cause → effect)
            correlations: Optional correlation data
        
        Returns:
            Graph creation result
        """
        if rules:
            graph = self.graph_builder.build_from_rules(rules)
        elif correlations:
            graph = self.graph_builder.build_from_correlations(correlations)
        else:
            # Empty graph
            graph = CausalGraph()
        
        # Validate graph
        validation = self.graph_builder.validate_graph(graph)
        
        if not validation['is_valid']:
            return {
                'success': False,
                'graph_id': graph_id,
                'validation': validation,
            }
        
        # Store graph
        self._graphs[graph_id] = graph
        
        return {
            'success': True,
            'graph_id': graph_id,
            'graph': graph.to_dict(),
            'validation': validation,
        }
    
    async def perform_intervention(
        self,
        graph_id: str,
        variable: str,
        value: Any,
        observed: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform causal intervention do(X=x).
        
        Args:
            graph_id: Graph identifier
            variable: Variable to intervene on
            value: Value to set
            observed: Optional observed values
        
        Returns:
            Intervention result
        """
        graph = self._graphs.get(graph_id)
        
        if not graph:
            return {'error': f"Graph {graph_id} not found"}
        
        result = self.do_calculus.intervene(graph, variable, value, observed)
        
        return result
    
    async def answer_counterfactual(
        self,
        graph_id: str,
        actual_observations: Dict[str, Any],
        counterfactual_intervention: Dict[str, Any],
        query_variable: str
    ) -> Dict[str, Any]:
        """
        Answer counterfactual question.
        
        Args:
            graph_id: Graph identifier
            actual_observations: What actually happened
            counterfactual_intervention: What if this had been different
            query_variable: What we want to know
        
        Returns:
            Counterfactual analysis
        """
        graph = self._graphs.get(graph_id)
        
        if not graph:
            return {'error': f"Graph {graph_id} not found"}
        
        result = self.counterfactual_engine.answer_counterfactual(
            graph,
            actual_observations,
            counterfactual_intervention,
            query_variable
        )
        
        return result
    
    async def estimate_causal_effect(
        self,
        graph_id: str,
        treatment: str,
        outcome: str,
        confounders: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Estimate causal effect of treatment on outcome.
        
        Args:
            graph_id: Graph identifier
            treatment: Treatment variable
            outcome: Outcome variable
            confounders: Optional confounding variables
        
        Returns:
            Causal effect estimation
        """
        graph = self._graphs.get(graph_id)
        
        if not graph:
            return {'error': f"Graph {graph_id} not found"}
        
        result = self.do_calculus.estimate_causal_effect(
            graph,
            treatment,
            outcome,
            confounders
        )
        
        return result
    
    async def get_graph(self, graph_id: str) -> Optional[Dict[str, Any]]:
        """Get causal graph"""
        graph = self._graphs.get(graph_id)
        
        if graph:
            return graph.to_dict()
        
        return None
    
    async def list_graphs(self) -> List[Dict[str, Any]]:
        """List all causal graphs"""
        return [
            {
                'graph_id': gid,
                'node_count': len(graph.nodes),
                'edge_count': len(graph.edges),
                'is_acyclic': graph.is_acyclic(),
            }
            for gid, graph in self._graphs.items()
        ]
    
    async def delete_graph(self, graph_id: str) -> bool:
        """Delete causal graph"""
        if graph_id in self._graphs:
            del self._graphs[graph_id]
            return True
        
        return False


# Singleton instance
causal_service = CausalService()
