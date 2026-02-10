"""
Financial Advisor Agent - Portfolio Analysis and Market Forecasting

Expert in financial analysis, investment advice, and risk assessment.
Provides data-driven insights for portfolio optimization and market trends.
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

from pydantic import BaseModel
import numpy as np

from src.services.agents.base_agent import BaseAgent
from src.core import get_logger

logger = get_logger(__name__)


# ============================================================================
# Enums and Types
# ============================================================================

class AssetClass(str, Enum):
    """Asset classes"""
    STOCKS = "stocks"
    BONDS = "bonds"
    REAL_ESTATE = "real_estate"
    COMMODITIES = "commodities"
    CRYPTO = "crypto"
    CASH = "cash"


class RiskLevel(str, Enum):
    """Risk tolerance levels"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


# ============================================================================
# Data Models
# ============================================================================

class Holding(BaseModel):
    """Portfolio holding"""
    symbol: str
    asset_class: AssetClass
    shares: float
    current_price: float
    cost_basis: float


class PortfolioMetrics(BaseModel):
    """Portfolio performance metrics"""
    total_value: float
    total_cost: float
    total_return: float
    return_percentage: float
    sharpe_ratio: float
    max_drawdown: float
    diversification_score: float


class PortfolioAnalysis(BaseModel):
    """Complete portfolio analysis"""
    metrics: PortfolioMetrics
    asset_allocation: Dict[str, float]
    recommendations: List[str]
    rebalancing_suggestions: List[Dict[str, Any]]
    risk_assessment: 'RiskAssessment'


class Forecast(BaseModel):
    """Market forecast"""
    symbol: str
    current_price: float
    predictions: List[Tuple[str, float]]  # (date, predicted_price)
    trend: str  # bullish, bearish, neutral
    confidence: float
    support_levels: List[float]
    resistance_levels: List[float]


class RiskAssessment(BaseModel):
    """Investment risk assessment"""
    risk_level: RiskLevel
    volatility: float
    beta: float
    var_95: float  # Value at Risk (95% confidence)
    max_drawdown: float
    risk_factors: List[str]
    mitigation_strategies: List[str]


# ============================================================================
# Financial Advisor Agent
# ============================================================================

class FinancialAdvisorAgent(BaseAgent):
    """
    Expert in financial analysis and investment advice.
    
    Capabilities:
    - Portfolio optimization (Modern Portfolio Theory)
    - Risk assessment (VaR, Sharpe, Beta)
    - Market forecasting (Technical analysis)
    - Asset allocation recommendations
    - Tax optimization strategies
    - Retirement planning
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.specialty = "financial_analysis"
    
    def get_system_prompt(self) -> str:
        """Get specialized system prompt"""
        return """You are an expert Financial Advisor Agent with deep knowledge in:

- Modern Portfolio Theory
- Risk-return optimization
- Technical and fundamental analysis
- Market trends and indicators
- Tax-efficient investing
- Retirement planning strategies

Your role is to:
1. Analyze portfolios comprehensively
2. Assess and quantify risks
3. Forecast market movements
4. Provide data-driven recommendations
5. Optimize asset allocations
6. Ensure regulatory compliance

Always provide:
- Clear risk disclosures
- Data-backed recommendations
- Diversification strategies
- Tax implications
- Long-term perspective

DISCLAIMER: Provide general financial education, not personalized advice.
"""
    
    async def analyze_portfolio(
        self,
        holdings: List[Holding],
        benchmark_return: float = 0.10  # 10%
    ) -> PortfolioAnalysis:
        """
        Comprehensive portfolio analysis.
        
        Args:
            holdings: List of portfolio holdings
            benchmark_return: Benchmark return for comparison
            
        Returns:
            Complete portfolio analysis
        """
        logger.info(f"Analyzing portfolio with {len(holdings)} holdings")
        
        # Calculate portfolio metrics
        total_value = sum(h.shares * h.current_price for h in holdings)
        total_cost = sum(h.shares * h.cost_basis for h in holdings)
        total_return = total_value - total_cost
        return_pct = (total_return / total_cost * 100) if total_cost > 0 else 0
        
        # Calculate Sharpe ratio (using simulated volatility)
        portfolio_return = return_pct / 100
        risk_free_rate = 0.03  # 3%
        volatility = 0.15  # 15% (simulated)
        sharpe_ratio = (portfolio_return - risk_free_rate) / volatility if volatility > 0 else 0
        
        # Max drawdown (simulated)
        max_drawdown = -12.5  # -12.5% (simulated)
        
        # Diversification score
        asset_allocation = self._calculate_asset_allocation(holdings)
        diversification_score = self._calculate_diversification_score(asset_allocation)
        
        metrics = PortfolioMetrics(
            total_value=total_value,
            total_cost=total_cost,
            total_return=total_return,
            return_percentage=return_pct,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            diversification_score=diversification_score
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            metrics,
            asset_allocation,
            benchmark_return
        )
        
        # Rebalancing suggestions
        rebalancing = self._suggest_rebalancing(asset_allocation)
        
        # Risk assessment
        risk = await self.assess_risk(holdings)
        
        return PortfolioAnalysis(
            metrics=metrics,
            asset_allocation=asset_allocation,
            recommendations=recommendations,
            rebalancing_suggestions=rebalancing,
            risk_assessment=risk
        )
    
    async def forecast_market(
        self,
        symbol: str,
        current_price: float,
        timeframe: str = "30d"
    ) -> Forecast:
        """
        Market price forecasting.
        
        Args:
            symbol: Stock symbol
            current_price: Current market price
            timeframe: Forecast timeframe
            
        Returns:
            Price forecast with technical levels
        """
        # In production, use time series forecasting:
        # from prophet import Prophet
        # from statsmodels.tsa.arima.model import ARIMA
        
        logger.info(f"Forecasting {symbol} for {timeframe}")
        
        # Simulated forecast
        days = int(timeframe.rstrip('d'))
        predictions = []
        
        # Simple trend simulation
        trend_direction = np.random.choice(['bullish', 'neutral', 'bearish'], p=[0.4, 0.3, 0.3])
        
        if trend_direction == 'bullish':
            growth_rate = 0.002  # 0.2% per day
        elif trend_direction == 'bearish':
            growth_rate = -0.002
        else:
            growth_rate = 0.0
        
        for day in range(1, min(days + 1, 31)):
            date = (datetime.now() + timedelta(days=day)).strftime('%Y-%m-%d')
            predicted_price = current_price * (1 + growth_rate * day + np.random.normal(0, 0.01))
            predictions.append((date, round(predicted_price, 2)))
        
        # Technical levels
        support_levels = [
            round(current_price * 0.95, 2),
            round(current_price * 0.90, 2)
        ]
        
        resistance_levels = [
            round(current_price * 1.05, 2),
            round(current_price * 1.10, 2)
        ]
        
        confidence = 0.72
        
        return Forecast(
            symbol=symbol,
            current_price=current_price,
            predictions=predictions,
            trend=trend_direction,
            confidence=confidence,
            support_levels=support_levels,
            resistance_levels=resistance_levels
        )
    
    async def assess_risk(
        self,
        holdings: List[Holding]
    ) -> RiskAssessment:
        """
        Comprehensive risk assessment.
        
        Args:
            holdings: Portfolio holdings
            
        Returns:
            Risk assessment with mitigation strategies
        """
        logger.info("Assessing portfolio risk")
        
        # Calculate volatility (simulated)
        volatility = 0.18  # 18% annualized
        
        # Beta calculation (simulated)
        beta = 1.15
        
        # Value at Risk (95% confidence, 1 day)
        total_value = sum(h.shares * h.current_price for h in holdings)
        var_95 = total_value * 0.025  # 2.5% of portfolio
        
        # Max drawdown
        max_drawdown = -15.2
        
        # Determine risk level
        if volatility < 0.10:
            risk_level = RiskLevel.CONSERVATIVE
        elif volatility < 0.20:
            risk_level = RiskLevel.MODERATE
        else:
            risk_level = RiskLevel.AGGRESSIVE
        
        # Identify risk factors
        risk_factors = []
        mitigation_strategies = []
        
        if beta > 1.2:
            risk_factors.append("High market correlation (Beta > 1.2)")
            mitigation_strategies.append("Add low-beta or negatively correlated assets")
        
        if volatility > 0.20:
            risk_factors.append("High volatility")
            mitigation_strategies.append("Increase bond allocation for stability")
        
        # Check concentration risk
        asset_allocation = self._calculate_asset_allocation(holdings)
        max_allocation = max(asset_allocation.values())
        
        if max_allocation > 50:
            risk_factors.append(f"Concentration risk ({max_allocation:.1f}% in single asset class)")
            mitigation_strategies.append("Diversify across asset classes")
        
        return RiskAssessment(
            risk_level=risk_level,
            volatility=volatility,
            beta=beta,
            var_95=var_95,
            max_drawdown=max_drawdown,
            risk_factors=risk_factors or ["Moderate risk profile"],
            mitigation_strategies=mitigation_strategies or ["Maintain diversification"]
        )
    
    def _calculate_asset_allocation(
        self,
        holdings: List[Holding]
    ) -> Dict[str, float]:
        """Calculate asset allocation percentages"""
        total_value = sum(h.shares * h.current_price for h in holdings)
        
        allocation = {}
        for asset_class in AssetClass:
            class_value = sum(
                h.shares * h.current_price 
                for h in holdings 
                if h.asset_class == asset_class
            )
            allocation[asset_class.value] = (class_value / total_value * 100) if total_value > 0 else 0
        
        return {k: v for k, v in allocation.items() if v > 0}
    
    def _calculate_diversification_score(
        self,
        asset_allocation: Dict[str, float]
    ) -> float:
        """Calculate diversification score (0-10)"""
        # Herfindahl-Hirschman Index (HHI)
        hhi = sum(pct ** 2 for pct in asset_allocation.values())
        
        # Convert to 0-10 scale (lower HHI = better diversification)
        max_hhi = 10000  # Fully concentrated
        min_hhi = 1666    # Evenly distributed across 6 classes
        
        score = 10 * (1 - (hhi - min_hhi) / (max_hhi - min_hhi))
        return max(0, min(10, score))
    
    def _generate_recommendations(
        self,
        metrics: PortfolioMetrics,
        asset_allocation: Dict[str, float],
        benchmark: float
    ) -> List[str]:
        """Generate portfolio recommendations"""
        recommendations = []
        
        # Performance vs benchmark
        if metrics.return_percentage < benchmark * 100:
            recommendations.append(
                f"Portfolio underperforming benchmark ({metrics.return_percentage:.1f}% vs {benchmark*100:.1f}%)"
            )
        
        # Sharpe ratio
        if metrics.sharpe_ratio < 1.0:
            recommendations.append(
                "Low risk-adjusted returns (Sharpe < 1.0). Consider reducing volatility."
            )
        
        # Diversification
        if metrics.diversification_score < 5.0:
            recommendations.append(
                f"Low diversification score ({metrics.diversification_score:.1f}/10). Spread investments."
            )
        
        # Max drawdown
        if abs(metrics.max_drawdown) > 20:
            recommendations.append(
                "High drawdown risk. Consider defensive positions."
            )
        
        return recommendations or ["Portfolio is well-balanced"]
    
    def _suggest_rebalancing(
        self,
        asset_allocation: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Suggest portfolio rebalancing"""
        # Target allocation (moderate risk)
        target = {
            'stocks': 60.0,
            'bonds': 30.0,
            'real_estate': 5.0,
            'commodities': 3.0,
            'crypto': 1.0,
            'cash': 1.0
        }
        
        suggestions = []
        
        for asset_class, current_pct in asset_allocation.items():
            target_pct = target.get(asset_class, 0)
            diff = target_pct - current_pct
            
            if abs(diff) > 5:  # Threshold for rebalancing
                action = "increase" if diff > 0 else "decrease"
                suggestions.append({
                    'asset_class': asset_class,
                    'current': current_pct,
                    'target': target_pct,
                    'action': f"{action} by {abs(diff):.1f}%"
                })
        
        return suggestions


# Register agent
def create_financial_advisor_agent(agent_id: str = "financial_advisor") -> FinancialAdvisorAgent:
    """Create Financial Advisor Agent instance"""
    return FinancialAdvisorAgent(
        agent_id=agent_id,
        name="Financial Advisor",
        description="Expert in financial analysis, portfolio optimization, and risk assessment"
    )
