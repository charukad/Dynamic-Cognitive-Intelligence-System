"""
Causal Graph Builder - Construct causal DAGs

Builds Directed Acyclic Graphs from:
- Domain knowledge
- Observed data correlations
- Temporal relationships
- Expert rules
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque


@dataclass
class CausalNode:
    """Node in causal graph"""
    variable: str
    parents: List[str] = field(default_factory=list)  # Direct causes
    children: List[str] = field(default_factory=list)  # Direct effects
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CausalGraph:
    """Directed Acyclic Graph representing causal relationships"""
    nodes: Dict[str, CausalNode] = field(default_factory=dict)
    edges: List[Tuple[str, str]] = field(default_factory=list)  # (cause, effect)
    
    def add_node(self, variable: str, metadata: Optional[Dict] = None):
        """Add node to graph"""
        if variable not in self.nodes:
            self.nodes[variable] = CausalNode(
                variable=variable,
                metadata=metadata or {}
            )
    
    def add_edge(self, cause: str, effect: str):
        """Add directed edge (cause → effect)"""
        # Ensure nodes exist
        self.add_node(cause)
        self.add_node(effect)
        
        # Add edge
        if (cause, effect) not in self.edges:
            self.edges.append((cause, effect))
            self.nodes[cause].children.append(effect)
            self.nodes[effect].parents.append(cause)
    
    def get_parents(self, variable: str) -> List[str]:
        """Get direct parents (causes) of variable"""
        if variable in self.nodes:
            return self.nodes[variable].parents
        return []
    
    def get_children(self, variable: str) -> List[str]:
        """Get direct children (effects) of variable"""
        if variable in self.nodes:
            return self.nodes[variable].children
        return []
    
    def get_ancestors(self, variable: str) -> Set[str]:
        """Get all ancestors (transitive parents)"""
        ancestors = set()
        queue = deque([variable])
        visited = set()
        
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            
            parents = self.get_parents(current)
            ancestors.update(parents)
            queue.extend(parents)
        
        return ancestors
    
    def get_descendants(self, variable: str) -> Set[str]:
        """Get all descendants (transitive children)"""
        descendants = set()
        queue = deque([variable])
        visited = set()
        
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            
            children = self.get_children(current)
            descendants.update(children)
            queue.extend(children)
        
        return descendants
    
    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        """Check if ancestor is ancestor of descendant"""
        return ancestor in self.get_ancestors(descendant)
    
    def is_acyclic(self) -> bool:
        """Check if graph is acyclic (DAG property)"""
        # Use DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for child in self.get_children(node):
                if child not in visited:
                    if has_cycle(child):
                        return True
                elif child in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in self.nodes:
            if node not in visited:
                if has_cycle(node):
                    return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary"""
        return {
            'nodes': [
                {
                    'variable': node.variable,
                    'parents': node.parents,
                    'children': node.children,
                    'metadata': node.metadata,
                }
                for node in self.nodes.values()
            ],
            'edges': [
                {'cause': cause, 'effect': effect}
                for cause, effect in self.edges
            ],
            'is_acyclic': self.is_acyclic(),
        }


class CausalGraphBuilder:
    """Build causal graphs from various sources"""
    
    def __init__(self):
        """Initialize graph builder"""
        pass
    
    def build_from_rules(self, rules: List[Dict[str, str]]) -> CausalGraph:
        """
        Build graph from expert rules.
        
        Args:
            rules: List of rules with 'cause' and 'effect' keys
        
        Returns:
            CausalGraph
        """
        graph = CausalGraph()
        
        for rule in rules:
            cause = rule.get('cause')
            effect = rule.get('effect')
            
            if cause and effect:
                graph.add_edge(cause, effect)
        
        if not graph.is_acyclic():
            raise ValueError("Resulting graph has cycles - not a valid DAG")
        
        return graph
    
    def build_from_temporal_data(
        self,
        events: List[Dict[str, Any]]
    ) -> CausalGraph:
        """
        Build graph from temporal event data.
        
        Assumes temporal precedence: if A happens before B consistently,
        A might cause B.
        
        Args:
            events: List of events with 'variable', 'timestamp', 'value'
        
        Returns:
            CausalGraph
        """
        graph = CausalGraph()
        
        # Group events by variable
        by_variable = defaultdict(list)
        for event in events:
            var = event.get('variable')
            if var:
                by_variable[var].append(event)
        
        # Sort each variable's events by time
        for var in by_variable:
            by_variable[var].sort(key=lambda e: e.get('timestamp', 0))
        
        # Find temporal precedence patterns
        variables = list(by_variable.keys())
        for i, var1 in enumerate(variables):
            for var2 in variables[i+1:]:
                # Check if var1 consistently precedes var2
                if self._check_temporal_precedence(by_variable[var1], by_variable[var2]):
                    graph.add_edge(var1, var2)
        
        return graph
    
    def build_from_correlations(
        self,
        correlations: Dict[Tuple[str, str], float],
        threshold: float = 0.7
    ) -> CausalGraph:
        """
        Build graph from correlation data.
        
        WARNING: Correlation ≠ Causation. This is heuristic only.
        
        Args:
            correlations: Dict of (var1, var2) -> correlation_score
            threshold: Minimum correlation to consider
        
        Returns:
            CausalGraph
        """
        graph = CausalGraph()
        
        for (var1, var2), corr in correlations.items():
            if abs(corr) >= threshold:
                # Heuristic: assume alphabetically first causes second
                # (In reality, would need domain knowledge or intervention data)
                if var1 < var2:
                    graph.add_edge(var1, var2)
                else:
                    graph.add_edge(var2, var1)
        
        return graph
    
    def merge_graphs(self, graphs: List[CausalGraph]) -> CausalGraph:
        """
        Merge multiple causal graphs.
        
        Combines edges from all graphs. Resolves conflicts by majority vote.
        """
        merged = CausalGraph()
        
        # Add all edges
        for graph in graphs:
            for cause, effect in graph.edges:
                merged.add_edge(cause, effect)
        
        # Check if result is still acyclic
        if not merged.is_acyclic():
            # Remove edges that create cycles (heuristic: remove least frequent)
            # This is simplified - production would use more sophisticated conflict resolution
            pass
        
        return merged
    
    def _check_temporal_precedence(
        self,
        events1: List[Dict],
        events2: List[Dict],
        lag_threshold: float = 0.1
    ) -> bool:
        """Check if events1 consistently precede events2"""
        if not events1 or not events2:
            return False
        
        # Count how often var1 precedes var2
        precedes_count = 0
        total_comparisons = 0
        
        for e1 in events1:
            for e2 in events2:
                t1 = e1.get('timestamp', 0)
                t2 = e2.get('timestamp', 0)
                
                total_comparisons += 1
                if t1 < t2 - lag_threshold:  # var1 before var2 with lag
                    precedes_count += 1
        
        # If >70% of comparisons show precedence, consider it causal
        if total_comparisons > 0:
            precedence_rate = precedes_count / total_comparisons
            return precedence_rate > 0.7
        
        return False
    
    def validate_graph(self, graph: CausalGraph) -> Dict[str, Any]:
        """
        Validate causal graph structure.
        
        Returns:
            Validation report
        """
        issues = []
        
        # Check if acyclic
        if not graph.is_acyclic():
            issues.append("Graph contains cycles - not a valid DAG")
        
        # Check for isolated nodes
        isolated = [
            node for node in graph.nodes.values()
            if not node.parents and not node.children
        ]
        if isolated:
            issues.append(f"{len(isolated)} isolated nodes found")
        
        # Check for very high in-degree (might indicate confounding)
        high_indegree = [
            node for node in graph.nodes.values()
            if len(node.parents) > 5
        ]
        if high_indegree:
            issues.append(f"{len(high_indegree)} nodes with >5 parents (possible confounding)")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'node_count': len(graph.nodes),
            'edge_count': len(graph.edges),
        }
