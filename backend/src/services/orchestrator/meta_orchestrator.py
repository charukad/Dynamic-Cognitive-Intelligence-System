"""Meta-orchestrator for coordinating multi-agent task execution."""

import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import UUID

from src.core import get_logger
from src.domain.models import Agent, Task, TaskStatus
from src.infrastructure.repositories import agent_repository, task_repository
from src.services.agents import agent_factory
from src.services.memory import (
    episodic_memory_service,
    knowledge_graph_service,
    embedding_pipeline,
)
from src.services.orchestrator.htn_planner import htn_planner
from src.services.orchestrator.thompson_router import thompson_router
from src.services.orchestrator.ai_enhancement_layer import (
    ai_enhancement_orchestrator,
    EnhancedResponse,
)

logger = get_logger(__name__)


class MetaOrchestrator:
    """
    Meta-orchestrator for coordinating multi-agent workflows.
    
    Integrates HTN planning, Thompson Sampling routing, and agent execution
    to handle complex multi-step tasks.
    """

    def __init__(self) -> None:
        """Initialize meta-orchestrator."""
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    async def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a user query using multi-agent orchestration with RAG.
        
        Enhancements:
        - Retrieves relevant context from ChromaDB (RAG)
        - Stores agent responses for future retrieval
        - Updates knowledge graph with new concepts
        
        Args:
            query: User query
            session_id: Optional session ID for context
            task_type: Optional task type hint for HTN decomposition
            
        Returns:
            Query result with agent responses and context
        """
        logger.info(f"Processing query with RAG: {query[:100]}...")

        # 1. Retrieve RAG context from past knowledge
        try:
            rag_context = await embedding_pipeline.build_rag_context(
                collection_name="knowledge_base",
                query=query,
                max_chunks=5,
            )
            logger.info(f"Retrieved RAG context: {len(rag_context)} chars")
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            rag_context = ""

        # Create root task with RAG context
        root_task = Task(
            description=query,
            context={
                "type": task_type or "general",
                "session_id": session_id,
                "rag_context": rag_context,  # ← Add RAG context
            },
            metadata={"is_root": True},
        )
        
        root_task = await task_repository.create(root_task)
        
        # Store in episodic memory
        await episodic_memory_service.store_memory(
            content=f"User query: {query}",
            task_id=root_task.id,
            session_id=session_id,
            tags=["user_query"],
        )

        # Check if task needs decomposition
        if not htn_planner.is_primitive(root_task):
            logger.info("Task requires decomposition")
            result = await self._execute_compound_task(root_task)
        else:
            logger.info("Task is primitive, executing directly")
            result = await self._execute_primitive_task(root_task)

        # 2. Store result in ChromaDB for future RAG
        try:
            response_text = result.get('response', result.get('result', {}).get('response', ''))
            if response_text:
                await embedding_pipeline.store_document(
                    collection_name="knowledge_base",
                    document=f"Q: {query}\nA: {response_text}",
                    metadata={
                        "type": "qa_pair",
                        "task_id": str(root_task.id),
                        "session_id": session_id or "unknown",
                    },
                )
                logger.info("Stored Q&A in knowledge base")
        except Exception as e:
            logger.error(f"Failed to store in ChromaDB: {e}")

        # 3. Update knowledge graph with concepts
        try:
            # Extract key concepts from query and response
            # (Simple keyword extraction - can be enhanced with NER)
            await self._update_knowledge_graph(
                query=query,
                response=response_text if response_text else "",
                task_id=root_task.id,
            )
        except Exception as e:
            logger.error(f"Failed to update knowledge graph: {e}")

        # Store result in episodic memory
        await episodic_memory_service.store_memory(
            content=f"Query result: {result.get('response', '')[:200]}",
            task_id=root_task.id,
            session_id=session_id,
            tags=["query_result"],
        )

        # Add RAG metadata to result
        result["rag_context_used"] = len(rag_context) > 0
        result["context_length"] = len(rag_context)

        return result

    async def process_query_stream(
        self,
        query: str,
        session_id: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Process query with streaming updates.
        
        Args:
            query: User query
            session_id: Session ID
            task_type: Task type hint
            
        Yields:
            Stream of execution updates
        """
        logger.info(f"Processing streaming query: {query[:100]}...")

        # Create root task
        root_task = Task(
            description=query,
            context={
                "type": task_type or "general",
                "session_id": session_id,
            },
            metadata={"is_root": True},
        )
        
        root_task = await task_repository.create(root_task)
        
        yield {
            "type": "task_created",
            "task_id": str(root_task.id),
            "description": root_task.description,
        }

        # Decompose if needed
        if not htn_planner.is_primitive(root_task):
            subtasks = htn_planner.decompose_task(root_task)
            
            yield {
                "type": "task_decomposed",
                "subtask_count": len(subtasks),
                "subtasks": [
                    {"description": st.description, "id": str(st.id)}
                    for st in subtasks
                ],
            }

            # Execute subtasks
            for i, subtask in enumerate(subtasks):
                subtask = await task_repository.create(subtask)
                
                yield {
                    "type": "subtask_started",
                    "subtask_index": i + 1,
                    "total_subtasks": len(subtasks),
                    "description": subtask.description,
                }

                result = await self._execute_primitive_task(subtask)
                
                yield {
                    "type": "subtask_completed",
                    "subtask_index": i + 1,
                    "result": result,
                }

            # Mark root task complete
            root_task.mark_completed({"subtasks_completed": len(subtasks)})
            await task_repository.update(root_task)
            
            yield {
                "type": "task_completed",
                "task_id": str(root_task.id),
                "status": "success",
            }
        else:
            # Execute primitive task
            result = await self._execute_primitive_task(root_task)
            
            yield {
                "type": "task_completed",
                "task_id": str(root_task.id),
                "result": result,
            }

    async def _execute_compound_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a compound task by decomposing and executing subtasks.
        
        Args:
            task: Compound task
            
        Returns:
            Aggregated results from subtasks
        """
        logger.info(f"Executing compound task: {task.description}")

        # Decompose task
        subtasks = htn_planner.decompose_task(task)
        
        if not subtasks:
            logger.warning("No subtasks created, treating as primitive")
            return await self._execute_primitive_task(task)

        # Create and execute subtasks
        results = []
        for subtask in subtasks:
            # Create subtask in repository
            created_subtask = await task_repository.create(subtask)
            
            # Execute subtask
            result = await self._execute_primitive_task(created_subtask)
            results.append(result)

        # Mark parent task as complete
        task.mark_completed({
            "subtasks_completed": len(subtasks),
            "subtask_results": results,
        })
        await task_repository.update(task)

        return {
            "task_id": str(task.id),
            "description": task.description,
            "subtasks": len(subtasks),
            "results": results,
            "status": "completed",
        }

    async def _execute_primitive_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a primitive task using agent selection and execution.
        
        Args:
            task: Primitive task
            
        Returns:
            Task execution result
        """
        logger.info(f"Executing primitive task: {task.description}")

        # Get available agents
        available_agents = await agent_repository.get_available_agents()
        
        if not available_agents:
            logger.error("No available agents")
            task.mark_failed("No available agents")
            await task_repository.update(task)
            return {
                "error": "No available agents",
                "task_id": str(task.id),
            }

        # Select agent using Thompson Sampling
        agent_type_hint = task.metadata.get("agent_type_hint")
        selected_agent = thompson_router.select_agent(
            available_agents,
            agent_type_hint=agent_type_hint,
        )

        # Assign task to agent
        task.assign_to(selected_agent.id)
        await task_repository.update(task)

        # Create agent instance and execute
        try:
            agent_instance = agent_factory.create_agent(selected_agent)
            
            task_input = {
                "problem": task.description,
                **task.input_data,
            }
            
            result = await agent_instance.execute(task_input)
            
            # Mark task as complete
            task.mark_completed(result)
            await task_repository.update(task)
            
            # Update router performance
            thompson_router.update_performance(selected_agent.id, success=True)
            
            # Update agent in repository
            await agent_repository.update(selected_agent)
            
            logger.info(f"Task {task.id} completed successfully")
            
            return {
                "task_id": str(task.id),
                "agent": selected_agent.name,
                "agent_type": selected_agent.agent_type.value,
                "result": result,
                "status": "completed",
            }
            
        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")
            
            # Mark task as failed
            task.mark_failed(str(e))
            await task_repository.update(task)
            
            # Update router performance
            thompson_router.update_performance(selected_agent.id, success=False)
            
            # Update agent in repository
            await agent_repository.update(selected_agent)
            
            return {
                "task_id": str(task.id),
                "agent": selected_agent.name,
                "error": str(e),
                "status": "failed",
            }

    async def get_task_status(self, task_id: UUID) -> Dict[str, Any]:
        """
        Get detailed task status including hierarchy.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task status information
        """
        task = await task_repository.get_by_id(task_id)
        
        if not task:
            return {"error": "Task not found"}

        # Get all tasks to build hierarchy
        all_tasks = await task_repository.list(limit=1000)
        
        hierarchy = htn_planner.get_task_hierarchy(task, all_tasks)
        
        return {
            "task": {
                "id": str(task.id),
                "description": task.description,
                "status": task.status.value,
                "priority": task.priority.value,
            },
            "hierarchy": hierarchy,
            "performance": thompson_router.get_performance_stats(),
        }


# Singleton instance
meta_orchestrator = MetaOrchestrator()
