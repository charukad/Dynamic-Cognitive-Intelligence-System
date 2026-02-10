"""Task API endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.domain.models import Task, TaskPriority, TaskStatus
from src.infrastructure.repositories import agent_repository, task_repository
from src.schemas import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_data: TaskCreate) -> TaskResponse:
    """
    Create a new task.

    Args:
        task_data: Task creation data

    Returns:
        Created task

    Raises:
        HTTPException: If validation fails
    """
    try:
        priority = TaskPriority(task_data.priority)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid priority. Must be one of: {[p.value for p in TaskPriority]}",
        )

    task = Task(
        description=task_data.description,
        priority=priority,
        parent_task_id=task_data.parent_task_id,
        input_data=task_data.input_data,
        context=task_data.context,
        metadata=task_data.metadata,
    )

    created_task = await task_repository.create(task)
    return TaskResponse.model_validate(created_task)


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(skip: int = 0, limit: int = 100) -> List[TaskResponse]:
    """
    List all tasks with pagination.

    Args:
        skip: Number of items to skip
        limit: Maximum number of items to return

    Returns:
        List of tasks
    """
    tasks = await task_repository.list(skip=skip, limit=limit)
    return [TaskResponse.model_validate(task) for task in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: UUID) -> TaskResponse:
    """
    Get task by ID.

    Args:
        task_id: Task UUID

    Returns:
        Task details

    Raises:
        HTTPException: If task not found
    """
    task = await task_repository.get_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    return TaskResponse.model_validate(task)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: UUID, task_data: TaskUpdate) -> TaskResponse:
    """
    Update task.

    Args:
        task_id: Task UUID
        task_data: Update data

    Returns:
        Updated task

    Raises:
        HTTPException: If task not found or validation fails
    """
    task = await task_repository.get_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    # Update fields
    if task_data.status is not None:
        try:
            task.status = TaskStatus(task_data.status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {[s.value for s in TaskStatus]}",
            )
    if task_data.priority is not None:
        try:
            task.priority = TaskPriority(task_data.priority)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority. Must be one of: {[p.value for p in TaskPriority]}",
            )
    if task_data.assigned_agent_id is not None:
        # Verify agent exists
        agent = await agent_repository.get_by_id(task_data.assigned_agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {task_data.assigned_agent_id} not found",
            )
        task.assigned_agent_id = task_data.assigned_agent_id
    if task_data.output_data is not None:
        task.output_data = task_data.output_data
    if task_data.error_message is not None:
        task.error_message = task_data.error_message
    if task_data.context is not None:
        task.context.update(task_data.context)
    if task_data.metadata is not None:
        task.metadata.update(task_data.metadata)

    updated_task = await task_repository.update(task)
    return TaskResponse.model_validate(updated_task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: UUID) -> None:
    """
    Delete task.

    Args:
        task_id: Task UUID

    Raises:
        HTTPException: If task not found
    """
    deleted = await task_repository.delete(task_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )


@router.get("/status/{status}", response_model=List[TaskResponse])
async def get_tasks_by_status(status: str) -> List[TaskResponse]:
    """
    Get tasks by status.

    Args:
        status: Task status

    Returns:
        List of tasks with the specified status
    """
    tasks = await task_repository.get_by_status(status)
    return [TaskResponse.model_validate(task) for task in tasks]


@router.get("/agent/{agent_id}", response_model=List[TaskResponse])
async def get_tasks_by_agent(agent_id: UUID) -> List[TaskResponse]:
    """
    Get tasks assigned to an agent.

    Args:
        agent_id: Agent UUID

    Returns:
        List of tasks assigned to the agent
    """
    tasks = await task_repository.get_by_agent(agent_id)
    return [TaskResponse.model_validate(task) for task in tasks]


@router.post("/{task_id}/assign/{agent_id}", response_model=TaskResponse)
async def assign_task_to_agent(task_id: UUID, agent_id: UUID) -> TaskResponse:
    """
    Assign task to agent.

    Args:
        task_id: Task UUID
        agent_id: Agent UUID

    Returns:
        Updated task

    Raises:
        HTTPException: If task or agent not found
    """
    task = await task_repository.get_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    agent = await agent_repository.get_by_id(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    task.assign_to(agent_id)
    updated_task = await task_repository.update(task)
    return TaskResponse.model_validate(updated_task)
