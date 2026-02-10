"""
Counterfactual Engine - "What if" scenario analysis

Answers "What if X had been different?" questions.

Process:
1. Observe actual outcome with X=x
2. Infer latent variables from observations
3. Perform intervention do(X=x')
4. Compute new outcome Y'
"""

from typing import Dict, Any, Optional, List
from .graph_builder import CausalGraph
from .do_calculus import DoCalculus


class CounterfactualEngine:
    """Answer counterfactual queries on causal graphs"""
    
    def __init__(self):
        """Initialize counterfactual engine"""
        self.do_calculus = DoCalculus()
    
    def answer_counterfactual(
        self,
        graph: CausalGraph,
        actual_observations: Dict[str, Any],
        counterfactual_intervention: Dict[str, Any],
        query_variable: str
    ) -> Dict[str, Any]:
        """
        Answer counterfactual question.
        
        Example:
            Actual: User asked for Python help (X=python), got code response (Y=code)
            Counterfactual: What if user had asked for JavaScript? (X'=javascript)
            Query: What would Y have been?
        
        Args:
            graph: Causal graph
            actual_observations: Actual observed values {var: value}
            counterfactual_intervention: Hypothetical intervention {var: value}
            query_variable: Variable to query in counterfactual world
        
        Returns:
            Counterfactual analysis
        """
        # Step 1: Record actual observations
        actual_world = {
            'observations': actual_observations,
            'outcome': actual_observations.get(query_variable),
        }
        
        # Step 2: Perform counterfactual intervention
        cf_var = list(counterfactual_intervention.keys())[0]
        cf_value = counterfactual_intervention[cf_var]
        
        intervention_result = self.do_calculus.intervene(
            graph,
            variable=cf_var,
            value=cf_value,
            observed=actual_observations
        )
        
        # Step 3: Simulate counterfactual outcome
        # In production, would use structural equation models
        # Here we provide a simplified analysis
        
        affected_vars = intervention_result['affected_variables']
        
        counterfactual_prediction = {
            'counterfactual_world': {
                'intervention': counterfactual_intervention,
                'affected_variables': affected_vars,
            },
            'predicted_outcome': {
                'variable': query_variable,
                'value': 'SIMULATED',  # Would compute from SCM in production
                'note': f"Outcome depends on causal path from {cf_var} to {query_variable}"
            },
            'comparison': {
                'actual_value': actual_observations.get(query_variable),
                'is_query_variable_affected': query_variable in affected_vars,
            },
        }
        
        return {
            'actual_world': actual_world,
            **counterfactual_prediction,
            'explanation': self._explain_counterfactual(
                cf_var, cf_value, query_variable, query_variable in affected_vars
            ),
        }
    
    def compare_scenarios(
        self,
        graph: CausalGraph,
        base_scenario: Dict[str, Any],
        alternative_scenarios: List[Dict[str, Any]],
        outcome_variable: str
    ) -> Dict[str, Any]:
        """
        Compare multiple counterfactual scenarios.
        
        Args:
            graph: Causal graph
            base_scenario: Base case observations
            alternative_scenarios: List of alternative interventions
            outcome_variable: Variable to compare across scenarios
        
        Returns:
            Scenario comparison
        """
        results = []
        
        # Base scenario
        base_outcome = base_scenario.get(outcome_variable)
        
        # Analyze each alternative
        for i, alt_scenario in enumerate(alternative_scenarios):
            cf_result = self.answer_counterfactual(
                graph,
                actual_observations=base_scenario,
                counterfactual_intervention=alt_scenario,
                query_variable=outcome_variable
            )
            
            results.append({
                'scenario_id': i + 1,
                'intervention': alt_scenario,
                'predicted_outcome': cf_result['predicted_outcome'],
                'differs_from_base': cf_result['comparison']['is_query_variable_affected'],
            })
        
        return {
            'base_scenario': {
                'observations': base_scenario,
                'outcome': base_outcome,
            },
            'alternative_scenarios': results,
            'total_alternatives': len(alternative_scenarios),
        }
    
    def explain_causal_path(
        self,
        graph: CausalGraph,
        cause: str,
        effect: str
    ) -> Dict[str, Any]:
        """
        Explain causal path from cause to effect.
        
        Args:
            graph: Causal graph
            cause: Cause variable
            effect: Effect variable
        
        Returns:
            Causal path explanation
        """
        # Check if effect is descendant of cause
        is_causal = cause in graph.get_ancestors(effect)
        
        if not is_causal:
            return {
                'has_causal_path': False,
                'cause': cause,
                'effect': effect,
                'explanation': f"No causal path from {cause} to {effect}",
            }
        
        # Find path (simplified - would use pathfinding in production)
        # For demo, just note that path exists
        
        return {
            'has_causal_path': True,
            'cause': cause,
            'effect': effect,
            'explanation': f"{cause} causally affects {effect} through graph structure",
            'note': 'Full path-finding would be implemented in production',
        }
    
    def assess_counterfactual_dependency(
        self,
        graph: CausalGraph,
        actual: Dict[str, Any],
        variable_of_interest: str
    ) -> Dict[str, Any]:
        """
        Assess how outcome depends on other variables counterfactually.
        
        "Which variables, if different, would have changed the outcome?"
        
        Args:
            graph: Causal graph
            actual: Actual observations
            variable_of_interest: Variable we care about
        
        Returns:
            Dependency analysis
        """
        ancestors = graph.get_ancestors(variable_of_interest)
        
        # Each ancestor could have counterfactually affected outcome
        dependencies = []
        for ancestor in ancestors:
            dependencies.append({
                'variable': ancestor,
                'relationship': 'ancestor',
                'would_affect_outcome': True,
                'note': f"Changing {ancestor} would affect {variable_of_interest}",
            })
        
        # Non-ancestors would not affect outcome
        non_ancestors = [
            node for node in graph.nodes.keys()
            if node not in ancestors and node != variable_of_interest
        ]
        
        for node in non_ancestors:
            dependencies.append({
                'variable': node,
                'relationship': 'independent',
                'would_affect_outcome': False,
                'note': f"Changing {node} would NOT affect {variable_of_interest}",
            })
        
        return {
            'variable_of_interest': variable_of_interest,
            'dependencies': dependencies,
            'total_ancestors': len(ancestors),
            'total_independent': len(non_ancestors),
        }
    
    def _explain_counterfactual(
        self,
        intervention_var: str,
        intervention_value: Any,
        query_var: str,
        is_affected: bool
    ) -> str:
        """Generate human-readable explanation"""
        if is_affected:
            return (
                f"If {intervention_var} had been '{intervention_value}' instead, "
                f"{query_var} would likely have been different due to the causal relationship."
            )
        else:
            return (
                f"Even if {intervention_var} had been '{intervention_value}', "
                f"{query_var} would have remained the same (no causal path)."
            )
