"""
Unit Tests for Monitoring Metrics Collector

Tests metrics collection, aggregation, and statistics.
"""

import pytest
import time
from src.services.monitoring.metrics import (
    MetricsCollector,
    MetricType,
    Metric,
)


class TestMetricsCollector:
    """Test suite for MetricsCollector."""
    
    @pytest.fixture
    def collector(self):
        """Create fresh MetricsCollector instance."""
        return MetricsCollector(max_history=100)
    
    # ========================================================================
    # Counter Tests
    # ========================================================================
    
    def test_increment_counter(self, collector):
        """Test counter increments correctly."""
        collector.increment_counter('requests', 1.0)
        assert collector.get_counter('requests') == 1.0
        
        collector.increment_counter('requests', 2.0)
        assert collector.get_counter('requests') == 3.0
    
    def test_increment_counter_with_tags(self, collector):
        """Test counter with tags creates separate metrics."""
        collector.increment_counter('requests', 1.0, {'endpoint': '/api/v1/agents'})
        collector.increment_counter('requests', 1.0, {'endpoint': '/api/v1/tasks'})
        
        count1 = collector.get_counter('requests', {'endpoint': '/api/v1/agents'})
        count2 = collector.get_counter('requests', {'endpoint': '/api/v1/tasks'})
        
        assert count1 == 1.0
        assert count2 == 1.0
    
    def test_get_counter_nonexistent(self, collector):
        """Test getting non-existent counter returns 0."""
        assert collector.get_counter('does_not_exist') == 0.0
    
    # ========================================================================
    # Gauge Tests
    # ========================================================================
    
    def test_set_gauge(self, collector):
        """Test gauge sets value correctly."""
        collector.set_gauge('cpu_usage', 45.5)
        assert collector.get_gauge('cpu_usage') == 45.5
        
        # Setting again overwrites
        collector.set_gauge('cpu_usage', 67.2)
        assert collector.get_gauge('cpu_usage') == 67.2
    
    def test_set_gauge_with_tags(self, collector):
        """Test gauge with tags."""
        collector.set_gauge('memory_mb', 1024.0, {'service': 'api'})
        collector.set_gauge('memory_mb', 512.0, {'service': 'worker'})
        
        api_mem = collector.get_gauge('memory_mb', {'service': 'api'})
        worker_mem = collector.get_gauge('memory_mb', {'service': 'worker'})
        
        assert api_mem == 1024.0
        assert worker_mem == 512.0
    
    def test_get_gauge_nonexistent(self, collector):
        """Test getting non-existent gauge returns 0."""
        assert collector.get_gauge('does_not_exist') == 0.0
    
    # ========================================================================
    # Histogram Tests
    # ========================================================================
    
    def test_record_histogram(self, collector):
        """Test histogram records values."""
        collector.record_histogram('latency', 100.0)
        collector.record_histogram('latency', 200.0)
        collector.record_histogram('latency', 150.0)
        
        stats = collector.get_histogram_stats('latency')
        
        assert stats['count'] == 3
        assert stats['min'] == 100.0
        assert stats['max'] == 200.0
        assert stats['avg'] == 150.0
    
    def test_histogram_percentiles(self, collector):
        """Test histogram calculates percentiles correctly."""
        # Record 100 values: 1, 2, 3, ..., 100
        for i in range(1, 101):
            collector.record_histogram('values', float(i))
        
        stats = collector.get_histogram_stats('values')
        
        assert stats['p50'] == 50.0 or stats['p50'] == 51.0  # Median
        assert stats['p95'] >= 95.0  # 95th percentile
        assert stats['p99'] >= 99.0  # 99th percentile
    
    def test_histogram_with_tags(self, collector):
        """Test histogram with tags."""
        collector.record_histogram('response_time', 100.0, {'endpoint': '/api'})
        collector.record_histogram('response_time', 200.0, {'endpoint': '/api'})
        
        stats = collector.get_histogram_stats('response_time', {'endpoint': '/api'})
        assert stats['count'] == 2
        assert stats['avg'] == 150.0
    
    def test_histogram_empty(self, collector):
        """Test histogram stats for empty histogram."""
        stats = collector.get_histogram_stats('nonexistent')
        
        assert stats['count'] == 0
        assert stats['avg'] == 0
        assert stats['p50'] == 0
    
    # ========================================================================
    # Timing Context Manager Tests
    # ========================================================================
    
    def test_timing_context_manager(self, collector):
        """Test timing context manager records duration."""
        with collector.timing('operation_duration'):
            time.sleep(0.01)  # 10ms
        
        stats = collector.get_histogram_stats('operation_duration')
        
        assert stats['count'] == 1
        assert stats['avg'] >= 10.0  # At least 10ms
        assert stats['avg'] < 50.0   # But not too long
    
    def test_timing_multiple_operations(self, collector):
        """Test timing multiple operations."""
        for _ in range(3):
            with collector.timing('op'):
                time.sleep(0.01)
        
        stats = collector.get_histogram_stats('op')
        assert stats['count'] == 3
    
    # ========================================================================
    # Recent Metrics Tests
    # ========================================================================
    
    def test_get_recent_metrics(self, collector):
        """Test getting recent metrics."""
        for i in range(5):
            collector.increment_counter(f'metric_{i}', 1.0)
        
        recent = collector.get_recent_metrics('metric_0', limit=10)
        assert len(recent) <= 10
        assert all('name' in m for m in recent)
        assert all('value' in m for m in recent)
    
    def test_recent_metrics_respects_limit(self, collector):
        """Test recent metrics respects limit."""
        for _ in range(20):
            collector.increment_counter('test', 1.0)
        
        recent = collector.get_recent_metrics('test', limit=5)
        assert len(recent) <= 5
    
    # ========================================================================
    # Summary Tests
    # ========================================================================
    
    def test_get_all_metrics_summary(self, collector):
        """Test getting summary of all metrics."""
        collector.increment_counter('requests', 10.0)
        collector.set_gauge('cpu', 50.0)
        collector.record_histogram('latency', 100.0)
        
        summary = collector.get_all_metrics_summary()
        
        assert 'counters' in summary
        assert 'gauges' in summary
        assert 'histogram_stats' in summary
        assert 'total_metrics_tracked' in summary
        
        assert summary['counters']['requests'] == 10.0
        assert summary['gauges']['cpu'] == 50.0
    
    # ========================================================================
    # Thread Safety Tests (Basic)
    # ========================================================================
    
    def test_concurrent_counter_increments(self, collector):
        """Test counter increments are thread-safe."""
        import threading
        
        def increment():
            for _ in range(100):
                collector.increment_counter('concurrent_test', 1.0)
        
        threads = [threading.Thread(target=increment) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have exactly 1000 increments (10 threads * 100 increments)
        assert collector.get_counter('concurrent_test') == 1000.0


class TestMetricDataModel:
    """Test Metric data model."""
    
    def test_metric_creation(self):
        """Test creating a Metric."""
        metric = Metric(
            name='test_metric',
            value=42.0,
            metric_type=MetricType.COUNTER,
            tags={'env': 'test'},
        )
        
        assert metric.name == 'test_metric'
        assert metric.value == 42.0
        assert metric.metric_type == MetricType.COUNTER
        assert metric.tags['env'] == 'test'
    
    def test_metric_to_dict(self):
        """Test Metric serialization to dict."""
        metric = Metric(
            name='test',
            value=10.0,
            metric_type=MetricType.GAUGE,
        )
        
        data = metric.to_dict()
        
        assert data['name'] == 'test'
        assert data['value'] == 10.0
        assert data['type'] == 'gauge'
        assert 'timestamp' in data
        assert 'tags' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
