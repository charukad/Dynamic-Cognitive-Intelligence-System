"""
Financial Advisor Agent API Routes

REST API for financial analysis and investment advice.
"""

from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core import get_logger
from src.services.agents.financial_agent import (
    create_financial_advisor_agent,
    Holding
)

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/agents/financial", tags=["financial"])


# ============================================================================
# Request/Response Models
# ============================================================================

class AnalyzePortfolioRequest(BaseModel):
    """Request to analyze portfolio"""
    holdings: List[Holding]
    benchmark_return: float = 0.10  # 10%


class ForecastRequest(BaseModel):
    """Request for market forecast"""
    symbol: str
    current_price: float
    timeframe: str = "30d"  # e.g., "30d", "90d"


class RiskAssessmentRequest(BaseModel):
    """Request for risk assessment"""
    holdings: List[Holding]


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/analyze-portfolio")
async def analyze_portfolio(request: AnalyzePortfolioRequest):
    """
    Comprehensive portfolio analysis.
    
    Includes:
    - Performance metrics (returns, Sharpe ratio)
    - Asset allocation breakdown
    - Diversification score
    - Risk assessment (VaR, drawdown)
    - Rebalancing recommendations
    - Actionable insights
    
    Returns:
    - Portfolio metrics
    - Asset allocation percentages
    - Personalized recommendations
    - Rebalancing suggestions
    """
    try:
        agent = create_financial_advisor_agent()
        
        analysis = await agent.analyze_portfolio(
            holdings=request.holdings,
            benchmark_return=request.benchmark_return
        )
        
        return analysis.dict()
        
    except Exception as e:
        logger.error(f"Portfolio analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forecast")
async def forecast_market(request: ForecastRequest):
    """
    Market price forecasting.
    
    Uses:
    - Technical analysis
    - Trend identification
    - Support/resistance levels
    - Statistical models
    
    Returns:
    - Price predictions (daily)
    - Trend direction (bullish/bearish/neutral)
    - Confidence score
    - Technical levels (support/resistance)
    """
    try:
        agent = create_financial_advisor_agent()
        
        forecast = await agent.forecast_market(
            symbol=request.symbol,
            current_price=request.current_price,
            timeframe=request.timeframe
        )
        
        return forecast.dict()
        
    except Exception as e:
        logger.error(f"Market forecast failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/risk-assessment")
async def assess_risk(request: RiskAssessmentRequest):
    """
    Comprehensive risk assessment.
    
    Metrics:
    - Volatility (annualized)
    - Beta (market correlation)
    - Value at Risk (VaR 95%)
    - Maximum drawdown
    - Risk level classification
    
    Returns:
    - Risk metrics
    - Risk factors identified
    - Mitigation strategies
    - Risk level (conservative/moderate/aggressive)
    """
    try:
        agent = create_financial_advisor_agent()
        
        assessment = await agent.assess_risk(
            holdings=request.holdings
        )
        
        return assessment.dict()
        
    except Exception as e:
        logger.error(f"Risk assessment failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
