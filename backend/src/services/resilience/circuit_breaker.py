"""
Circuit Breaker Pattern for Resilience

Prevents cascading failures by:
- Detecting failures and opening circuit
- Failing fast when circuit is open
- Automatically recovering when stable
- Tracking failure rates and recovery
"""

import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, Optional

from src.core import get_logger

logger = get_logger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitStats:
    """Circuit breaker statistics."""
    
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0  # Calls rejected while open
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    
    @property
    def failure_rate(self) -> float:
        """Calculate current failure rate."""
        if self.total_calls == 0:
            return 0.0
        return self.failed_calls / self.total_calls
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        return 1.0 - self.failure_rate
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_calls': self.total_calls,
            'successful_calls': self.successful_calls,
            'failed_calls': self.failed_calls,
            'rejected_calls': self.rejected_calls,
            'failure_rate': self.failure_rate,
            'success_rate': self.success_rate,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'last_success_time': self.last_success_time.isoformat() if self.last_success_time else None,
        }


# ============================================================================
# Circuit Breaker
# ============================================================================

class CircuitBreaker:
    """
    Circuit breaker for fault tolerance.
    
    States:
    - CLOSED: Normal operation, failures counted
    - OPEN: Failing fast, not executing function
    - HALF_OPEN: Testing if system recovered
    
    Transition logic:
    - CLOSED → OPEN: When failure_threshold exceeded
    - OPEN → HALF_OPEN: After recovery_timeout
    - HALF_OPEN → CLOSED: After success_threshold successes
    - HALF_OPEN → OPEN: On any failure
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
        timeout: int = 30,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds before trying to recover (OPEN → HALF_OPEN)
            success_threshold: Successes needed in HALF_OPEN to close circuit
            timeout: Timeout in seconds for individual calls
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.timeout = timeout
        
        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()
        self.consecutive_successes = 0
        self.consecutive_failures = 0
        self.opened_at: Optional[datetime] = None
        
        self._lock = Lock()
        
        logger.info(
            f"Initialized CircuitBreaker: "
            f"failure_threshold={failure_threshold}, "
            f"recovery_timeout={recovery_timeout}s"
        )
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpen: When circuit is open
            Exception: Original exception if function fails
        """
        with self._lock:
            # Check if circuit should transition
            self._check_state_transition()
            
            # If open, reject immediately
            if self.state == CircuitState.OPEN:
                self.stats.rejected_calls += 1
                raise CircuitBreakerOpen(
                    f"Circuit breaker is OPEN. "
                    f"Will retry in {self._time_until_recovery():.0f}s"
                )
        
        # Execute function
        try:
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Check timeout
            if duration > self.timeout:
                raise TimeoutError(f"Call exceeded timeout ({duration:.2f}s > {self.timeout}s)")
            
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call."""
        with self._lock:
            self.stats.total_calls += 1
            self.stats.successful_calls += 1
            self.stats.last_success_time = datetime.now()
            
            self.consecutive_successes += 1
            self.consecutive_failures = 0
            
            # If in HALF_OPEN, check if we can close
            if self.state == CircuitState.HALF_OPEN:
                if self.consecutive_successes >= self.success_threshold:
                    self._transition_to_closed()
    
    def _on_failure(self):
        """Handle failed call."""
        with self._lock:
            self.stats.total_calls += 1
            self.stats.failed_calls += 1
            self.stats.last_failure_time = datetime.now()
            
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            
            # Check if we should open circuit
            if self.state == CircuitState.CLOSED:
                if self.consecutive_failures >= self.failure_threshold:
                    self._transition_to_open()
            elif self.state == CircuitState.HALF_OPEN:
                # Any failure in HALF_OPEN returns to OPEN
                self._transition_to_open()
    
    def _check_state_transition(self):
        """Check if state should transition."""
        if self.state == CircuitState.OPEN:
            # Check if enough time passed to try recovery
            if self.opened_at and datetime.now() - self.opened_at >= timedelta(seconds=self.recovery_timeout):
                self._transition_to_half_open()
    
    def _transition_to_open(self):
        """Transition to OPEN state."""
        self.state = CircuitState.OPEN
        self.opened_at = datetime.now()
        logger.warning(
            f"Circuit breaker OPENED: "
            f"{self.consecutive_failures} consecutive failures"
        )
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state."""
        self.state = CircuitState.HALF_OPEN
        self.consecutive_successes = 0
        logger.info("Circuit breaker entering HALF_OPEN state (testing recovery)")
    
    def _transition_to_closed(self):
        """Transition to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.consecutive_failures = 0
        self.opened_at = None
        logger.info("Circuit breaker CLOSED (recovered)")
    
    def _time_until_recovery(self) -> float:
        """Calculate seconds until recovery attempt."""
        if not self.opened_at:
            return 0.0
        
        recovery_time = self.opened_at + timedelta(seconds=self.recovery_timeout)
        return (recovery_time - datetime.now()).total_seconds()
    
    def reset(self):
        """Reset circuit breaker to initial state."""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.stats = CircuitStats()
            self.consecutive_successes = 0
            self.consecutive_failures = 0
            self.opened_at = None
            logger.info("Circuit breaker reset")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        stats_dict = self.stats.to_dict()
        stats_dict['state'] = self.state.value
        stats_dict['consecutive_successes'] = self.consecutive_successes
        stats_dict['consecutive_failures'] = self.consecutive_failures
        
        if self.state == CircuitState.OPEN:
            stats_dict['time_until_recovery'] = self._time_until_recovery()
        
        return stats_dict


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""
    pass


# ============================================================================
# Retry Logic with Exponential Backoff
# ============================================================================

class RetryPolicy:
    """
    Retry policy with exponential backoff.
    
    Automatically retries failed operations with increasing delays.
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
    ):
        """
        Initialize retry policy.
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            backoff_factor: Multiplier for delay after each retry
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        
        logger.info(
            f"Initialized RetryPolicy: "
            f"max_retries={max_retries}, "
            f"initial_delay={initial_delay}s"
        )
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: Last exception if all retries fail
        """
        last_exception = None
        delay = self.initial_delay
        
        for attempt in range(self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"Retry succeeded on attempt {attempt + 1}")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * self.backoff_factor, self.max_delay)
                else:
                    logger.error(f"All {self.max_retries + 1} attempts failed")
        
        raise last_exception


# ============================================================================
# Singleton Instances
# ============================================================================

# Create default instances for common use cases
default_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    success_threshold=2,
)

default_retry_policy = RetryPolicy(
    max_retries=3,
    initial_delay=1.0,
    backoff_factor=2.0,
)

# Circuit breaker registry for tracking multiple service breakers
circuit_breaker_registry: Dict[str, CircuitBreaker] = {
    'default': default_circuit_breaker,
}
