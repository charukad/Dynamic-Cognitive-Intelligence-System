"""
Production Monitoring System

Real-time metrics collection and observability:
- Performance metrics (latency, throughput, errors)
- Resource utilization (CPU, memory, connections)
- Agent-specific metrics (success rate, confidence, tasks)
- Request tracing and profiling
"""

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Deque
from uuid import UUID, uuid4

from src.core import get_logger

logger = get_logger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class MetricType(Enum):
    """Types of metrics to collect."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Metric:
    """Single metric measurement."""
    
    name: str
    value: float
    metric_type: MetricType
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'value': self.value,
            'type': self.metric_type.value,
            'tags': self.tags,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class RequestTrace:
    """Distributed trace for request."""
    
    trace_id: UUID
    span_id: UUID
    operation: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: str = "in_progress"
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_span_id: Optional[UUID] = None
    
    def finish(self):
        """Mark trace as finished."""
        self.end_time = datetime.now()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = "completed"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'trace_id': str(self.trace_id),
            'span_id': str(self.span_id),
            'operation': self.operation,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_ms': self.duration_ms,
            'status': self.status,
            'metadata': self.metadata,
            'parent_span_id': str(self.parent_span_id) if self.parent_span_id else None,
        }


# ============================================================================
# Metrics Collector
# ============================================================================

class MetricsCollector:
    """
    Prometheus-style metrics collection.
    
    Collects and aggregates metrics for monitoring dashboards.
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize metrics collector.
        
        Args:
            max_history: Maximum metrics to keep in memory
        """
        self.max_history = max_history
        self.metrics: Dict[str, Deque[Metric]] = defaultdict(lambda: deque(maxlen=max_history))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.start_time = datetime.now()
        
        self._lock = Lock()
        
        logger.info("Initialized MetricsCollector")
    
    def get_uptime_hours(self) -> float:
        """Get application uptime in hours."""
        delta = datetime.now() - self.start_time
        return delta.total_seconds() / 3600.0
    
    def increment_counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        with self._lock:
            key = self._make_key(name, tags)
            self.counters[key] += value
            
            metric = Metric(
                name=name,
                value=self.counters[key],
                metric_type=MetricType.COUNTER,
                tags=tags or {},
            )
            self.metrics[name].append(metric)
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric (current value)."""
        with self._lock:
            key = self._make_key(name, tags)
            self.gauges[key] = value
            
            metric = Metric(
                name=name,
                value=value,
                metric_type=MetricType.GAUGE,
                tags=tags or {},
            )
            self.metrics[name].append(metric)
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a value in histogram."""
        with self._lock:
            key = self._make_key(name, tags)
            self.histograms[key].append(value)
            
            # Keep only recent values
            if len(self.histograms[key]) > 100:
                self.histograms[key] = self.histograms[key][-100:]
            
            metric = Metric(
                name=name,
                value=value,
                metric_type=MetricType.HISTOGRAM,
                tags=tags or {},
            )
            self.metrics[name].append(metric)
    
    def timing(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager for timing operations."""
        return TimingContext(self, name, tags)
    
    def get_counter(self, name: str, tags: Optional[Dict[str, str]] = None) -> float:
        """Get current counter value."""
        key = self._make_key(name, tags)
        return self.counters.get(key, 0.0)
    
    def get_gauge(self, name: str, tags: Optional[Dict[str, str]] = None) -> float:
        """Get current gauge value."""
        key = self._make_key(name, tags)
        return self.gauges.get(key, 0.0)
    
    def get_histogram_stats(self, name: str, tags: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Get histogram statistics (p50, p95, p99, avg)."""
        key = self._make_key(name, tags)
        values = self.histograms.get(key, [])
        
        if not values:
            return {'count': 0, 'avg': 0, 'p50': 0, 'p95': 0, 'p99': 0}
        
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        
        return {
            'count': n,
            'avg': sum(sorted_vals) / n,
            'p50': sorted_vals[int(n * 0.5)],
            'p95': sorted_vals[int(n * 0.95)] if n > 1 else sorted_vals[0],
            'p99': sorted_vals[int(n * 0.99)] if n > 1 else sorted_vals[0],
            'min': sorted_vals[0],
            'max': sorted_vals[-1],
        }
    
    def get_recent_metrics(self, name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent metrics for a given name."""
        metrics = list(self.metrics[name])[-limit:]
        return [m.to_dict() for m in metrics]
    
    def get_all_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        return {
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'histogram_stats': {
                name: self.get_histogram_stats(name)
                for name in self.histograms.keys()
            },
            'total_metrics_tracked': len(self.metrics),
        }
    
    def _make_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """Create unique key from name and tags."""
        if not tags:
            return name
        tag_str = ','.join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{tag_str}}}"


class TimingContext:
    """Context manager for timing operations."""
    
    def __init__(self, collector: MetricsCollector, name: str, tags: Optional[Dict[str, str]]):
        self.collector = collector
        self.name = name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        self.collector.record_histogram(self.name, duration_ms, self.tags)


# ============================================================================
# Distributed Tracing
# ============================================================================

class Tracer:
    """
    Distributed tracing system for request tracking.
    
    Traces requests across multiple services/agents.
    """
    
    def __init__(self, max_traces: int = 1000):
        """Initialize tracer."""
        self.max_traces = max_traces
        self.active_traces: Dict[UUID, RequestTrace] = {}
        self.completed_traces: Deque[RequestTrace] = deque(maxlen=max_traces)
        
        self._lock = Lock()
        
        logger.info("Initialized Tracer")
    
    def start_trace(
        self,
        operation: str,
        metadata: Optional[Dict[str, Any]] = None,
        parent_span_id: Optional[UUID] = None,
    ) -> RequestTrace:
        """Start a new trace."""
        trace = RequestTrace(
            trace_id=uuid4(),
            span_id=uuid4(),
            operation=operation,
            start_time=datetime.now(),
            metadata=metadata or {},
            parent_span_id=parent_span_id,
        )
        
        with self._lock:
            self.active_traces[trace.span_id] = trace
        
        logger.debug(f"Started trace: {operation} [{trace.trace_id}]")
        return trace
    
    def finish_trace(self, span_id: UUID):
        """Finish a trace."""
        with self._lock:
            trace = self.active_traces.pop(span_id, None)
            if trace:
                trace.finish()
                self.completed_traces.append(trace)
                logger.debug(f"Finished trace: {trace.operation} [{trace.duration_ms:.2f}ms]")
    
    def get_trace(self, trace_id: UUID) -> Optional[RequestTrace]:
        """Get trace by ID."""
        # Check active
        for trace in self.active_traces.values():
            if trace.trace_id == trace_id:
                return trace
        
        # Check completed
        for trace in self.completed_traces:
            if trace.trace_id == trace_id:
                return trace
        
        return None
    
    def get_recent_traces(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent completed traces."""
        traces = list(self.completed_traces)[-limit:]
        return [t.to_dict() for t in reversed(traces)]
    
    def get_active_traces(self) -> List[Dict[str, Any]]:
        """Get currently active traces."""
        return [t.to_dict() for t in self.active_traces.values()]
    
    def trace_context(self, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """Context manager for tracing."""
        return TraceContext(self, operation, metadata)


class TraceContext:
    """Context manager for distributed tracing."""
    
    def __init__(self, tracer: Tracer, operation: str, metadata: Optional[Dict[str, Any]]):
        self.tracer = tracer
        self.operation = operation
        self.metadata = metadata
        self.trace = None
    
    def __enter__(self) -> RequestTrace:
        self.trace = self.tracer.start_trace(self.operation, self.metadata)
        return self.trace
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.trace.metadata['error'] = str(exc_val)
            self.trace.status = "error"
        self.tracer.finish_trace(self.trace.span_id)


# ============================================================================
# Singleton Instances
# ============================================================================

metrics_collector = MetricsCollector()
tracer = Tracer()
