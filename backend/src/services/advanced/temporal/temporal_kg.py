"""
Temporal Knowledge Graphs

Time-aware knowledge representation enabling:
- Temporal reasoning (before, after, during, overlaps)
- Event timeline construction
- Temporal queries
- Historical knowledge tracking
- Validity periods for facts
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from src.core import get_logger

logger = get_logger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class TemporalRelation(Enum):
    """Allen's interval algebra relations."""
    BEFORE = "before"
    AFTER = "after"
    DURING = "during"
    OVERLAPS = "overlaps"
    MEETS = "meets"
    STARTS = "starts"
    FINISHES = "finishes"
    EQUALS = "equals"


@dataclass
class TimeInterval:
    """Time interval with start and end."""
    
    start: datetime
    end: Optional[datetime] = None  # None = ongoing
    
    def duration(self) -> Optional[timedelta]:
        """Get interval duration."""
        if self.end is None:
            return None
        return self.end - self.start
    
    def is_ongoing(self) -> bool:
        """Check if interval is still ongoing."""
        return self.end is None
    
    def contains(self, timestamp: datetime) -> bool:
        """Check if timestamp is within interval."""
        if timestamp < self.start:
            return False
        if self.end and timestamp > self.end:
            return False
        return True
    
    def relation_to(self, other: 'TimeInterval') -> TemporalRelation:
        """Determine Allen's interval relation to another interval."""
        # Before: this.end < other.start
        if self.end and self.end < other.start:
            return TemporalRelation.BEFORE
        
        # After: this.start > other.end
        if other.end and self.start > other.end:
            return TemporalRelation.AFTER
        
        # Equals: same start and end
        if self.start == other.start and self.end == other.end:
            return TemporalRelation.EQUALS
        
        # During: this is fully contained in other
        if self.start >= other.start and (self.end and other.end and self.end <= other.end):
            return TemporalRelation.DURING
        
        # Overlaps: partial overlap
        if self.start < other.start and (self.end and self.end > other.start):
            return TemporalRelation.OVERLAPS
        
        # Default
        return TemporalRelation.OVERLAPS


@dataclass
class TemporalFact:
    """Fact with temporal validity."""
    
    id: UUID
    subject: str
    predicate: str
    object: str
    valid_time: TimeInterval
    confidence: float = 1.0
    source: str = "system"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'subject': self.subject,
            'predicate': self.predicate,
            'object': self.object,
            'valid_start': self.valid_time.start.isoformat(),
            'valid_end': self.valid_time.end.isoformat() if self.valid_time.end else None,
            'confidence': self.confidence,
            'source': self.source,
        }
    
    def is_valid_at(self, timestamp: datetime) -> bool:
        """Check if fact is valid at given time."""
        return self.valid_time.contains(timestamp)


@dataclass
class TemporalEvent:
    """Event occurring at a specific time."""
    
    id: UUID
    name: str
    description: str
    time_interval: TimeInterval
    event_type: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'start_time': self.time_interval.start.isoformat(),
            'end_time': self.time_interval.end.isoformat() if self.time_interval.end else None,
            'event_type': self.event_type,
            'metadata': self.metadata,
        }


# ============================================================================
# Temporal Knowledge Graph
# ============================================================================

class TemporalKnowledgeGraph:
    """
    Time-aware knowledge graph.
    
    Features:
    - Facts with validity periods
    - Temporal reasoning and queries
    - Event timeline construction
    - Historical state reconstruction
    """
    
    def __init__(self):
        """Initialize temporal knowledge graph."""
        self.facts: Dict[str, TemporalFact] = {}
        self.events: Dict[str, TemporalEvent] = {}
        
        logger.info("Initialized TemporalKnowledgeGraph")
    
    def add_fact(
        self,
        subject: str,
        predicate: str,
        obj: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        confidence: float = 1.0,
    ) -> TemporalFact:
        """
        Add temporal fact to graph.
        
        Args:
            subject: Subject entity
            predicate: Relationship/property
            obj: Object entity/value
            start_time: Validity start time
            end_time: Validity end time (None = ongoing)
            confidence: Confidence score
            
        Returns:
            Created temporal fact
        """
        fact = TemporalFact(
            id=uuid4(),
            subject=subject,
            predicate=predicate,
            object=obj,
            valid_time=TimeInterval(start=start_time, end=end_time),
            confidence=confidence,
        )
        
        self.facts[str(fact.id)] = fact
        logger.debug(f"Added fact: {subject} {predicate} {obj} [{start_time}→{end_time}]")
        
        return fact
    
    def add_event(
        self,
        name: str,
        description: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        event_type: str = "generic",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TemporalEvent:
        """Add temporal event."""
        event = TemporalEvent(
            id=uuid4(),
            name=name,
            description=description,
            time_interval=TimeInterval(start=start_time, end=end_time),
            event_type=event_type,
            metadata=metadata or {},
        )
        
        self.events[str(event.id)] = event
        logger.debug(f"Added event: {name} at {start_time}")
        
        return event
    
    def query_at_time(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> List[TemporalFact]:
        """
        Query facts valid at specific time.
        
        Args:
            subject: Filter by subject (None = any)
            predicate: Filter by predicate (None = any)
            timestamp: Query timestamp (None = now)
            
        Returns:
            List of valid facts
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        results = []
        
        for fact in self.facts.values():
            # Check temporal validity
            if not fact.is_valid_at(timestamp):
                continue
            
            # Check filters
            if subject and fact.subject != subject:
                continue
            if predicate and fact.predicate != predicate:
                continue
            
            results.append(fact)
        
        logger.debug(f"Query at {timestamp}: found {len(results)} facts")
        return results
    
    def query_between_times(
        self,
        start: datetime,
        end: datetime,
        subject: Optional[str] = None,
    ) -> List[TemporalFact]:
        """Query facts valid during time range."""
        results = []
        query_interval = TimeInterval(start=start, end=end)
        
        for fact in self.facts.values():
            # Check if fact's validity overlaps with query range
            if self._intervals_overlap(fact.valid_time, query_interval):
                if subject is None or fact.subject == subject:
                    results.append(fact)
        
        return results
    
    def get_timeline(
        self,
        start: datetime,
        end: datetime,
        entity: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Construct timeline of events and fact changes.
        
        Args:
            start: Timeline start
            end: Timeline end
            entity: Filter by entity (None = all)
            
        Returns:
            Chronological list of timeline items
        """
        timeline_items = []
        
        # Add events
        for event in self.events.values():
            if event.time_interval.start >= start and event.time_interval.start <= end:
                if entity is None or entity in event.description:
                    timeline_items.append({
                        'type': 'event',
                        'timestamp': event.time_interval.start,
                        'name': event.name,
                        'description': event.description,
                        'event_type': event.event_type,
                    })
        
        # Add fact changes (start/end of validity)
        for fact in self.facts.values():
            if entity is None or fact.subject == entity or fact.object == entity:
                # Fact became valid
                if fact.valid_time.start >= start and fact.valid_time.start <= end:
                    timeline_items.append({
                        'type': 'fact_start',
                        'timestamp': fact.valid_time.start,
                        'description': f"{fact.subject} {fact.predicate} {fact.object}",
                        'confidence': fact.confidence,
                    })
                
                # Fact became invalid
                if fact.valid_time.end and fact.valid_time.end >= start and fact.valid_time.end <= end:
                    timeline_items.append({
                        'type': 'fact_end',
                        'timestamp': fact.valid_time.end,
                        'description': f"{fact.subject} {fact.predicate} {fact.object} (ended)",
                    })
        
        # Sort by timestamp
        timeline_items.sort(key=lambda x: x['timestamp'])
        
        logger.info(f"Generated timeline: {len(timeline_items)} items")
        return timeline_items
    
    def temporal_reasoning(
        self,
        event1_name: str,
        event2_name: str,
    ) -> Optional[TemporalRelation]:
        """
        Reason about temporal relationship between events.
        
        Args:
            event1_name: First event name
            event2_name: Second event name
            
        Returns:
            Temporal relation or None if events not found
        """
        # Find events
        event1 = next((e for e in self.events.values() if e.name == event1_name), None)
        event2 = next((e for e in self.events.values() if e.name == event2_name), None)
        
        if not event1 or not event2:
            return None
        
        return event1.time_interval.relation_to(event2.time_interval)
    
    def reconstruct_state_at(
        self,
        entity: str,
        timestamp: datetime,
    ) -> Dict[str, Any]:
        """
        Reconstruct entity state at given time.
        
        Args:
            entity: Entity to reconstruct
            timestamp: Point in time
            
        Returns:
            Entity state (properties and relationships)
        """
        state = {'entity': entity, 'timestamp': timestamp.isoformat(), 'properties': {}}
        
        # Get all facts about entity valid at timestamp
        relevant_facts = self.query_at_time(subject=entity, timestamp=timestamp)
        
        for fact in relevant_facts:
            state['properties'][fact.predicate] = {
                'value': fact.object,
                'confidence': fact.confidence,
            }
        
        return state
    
    def _intervals_overlap(self, int1: TimeInterval, int2: TimeInterval) -> bool:
        """Check if two time intervals overlap."""
        # If either interval is ongoing, check if starts overlap
        if int1.is_ongoing() or int2.is_ongoing():
            return int1.start <= (int2.end or datetime.max) and int2.start <= datetime.max
        
        # Both have end times
        return int1.start <= int2.end and int2.start <= int1.end
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get temporal graph statistics."""
        ongoing_facts = sum(1 for f in self.facts.values() if f.valid_time.is_ongoing())
        ongoing_events = sum(1 for e in self.events.values() if e.time_interval.is_ongoing())
        
        return {
            'total_facts': len(self.facts),
            'total_events': len(self.events),
            'ongoing_facts': ongoing_facts,
            'ongoing_events': ongoing_events,
            'avg_fact_confidence': (
                sum(f.confidence for f in self.facts.values()) /
                len(self.facts) if self.facts else 0.0
            ),
        }


# ============================================================================
# Singleton Instance
# ============================================================================

temporal_kg = TemporalKnowledgeGraph()
