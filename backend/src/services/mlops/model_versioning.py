"""
Model Versioning & A/B Testing System

Enterprise model management:
- Version control for LLM configurations
- A/B testing for model variants
- Performance tracking and comparison
- Rollback capabilities
- Canary deployments
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
import random

from src.core import get_logger

logger = get_logger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class ModelStatus(Enum):
    """Model deployment status."""
    DRAFT = "draft"
    TESTING = "testing"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class DeploymentStrategy(Enum):
    """Deployment strategies for models."""
    IMMEDIATE = "immediate"  # Replace all traffic
    CANARY = "canary"  # Gradual rollout
    AB_TEST = "ab_test"  # Split traffic for testing
    SHADOW = "shadow"  # Run alongside without serving


@dataclass
class ModelVersion:
    """Version of an AI model configuration."""
    
    id: UUID
    name: str
    version: str  # Semantic versioning (e.g., "1.2.3")
    description: str
    
    # Model configuration
    model_config: Dict[str, Any]
    prompt_template: str
    system_prompt: str
    temperature: float
    max_tokens: int
    
    # Metadata
    created_at: datetime
    created_by: str
    status: ModelStatus
    tags: List[str] = field(default_factory=list)
    
    # Performance metrics
    total_requests: int = 0
    successful_requests: int = 0
    avg_latency_ms: float = 0.0
    avg_user_rating: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'model_config': self.model_config,
            'prompt_template': self.prompt_template,
            'system_prompt': self.system_prompt,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'status': self.status.value,
            'tags': self.tags,
            'metrics': {
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'success_rate': self.success_rate,
                'avg_latency_ms': self.avg_latency_ms,
                'avg_user_rating': self.avg_user_rating,
            },
        }
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests


@dataclass
class ABTest:
    """A/B test configuration."""
    
    id: UUID
    name: str
    description: str
    
    # Test configuration
    variant_a_id: UUID  # Control
    variant_b_id: UUID  # Treatment
    traffic_split: float = 0.5  # % to variant B (0.0 - 1.0)
    
    # Test status
    status: str = "running"  # running, completed, cancelled
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    
    # Metrics
    variant_a_requests: int = 0
    variant_b_requests: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'variant_a_id': str(self.variant_a_id),
            'variant_b_id': str(self.variant_b_id),
            'traffic_split': self.traffic_split,
            'status': self.status,
            'started_at': self.started_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'total_requests': self.variant_a_requests + self.variant_b_requests,
            'variant_a_requests': self.variant_a_requests,
            'variant_b_requests': self.variant_b_requests,
        }


# ============================================================================
# Model Version Manager
# ============================================================================

class ModelVersionManager:
    """
    Manage model versions and deployments.
    
    Features:
    - Version control for models
    - A/B testing
    - Traffic routing
    - Performance tracking
    """
    
    def __init__(self):
        """Initialize model version manager."""
        self.versions: Dict[str, ModelVersion] = {}
        self.ab_tests: Dict[str, ABTest] = {}
        self.active_version_id: Optional[str] = None
        
        logger.info("Initialized ModelVersionManager")
    
    def create_version(
        self,
        name: str,
        version: str,
        description: str,
        model_config: Dict[str, Any],
        prompt_template: str,
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        created_by: str = "system",
        tags: Optional[List[str]] = None,
    ) -> ModelVersion:
        """Create new model version."""
        model_version = ModelVersion(
            id=uuid4(),
            name=name,
            version=version,
            description=description,
            model_config=model_config,
            prompt_template=prompt_template,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            created_at=datetime.now(),
            created_by=created_by,
            status=ModelStatus.DRAFT,
            tags=tags or [],
        )
        
        self.versions[str(model_version.id)] = model_version
        logger.info(f"Created model version: {name} v{version}")
        
        return model_version
    
    def deploy_version(
        self,
        version_id: str,
        strategy: DeploymentStrategy = DeploymentStrategy.IMMEDIATE,
    ) -> bool:
        """Deploy a model version."""
        if version_id not in self.versions:
            logger.error(f"Version not found: {version_id}")
            return False
        
        version = self.versions[version_id]
        
        if strategy == DeploymentStrategy.IMMEDIATE:
            # Deprecate current active version
            if self.active_version_id:
                self.versions[self.active_version_id].status = ModelStatus.DEPRECATED
            
            # Activate new version
            version.status = ModelStatus.ACTIVE
            self.active_version_id = version_id
            
            logger.info(f"Deployed version {version.version} (immediate)")
            return True
        
        elif strategy == DeploymentStrategy.AB_TEST:
            version.status = ModelStatus.TESTING
            logger.info(f"Version {version.version} set to testing mode")
            return True
        
        return False
    
    def create_ab_test(
        self,
        name: str,
        description: str,
        variant_a_id: str,
        variant_b_id: str,
        traffic_split: float = 0.5,
    ) -> ABTest:
        """Create A/B test between two model versions."""
        # Validate versions exist
        if variant_a_id not in self.versions or variant_b_id not in self.versions:
            raise ValueError("Both variant versions must exist")
        
        ab_test = ABTest(
            id=uuid4(),
            name=name,
            description=description,
            variant_a_id=UUID(variant_a_id),
            variant_b_id=UUID(variant_b_id),
            traffic_split=traffic_split,
        )
        
        self.ab_tests[str(ab_test.id)] = ab_test
        
        # Mark versions as testing
        self.versions[variant_a_id].status = ModelStatus.TESTING
        self.versions[variant_b_id].status = ModelStatus.TESTING
        
        logger.info(
            f"Created A/B test: {name} "
            f"(A={variant_a_id[:8]}, B={variant_b_id[:8]}, split={traffic_split})"
        )
        
        return ab_test
    
    def route_request(self, ab_test_id: Optional[str] = None) -> ModelVersion:
        """
        Route request to appropriate model version.
        
        Args:
            ab_test_id: Optional A/B test ID for traffic splitting
            
        Returns:
            Model version to use
        """
        # If A/B test specified, route accordingly
        if ab_test_id and ab_test_id in self.ab_tests:
            ab_test = self.ab_tests[ab_test_id]
            
            # Random selection based on traffic split
            if random.random() < ab_test.traffic_split:
                # Variant B
                ab_test.variant_b_requests += 1
                version_id = str(ab_test.variant_b_id)
            else:
                # Variant A (control)
                ab_test.variant_a_requests += 1
                version_id = str(ab_test.variant_a_id)
            
            return self.versions[version_id]
        
        # Default: return active version
        if self.active_version_id:
            return self.versions[self.active_version_id]
        
        # Fallback: return any active version
        active_versions = [
            v for v in self.versions.values() 
            if v.status == ModelStatus.ACTIVE
        ]
        
        if active_versions:
            return active_versions[0]
        
        raise ValueError("No active model version available")
    
    def record_metrics(
        self,
        version_id: str,
        success: bool,
        latency_ms: float,
        user_rating: Optional[float] = None,
    ):
        """Record metrics for a model version."""
        if version_id not in self.versions:
            return
        
        version = self.versions[version_id]
        version.total_requests += 1
        
        if success:
            version.successful_requests += 1
        
        # Update running average for latency
        n = version.total_requests
        version.avg_latency_ms = (
            (version.avg_latency_ms * (n - 1) + latency_ms) / n
        )
        
        # Update running average for user rating
        if user_rating is not None:
            if version.avg_user_rating == 0:
                version.avg_user_rating = user_rating
            else:
                version.avg_user_rating = (
                    (version.avg_user_rating * (n - 1) + user_rating) / n
                )
    
    def compare_versions(
        self,
        version_a_id: str,
        version_b_id: str,
    ) -> Dict[str, Any]:
        """Compare two model versions."""
        if version_a_id not in self.versions or version_b_id not in self.versions:
            return {'error': 'One or both versions not found'}
        
        v_a = self.versions[version_a_id]
        v_b = self.versions[version_b_id]
        
        return {
            'version_a': {
                'name': f"{v_a.name} v{v_a.version}",
                'metrics': {
                    'success_rate': v_a.success_rate,
                    'avg_latency_ms': v_a.avg_latency_ms,
                    'avg_user_rating': v_a.avg_user_rating,
                    'total_requests': v_a.total_requests,
                },
            },
            'version_b': {
                'name': f"{v_b.name} v{v_b.version}",
                'metrics': {
                    'success_rate': v_b.success_rate,
                    'avg_latency_ms': v_b.avg_latency_ms,
                    'avg_user_rating': v_b.avg_user_rating,
                    'total_requests': v_b.total_requests,
                },
            },
            'comparison': {
                'success_rate_diff': v_b.success_rate - v_a.success_rate,
                'latency_diff_ms': v_b.avg_latency_ms - v_a.avg_latency_ms,
                'rating_diff': v_b.avg_user_rating - v_a.avg_user_rating,
                'better_version': self._determine_winner(v_a, v_b),
            },
        }
    
    def _determine_winner(self, v_a: ModelVersion, v_b: ModelVersion) -> str:
        """Determine which version is better overall."""
        # Simple scoring: success rate (40%) + rating (40%) - latency penalty (20%)
        score_a = (
            v_a.success_rate * 0.4 +
            (v_a.avg_user_rating / 5.0) * 0.4 -
            (v_a.avg_latency_ms / 5000) * 0.2
        )
        
        score_b = (
            v_b.success_rate * 0.4 +
            (v_b.avg_user_rating / 5.0) * 0.4 -
            (v_b.avg_latency_ms / 5000) * 0.2
        )
        
        if score_b > score_a:
            return 'version_b'
        elif score_a > score_b:
            return 'version_a'
        else:
            return 'tie'
    
    def get_version(self, version_id: str) -> Optional[ModelVersion]:
        """Get model version by ID."""
        return self.versions.get(version_id)
    
    def list_versions(self, status: Optional[ModelStatus] = None) -> List[Dict[str, Any]]:
        """List all model versions, optionally filtered by status."""
        versions = self.versions.values()
        
        if status:
            versions = [v for v in versions if v.status == status]
        
        return [v.to_dict() for v in versions]
    
    def list_ab_tests(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all A/B tests."""
        tests = self.ab_tests.values()
        
        if status:
            tests = [t for t in tests if t.status == status]
        
        return [t.to_dict() for t in tests]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics."""
        return {
            'total_versions': len(self.versions),
            'active_versions': len([v for v in self.versions.values() if v.status == ModelStatus.ACTIVE]),
            'testing_versions': len([v for v in self.versions.values() if v.status == ModelStatus.TESTING]),
            'total_ab_tests': len(self.ab_tests),
            'running_ab_tests': len([t for t in self.ab_tests.values() if t.status == 'running']),
        }


# ============================================================================
# Singleton Instance
# ============================================================================

model_version_manager = ModelVersionManager()
