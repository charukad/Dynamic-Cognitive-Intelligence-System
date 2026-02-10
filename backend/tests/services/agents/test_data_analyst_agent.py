"""
Unit Tests for Data Analyst Agent

Tests all capabilities:
- Data profiling
- Statistical analysis
- Visualization
- SQL generation
- Anomaly detection
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, AsyncMock, patch

from src.services.agents.data_analyst_agent import DataAnalystAgent


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def agent():
    """Create Data Analyst Agent instance"""
    return DataAnalystAgent()


@pytest.fixture
def sample_data():
    """Create sample dataset for testing"""
    np.random.seed(42)
    return pd.DataFrame({
        'numeric_col': np.random.normal(100, 15, 100),
        'category_col': np.random.choice(['A', 'B', 'C'], 100),
        'text_col': ['text_' + str(i) for i in range(100)],
        'null_col': [None if i % 10 == 0 else i for i in range(100)]
    })


# ============================================================================
# Data Profiling Tests
# ============================================================================

class TestDataProfiling:
    """Test data profiling capabilities"""
    
    @pytest.mark.asyncio
    async def test_basic_profiling(self, agent, sample_data):
        """Test basic data profiling"""
        result = await agent.profile_data(sample_data)
        
        assert 'num_rows' in result
        assert 'num_columns' in result
        assert result['num_rows'] == 100
        assert result['num_columns'] == 4
        
        # Check column info
        assert 'columns' in result
        assert len(result['columns']) == 4
    
    @pytest.mark.asyncio
    async def test_null_detection(self, agent, sample_data):
        """Test null value detection"""
        result = await agent.profile_data(sample_data)
        
        # null_col should have 10 nulls
        null_col_info = next(
            col for col in result['columns']
            if col['name'] == 'null_col'
        )
        
        assert null_col_info['null_count'] == 10
        assert null_col_info['null_percentage'] == 10.0
    
    @pytest.mark.asyncio
    async def test_type_detection(self, agent, sample_data):
        """Test column type detection"""
        result = await agent.profile_data(sample_data)
        
        column_types = {
            col['name']: col['type']
            for col in result['columns']
        }
        
        assert 'float' in column_types['numeric_col']
        assert 'object' in column_types['category_col']


# ============================================================================
# Statistical Analysis Tests
# ============================================================================

class TestStatisticalAnalysis:
    """Test statistical analysis capabilities"""
    
    @pytest.mark.asyncio
    async def test_t_test(self, agent):
        """Test t-test analysis"""
        # Create two samples
        group1 = np.random.normal(100, 10, 50)
        group2 = np.random.normal(110, 10, 50)
        
        result = await agent.perform_t_test(group1, group2)
        
        assert 'statistic' in result
        assert 'p_value' in result
        assert 'significant' in result
    
    @pytest.mark.asyncio
    async def test_correlation(self, agent, sample_data):
        """Test correlation analysis"""
        # Add correlated column
        sample_data['correlated'] = sample_data['numeric_col'] * 2 + np.random.normal(0, 1, 100)
        
        result = await agent.calculate_correlation(
            sample_data['numeric_col'],
            sample_data['correlated']
        )
        
        assert 'correlation' in result
        assert result['correlation'] > 0.8  # Should be highly correlated
    
    @pytest.mark.asyncio
    async def test_chi_square(self, agent, sample_data):
        """Test chi-square test"""
        result = await agent.perform_chi_square(
            sample_data['category_col'],
            sample_data['category_col']  # Same column should show no relationship
        )
        
        assert 'statistic' in result
        assert 'p_value' in result


# ============================================================================
# Visualization Tests
# ============================================================================

class TestVisualization:
    """Test visualization generation"""
    
    @pytest.mark.asyncio
    async def test_histogram(self, agent, sample_data):
        """Test histogram generation"""
        result = await agent.create_visualization(
            data=sample_data,
            viz_type='histogram',
            column='numeric_col'
        )
        
        assert 'chart_data' in result
        assert result['type'] == 'histogram'
    
    @pytest.mark.asyncio
    async def test_bar_chart(self, agent, sample_data):
        """Test bar chart generation"""
        result = await agent.create_visualization(
            data=sample_data,
            viz_type='bar',
            column='category_col'
        )
        
        assert 'chart_data' in result
        assert result['type'] == 'bar'
    
    @pytest.mark.asyncio
    async def test_scatter_plot(self, agent, sample_data):
        """Test scatter plot generation"""
        sample_data['y_col'] = np.random.normal(50, 10, 100)
        
        result = await agent.create_visualization(
            data=sample_data,
            viz_type='scatter',
            x_column='numeric_col',
            y_column='y_col'
        )
        
        assert 'chart_data' in result
        assert result['type'] == 'scatter'


# ============================================================================
# SQL Generation Tests
# ============================================================================

class TestSQLGeneration:
    """Test SQL query generation"""
    
    @pytest.mark.asyncio
    async def test_simple_select(self, agent):
        """Test simple SELECT query generation"""
        query = "show me all users"
        
        result = await agent.generate_sql(
            query=query,
            schema={'users': ['id', 'name', 'email']}
        )
        
        assert 'SELECT' in result['sql'].upper()
        assert 'users' in result['sql'].lower()
    
    @pytest.mark.asyncio
    async def test_filter_query(self, agent):
        """Test query with WHERE clause"""
        query = "find users where age > 25"
        
        result = await agent.generate_sql(
            query=query,
            schema={'users': ['id', 'name', 'age']}
        )
        
        assert 'WHERE' in result['sql'].upper()
        assert 'age' in result['sql'].lower()
    
    @pytest.mark.asyncio
    async def test_join_query(self, agent):
        """Test query with JOIN"""
        query = "show user orders"
        
        result = await agent.generate_sql(
            query=query,
            schema={
                'users': ['id', 'name'],
                'orders': ['id', 'user_id', 'total']
            }
        )
        
        assert 'JOIN' in result['sql'].upper()


# ============================================================================
# Anomaly Detection Tests
# ============================================================================

class TestAnomalyDetection:
    """Test anomaly detection"""
    
    @pytest.mark.asyncio
    async def test_iqr_method(self, agent):
        """Test IQR-based anomaly detection"""
        # Create data with outliers
        data = np.concatenate([
            np.random.normal(100, 10, 95),
            np.array([200, 250, 300, 350, 400])  # Outliers
        ])
        
        result = await agent.detect_anomalies(
            data=data,
            method='iqr'
        )
        
        assert 'anomalies' in result
        assert len(result['anomaly_indices']) > 0
    
    @pytest.mark.asyncio
    async def test_zscore_method(self, agent):
        """Test Z-score anomaly detection"""
        data = np.concatenate([
            np.random.normal(100, 10, 95),
            np.array([200, 250, 300, 350, 400])
        ])
        
        result = await agent.detect_anomalies(
            data=data,
            method='zscore',
            threshold=3.0
        )
        
        assert 'anomalies' in result
        assert len(result['anomaly_indices']) > 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Test end-to-end workflows"""
    
    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self, agent, sample_data):
        """Test complete analysis workflow"""
        # 1. Profile data
        profile = await agent.profile_data(sample_data)
        assert profile is not None
        
        # 2. Create visualization
        viz = await agent.create_visualization(
            data=sample_data,
            viz_type='histogram',
            column='numeric_col'
        )
        assert viz is not None
        
        # 3. Detect anomalies
        anomalies = await agent.detect_anomalies(
            data=sample_data['numeric_col'].values,
            method='iqr'
        )
        assert anomalies is not None


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling"""
    
    @pytest.mark.asyncio
    async def test_empty_data(self, agent):
        """Test handling of empty dataset"""
        empty_df = pd.DataFrame()
        
        with pytest.raises(ValueError):
            await agent.profile_data(empty_df)
    
    @pytest.mark.asyncio
    async def test_invalid_column(self, agent, sample_data):
        """Test invalid column name"""
        with pytest.raises(KeyError):
            await agent.create_visualization(
                data=sample_data,
                viz_type='histogram',
                column='nonexistent_column'
            )
