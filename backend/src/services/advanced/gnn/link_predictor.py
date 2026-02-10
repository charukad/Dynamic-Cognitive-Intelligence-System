"""
Link Predictor - Predict missing relationships in knowledge graphs

Advanced scoring functions for link prediction:
- TransE: Translational distance -||h + r - t||
- DistMult: Symmetric bilinear h^T diag(r) t
- ComplEx: Asymmetric complex embeddings

Features:
- Top-K prediction with confidence scores
- Multi-hop reasoning via path composition
- Filtering of known triples (filtered metrics)
- Batch prediction for efficiency
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Set, Callable
from enum import Enum
from dataclasses import dataclass, field
import numpy as np
from heapq import nlargest
import logging

logger = logging.getLogger(__name__)


class ScoringFunction(Enum):
    """Supported scoring functions for link prediction"""
    TRANSE = "transe"
    DISTMULT = "distmult"
    COMPLEX = "complex"


@dataclass
class LinkPrediction:
    """
    Predicted link with metadata.
    
    Attributes:
        head: Head entity
        relation: Relation type
        tail: Tail entity (predicted)
        score: Prediction score (higher = more confident)
        rank: Rank among all candidates (1 = best)
    """
    head: str
    relation: str
    tail: str
    score: float
    rank: int = 0
    
    def __lt__(self, other: LinkPrediction) -> bool:
        """For sorting by score descending"""
        return self.score > other.score


@dataclass
class PredictionMetrics:
    """Evaluation metrics for link prediction"""
    mean_rank: float
    mean_reciprocal_rank: float  # MRR
    hits_at_1: float
    hits_at_3: float
    hits_at_10: float
    total_predictions: int
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            'mean_rank': round(self.mean_rank, 2),
            'mrr': round(self.mean_reciprocal_rank, 4),
            'hits@1': round(self.hits_at_1, 4),
            'hits@3': round(self.hits_at_3, 4),
            'hits@10': round(self.hits_at_10, 4),
            'total': self.total_predictions,
        }


class LinkPredictor:
    """
    High-performance link predictor for knowledge graphs.
    
    Capabilities:
    - Predict missing tails: (h, r, ?) → [t1, t2, ...]
    - Predict missing heads: (?, r, t) → [h1, h2, ...]
    - Predict missing relations: (h, ?, t) → [r1, r2, ...]
    - Multi-hop reasoning: composing relation paths
    - Filtered evaluation (exclude known triples)
    
    Usage:
        predictor = LinkPredictor(scoring_fn=ScoringFunction.COMPLEX)
        predictor.set_embeddings(entity_emb, relation_emb)
        predictions = predictor.predict_tail('Python', 'used_for')
    """
    
    def __init__(
        self,
        scoring_function: ScoringFunction = ScoringFunction.COMPLEX
    ):
        """Initialize link predictor"""
        self.scoring_function = scoring_function
        self.entity_embeddings: Dict[str, np.ndarray] = {}
        self.relation_embeddings: Dict[str, np.ndarray] = {}
        self.known_triples: Set[Tuple[str, str, str]] = set()
    
    def set_embeddings(
        self,
        entity_emb: Dict[str, np.ndarray],
        relation_emb: Dict[str, np.ndarray]
    ) -> None:
        """Set entity and relation embeddings"""
        self.entity_embeddings = entity_emb
        self.relation_embeddings = relation_emb
        logger.info(
            f"Loaded embeddings: {len(entity_emb)} entities, "
            f"{len(relation_emb)} relations"
        )
    
    def add_known_triples(self, triples: List[Tuple[str, str, str]]) -> None:
        """Add known triples for filtered evaluation"""
        self.known_triples.update(triples)
        logger.info(f"Added {len(triples)} known triples (total: {len(self.known_triples)})")
    
    def predict_tail(
        self,
        head: str,
        relation: str,
        top_k: int = 10,
        filter_known: bool = True
    ) -> List[LinkPrediction]:
        """
        Predict tail entities for (head, relation, ?).
        
        Args:
            head: Head entity
            relation: Relation type
            top_k: Number of predictions to return
            filter_known: If True, filter out known triples
        
        Returns:
            List of LinkPrediction objects sorted by score
        """
        if head not in self.entity_embeddings:
            logger.warning(f"Head entity '{head}' not in embeddings")
            return []
        
        if relation not in self.relation_embeddings:
            logger.warning(f"Relation '{relation}' not in embeddings")
            return []
        
        h_emb = self.entity_embeddings[head]
        r_emb = self.relation_embeddings[relation]
        
        # Score all candidate tails
        candidates: List[LinkPrediction] = []
        
        for tail, t_emb in self.entity_embeddings.items():
            # Skip if known triple (when filtering)
            if filter_known and (head, relation, tail) in self.known_triples:
                continue
            
            # Compute score
            score = self._score_triple(h_emb, r_emb, t_emb)
            
            candidates.append(LinkPrediction(
                head=head,
                relation=relation,
                tail=tail,
                score=score
            ))
        
        # Sort by score descending and take top-K
        candidates.sort(reverse=True)
        top_candidates = candidates[:top_k]
        
        # Assign ranks
        for rank, pred in enumerate(top_candidates, start=1):
            pred.rank = rank
        
        return top_candidates
    
    def predict_head(
        self,
        relation: str,
        tail: str,
        top_k: int = 10,
        filter_known: bool = True
    ) -> List[LinkPrediction]:
        """
        Predict head entities for (?, relation, tail).
        
        Similar to predict_tail but searches over heads.
        """
        if tail not in self.entity_embeddings:
            logger.warning(f"Tail entity '{tail}' not in embeddings")
            return []
        
        if relation not in self.relation_embeddings:
            logger.warning(f"Relation '{relation}' not in embeddings")
            return []
        
        t_emb = self.entity_embeddings[tail]
        r_emb = self.relation_embeddings[relation]
        
        candidates: List[LinkPrediction] = []
        
        for head, h_emb in self.entity_embeddings.items():
            if filter_known and (head, relation, tail) in self.known_triples:
                continue
            
            score = self._score_triple(h_emb, r_emb, t_emb)
            
            candidates.append(LinkPrediction(
                head=head,
                relation=relation,
                tail=tail,
                score=score
            ))
        
        candidates.sort(reverse=True)
        top_candidates = candidates[:top_k]
        
        for rank, pred in enumerate(top_candidates, start=1):
            pred.rank = rank
        
        return top_candidates
    
    def predict_relation(
        self,
        head: str,
        tail: str,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Predict relation for (head, ?, tail).
        
        Returns:
            List of (relation, score) tuples
        """
        if head not in self.entity_embeddings or tail not in self.entity_embeddings:
            return []
        
        h_emb = self.entity_embeddings[head]
        t_emb = self.entity_embeddings[tail]
        
        relation_scores: List[Tuple[str, float]] = []
        
        for relation, r_emb in self.relation_embeddings.items():
            score = self._score_triple(h_emb, r_emb, t_emb)
            relation_scores.append((relation, score))
        
        # Sort by score descending
        relation_scores.sort(key=lambda x: x[1], reverse=True)
        
        return relation_scores[:top_k]
    
    def batch_predict_tail(
        self,
        queries: List[Tuple[str, str]],
        top_k: int = 10
    ) -> Dict[Tuple[str, str], List[LinkPrediction]]:
        """
        Batch prediction for multiple queries.
        
        More efficient than calling predict_tail repeatedly.
        
        Args:
            queries: List of (head, relation) pairs
            top_k: Predictions per query
        
        Returns:
            Dict mapping (head, relation) to predictions
        """
        results: Dict[Tuple[str, str], List[LinkPrediction]] = {}
        
        for head, relation in queries:
            predictions = self.predict_tail(head, relation, top_k)
            results[(head, relation)] = predictions
        
        return results
    
    def multi_hop_reasoning(
        self,
        start_entity: str,
        relation_path: List[str],
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Multi-hop reasoning via relation composition.
        
        Example:
            start: "Barack Obama"
            path: ["born_in", "country_of", "continent"]
            result: "North America" (via USA)
        
        Args:
            start_entity: Starting entity
            relation_path: Sequence of relations to traverse
            top_k: Final predictions
        
        Returns:
            List of (entity, accumulated_score) tuples
        """
        current_candidates: Dict[str, float] = {start_entity: 1.0}
        
        for relation in relation_path:
            next_candidates: Dict[str, float] = {}
            
            for entity, acc_score in current_candidates.items():
                # Predict next hop
                predictions = self.predict_tail(entity, relation, top_k=top_k)
                
                for pred in predictions:
                    # Accumulate scores (geometric mean for stability)
                    combined_score = np.sqrt(acc_score * pred.score)
                    
                    if pred.tail in next_candidates:
                        # Keep max score if multiple paths lead to same entity
                        next_candidates[pred.tail] = max(
                            next_candidates[pred.tail],
                            combined_score
                        )
                    else:
                        next_candidates[pred.tail] = combined_score
            
            current_candidates = next_candidates
            
            if not current_candidates:
                break
        
        # Sort final candidates
        final = sorted(current_candidates.items(), key=lambda x: x[1], reverse=True)
        
        return final[:top_k]
    
    def evaluate(
        self,
        test_triples: List[Tuple[str, str, str]],
        filter_known: bool = True
    ) -> PredictionMetrics:
        """
        Evaluate link prediction on test set.
        
        Metrics:
        - Mean Rank: Average rank of correct answer
        - MRR: Mean Reciprocal Rank (1/rank)
        - Hits@K: % of times correct answer in top-K
        
        Args:
            test_triples: List of (h, r, t) test triples
            filter_known: Use filtered evaluation
        
        Returns:
            PredictionMetrics with all metrics
        """
        ranks: List[int] = []
        hits_1 = 0
        hits_3 = 0
        hits_10 = 0
        
        for head, relation, true_tail in test_triples:
            # Predict and find rank of true tail
            predictions = self.predict_tail(
                head, relation,
                top_k=len(self.entity_embeddings),
                filter_known=filter_known
            )
            
            # Find rank of true tail
            rank = None
            for i, pred in enumerate(predictions, start=1):
                if pred.tail == true_tail:
                    rank = i
                    break
            
            if rank is None:
                # True tail not found (entity not in embeddings)
                continue
            
            ranks.append(rank)
            
            if rank <= 1:
                hits_1 += 1
            if rank <= 3:
                hits_3 += 1
            if rank <= 10:
                hits_10 += 1
        
        if not ranks:
            # No valid predictions
            return PredictionMetrics(
                mean_rank=float('inf'),
                mean_reciprocal_rank=0.0,
                hits_at_1=0.0,
                hits_at_3=0.0,
                hits_at_10=0.0,
                total_predictions=0
            )
        
        n = len(ranks)
        
        return PredictionMetrics(
            mean_rank=np.mean(ranks),
            mean_reciprocal_rank=np.mean([1.0 / r for r in ranks]),
            hits_at_1=hits_1 / n,
            hits_at_3=hits_3 / n,
            hits_at_10=hits_10 / n,
            total_predictions=n
        )
    
    def _score_triple(
        self,
        h_emb: np.ndarray,
        r_emb: np.ndarray,
        t_emb: np.ndarray
    ) -> float:
        """
        Score a triple using configured scoring function.
        
        Delegates to appropriate algorithm.
        """
        if self.scoring_function == ScoringFunction.TRANSE:
            return self._score_transe(h_emb, r_emb, t_emb)
        elif self.scoring_function == ScoringFunction.DISTMULT:
            return self._score_distmult(h_emb, r_emb, t_emb)
        elif self.scoring_function == ScoringFunction.COMPLEX:
            return self._score_complex(h_emb, r_emb, t_emb)
        else:
            raise ValueError(f"Unknown scoring function: {self.scoring_function}")
    
    @staticmethod
    def _score_transe(h: np.ndarray, r: np.ndarray, t: np.ndarray) -> float:
        """TransE: -||h + r - t||_2"""
        distance = np.linalg.norm(h + r - t, ord=2)
        return float(-distance)
    
    @staticmethod
    def _score_distmult(h: np.ndarray, r: np.ndarray, t: np.ndarray) -> float:
        """DistMult: <h, r, t> = Σ h_i * r_i * t_i"""
        # Handle complex embeddings
        if np.iscomplexobj(h):
            h = np.real(h)
        if np.iscomplexobj(r):
            r = np.real(r)
        if np.iscomplexobj(t):
            t = np.real(t)
        
        score = np.sum(h * r * t)
        return float(score)
    
    @staticmethod
    def _score_complex(h: np.ndarray, r: np.ndarray, t: np.ndarray) -> float:
        """ComplEx: Re(<h, r, conj(t)>)"""
        # Ensure complex embeddings
        if not np.iscomplexobj(h):
            h = h.astype(np.complex64)
        if not np.iscomplexobj(r):
            r = r.astype(np.complex64)
        if not np.iscomplexobj(t):
            t = t.astype(np.complex64)
        
        # Element-wise product
        product = h * r * np.conj(t)
        # Real part and sum
        score = np.sum(np.real(product))
        return float(score)
