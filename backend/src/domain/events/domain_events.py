"""Domain events for event-driven architecture."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


@dataclass
class DomainEvent:
    """Base class for all domain events."""
    
    event_id: UUID = field(default_factory=uuid4)
    event_type: str = field(default="")
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Set event type from class name if not provided."""
        if not self.event_type:
            self.event_type = self.__class__.__name__


# Agent Events
@dataclass
class AgentCreatedEvent(DomainEvent):
    """Event fired when an agent is created."""
    
    agent_id: UUID = field(default_factory=uuid4)
    agent_name: str = ""
    agent_type: str = ""


@dataclass
class AgentStatusChangedEvent(DomainEvent):
    """Event fired when agent status changes."""
    
    agent_id: UUID = field(default_factory=uuid4)
    previous_status: str = ""
    new_status: str = ""


@dataclass
class AgentTaskAssignedEvent(DomainEvent):
    """Event fired when a task is assigned to an agent."""
    
    agent_id: UUID = field(default_factory=uuid4)
    task_id: UUID = field(default_factory=uuid4)


@dataclass
class AgentTaskCompletedEvent(DomainEvent):
    """Event fired when agent completes a task."""
    
    agent_id: UUID = field(default_factory=uuid4)
    task_id: UUID = field(default_factory=uuid4)
    result: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0


# Task Events
@dataclass
class TaskCreatedEvent(DomainEvent):
    """Event fired when a task is created."""
    
    task_id: UUID = field(default_factory=uuid4)
    task_title: str = ""
    task_type: str = ""
    priority: str = ""


@dataclass
class TaskStatusChangedEvent(DomainEvent):
    """Event fired when task status changes."""
    
    task_id: UUID = field(default_factory=uuid4)
    previous_status: str = ""
    new_status: str = ""


@dataclass
class TaskCompletedEvent(DomainEvent):
    """Event fired when a task is completed."""
    
    task_id: UUID = field(default_factory=uuid4)
    result: Dict[str, Any] = field(default_factory=dict)
    success: bool = True


@dataclass
class TaskFailedEvent(DomainEvent):
    """Event fired when a task fails."""
    
    task_id: UUID = field(default_factory=uuid4)
    error_message: str = ""
    error_type: str = ""


# Memory Events
@dataclass
class MemoryStoredEvent(DomainEvent):
    """Event fired when memory is stored."""
    
    memory_id: UUID = field(default_factory=uuid4)
    memory_type: str = ""
    session_id: Optional[str] = None


@dataclass
class MemoryRetrievedEvent(DomainEvent):
    """Event fired when memory is retrieved."""
    
    query: str = ""
    results_count: int = 0
    memory_type: str = ""


# Query Events
@dataclass
class QueryReceivedEvent(DomainEvent):
    """Event fired when a query is received."""
    
    query_id: UUID = field(default_factory=uuid4)
    query_text: str = ""
    session_id: str = ""


@dataclass
class QueryCompletedEvent(DomainEvent):
    """Event fired when a query is completed."""
    
    query_id: UUID = field(default_factory=uuid4)
    response: str = ""
    processing_time_ms: float = 0.0


class DomainEventDispatcher:
    """
    Dispatcher for domain events.
    
    Implements the Observer pattern for event-driven architecture.
    """
    
    def __init__(self):
        """Initialize event dispatcher."""
        self._handlers: Dict[str, List[Any]] = {}
    
    def subscribe(self, event_type: str, handler: Any) -> None:
        """
        Subscribe a handler to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Callable handler function
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        self._handlers[event_type].append(handler)
    
    def unsubscribe(self, event_type: str, handler: Any) -> None:
        """
        Unsubscribe a handler from an event type.
        
        Args:
            event_type: Type of event
            handler: Handler to remove
        """
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)
    
    async def dispatch(self, event: DomainEvent) -> None:
        """
        Dispatch an event to all subscribed handlers.
        
        Args:
            event: Domain event to dispatch
        """
        handlers = self._handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                if callable(handler):
                    # Handle both sync and async handlers
                    import asyncio
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
            except Exception as e:
                # Log error but continue with other handlers
                print(f"Error in event handler: {e}")
    
    def clear(self) -> None:
        """Clear all event handlers."""
        self._handlers.clear()


# Global event dispatcher instance
event_dispatcher = DomainEventDispatcher()
