"""
Multi-modal Fusion Layer

Combines embeddings from different modalities into unified representations.
Implements attention-based fusion strategies.
"""

from typing import Any, Dict, List, Literal, Optional
import numpy as np

from pydantic import BaseModel

from src.core import get_logger

logger = get_logger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class ModalityEmbedding(BaseModel):
    """Embedding from a single modality"""
    modality: Literal["text", "image", "audio", "video"]
    vector: List[float]
    weight: float = 1.0
    metadata: Dict[str, Any] = {}


class UnifiedEmbedding(BaseModel):
    """Unified multi-modal embedding"""
    vector: List[float]
    modalities_used: List[str]
    fusion_strategy: str
    dimensions: int


# ============================================================================
# Fusion Layer
# ============================================================================

class FusionLayer:
    """
    Fuses embeddings from multiple modalities.
    
    Strategies:
    - Early Fusion: Concatenate raw features
    - Late Fusion: Combine predictions
    - Attention Fusion: Learned cross-modal attention
    """
    
    def __init__(self, target_dim: int = 512):
        """
        Initialize fusion layer.
        
        Args:
            target_dim: Target dimension for unified embedding
        """
        self.target_dim = target_dim
    
    async def fuse_embeddings(
        self,
        embeddings: List[ModalityEmbedding],
        strategy: Literal["early", "late", "attention"] = "attention"
    ) -> UnifiedEmbedding:
        """
        Fuse embeddings from multiple modalities.
        
        Args:
            embeddings: List of modality embeddings
            strategy: Fusion strategy
            
        Returns:
            Unified embedding
        """
        if not embeddings:
            raise ValueError("No embeddings to fuse")
        
        if len(embeddings) == 1:
            # Single modality - just normalize
            return await self._normalize_single(embeddings[0])
        
        logger.info(
            f"Fusing {len(embeddings)} modalities using {strategy} fusion"
        )
        
        if strategy == "early":
            result = await self._early_fusion(embeddings)
        elif strategy == "late":
            result = await self._late_fusion(embeddings)
        elif strategy == "attention":
            result = await self._attention_fusion(embeddings)
        else:
            raise ValueError(f"Unknown fusion strategy: {strategy}")
        
        return result
    
    async def _early_fusion(
        self,
        embeddings: List[ModalityEmbedding]
    ) -> UnifiedEmbedding:
        """
        Early fusion: Concatenate features then project.
        
        Args:
            embeddings: List of embeddings
            
        Returns:
            Fused embedding
        """
        # Concatenate all embeddings
        concatenated = []
        for emb in embeddings:
            concatenated.extend(emb.vector)
        
        # Project to target dimension
        # In production: use learned linear projection
        # W = torch.nn.Linear(len(concatenated), self.target_dim)
        # projected = W(torch.tensor(concatenated))
        
        # Simulated projection (use PCA-like dimensionality reduction)
        if len(concatenated) > self.target_dim:
            # Downsample
            indices = np.linspace(0, len(concatenated) - 1, self.target_dim, dtype=int)
            projected = [concatenated[i] for i in indices]
        else:
            # Pad with zeros
            projected = concatenated + [0.0] * (self.target_dim - len(concatenated))
        
        return UnifiedEmbedding(
            vector=projected,
            modalities_used=[emb.modality for emb in embeddings],
            fusion_strategy="early",
            dimensions=len(projected)
        )
    
    async def _late_fusion(
        self,
        embeddings: List[ModalityEmbedding]
    ) -> UnifiedEmbedding:
        """
        Late fusion: Weighted average of embeddings.
        
        Args:
            embeddings: List of embeddings
            
        Returns:
            Fused embedding
        """
        # Normalize all to same dimension first
        normalized = []
        for emb in embeddings:
            if len(emb.vector) == self.target_dim:
                normalized.append(np.array(emb.vector) * emb.weight)
            else:
                # Resize to target dim
                resized = self._resize_vector(emb.vector, self.target_dim)
                normalized.append(np.array(resized) * emb.weight)
        
        # Weighted average
        total_weight = sum(emb.weight for emb in embeddings)
        fused = sum(normalized) / total_weight
        
        # Normalize to unit length
        fused = fused / (np.linalg.norm(fused) + 1e-8)
        
        return UnifiedEmbedding(
            vector=fused.tolist(),
            modalities_used=[emb.modality for emb in embeddings],
            fusion_strategy="late",
            dimensions=len(fused)
        )
    
    async def _attention_fusion(
        self,
        embeddings: List[ModalityEmbedding]
    ) -> UnifiedEmbedding:
        """
        Attention fusion: Cross-modal attention.
        
        Implements simplified transformer-style attention:
        Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V
        
        Args:
            embeddings: List of embeddings
            
        Returns:
            Fused embedding
        """
        # Normalize all to same dimension
        normalized = []
        for emb in embeddings:
            resized = self._resize_vector(emb.vector, self.target_dim)
            normalized.append(np.array(resized))
        
        # Stack embeddings (num_modalities, dim)
        stacked = np.array(normalized)
        
        # Self-attention across modalities
        # Q = K = V = stacked
        # In production, use learned projection matrices
        
        # Compute attention scores
        # scores = QK^T / sqrt(d_k)
        scores = np.matmul(stacked, stacked.T) / np.sqrt(self.target_dim)
        
        # Apply softmax
        attention_weights = self._softmax(scores, axis=1)
        
        # Apply weights: output = attention_weights @ V
        attended = np.matmul(attention_weights, stacked)
        
        # Aggregate across modalities (mean)
        fused = np.mean(attended, axis=0)
        
        # Normalize
        fused = fused / (np.linalg.norm(fused) + 1e-8)
        
        return UnifiedEmbedding(
            vector=fused.tolist(),
            modalities_used=[emb.modality for emb in embeddings],
            fusion_strategy="attention",
            dimensions=len(fused)
        )
    
    async def _normalize_single(
        self,
        embedding: ModalityEmbedding
    ) -> UnifiedEmbedding:
        """Normalize single modality embedding"""
        resized = self._resize_vector(embedding.vector, self.target_dim)
        normalized = np.array(resized)
        normalized = normalized / (np.linalg.norm(normalized) + 1e-8)
        
        return UnifiedEmbedding(
            vector=normalized.tolist(),
            modalities_used=[embedding.modality],
            fusion_strategy="single",
            dimensions=len(normalized)
        )
    
    def _resize_vector(
        self,
        vector: List[float],
        target_dim: int
    ) -> List[float]:
        """Resize vector to target dimension"""
        if len(vector) == target_dim:
            return vector
        elif len(vector) > target_dim:
            # Downsample
            indices = np.linspace(0, len(vector) - 1, target_dim, dtype=int)
            return [vector[i] for i in indices]
        else:
            # Pad with mean
            mean_val = np.mean(vector)
            return vector + [mean_val] * (target_dim - len(vector))
    
    def _softmax(self, x: np.ndarray, axis: int = -1) -> np.ndarray:
        """Compute softmax"""
        exp_x = np.exp(x - np.max(x, axis=axis, keepdims=True))
        return exp_x / np.sum(exp_x, axis=axis, keepdims=True)
    
    async def compute_cross_modal_similarity(
        self,
        emb1: ModalityEmbedding,
        emb2: ModalityEmbedding
    ) -> float:
        """
        Compute similarity between embeddings from different modalities.
        
        Args:
            emb1: First embedding
            emb2: Second embedding
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Resize to same dimension
        v1 = np.array(self._resize_vector(emb1.vector, self.target_dim))
        v2 = np.array(self._resize_vector(emb2.vector, self.target_dim))
        
        # Cosine similarity
        similarity = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
        
        # Normalize to 0-1
        return float((similarity + 1) / 2)


# Global instance
fusion_layer = FusionLayer(target_dim=512)
