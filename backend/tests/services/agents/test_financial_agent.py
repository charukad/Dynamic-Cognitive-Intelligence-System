"""
Unit Tests for Financial Advisor Agent

Tests all capabilities:
- Portfolio analysis
- Market forecasting
- Risk assessment
- Asset allocation
- Rebalancing recommendations
"""

import pytest
import numpy as np
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from src.services.agents.financial_agent import FinancialAdvisorAgent


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def agent():
    """Create Financial Advisor Agent instance"""
    return FinancialAdvisorAgent()


@pytest.fixture
def sample_portfolio():
    """Sample portfolio data"""
    return {
        'holdings': [
            {'symbol': 'AAPL', 'shares': 100, 'purchase_price': 150.00},
            {'symbol': 'GOOGL', 'shares': 50, 'purchase_price': 2800.00},
            {'symbol': 'MSFT', 'shares': 75, 'purchase_price': 300.00},
            {'symbol': 'TSLA', 'shares': 30, 'purchase_price': 700.00}
        ],
        'cash': 10000.00
    }


@pytest.fixture
def sample_prices():
    """Sample current market prices"""
    return {
        'AAPL': 180.00,
        'GOOGL': 3000.00,
        'MSFT': 350.00,
        'TSLA': 800.00
    }


@pytest.fixture
def sample_historical_data():
    """Sample historical price data"""
    np.random.seed(42)
    dates = [datetime.now() - timedelta(days=i) for i in range(252, 0, -1)]  # 1 year
    
    return {
        'AAPL': {
            'dates': dates,
            'prices': np.random.normal(170, 10, 252)
        },
        'GOOGL': {
            'dates': dates,
            'prices': np.random.normal(2900, 100, 252)
        }
    }


# ============================================================================
# Portfolio Analysis Tests
# ============================================================================

class TestPortfolioAnalysis:
    """Test portfolio analysis capabilities"""
    
    @pytest.mark.asyncio
    async def test_portfolio_value_calculation(self, agent, sample_portfolio, sample_prices):
        """Test total portfolio value calculation"""
        result = await agent.analyze_portfolio(
            portfolio=sample_portfolio,
            current_prices=sample_prices
        )
        
        assert 'total_value' in result
        assert 'total_gain_loss' in result
        assert result['total_value'] > 0
    
    @pytest.mark.asyncio
    async def test_portfolio_allocation(self, agent, sample_portfolio, sample_prices):
        """Test asset allocation percentages"""
        result = await agent.analyze_portfolio(
            portfolio=sample_portfolio,
            current_prices=sample_prices
        )
        
        assert 'allocation' in result
        
        # Allocations should sum to 100%
        total_allocation = sum(h['percentage'] for h in result['allocation'])
        assert 95 <= total_allocation <= 105  # Allow small rounding errors
    
    @pytest.mark.asyncio
    async def test_sharpe_ratio(self, agent, sample_historical_data):
        """Test Sharpe ratio calculation"""
        result = await agent.calculate_sharpe_ratio(
            returns=sample_historical_data['AAPL']['prices']
        )
        
        assert 'sharpe_ratio' in result
        assert isinstance(result['sharpe_ratio'], float)
    
    @pytest.mark.asyncio
    async def test_portfolio_diversification(self, agent, sample_portfolio, sample_prices):
        """Test diversification metrics"""
        result = await agent.analyze_portfolio(
            portfolio=sample_portfolio,
            current_prices=sample_prices
        )
        
        assert 'diversification_score' in result
        assert 0 <= result['diversification_score'] <= 1


# ============================================================================
# Risk Assessment Tests
# ============================================================================

class TestRiskAssessment:
    """Test risk assessment capabilities"""
    
    @pytest.mark.asyncio
    async def test_value_at_risk(self, agent, sample_historical_data):
        """Test VaR (Value at Risk) calculation"""
        result = await agent.calculate_var(
            returns=sample_historical_data['AAPL']['prices'],
            confidence_level=0.95
        )
        
        assert 'var' in result
        assert 'confidence_level' in result
        assert result['confidence_level'] == 0.95
    
    @pytest.mark.asyncio
    async def test_beta_calculation(self, agent, sample_historical_data):
        """Test Beta calculation"""
        result = await agent.calculate_beta(
            stock_returns=sample_historical_data['AAPL']['prices'],
            market_returns=sample_historical_data['GOOGL']['prices']
        )
        
        assert 'beta' in result
        assert isinstance(result['beta'], float)
    
    @pytest.mark.asyncio
    async def test_volatility_analysis(self, agent, sample_historical_data):
        """Test volatility calculation"""
        result = await agent.calculate_volatility(
            prices=sample_historical_data['AAPL']['prices']
        )
        
        assert 'volatility' in result
        assert 'annualized_volatility' in result
        assert result['volatility'] >= 0
    
    @pytest.mark.asyncio
    async def test_drawdown_analysis(self, agent, sample_historical_data):
        """Test maximum drawdown calculation"""
        result = await agent.calculate_drawdown(
            prices=sample_historical_data['AAPL']['prices']
        )
        
        assert 'max_drawdown' in result
        assert 'drawdown_period' in result
        assert result['max_drawdown'] <= 0  # Drawdown is negative


# ============================================================================
# Market Forecasting Tests
# ============================================================================

class TestMarketForecasting:
    """Test market forecasting capabilities"""
    
    @pytest.mark.asyncio
    async def test_price_forecast(self, agent, sample_historical_data):
        """Test price forecasting"""
        result = await agent.forecast_price(
            historical_data=sample_historical_data['AAPL'],
            forecast_days=30
        )
        
        assert 'forecast' in result
        assert 'confidence_interval' in result
        assert len(result['forecast']) == 30
    
    @pytest.mark.asyncio
    async def test_trend_analysis(self, agent, sample_historical_data):
        """Test trend identification"""
        result = await agent.analyze_trend(
            prices=sample_historical_data['AAPL']['prices']
        )
        
        assert 'trend' in result  # 'bullish', 'bearish', 'neutral'
        assert 'strength' in result
        assert result['trend'] in ['bullish', 'bearish', 'neutral']
    
    @pytest.mark.asyncio
    async def test_support_resistance(self, agent, sample_historical_data):
        """Test support and resistance levels"""
        result = await agent.find_support_resistance(
            prices=sample_historical_data['AAPL']['prices']
        )
        
        assert 'support_levels' in result
        assert 'resistance_levels' in result
        assert len(result['support_levels']) > 0


# ============================================================================
# Asset Allocation Tests
# ============================================================================

class TestAssetAllocation:
    """Test asset allocation optimization"""
    
    @pytest.mark.asyncio
    async def test_optimal_allocation(self, agent):
        """Test optimal portfolio allocation"""
        assets = {
            'AAPL': {'expected_return': 0.12, 'risk': 0.18},
            'GOOGL': {'expected_return': 0.15, 'risk': 0.22},
            'MSFT': {'expected_return': 0.10, 'risk': 0.15}
        }
        
        result = await agent.optimize_allocation(
            assets=assets,
            target_return=0.12,
            risk_tolerance='moderate'
        )
        
        assert 'allocations' in result
        assert 'expected_return' in result
        assert 'expected_risk' in result
        
        # Allocations should sum to 100%
        total = sum(result['allocations'].values())
        assert 99 <= total <= 101
    
    @pytest.mark.asyncio
    async def test_risk_tolerance_levels(self, agent):
        """Test different risk tolerance levels"""
        assets = {
            'SAFE': {'expected_return': 0.05, 'risk': 0.05},
            'RISKY': {'expected_return': 0.20, 'risk': 0.30}
        }
        
        # Conservative should prefer SAFE
        conservative = await agent.optimize_allocation(
            assets=assets,
            risk_tolerance='conservative'
        )
        
        # Aggressive should prefer RISKY
        aggressive = await agent.optimize_allocation(
            assets=assets,
            risk_tolerance='aggressive'
        )
        
        assert conservative['allocations']['SAFE'] > aggressive['allocations']['SAFE']


# ============================================================================
# Rebalancing Tests
# ============================================================================

class TestRebalancing:
    """Test portfolio rebalancing"""
    
    @pytest.mark.asyncio
    async def test_rebalancing_recommendations(self, agent, sample_portfolio, sample_prices):
        """Test rebalancing recommendations"""
        target_allocation = {
            'AAPL': 25,
            'GOOGL': 25,
            'MSFT': 25,
            'TSLA': 25
        }
        
        result = await agent.recommend_rebalancing(
            portfolio=sample_portfolio,
            current_prices=sample_prices,
            target_allocation=target_allocation
        )
        
        assert 'recommendations' in result
        assert 'trades' in result
    
    @pytest.mark.asyncio
    async def test_rebalancing_threshold(self, agent, sample_portfolio, sample_prices):
        """Test rebalancing with threshold"""
        target_allocation = {
            'AAPL': 25,
            'GOOGL': 25,
            'MSFT': 25,
            'TSLA': 25
        }
        
        result = await agent.recommend_rebalancing(
            portfolio=sample_portfolio,
            current_prices=sample_prices,
            target_allocation=target_allocation,
            threshold=5.0  # Only rebalance if > 5% off target
        )
        
        assert 'needs_rebalancing' in result


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Test end-to-end workflows"""
    
    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self, agent, sample_portfolio, sample_prices, sample_historical_data):
        """Test complete financial analysis workflow"""
        # 1. Analyze portfolio
        analysis = await agent.analyze_portfolio(
            portfolio=sample_portfolio,
            current_prices=sample_prices
        )
        assert analysis is not None
        
        # 2. Assess risk
        risk = await agent.calculate_var(
            returns=sample_historical_data['AAPL']['prices']
        )
        assert risk is not None
        
        # 3. Forecast
        forecast = await agent.forecast_price(
            historical_data=sample_historical_data['AAPL'],
            forecast_days=30
        )
        assert forecast is not None


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling"""
    
    @pytest.mark.asyncio
    async def test_empty_portfolio(self, agent, sample_prices):
        """Test analysis of empty portfolio"""
        empty_portfolio = {'holdings': [], 'cash': 0}
        
        with pytest.raises(ValueError):
            await agent.analyze_portfolio(
                portfolio=empty_portfolio,
                current_prices=sample_prices
            )
    
    @pytest.mark.asyncio
    async def test_missing_prices(self, agent, sample_portfolio):
        """Test missing price data"""
        incomplete_prices = {'AAPL': 180.00}  # Missing other symbols
        
        with pytest.raises(ValueError):
            await agent.analyze_portfolio(
                portfolio=sample_portfolio,
                current_prices=incomplete_prices
            )
    
    @pytest.mark.asyncio
    async def test_invalid_allocation(self, agent):
        """Test invalid allocation percentages"""
        invalid_allocation = {
            'AAPL': 60,
            'GOOGL': 60  # Sums to 120%!
        }
        
        with pytest.raises(ValueError):
            await agent.validate_allocation(invalid_allocation)
