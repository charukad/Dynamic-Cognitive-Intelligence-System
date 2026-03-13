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
from src.domain.models.agent import Agent, AgentStatus, AgentType

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
    
    def __init__(
        self,
        agent_id: str = "financial_advisor",
        name: str = "Financial Advisor Agent",
        description: str = "Expert in financial analysis, portfolio optimization, and risk assessment",
    ):
        agent = Agent(
            id=agent_id,
            name=name,
            agent_type=AgentType.FINANCIAL,
            status=AgentStatus.IDLE,
            capabilities=["portfolio_analysis", "risk_assessment", "market_forecasting"],
            system_prompt=self.get_system_prompt(),
            metadata={"description": description},
        )
        super().__init__(agent=agent)
        self.specialty = "financial_analysis"

    async def process(self, task_input: dict) -> dict:
        """Process generic financial tasks."""
        action = task_input.get("action", "analyze_portfolio")

        if action == "analyze_portfolio":
            return await self.analyze_portfolio(
                portfolio=task_input.get("portfolio"),
                current_prices=task_input.get("current_prices"),
            )
        if action == "forecast_price":
            return await self.forecast_price(
                historical_data=task_input.get("historical_data", {}),
                forecast_days=task_input.get("forecast_days", 30),
            )
        if action == "optimize_allocation":
            return await self.optimize_allocation(
                assets=task_input.get("assets", {}),
                target_return=task_input.get("target_return"),
                risk_tolerance=task_input.get("risk_tolerance", "moderate"),
            )

        return {
            "status": "completed",
            "message": f"Processed financial action: {action}",
        }
    
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
        holdings: Optional[List[Holding]] = None,
        benchmark_return: float = 0.10,  # 10%
        portfolio: Optional[Dict[str, Any]] = None,
        current_prices: Optional[Dict[str, float]] = None,
    ) -> PortfolioAnalysis | Dict[str, Any]:
        """
        Comprehensive portfolio analysis.
        
        Args:
            holdings: List of portfolio holdings
            benchmark_return: Benchmark return for comparison
            
        Returns:
            Complete portfolio analysis
        """
        if portfolio is not None:
            return await self._analyze_portfolio_legacy(portfolio, current_prices)

        if not holdings:
            raise ValueError("Portfolio holdings are required")

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

    async def _analyze_portfolio_legacy(
        self,
        portfolio: Dict[str, Any],
        current_prices: Optional[Dict[str, float]],
    ) -> Dict[str, Any]:
        """Legacy dictionary-style portfolio analysis used by unit tests."""
        holdings = portfolio.get("holdings", [])
        cash = float(portfolio.get("cash", 0.0))

        if not holdings:
            raise ValueError("Portfolio must include at least one holding")
        if not current_prices:
            raise ValueError("Current prices are required")

        missing_prices = [h["symbol"] for h in holdings if h["symbol"] not in current_prices]
        if missing_prices:
            raise ValueError(f"Missing prices for symbols: {', '.join(missing_prices)}")

        position_values: List[Dict[str, Any]] = []
        total_positions_value = 0.0
        total_cost = 0.0
        total_gain_loss = 0.0

        for holding in holdings:
            symbol = holding["symbol"]
            shares = float(holding.get("shares", 0.0))
            purchase_price = float(holding.get("purchase_price", 0.0))
            current_price = float(current_prices[symbol])

            current_value = shares * current_price
            cost_basis = shares * purchase_price
            gain_loss = current_value - cost_basis

            position_values.append(
                {
                    "symbol": symbol,
                    "value": round(current_value, 2),
                    "gain_loss": round(gain_loss, 2),
                }
            )

            total_positions_value += current_value
            total_cost += cost_basis
            total_gain_loss += gain_loss

        allocation = []
        for position in position_values:
            pct = (position["value"] / total_positions_value * 100.0) if total_positions_value > 0 else 0.0
            allocation.append(
                {
                    "symbol": position["symbol"],
                    "value": position["value"],
                    "percentage": round(pct, 2),
                }
            )

        weights = np.array([row["percentage"] / 100.0 for row in allocation], dtype=float)
        hhi = float(np.sum(weights ** 2)) if weights.size else 1.0
        diversification_score = max(0.0, min(1.0, 1.0 - hhi))

        return {
            "total_value": round(total_positions_value + cash, 2),
            "total_cost": round(total_cost + cash, 2),
            "total_gain_loss": round(total_gain_loss, 2),
            "allocation": allocation,
            "diversification_score": round(diversification_score, 4),
            "cash": round(cash, 2),
        }

    async def calculate_sharpe_ratio(
        self,
        returns: np.ndarray | List[float],
        risk_free_rate: float = 0.03,
    ) -> Dict[str, float]:
        """Calculate annualized Sharpe ratio."""
        series = self._to_returns_array(returns)
        if series.size == 0:
            return {"sharpe_ratio": 0.0}

        daily_rf = risk_free_rate / 252.0
        excess = series - daily_rf
        volatility = float(np.std(excess, ddof=1)) if excess.size > 1 else 0.0
        sharpe = (float(np.mean(excess)) / volatility * np.sqrt(252.0)) if volatility > 0 else 0.0
        return {"sharpe_ratio": float(sharpe)}

    async def calculate_var(
        self,
        returns: np.ndarray | List[float],
        confidence_level: float = 0.95,
    ) -> Dict[str, float]:
        """Calculate historical Value at Risk."""
        series = self._to_returns_array(returns)
        percentile = (1.0 - confidence_level) * 100.0
        var = -float(np.percentile(series, percentile)) if series.size else 0.0
        return {"var": float(var), "confidence_level": confidence_level}

    async def calculate_beta(
        self,
        stock_returns: np.ndarray | List[float],
        market_returns: np.ndarray | List[float],
    ) -> Dict[str, float]:
        """Calculate portfolio beta relative to market series."""
        stock = self._to_returns_array(stock_returns)
        market = self._to_returns_array(market_returns)
        length = min(stock.size, market.size)
        if length < 2:
            return {"beta": 0.0}

        stock = stock[-length:]
        market = market[-length:]
        market_var = float(np.var(market, ddof=1))
        if market_var == 0:
            return {"beta": 0.0}

        covariance = float(np.cov(stock, market, ddof=1)[0, 1])
        return {"beta": float(covariance / market_var)}

    async def calculate_volatility(
        self,
        prices: np.ndarray | List[float],
    ) -> Dict[str, float]:
        """Calculate daily and annualized volatility from prices."""
        returns = self._to_returns_array(prices)
        if returns.size == 0:
            return {"volatility": 0.0, "annualized_volatility": 0.0}

        volatility = float(np.std(returns, ddof=1)) if returns.size > 1 else 0.0
        annualized = volatility * float(np.sqrt(252.0))
        return {"volatility": volatility, "annualized_volatility": annualized}

    async def calculate_drawdown(
        self,
        prices: np.ndarray | List[float],
    ) -> Dict[str, Any]:
        """Calculate maximum drawdown and rough drawdown period."""
        price_arr = np.asarray(prices, dtype=float)
        if price_arr.size == 0:
            return {"max_drawdown": 0.0, "drawdown_period": {"start": 0, "end": 0}}

        peaks = np.maximum.accumulate(price_arr)
        drawdowns = np.divide(price_arr, peaks, out=np.ones_like(price_arr), where=peaks > 0) - 1.0
        end_idx = int(np.argmin(drawdowns))
        max_drawdown = float(drawdowns[end_idx])
        start_idx = int(np.argmax(price_arr[: end_idx + 1])) if end_idx > 0 else 0

        return {
            "max_drawdown": max_drawdown,
            "drawdown_period": {"start": start_idx, "end": end_idx},
        }

    async def forecast_price(
        self,
        historical_data: Dict[str, Any],
        forecast_days: int = 30,
    ) -> Dict[str, Any]:
        """Forecast future prices using drift from historical data."""
        prices = np.asarray(historical_data.get("prices", []), dtype=float)
        if prices.size < 2:
            raise ValueError("Historical data must include at least 2 price points")

        returns = self._to_returns_array(prices)
        drift = float(np.mean(returns)) if returns.size else 0.0
        vol = float(np.std(returns, ddof=1)) if returns.size > 1 else 0.0
        last_price = float(prices[-1])

        forecast = []
        confidence_interval = []
        for day in range(1, forecast_days + 1):
            predicted = last_price * ((1.0 + drift) ** day)
            uncertainty = 1.96 * vol * np.sqrt(day / 252.0)
            lower = predicted * (1.0 - uncertainty)
            upper = predicted * (1.0 + uncertainty)
            forecast.append(round(predicted, 2))
            confidence_interval.append((round(lower, 2), round(upper, 2)))

        return {
            "forecast": forecast,
            "confidence_interval": confidence_interval,
        }

    async def analyze_trend(
        self,
        prices: np.ndarray | List[float],
    ) -> Dict[str, Any]:
        """Classify trend direction and strength from price slope."""
        series = np.asarray(prices, dtype=float)
        if series.size < 2:
            return {"trend": "neutral", "strength": 0.0}

        x = np.arange(series.size, dtype=float)
        slope = float(np.polyfit(x, series, 1)[0])
        baseline = max(float(np.mean(series)), 1e-6)
        normalized_slope = slope / baseline

        if normalized_slope > 0.0005:
            trend = "bullish"
        elif normalized_slope < -0.0005:
            trend = "bearish"
        else:
            trend = "neutral"

        strength = max(0.0, min(1.0, abs(normalized_slope) * 100.0))
        return {"trend": trend, "strength": round(strength, 4)}

    async def find_support_resistance(
        self,
        prices: np.ndarray | List[float],
    ) -> Dict[str, List[float]]:
        """Estimate support/resistance using empirical quantiles."""
        series = np.asarray(prices, dtype=float)
        if series.size == 0:
            return {"support_levels": [], "resistance_levels": []}

        support_levels = [
            round(float(np.percentile(series, 10)), 2),
            round(float(np.percentile(series, 25)), 2),
        ]
        resistance_levels = [
            round(float(np.percentile(series, 75)), 2),
            round(float(np.percentile(series, 90)), 2),
        ]
        return {"support_levels": support_levels, "resistance_levels": resistance_levels}

    async def optimize_allocation(
        self,
        assets: Dict[str, Dict[str, float]],
        target_return: Optional[float] = None,
        risk_tolerance: str = "moderate",
    ) -> Dict[str, Any]:
        """Optimize allocation by balancing expected return and risk tolerance."""
        if not assets:
            raise ValueError("Assets are required for allocation optimization")

        tolerance = (risk_tolerance or "moderate").lower()
        risk_penalty = {
            "conservative": 1.8,
            "moderate": 1.0,
            "aggressive": 0.3,
        }.get(tolerance, 1.0)

        scored = {}
        for symbol, metrics in assets.items():
            expected_return = float(metrics.get("expected_return", 0.0))
            risk = float(metrics.get("risk", 0.0))
            score = expected_return - (risk_penalty * risk)
            if target_return is not None:
                score -= abs(expected_return - target_return) * 0.1
            scored[symbol] = score

        min_score = min(scored.values())
        shifted = {symbol: score - min_score + 1e-6 for symbol, score in scored.items()}
        total = sum(shifted.values())
        if total <= 0:
            weight = 100.0 / len(shifted)
            allocations = {symbol: round(weight, 2) for symbol in shifted}
        else:
            allocations = {
                symbol: round((value / total) * 100.0, 2)
                for symbol, value in shifted.items()
            }

        drift = 100.0 - sum(allocations.values())
        first_key = next(iter(allocations))
        allocations[first_key] = round(allocations[first_key] + drift, 2)

        expected_return = sum(
            (allocations[symbol] / 100.0) * float(assets[symbol].get("expected_return", 0.0))
            for symbol in allocations
        )
        expected_risk = float(
            np.sqrt(
                sum(
                    ((allocations[symbol] / 100.0) * float(assets[symbol].get("risk", 0.0))) ** 2
                    for symbol in allocations
                )
            )
        )

        return {
            "allocations": allocations,
            "expected_return": expected_return,
            "expected_risk": expected_risk,
        }

    async def recommend_rebalancing(
        self,
        portfolio: Dict[str, Any],
        current_prices: Dict[str, float],
        target_allocation: Dict[str, float],
        threshold: float = 3.0,
    ) -> Dict[str, Any]:
        """Generate symbol-level rebalancing recommendations."""
        analysis = await self._analyze_portfolio_legacy(portfolio, current_prices)
        current_allocation = {row["symbol"]: row["percentage"] for row in analysis["allocation"]}

        trades = []
        recommendations = []
        total_positions_value = sum(row["value"] for row in analysis["allocation"])

        for symbol, target_pct in target_allocation.items():
            current_pct = current_allocation.get(symbol, 0.0)
            diff = target_pct - current_pct
            if abs(diff) < threshold:
                continue

            current_price = float(current_prices.get(symbol, 0.0))
            value_delta = total_positions_value * (diff / 100.0)
            shares_delta = (value_delta / current_price) if current_price > 0 else 0.0
            action = "buy" if diff > 0 else "sell"

            trades.append(
                {
                    "symbol": symbol,
                    "action": action,
                    "shares": round(abs(shares_delta), 4),
                    "value": round(abs(value_delta), 2),
                }
            )
            recommendations.append(
                f"{action.title()} {abs(shares_delta):.2f} shares of {symbol} to move from "
                f"{current_pct:.1f}% to {target_pct:.1f}%."
            )

        needs_rebalancing = len(trades) > 0
        if not needs_rebalancing:
            recommendations.append("Allocation is within threshold; no rebalancing needed.")

        return {
            "needs_rebalancing": needs_rebalancing,
            "recommendations": recommendations,
            "trades": trades,
            "current_allocation": current_allocation,
            "target_allocation": target_allocation,
        }

    async def validate_allocation(self, allocation: Dict[str, float]) -> Dict[str, Any]:
        """Validate that allocations are non-negative and sum to ~100%."""
        total = float(sum(allocation.values()))
        if any(value < 0 for value in allocation.values()):
            raise ValueError("Allocation values must be non-negative")
        if not 99.0 <= total <= 101.0:
            raise ValueError("Allocation must sum to 100% (+/-1%)")
        return {"is_valid": True, "total": total}

    def _to_returns_array(self, values: np.ndarray | List[float]) -> np.ndarray:
        """Convert series to returns array, interpreting large-magnitude data as prices."""
        series = np.asarray(values, dtype=float)
        series = series[~np.isnan(series)]
        if series.size == 0:
            return np.array([], dtype=float)

        if np.max(np.abs(series)) > 2.0:
            if series.size < 2:
                return np.array([], dtype=float)
            with np.errstate(divide="ignore", invalid="ignore"):
                returns = np.diff(series) / series[:-1]
        else:
            returns = series

        returns = returns[np.isfinite(returns)]
        return returns.astype(float)
    
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
