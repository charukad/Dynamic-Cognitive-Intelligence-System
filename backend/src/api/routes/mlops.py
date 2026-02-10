"""
MLOps API - Model Versioning, A/B Testing, and Prompt Optimization

Enterprise AI operations endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.services.mlops.model_versioning import model_version_manager, DeploymentStrategy
from src.services.mlops.prompt_optimizer import prompt_optimizer

router = APIRouter(prefix="/mlops", tags=["mlops"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateModelVersionRequest(BaseModel):
    """Create new model version."""
    name: str
    version: str
    description: str
    config: Dict[str, Any]  # Renamed from model_config (reserved in Pydantic 2.x)
    prompt_template: str
    system_prompt: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=1)
    created_by: str = "system"
    tags: List[str] = Field(default_factory=list)


class CreateABTestRequest(BaseModel):
    """Create A/B test."""
    name: str
    description: str
    variant_a_id: str
    variant_b_id: str
    traffic_split: float = Field(default=0.5, ge=0.0, le=1.0)


class RecordMetricsRequest(BaseModel):
    """Record model metrics."""
    version_id: str
    success: bool
    latency_ms: float
    user_rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)


class CreatePromptTemplateRequest(BaseModel):
    """Create prompt template."""
    name: str
    template: str
    description: str
    variables: List[str]
    category: str
    tags: List[str] = Field(default_factory=list)


class AddFewShotExampleRequest(BaseModel):
    """Add few-shot example."""
    input: str
    output: str
    category: str
    quality_score: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Model Versioning Endpoints
# ============================================================================

@router.post("/models/versions")
async def create_model_version(request: CreateModelVersionRequest) -> Dict[str, Any]:
    """Create new model version."""
    try:
        version = model_version_manager.create_version(
            name=request.name,
            version=request.version,
            description=request.description,
            model_config=request.config,  # Use renamed field
            prompt_template=request.prompt_template,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            created_by=request.created_by,
            tags=request.tags,
        )
        
        return {'success': True, 'version': version.to_dict()}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create version: {str(e)}"
        )


@router.get("/models/versions")
async def list_model_versions(status_filter: Optional[str] = None) -> Dict[str, Any]:
    """List all model versions."""
    from src.services.mlops.model_versioning import ModelStatus
    
    status_enum = ModelStatus(status_filter) if status_filter else None
    versions = model_version_manager.list_versions(status_enum)
    
    return {
        'versions': versions,
        'count': len(versions),
    }


@router.get("/models/versions/{version_id}")
async def get_model_version(version_id: str) -> Dict[str, Any]:
    """Get specific model version."""
    version = model_version_manager.get_version(version_id)
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version not found: {version_id}"
        )
    
    return version.to_dict()


@router.post("/models/versions/{version_id}/deploy")
async def deploy_model_version(
    version_id: str,
    strategy: str = "immediate"
) -> Dict[str, Any]:
    """Deploy model version."""
    try:
        strat = DeploymentStrategy(strategy)
        success = model_version_manager.deploy_version(version_id, strat)
        
        return {
            'success': success,
            'version_id': version_id,
            'strategy': strategy,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deployment failed: {str(e)}"
        )


@router.post("/models/metrics")
async def record_model_metrics(request: RecordMetricsRequest) -> Dict[str, Any]:
    """Record model performance metrics."""
    model_version_manager.record_metrics(
        version_id=request.version_id,
        success=request.success,
        latency_ms=request.latency_ms,
        user_rating=request.user_rating,
    )
    
    return {'success': True, 'message': 'Metrics recorded'}


@router.get("/models/compare")
async def compare_model_versions(
    version_a: str,
    version_b: str,
) -> Dict[str, Any]:
    """Compare two model versions."""
    comparison = model_version_manager.compare_versions(version_a, version_b)
    return comparison


# ============================================================================
# A/B Testing Endpoints
# ============================================================================

@router.post("/ab-tests")
async def create_ab_test(request: CreateABTestRequest) -> Dict[str, Any]:
    """Create A/B test."""
    try:
        ab_test = model_version_manager.create_ab_test(
            name=request.name,
            description=request.description,
            variant_a_id=request.variant_a_id,
            variant_b_id=request.variant_b_id,
            traffic_split=request.traffic_split,
        )
        
        return {'success': True, 'ab_test': ab_test.to_dict()}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create A/B test: {str(e)}"
        )


@router.get("/ab-tests")
async def list_ab_tests(status_filter: Optional[str] = None) -> Dict[str, Any]:
    """List all A/B tests."""
    tests = model_version_manager.list_ab_tests(status_filter)
    
    return {
        'ab_tests': tests,
        'count': len(tests),
    }


@router.get("/ab-tests/{test_id}/route")
async def route_ab_test_request(test_id: str) -> Dict[str, Any]:
    """Route request through A/B test."""
    try:
        version = model_version_manager.route_request(test_id)
        return {
            'version_id': str(version.id),
            'version_name': version.name,
            'version_number': version.version,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Routing failed: {str(e)}"
        )


# ============================================================================
# Prompt Optimization Endpoints
# ============================================================================

@router.post("/prompts/templates")
async def create_prompt_template(request: CreatePromptTemplateRequest) -> Dict[str, Any]:
    """Create prompt template."""
    try:
        template = prompt_optimizer.create_template(
            name=request.name,
            template=request.template,
            description=request.description,
            variables=request.variables,
            category=request.category,
            tags=request.tags,
        )
        
        return {'success': True, 'template': template.to_dict()}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}"
        )


@router.get("/prompts/templates")
async def list_prompt_templates(category: Optional[str] = None) -> Dict[str, Any]:
    """List prompt templates."""
    templates = prompt_optimizer.list_templates(category)
    
    return {
        'templates': templates,
        'count': len(templates),
    }


@router.post("/prompts/examples")
async def add_few_shot_example(request: AddFewShotExampleRequest) -> Dict[str, Any]:
    """Add few-shot example."""
    example = prompt_optimizer.add_example(
        input=request.input,
        output=request.output,
        category=request.category,
        quality_score=request.quality_score,
        metadata=request.metadata,
    )
    
    return {'success': True, 'example': example.to_dict()}


@router.get("/prompts/examples/{category}")
async def get_few_shot_examples(
    category: str,
    limit: int = 3,
    min_quality: float = 0.7,
) -> Dict[str, Any]:
    """Get best few-shot examples for category."""
    examples = prompt_optimizer.get_examples(category, limit, min_quality)
    
    return {
        'category': category,
        'examples': [ex.to_dict() for ex in examples],
        'count': len(examples),
    }


@router.get("/prompts/best/{category}")
async def get_best_template(category: str) -> Dict[str, Any]:
    """Get best performing template for category."""
    template = prompt_optimizer.get_best_template(category)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No templates found for category: {category}"
        )
    
    return template.to_dict()


# ============================================================================
# Statistics Endpoints
# ============================================================================

@router.get("/stats")
async def get_mlops_stats() -> Dict[str, Any]:
    """Get MLOps statistics."""
    return {
        'model_versioning': model_version_manager.get_statistics(),
        'prompt_optimization': prompt_optimizer.get_statistics(),
    }
