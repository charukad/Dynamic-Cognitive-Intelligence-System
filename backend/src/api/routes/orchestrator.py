"""Orchestrator API routes for HTN Planner visualization."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.domain.models import Task, TaskStatus
from src.services.orchestrator.htn_planner import htn_planner

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


# ============================================================================
# Response Models
# ============================================================================

class PlanNodeResponse(BaseModel):
    """Node in the execution plan tree."""
    
    id: str
    description: str
    status: str
    priority: str
    is_primitive: bool
    agent_type_hint: Optional[str] = None
    children: List['PlanNodeResponse'] = Field(default_factory=list)


class ExecutionPlanResponse(BaseModel):
    """Complete execution plan visualization data."""
    
    root_task: Optional[PlanNodeResponse] = None
    total_nodes: int
    primitive_count: int
    compound_count: int
    status_breakdown: Dict[str, int]


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/plan/demo")
async def get_demo_plan() -> Dict[str, Any]:
    """
    Get a demo execution plan for visualization testing.
    
    Returns:
        Demo task hierarchy
    """
    demo_plan = {
        "id": "demo-task-1",
        "description": "Analyze quarterly financial data",
        "status": "in_progress",
        "priority": "high",
        "is_primitive": False,
        "children": [
            {
                "id": "demo-subtask-1",
                "description": "Gather relevant data",
                "status": "completed",
                "priority": "high",
                "is_primitive": True,
            },
            {
                "id": "demo-subtask-2",
                "description": "Perform logical analysis",
                "status": "in_progress",
                "priority": "high",
                "is_primitive": True,
            },
            {
                "id": "demo-subtask-3",
                "description": "Critique findings",
                "status": "pending",
                "priority": "medium",
                "is_primitive": True,
            },
        ]
    }
    
    return {"task_hierarchy": demo_plan}


@router.get("/plan/{task_id}", response_model=ExecutionPlanResponse)
async def get_execution_plan(task_id: UUID) -> ExecutionPlanResponse:
    """
    Get the execution plan tree for visualization.
    
    Args:
        task_id: Root task ID
        
    Returns:
        Hierarchical execution plan with all subtasks
    """
    # In production, fetch tasks from database
    # For now, simulate with mock data
    
    # TODO: Replace with actual database query
    # tasks = await task_repository.get_all_for_plan(task_id)
    
    # Mock response for development
    mock_plan = PlanNodeResponse(
        id=str(task_id),
        description="Analyze quarterly financial data",
        status="in_progress",
        priority="high",
        is_primitive=False,
        children=[
            PlanNodeResponse(
                id="subtask-1",
                description="Gather relevant data",
                status="completed",
                priority="high",
                is_primitive=True,
                agent_type_hint="scholar",
            ),
            PlanNodeResponse(
                id="subtask-2",
                description="Perform logical analysis",
                status="in_progress",
                priority="high",
                is_primitive=True,
                agent_type_hint="logician",
            ),
            PlanNodeResponse(
                id="subtask-3",
                description="Critique findings",
                status="pending",
                priority="medium",
                is_primitive=True,
                agent_type_hint="critic",
            ),
        ]
    )
    
    return ExecutionPlanResponse(
        root_task=mock_plan,
        total_nodes=4,
        primitive_count=3,
        compound_count=1,
        status_breakdown={
            "completed": 1,
            "in_progress": 1,
            "pending": 2,
        }
    )


@router.get("/methods", response_model=List[Dict[str, Any]])
async def get_decomposition_methods() -> List[Dict[str, Any]]:
    """
    Get all registered HTN decomposition methods.
    
    Returns:
        List of method definitions
    """
    methods = []
    
    for task_type, method_list in htn_planner.methods.items():
        for method in method_list:
            methods.append({
                "task_type": task_type,
                "method_name": method.name,
                "preconditions": method.preconditions,
                "subtask_count": len(method.subtasks),
                "subtasks": method.subtasks,
            })
    
    return methods


@router.get("/plan/demo")
async def get_demo_plan() -> Dict[str, Any]:
    """
    Get a demo execution plan for visualization testing.
    
    Returns:
        Demo task hierarchy
    """
    demo_plan = {
        "id": "demo-task-1",
        "description": "Analyze quarterly financial data",
        "status": "in_progress",
        "priority": "high",
        "is_primitive": False,
        "children": [
            {
                "id": "demo-subtask-1",
                "description": "Gather relevant data",
                "status": "completed",
                "priority": "high",
                "is_primitive": True,
            },
            {
                "id": "demo-subtask-2",
                "description": "Perform logical analysis",
                "status": "in_progress",
                "priority": "high",
                "is_primitive": True,
            },
            {
                "id": "demo-subtask-3",
                "description": "Critique findings",
                "status": "pending",
                "priority": "medium",
                "is_primitive": True,
            },
        ]
    }
    
    return {"task_hierarchy": demo_plan}
