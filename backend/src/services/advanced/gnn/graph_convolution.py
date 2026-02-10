"""
Graph Convolution Networks - Message passing on knowledge graphs

Implements advanced graph convolutions:
- GCN (Graph Convolutional Networks): Kipf & Welling 2017
- GAT (Graph Attention Networks): Veličković et al. 2018
- Multi-head attention with learnable weights

Design: Clean separation of concerns, Protocol-based interfaces
Performance: Sparse matrix operations, vectorized computations
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Set, Callable
from enum import Enum
from dataclasses import dataclass
import numpy as np
from abc import ABC, abstractmethod
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class ConvolutionType(Enum):
    """Supported convolution types"""
    GCN = "gcn"  # Graph Convolutional Network
    GAT = "gat"  # Graph Attention Network
    SAGE = "graphsage"  # GraphSAGE


@dataclass
class GraphStructure:
    """
    Adjacency structure for graph convolutions.
    
    Optimized representation:
    - Edge list for sparse graphs
    - Neighborhood dict for fast lookup
    - Degree normalization for GCN
    """
    edges: List[Tuple[str, str]]  # (source, target) pairs
    node_features: Dict[str, np.ndarray]
    num_nodes: int
    num_edges: int
    
    _adjacency_list: Optional[Dict[str, Set[str]]] = None
    _degree: Optional[Dict[str, int]] = None
    
    def __post_init__(self):
        """Build adjacency list and compute degrees"""
        self._build_adjacency_list()
        self._compute_degrees()
    
    def _build_adjacency_list(self) -> None:
        """Build adjacency list from edge list"""
        self._adjacency_list = defaultdict(set)
        
        for source, target in self.edges:
            self._adjacency_list[source].add(target)
            # For undirected graphs, uncomment:
            # self._adjacency_list[target].add(source)
    
    def _compute_degrees(self) -> None:
        """Compute node degrees for normalization"""
        self._degree = defaultdict(int)
        
        for source, target in self.edges:
            self._degree[source] += 1
            self._degree[target] += 1  # In-degree
    
    def get_neighbors(self, node: str) -> Set[str]:
        """Get neighbors of a node"""
        return self._adjacency_list.get(node, set())
    
    def get_degree(self, node: str) -> int:
        """Get degree of a node"""
        return self._degree.get(node, 0)


class ConvolutionLayer(ABC):
    """Abstract base for graph convolution layers"""
    
    def __init__(self, input_dim: int, output_dim: int):
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.weights: Optional[np.ndarray] = None
        self.bias: Optional[np.ndarray] = None
        self._initialize_parameters()
    
    @abstractmethod
    def forward(
        self,
        graph: GraphStructure,
        node_features: Dict[str, np.ndarray]
    ) -> Dict[str, np.ndarray]:
        """Forward pass through convolution layer"""
        pass
    
    def _initialize_parameters(self) -> None:
        """Xavier/He initialization for weights"""
        # Xavier: uniform(-sqrt(6 / (in + out)), sqrt(6 / (in + out)))
        bound = np.sqrt(6.0 / (self.input_dim + self.output_dim))
        self.weights = np.random.uniform(
            -bound, bound, size=(self.input_dim, self.output_dim)
        ).astype(np.float32)
        
        self.bias = np.zeros(self.output_dim, dtype=np.float32)


class GCNLayer(ConvolutionLayer):
    """
    Graph Convolutional Network Layer (Kipf & Welling, 2017)
    
    Formula: H^(l+1) = σ(D^(-1/2) A D^(-1/2) H^(l) W^(l))
    
    Where:
    - A: Adjacency matrix (with self-loops)
    - D: Degree matrix
    - H: Node feature matrix
    - W: Learnable weight matrix
    - σ: Activation function (ReLU)
    
    Key insight: Symmetric normalization preserves scale
    """
    
    def __init__(self, input_dim: int, output_dim: int, add_self_loops: bool = True):
        super().__init__(input_dim, output_dim)
        self.add_self_loops = add_self_loops
    
    def forward(
        self,
        graph: GraphStructure,
        node_features: Dict[str, np.ndarray]
    ) -> Dict[str, np.ndarray]:
        """
        GCN forward pass with symmetric normalization.
        
        Steps:
        1. Add self-loops (optional)
        2. Aggregate neighbor features
        3. Normalize by degree
        4. Apply weight transformation
        5. Add bias and activate
        """
        new_features: Dict[str, np.ndarray] = {}
        
        for node in node_features.keys():
            # Get neighbors
            neighbors = graph.get_neighbors(node)
            
            # Add self-loop
            if self.add_self_loops:
                neighbors = neighbors | {node}
            
            # Aggregate neighbor features
            aggregated = np.zeros(self.input_dim, dtype=np.float32)
            
            for neighbor in neighbors:
                if neighbor in node_features:
                    # Symmetric normalization: 1 / sqrt(deg(u) * deg(v))
                    deg_u = graph.get_degree(node) + (1 if self.add_self_loops else 0)
                    deg_v = graph.get_degree(neighbor) + (1 if self.add_self_loops else 0)
                    
                    norm = 1.0 / np.sqrt(deg_u * deg_v + 1e-10)
                    aggregated += norm * node_features[neighbor]
            
            # Linear transformation: h_new = W @ h_agg + b
            transformed = np.dot(aggregated, self.weights) + self.bias
            
            # ReLU activation
            activated = np.maximum(0, transformed)
            
            new_features[node] = activated
        
        return new_features


class GATLayer(ConvolutionLayer):
    """
    Graph Attention Network Layer (Veličković et al., 2018)
    
    Formula: h_i^(l+1) = σ(Σ_{j∈N(i)} α_ij W h_j^(l))
    
    Where α_ij = attention coefficient (learned)
    
    Attention mechanism:
        e_ij = LeakyReLU(a^T [Wh_i || Wh_j])
        α_ij = softmax_j(e_ij)
    
    Key innovation: Attention weights capture importance of neighbors
    Multi-head: Use multiple attention heads and concatenate
    """
    
    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        num_heads: int = 8,
        dropout: float = 0.0,
        concat_heads: bool = True
    ):
        """
        Initialize GAT layer.
        
        Args:
            input_dim: Input feature dimension
            output_dim: Output dimension per attention head
            num_heads: Number of attention heads
            dropout: Dropout rate (0.0 = no dropout)
            concat_heads: If True, concatenate heads; else, average
        """
        self.num_heads = num_heads
        self.dropout = dropout
        self.concat_heads = concat_heads
        
        # Adjust output dim if concatenating
        effective_out_dim = output_dim if not concat_heads else output_dim // num_heads
        
        super().__init__(input_dim, effective_out_dim)
        
        # Multi-head parameters
        self.head_weights: List[np.ndarray] = []
        self.attention_weights: List[np.ndarray] = []
        
        for _ in range(num_heads):
            # Weight matrix for this head
            bound = np.sqrt(6.0 / (input_dim + effective_out_dim))
            W = np.random.uniform(
                -bound, bound, size=(input_dim, effective_out_dim)
            ).astype(np.float32)
            self.head_weights.append(W)
            
            # Attention mechanism parameters: a ∈ R^(2*out_dim)
            a = np.random.randn(2 * effective_out_dim).astype(np.float32) * 0.01
            self.attention_weights.append(a)
        
        logger.info(f"Initialized GAT with {num_heads} heads, dim {effective_out_dim} each")
    
    def forward(
        self,
        graph: GraphStructure,
        node_features: Dict[str, np.ndarray]
    ) -> Dict[str, np.ndarray]:
        """
        Multi-head attention forward pass.
        
        For each head:
        1. Compute attention scores for all edges
        2. Normalize attention with softmax
        3. Aggregate neighbors weighted by attention
        
        Finally: Concatenate or average all heads
        """
        multi_head_outputs: List[Dict[str, np.ndarray]] = []
        
        # Process each attention head
        for head_idx in range(self.num_heads):
            head_output = self._attention_head_forward(
                graph,
                node_features,
                self.head_weights[head_idx],
                self.attention_weights[head_idx]
            )
            multi_head_outputs.append(head_output)
        
        # Combine heads
        final_features: Dict[str, np.ndarray] = {}
        
        for node in node_features.keys():
            if self.concat_heads:
                # Concatenate all head outputs
                concat = np.concatenate([
                    head[node] for head in multi_head_outputs if node in head
                ])
                final_features[node] = concat
            else:
                # Average all head outputs
                avg = np.mean([
                    head[node] for head in multi_head_outputs if node in head
                ], axis=0)
                final_features[node] = avg
        
        return final_features
    
    def _attention_head_forward(
        self,
        graph: GraphStructure,
        node_features: Dict[str, np.ndarray],
        W: np.ndarray,
        a: np.ndarray
    ) -> Dict[str, np.ndarray]:
        """Single attention head forward pass"""
        new_features: Dict[str, np.ndarray] = {}
        
        # Precompute W @ h for all nodes
        transformed_features: Dict[str, np.ndarray] = {}
        for node, feat in node_features.items():
            transformed_features[node] = np.dot(feat, W)
        
        for node in node_features.keys():
            neighbors = graph.get_neighbors(node) | {node}  # Include self
            
            if not neighbors:
                new_features[node] = transformed_features[node]
                continue
            
            # Compute attention scores for all neighbors
            attention_scores: Dict[str, float] = {}
            
            for neighbor in neighbors:
                if neighbor not in transformed_features:
                    continue
                
                # Attention score: e_ij = LeakyReLU(a^T [Wh_i || Wh_j])
                h_i = transformed_features[node]
                h_j = transformed_features[neighbor]
                
                concat = np.concatenate([h_i, h_j])
                e_ij = self._leaky_relu(np.dot(a, concat), alpha=0.2)
                
                attention_scores[neighbor] = e_ij
            
            # Softmax normalization
            normalized_attention = self._softmax(attention_scores)
            
            # Weighted aggregation
            aggregated = np.zeros_like(transformed_features[node])
            
            for neighbor, alpha_ij in normalized_attention.items():
                aggregated += alpha_ij * transformed_features[neighbor]
            
            # Apply activation (ELU typically used in GAT)
            activated = self._elu(aggregated)
            
            new_features[node] = activated
        
        return new_features
    
    @staticmethod
    def _leaky_relu(x: float, alpha: float = 0.2) -> float:
        """LeakyReLU activation"""
        return x if x > 0 else alpha * x
    
    @staticmethod
    def _softmax(scores: Dict[str, float]) -> Dict[str, float]:
        """Softmax over dictionary of scores"""
        # Numerical stability: subtract max
        max_score = max(scores.values()) if scores else 0
        exp_scores = {k: np.exp(v - max_score) for k, v in scores.items()}
        
        sum_exp = sum(exp_scores.values())
        
        return {k: v / (sum_exp + 1e-10) for k, v in exp_scores.items()}
    
    @staticmethod
    def _elu(x: np.ndarray, alpha: float = 1.0) -> np.ndarray:
        """ELU activation"""
        return np.where(x > 0, x, alpha * (np.exp(x) - 1))


class GraphConvolution:
    """
    High-level graph convolution manager.
    
    Features:
    - Stacked convolution layers
    - Residual connections
    - Batch normalization (optional)
    - Multi-layer GCN/GAT networks
    
    Usage:
        conv = GraphConvolution(
            convolution_type=ConvolutionType.GAT,
            layer_dims=[128, 128, 64]
        )
        output = conv.forward(graph, features)
    """
    
    def __init__(
        self,
        convolution_type: ConvolutionType,
        layer_dims: List[int],
        use_residual: bool = True
    ):
        """
        Initialize stacked convolution network.
        
        Args:
            convolution_type: GCN or GAT
            layer_dims: Dimensions for each layer [input, hidden1, ..., output]
            use_residual: Whether to use residual connections
        """
        self.convolution_type = convolution_type
        self.layer_dims = layer_dims
        self.use_residual = use_residual
        
        self.layers: List[ConvolutionLayer] = []
        
        # Build layers
        for i in range(len(layer_dims) - 1):
            layer = self._create_layer(layer_dims[i], layer_dims[i + 1])
            self.layers.append(layer)
        
        logger.info(
            f"Initialized {convolution_type.value.upper()} with "
            f"{len(self.layers)} layers: {layer_dims}"
        )
    
    def forward(
        self,
        graph: GraphStructure,
        node_features: Dict[str, np.ndarray]
    ) -> Dict[str, np.ndarray]:
        """
        Forward pass through all layers.
        
        Applies convolutions sequentially with optional residual connections.
        """
        current_features = node_features
        
        for i, layer in enumerate(self.layers):
            next_features = layer.forward(graph, current_features)
            
            # Residual connection (if dimensions match)
            if self.use_residual and i > 0:
                # Only add residual if dimensions match
                first_node = next(iter(next_features.keys()))
                if current_features[first_node].shape == next_features[first_node].shape:
                    next_features = {
                        node: next_features[node] + current_features.get(node, 0)
                        for node in next_features.keys()
                    }
            
            current_features = next_features
        
        return current_features
    
    def _create_layer(self, input_dim: int, output_dim: int) -> ConvolutionLayer:
        """Factory for creating convolution layers"""
        if self.convolution_type == ConvolutionType.GCN:
            return GCNLayer(input_dim, output_dim)
        elif self.convolution_type == ConvolutionType.GAT:
            return GATLayer(input_dim, output_dim, num_heads=4)
        else:
            raise ValueError(f"Unsupported convolution type: {self.convolution_type}")
