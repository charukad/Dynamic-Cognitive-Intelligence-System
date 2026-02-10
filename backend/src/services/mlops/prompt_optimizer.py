"""
Advanced Prompt Optimization Framework

Automatic prompt engineering and optimization:
- Prompt versioning and A/B testing
- Few-shot example management
- Performance-based prompt selection
- Automatic prompt refinement
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from src.core import get_logger

logger = get_logger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class PromptTemplate:
    """Prompt template with variables."""
    
    id: UUID
    name: str
    template: str  # Template with {variables}
    description: str
    variables: List[str]  # List of variable names
    
    # Metadata
    created_at: datetime
    category: str  # e.g., "summarization", "classification", "generation"
    tags: List[str] = field(default_factory=list)
    
    # Performance metrics
    total_uses: int = 0
    successful_uses: int = 0
    avg_output_quality: float = 0.0  # User ratings
    avg_latency_ms: float = 0.0
    
    def format(self, **kwargs) -> str:
        """Format template with provided variables."""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'name': self.name,
            'template': self.template,
            'description': self.description,
            'variables': self.variables,
            'created_at': self.created_at.isoformat(),
            'category': self.category,
            'tags': self.tags,
            'metrics': {
                'total_uses': self.total_uses,
                'successful_uses': self.successful_uses,
                'success_rate': self.success_rate,
                'avg_output_quality': self.avg_output_quality,
                'avg_latency_ms': self.avg_latency_ms,
            },
        }
    
    @property
    def success_rate(self) -> float:
        if self.total_uses == 0:
            return 0.0
        return self.successful_uses / self.total_uses


@dataclass
class FewShotExample:
    """Few-shot learning example."""
    
    id: UUID
    input: str
    output: str
    category: str
    quality_score: float = 1.0  # How good this example is (0-1)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'input': self.input,
            'output': self.output,
            'category': self.category,
            'quality_score': self.quality_score,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
        }


# ============================================================================
# Prompt Optimizer
# ============================================================================

class PromptOptimizer:
    """
    Automatic prompt optimization system.
    
    Features:
    - Template management
    - Few-shot example selection
    - Performance tracking
    - Automatic refinement
    """
    
    def __init__(self):
        """Initialize prompt optimizer."""
        self.templates: Dict[str, PromptTemplate] = {}
        self.examples: Dict[str, List[FewShotExample]] = {}  # category -> examples
        
        # Initialize with default templates
        self._initialize_default_templates()
        
        logger.info("Initialized PromptOptimizer")
    
    def _initialize_default_templates(self):
        """Create default prompt templates."""
        # Summarization template
        self.create_template(
            name="Summarization",
            template="Summarize the following text concisely:\n\n{text}\n\nSummary:",
            description="Basic summarization prompt",
            variables=["text"],
            category="summarization",
        )
        
        # Classification template
        self.create_template(
            name="Classification",
            template="Classify the following text into one of these categories: {categories}\n\nText: {text}\n\nCategory:",
            description="Text classification prompt",
            variables=["text", "categories"],
            category="classification",
        )
        
        # Question answering
        self.create_template(
            name="Question Answering",
            template="Context: {context}\n\nQuestion: {question}\n\nAnswer:",
            description="Question answering with context",
            variables=["context", "question"],
            category="qa",
        )
    
    def create_template(
        self,
        name: str,
        template: str,
        description: str,
        variables: List[str],
        category: str,
        tags: Optional[List[str]] = None,
    ) -> PromptTemplate:
        """Create new prompt template."""
        prompt_template = PromptTemplate(
            id=uuid4(),
            name=name,
            template=template,
            description=description,
            variables=variables,
            created_at=datetime.now(),
            category=category,
            tags=tags or [],
        )
        
        self.templates[str(prompt_template.id)] = prompt_template
        logger.info(f"Created prompt template: {name}")
        
        return prompt_template
    
    def add_example(
        self,
        input: str,
        output: str,
        category: str,
        quality_score: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FewShotExample:
        """Add few-shot example."""
        example = FewShotExample(
            id=uuid4(),
            input=input,
            output=output,
            category=category,
            quality_score=quality_score,
            metadata=metadata or {},
        )
        
        if category not in self.examples:
            self.examples[category] = []
        
        self.examples[category].append(example)
        logger.info(f"Added few-shot example to category: {category}")
        
        return example
    
    def get_examples(
        self,
        category: str,
        limit: int = 3,
        min_quality: float = 0.7,
    ) -> List[FewShotExample]:
        """
        Get best few-shot examples for a category.
        
        Args:
            category: Example category
            limit: Maximum number of examples
            min_quality: Minimum quality score
            
        Returns:
            List of best examples
        """
        if category not in self.examples:
            return []
        
        # Filter by quality
        quality_examples = [
            ex for ex in self.examples[category]
            if ex.quality_score >= min_quality
        ]
        
        # Sort by quality score
        quality_examples.sort(key=lambda x: x.quality_score, reverse=True)
        
        return quality_examples[:limit]
    
    def build_few_shot_prompt(
        self,
        template_id: str,
        examples: List[FewShotExample],
        **variables,
    ) -> str:
        """
        Build prompt with few-shot examples.
        
        Args:
            template_id: Template to use
            examples: Few-shot examples to include
            **variables: Template variables
            
        Returns:
            Complete prompt with examples
        """
        if template_id not in self.templates:
            raise ValueError(f"Template not found: {template_id}")
        
        template = self.templates[template_id]
        
        # Build few-shot section
        few_shot_section = ""
        if examples:
            few_shot_section = "Here are some examples:\n\n"
            for i, example in enumerate(examples, 1):
                few_shot_section += f"Example {i}:\n"
                few_shot_section += f"Input: {example.input}\n"
                few_shot_section += f"Output: {example.output}\n\n"
        
        # Format main template
        main_prompt = template.format(**variables)
        
        # Combine
        complete_prompt = few_shot_section + main_prompt
        
        return complete_prompt
    
    def record_template_usage(
        self,
        template_id: str,
        success: bool,
        output_quality: Optional[float] = None,
        latency_ms: float = 0.0,
    ):
        """Record template usage metrics."""
        if template_id not in self.templates:
            return
        
        template = self.templates[template_id]
        template.total_uses += 1
        
        if success:
            template.successful_uses += 1
        
        # Update running averages
        n = template.total_uses
        
        template.avg_latency_ms = (
            (template.avg_latency_ms * (n - 1) + latency_ms) / n
        )
        
        if output_quality is not None:
            template.avg_output_quality = (
                (template.avg_output_quality * (n - 1) + output_quality) / n
            )
    
    def get_best_template(self, category: str) -> Optional[PromptTemplate]:
        """Get best performing template for a category."""
        category_templates = [
            t for t in self.templates.values()
            if t.category == category and t.total_uses > 0
        ]
        
        if not category_templates:
            return None
        
        # Sort by composite score: quality (70%) + success rate (30%)
        category_templates.sort(
            key=lambda t: (t.avg_output_quality * 0.7 + t.success_rate * 0.3),
            reverse=True
        )
        
        return category_templates[0]
    
    def optimize_template(
        self,
        template_id: str,
        feedback: List[Dict[str, Any]],
    ) -> PromptTemplate:
        """
        Optimize template based on feedback.
        
        Args:
            template_id: Template to optimize
            feedback: List of feedback items with 'input', 'output', 'quality'
            
        Returns:
            Optimized template (new version)
        """
        if template_id not in self.templates:
            raise ValueError(f"Template not found: {template_id}")
        
        original = self.templates[template_id]
        
        # Simple optimization: add successful examples as few-shot
        high_quality_feedback = [
            f for f in feedback
            if f.get('quality', 0) >= 0.8
        ]
        
        for item in high_quality_feedback:
            self.add_example(
                input=item.get('input', ''),
                output=item.get('output', ''),
                category=original.category,
                quality_score=item.get('quality', 1.0),
            )
        
        # Create new version with updated description
        new_template = self.create_template(
            name=f"{original.name} v2",
            template=original.template,
            description=f"{original.description} (optimized)",
            variables=original.variables,
            category=original.category,
            tags=original.tags + ['optimized'],
        )
        
        logger.info(f"Created optimized template version: {new_template.name}")
        
        return new_template
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get optimizer statistics."""
        total_examples = sum(len(exs) for exs in self.examples.values())
        
        return {
            'total_templates': len(self.templates),
            'total_examples': total_examples,
            'categories': list(self.examples.keys()),
            'avg_template_quality': (
                sum(t.avg_output_quality for t in self.templates.values()) /
                len(self.templates) if self.templates else 0.0
            ),
        }
    
    def list_templates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all templates, optionally filtered by category."""
        templates = self.templates.values()
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        return [t.to_dict() for t in templates]


# ============================================================================
# Singleton Instance
# ============================================================================

prompt_optimizer = PromptOptimizer()
