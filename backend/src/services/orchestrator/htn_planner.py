"""Hierarchical Task Network (HTN) Planner for task decomposition."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional
from uuid import UUID

from src.core import get_logger
from src.domain.models import Task, TaskPriority, TaskStatus

logger = get_logger(__name__)


class TaskType(str, Enum):
    """Types of tasks in HTN hierarchy."""
    
    PRIMITIVE = "primitive"  # Atomic task that can be executed directly
    COMPOUND = "compound"    # Complex task that must be decomposed
    GOAL = "goal"            # High-level goal/objective


@dataclass
class HTNMethod:
    """
    HTN decomposition method.
    
    Defines how to decompose a compound task into subtasks.
    """
    
    name: str
    preconditions: dict[str, Any]
    subtasks: List[dict[str, Any]]
    
    def matches(self, task_context: dict[str, Any]) -> bool:
        """
        Check if method preconditions are satisfied.
        
        Args:
            task_context: Current task context
            
        Returns:
            True if preconditions match
        """
        for key, expected_value in self.preconditions.items():
            if task_context.get(key) != expected_value:
                return False
        return True


class HTNPlanner:
    """
    Hierarchical Task Network planner for intelligent task decomposition.
    
    Breaks down complex tasks into executable subtasks using HTN planning.
    """

    def __init__(self) -> None:
        """Initialize HTN planner."""
        self.methods: dict[str, List[HTNMethod]] = {}
        self._register_default_methods()

    def _register_default_methods(self) -> None:
        """Register default decomposition methods."""
        
        # Method: Research task decomposition
        self.register_method(
            task_type="research",
            method=HTNMethod(
                name="decompose_research",
                preconditions={"type": "research"},
                subtasks=[
                    {
                        "description": "Gather background information",
                        "agent_type": "scholar",
                        "priority": "high",
                    },
                    {
                        "description": "Analyze and synthesize findings",
                        "agent_type": "logician",
                        "priority": "medium",
                    },
                    {
                        "description": "Create comprehensive report",
                        "agent_type": "scholar",
                        "priority": "medium",
                    },
                ],
            ),
        )

        # Method: Code development task decomposition
        self.register_method(
            task_type="coding",
            method=HTNMethod(
                name="decompose_coding",
                preconditions={"type": "coding"},
                subtasks=[
                    {
                        "description": "Design solution architecture",
                        "agent_type": "logician",
                        "priority": "high",
                    },
                    {
                        "description": "Implement code",
                        "agent_type": "coder",
                        "priority": "high",
                    },
                    {
                        "description": "Review and critique code",
                        "agent_type": "critic",
                        "priority": "medium",
                    },
                ],
            ),
        )

        # Method: Creative problem solving
        self.register_method(
            task_type="creative",
            method=HTNMethod(
                name="decompose_creative",
                preconditions={"type": "creative"},
                subtasks=[
                    {
                        "description": "Brainstorm creative solutions",
                        "agent_type": "creative",
                        "priority": "high",
                    },
                    {
                        "description": "Evaluate feasibility",
                        "agent_type": "critic",
                        "priority": "medium",
                    },
                    {
                        "description": "Refine and synthesize best ideas",
                        "agent_type": "executive",
                        "priority": "medium",
                    },
                ],
            ),
        )

        # Method: Analysis task
        self.register_method(
            task_type="analysis",
            method=HTNMethod(
                name="decompose_analysis",
                preconditions={"type": "analysis"},
                subtasks=[
                    {
                        "description": "Gather relevant data",
                        "agent_type": "scholar",
                        "priority": "high",
                    },
                    {
                        "description": "Perform logical analysis",
                        "agent_type": "logician",
                        "priority": "high",
                    },
                    {
                        "description": "Critique findings",
                        "agent_type": "critic",
                        "priority": "medium",
                    },
                    {
                        "description": "Synthesize conclusions",
                        "agent_type": "executive",
                        "priority": "medium",
                    },
                ],
            ),
        )

    def register_method(self, task_type: str, method: HTNMethod) -> None:
        """
        Register a decomposition method for a task type.
        
        Args:
            task_type: Type of task
            method: HTN decomposition method
        """
        if task_type not in self.methods:
            self.methods[task_type] = []
        self.methods[task_type].append(method)
        logger.info(f"Registered HTN method: {method.name} for task type: {task_type}")

    def decompose_task(self, task: Task) -> List[Task]:
        """
        Decompose a complex task into subtasks.
        
        Args:
            task: Task to decompose
            
        Returns:
            List of subtasks (empty if task is primitive)
        """
        # Check if task context indicates it's compound
        task_type = task.context.get("type", "unknown")
        
        if task_type not in self.methods:
            logger.info(f"No decomposition method for task type: {task_type}. Treating as primitive.")
            return []

        # Find matching method
        for method in self.methods[task_type]:
            if method.matches(task.context):
                logger.info(f"Decomposing task {task.id} using method: {method.name}")
                return self._create_subtasks(task, method)

        logger.info(f"No matching method found for task {task.id}. Treating as primitive.")
        return []

    def _create_subtasks(self, parent_task: Task, method: HTNMethod) -> List[Task]:
        """
        Create subtasks from HTN method.
        
        Args:
            parent_task: Parent task
            method: Decomposition method
            
        Returns:
            List of created subtasks
        """
        subtasks = []
        
        for i, subtask_spec in enumerate(method.subtasks):
            # Create subtask context
            subtask_context = {
                **parent_task.context,
                "parent_task_id": str(parent_task.id),
                "subtask_index": i,
                "total_subtasks": len(method.subtasks),
            }
            
            # Remove type to prevent recursive decomposition
            subtask_context.pop("type", None)
            
            # Create subtask
            subtask = Task(
                description=subtask_spec["description"],
                priority=TaskPriority(subtask_spec.get("priority", "medium")),
                parent_task_id=parent_task.id,
                context=subtask_context,
                metadata={
                    "agent_type_hint": subtask_spec.get("agent_type"),
                    "decomposition_method": method.name,
                },
            )
            
            subtasks.append(subtask)
            logger.debug(f"Created subtask {i+1}/{len(method.subtasks)}: {subtask.description}")

        logger.info(f"Decomposed task {parent_task.id} into {len(subtasks)} subtasks")
        return subtasks

    def is_primitive(self, task: Task) -> bool:
        """
        Check if a task is primitive (cannot be decomposed further).
        
        Args:
            task: Task to check
            
        Returns:
            True if task is primitive
        """
        task_type = task.context.get("type", "unknown")
        
        # If no methods exist for task type, it's primitive
        if task_type not in self.methods:
            return True
        
        # If no methods match, it's primitive
        for method in self.methods[task_type]:
            if method.matches(task.context):
                return False
        
        return True

    def get_task_hierarchy(self, root_task: Task, all_tasks: List[Task]) -> dict[str, Any]:
        """
        Build task hierarchy tree.
        
        Args:
            root_task: Root task
            all_tasks: All tasks in system
            
        Returns:
            Hierarchical task tree
        """
        def build_tree(task: Task) -> dict[str, Any]:
            children = [
                build_tree(t) 
                for t in all_tasks 
                if t.parent_task_id == task.id
            ]
            
            return {
                "id": str(task.id),
                "description": task.description,
                "status": task.status.value,
                "priority": task.priority.value,
                "is_primitive": self.is_primitive(task),
                "children": children,
            }
        
        return build_tree(root_task)


# Singleton instance
htn_planner = HTNPlanner()
