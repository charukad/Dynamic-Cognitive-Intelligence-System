"""
GNN API Endpoints

REST API for graph neural network operations:
- Train embeddings on knowledge graphs
- Apply graph convolutions
- Predict missing links
- Multi-hop reasoning
- Model management
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, validator

from src.services.advanced.gnn import (
    gnn_service,
    EmbeddingMethod,
    ConvolutionType
)
from src.services.advanced.gnn.node_embedder import EmbeddingConfig


router = APIRouter(prefix="/v1/gnn", tags=["gnn"])


# Request Models
class TripleModel(BaseModel):
    """Knowledge graph triple"""
    head: str = Field(..., min_length=1, description="Head entity")
    relation: str = Field(..., min_length=1, description="Relation type")
    tail: str = Field(..., min_length=1, description="Tail entity")


class TrainEmbeddingsRequest(BaseModel):
    """Request to train embeddings"""
    triples: List[TripleModel] = Field(..., min_items=1, description="Knowledge graph triples")
    embedding_method: str = Field("complex", description="Embedding algorithm: transe, distmult, complex")
    embedding_dim: int = Field(128, ge=16, le=512, description="Embedding dimension")
    num_epochs: int = Field(100, ge=1, le=1000, description="Training epochs")
    learning_rate: float = Field(0.01, gt=0, description="Learning rate")
    
    @validator('embedding_method')
    def validate_method(cls, v):
        valid = ['transe', 'distmult', 'complex']
        if v.lower() not in valid:
            raise ValueError(f"Must be one of: {valid}")
        return v.lower()


class ApplyConvolutionRequest(BaseModel):
    """Request to apply graph convolution"""
    edges: List[List[str]] = Field(..., description="Graph edges as [source, target] pairs")
    convolution_type: str = Field("gat", description="Convolution type: gcn, gat")
    layer_dims: Optional[List[int]] = Field(None, description="Layer dimensions")
    
    @validator('convolution_type')
    def validate_conv_type(cls, v):
        valid = ['gcn', 'gat']
        if v.lower() not in valid:
            raise ValueError(f"Must be one of: {valid}")
        return v.lower()
    
    @validator('edges')
    def validate_edges(cls, v):
        for edge in v:
            if len(edge) != 2:
                raise ValueError("Each edge must be [source, target] pair")
        return v


class PredictLinkRequest(BaseModel):
    """Request to predict missing link"""
    head: str = Field(..., description="Head entity")
    relation: str = Field(..., description="Relation type")
    top_k: int = Field(10, ge=1, le=100, description="Number of predictions")
    filter_known: bool = Field(True, description="Filter known triples")


class PredictHeadRequest(BaseModel):
    """Request to predict missing head"""
    relation: str
    tail: str
    top_k: int = Field(10, ge=1, le=100)


class PredictRelationRequest(BaseModel):
    """Request to predict relation"""
    head: str
    tail: str
    top_k: int = Field(5, ge=1, le=20)


class MultiHopRequest(BaseModel):
    """Request for multi-hop reasoning"""
    start_entity: str = Field(..., description="Starting entity")
    relation_path: List[str] = Field(..., min_items=1, description="Sequence of relations")
    top_k: int = Field(5, ge=1, le=50)


# Endpoints
@router.post("/models/{model_id}/train", status_code=status.HTTP_201_CREATED)
async def train_embeddings(model_id: str, request: TrainEmbeddingsRequest):
    """
    Train node embeddings on knowledge graph.
    
    Creates a new GNN model with learned entity and relation embeddings.
    """
    # Convert request to format expected by service
    triples = [t.dict() for t in request.triples]
    
    # Parse embedding method
    method = EmbeddingMethod(request.embedding_method)
    
    # Create config
    config = EmbeddingConfig(
        embedding_dim=request.embedding_dim,
        num_epochs=request.num_epochs,
        learning_rate=request.learning_rate
    )
    
    try:
        result = await gnn_service.train_embeddings(
            model_id=model_id,
            triples=triples,
            embedding_method=method,
            config=config
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/models/{model_id}/convolution", status_code=status.HTTP_200_OK)
async def apply_convolution(model_id: str, request: ApplyConvolutionRequest):
    """
    Apply graph convolution to enhance embeddings.
    
    Uses GCN or GAT to propagate information across graph structure.
    """
    # Convert edges
    edges = [(e[0], e[1]) for e in request.edges]
    
    conv_type = ConvolutionType(request.convolution_type)
    
    try:
        result = await gnn_service.apply_convolution(
            model_id=model_id,
            graph_edges=edges,
            convolution_type=conv_type,
            layer_dims=request.layer_dims
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/models/{model_id}/predict/tail", status_code=status.HTTP_200_OK)
async def predict_tail(model_id: str, request: PredictLinkRequest):
    """
    Predict missing tail entities for (head, relation, ?).
    
    Returns top-K predictions with scores.
    """
    try:
        predictions = await gnn_service.predict_link(
            model_id=model_id,
            head=request.head,
            relation=request.relation,
            top_k=request.top_k,
            filter_known=request.filter_known
        )
        
        return {
            'head': request.head,
            'relation': request.relation,
            'predictions': predictions,
            'total': len(predictions),
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/models/{model_id}/predict/head", status_code=status.HTTP_200_OK)
async def predict_head(model_id: str, request: PredictHeadRequest):
    """Predict missing head entities for (?, relation, tail)"""
    try:
        predictions = await gnn_service.predict_head(
            model_id=model_id,
            relation=request.relation,
            tail=request.tail,
            top_k=request.top_k
        )
        
        return {
            'relation': request.relation,
            'tail': request.tail,
            'predictions': predictions,
            'total': len(predictions),
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/models/{model_id}/predict/relation", status_code=status.HTTP_200_OK)
async def predict_relation(model_id: str, request: PredictRelationRequest):
    """Predict relation for (head, ?, tail)"""
    try:
        predictions = await gnn_service.predict_relation(
            model_id=model_id,
            head=request.head,
            tail=request.tail,
            top_k=request.top_k
        )
        
        return {
            'head': request.head,
            'tail': request.tail,
            'predictions': predictions,
            'total': len(predictions),
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/models/{model_id}/reason", status_code=status.HTTP_200_OK)
async def multi_hop_reasoning(model_id: str, request: MultiHopRequest):
    """
    Multi-hop reasoning via relation path composition.
    
    Example: "Python" → ["created_by", "works_at"] → Organizations
    """
    try:
        results = await gnn_service.multi_hop_reasoning(
            model_id=model_id,
            start_entity=request.start_entity,
            relation_path=request.relation_path,
            top_k=request.top_k
        )
        
        return {
            'start_entity': request.start_entity,
            'relation_path': request.relation_path,
            'results': results,
            'total': len(results),
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/models/{model_id}/similar/{entity}", status_code=status.HTTP_200_OK)
async def find_similar(model_id: str, entity: str, top_k: int = 10):
    """Find most similar entities using cosine similarity"""
    try:
        similar = await gnn_service.find_similar_entities(
            model_id=model_id,
            entity=entity,
            top_k=top_k
        )
        
        return {
            'query_entity': entity,
            'similar_entities': similar,
            'total': len(similar),
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/models/{model_id}/embedding/{entity}", status_code=status.HTTP_200_OK)
async def get_embedding(model_id: str, entity: str):
    """Get embedding vector for entity"""
    try:
        embedding = await gnn_service.get_embedding(model_id, entity)
        
        if embedding is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entity '{entity}' not found in model '{model_id}'"
            )
        
        return {
            'entity': entity,
            'embedding': embedding,
            'dimension': len(embedding),
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/models/{model_id}", status_code=status.HTTP_200_OK)
async def get_model(model_id: str):
    """Get model metadata"""
    try:
        model = await gnn_service.get_model(model_id)
        return model
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/models", status_code=status.HTTP_200_OK)
async def list_models():
    """List all trained GNN models"""
    models = await gnn_service.list_models()
    
    return {
        'models': models,
        'total': len(models),
    }


@router.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(model_id: str):
    """Delete GNN model"""
    success = await gnn_service.delete_model(model_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_id}' not found"
        )
    
    return None


@router.post("/models/{model_id}/evaluate", status_code=status.HTTP_200_OK)
async def evaluate_model(model_id: str, triples: List[TripleModel]):
    """
    Evaluate model on test triples.
    
    Returns metrics: MRR, Hits@K, Mean Rank
    """
    if not triples:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test triples cannot be empty"
        )
    
    test_triples = [t.dict() for t in triples]
    
    try:
        metrics = await gnn_service.evaluate_model(model_id, test_triples)
        
        return {
            'model_id': model_id,
            'test_size': len(triples),
            'metrics': metrics,
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
