"""
Data Analyst Agent API Routes

REST API for data analysis capabilities.
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import pandas as pd
from io import StringIO

from src.core import get_logger
from src.services.agents.data_analyst_agent import create_data_analyst_agent

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/agents/data-analyst", tags=["data-analyst"])


# ============================================================================
# Request/Response Models
# ============================================================================

class AnalyzeDataRequest(BaseModel):
    """Request to analyze dataset"""
    data_csv: str  # CSV string
    include_visualizations: bool = True
    include_statistical_tests: bool = True


class VisualizeDataRequest(BaseModel):
    """Request to generate visualization"""
    data_csv: str
    chart_type: str  # line, bar, scatter, heatmap, box, hist
    x: Optional[str] = None
    y: Optional[str] = None
    hue: Optional[str] = None
    title: Optional[str] = None


class StatisticalTestRequest(BaseModel):
    """Request for statistical test"""
    data_csv: str
    test_type: str  # ttest, anova, chi2, correlation
    params: Dict[str, str] = {}


class SQLQueryRequest(BaseModel):
    """Request to generate SQL"""
    natural_language: str
    schema: Optional[Dict[str, List[str]]] = None


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/analyze")
async def analyze_dataset(request: AnalyzeDataRequest):
    """
    Comprehensive dataset analysis.
    
    Returns:
    - Data profile (stats, nulls, dtypes)
    - Key insights
    - Recommendations
    - Visualizations (optional)
    - Statistical tests (optional)
    """
    try:
        # Parse CSV
        data = pd.read_csv(StringIO(request.data_csv))
        
        # Create agent
        agent = create_data_analyst_agent()
        
        # Analyze
        report = await agent.analyze_dataset(
            data,
            include_visualizations=request.include_visualizations,
            include_statistical_tests=request.include_statistical_tests
        )
        
        return report.dict()
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visualize")
async def generate_visualization(request: VisualizeDataRequest):
    """
    Generate data visualization.
    
    Chart types:
    - line: Line chart
    - bar: Bar chart
    - scatter: Scatter plot
    - heatmap: Correlation heatmap
    - box: Box plot
    - hist: Histogram
    """
    try:
        # Parse CSV
        data = pd.read_csv(StringIO(request.data_csv))
        
        # Create agent
        agent = create_data_analyst_agent()
        
        # Generate visualization
        viz = await agent.generate_visualization(
            data,
            viz_type=request.chart_type,
            x=request.x,
            y=request.y,
            hue=request.hue,
            title=request.title
        )
        
        return viz.dict()
        
    except Exception as e:
        logger.error(f"Visualization failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/statistical-test")
async def run_statistical_test(request: StatisticalTestRequest):
    """
    Run statistical hypothesis test.
    
    Test types:
    - ttest: Two-sample t-test
    - anova: One-way ANOVA
    - chi2: Chi-square test
    - correlation: Pearson correlation
    """
    try:
        # Parse CSV
        data = pd.read_csv(StringIO(request.data_csv))
        
        # Create agent
        agent = create_data_analyst_agent()
        
        # Run test
        result = await agent.run_statistical_test(
            data,
            test_type=request.test_type,
            **request.params
        )
        
        return result.dict()
        
    except Exception as e:
        logger.error(f"Statistical test failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-sql")
async def generate_sql_query(request: SQLQueryRequest):
    """
    Generate SQL query from natural language.
    
    Example:
    "Show me the average sales by region"
    → SELECT region, AVG(sales) FROM sales_data GROUP BY region;
    """
    try:
        # Create agent
        agent = create_data_analyst_agent()
        
        # Generate SQL
        sql = await agent.generate_sql_query(
            request.natural_language,
            schema=request.schema
        )
        
        return {"sql_query": sql}
        
    except Exception as e:
        logger.error(f"SQL generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-anomalies")
async def detect_anomalies(
    data_csv: str,
    column: str,
    method: str = "iqr"
):
    """
    Detect anomalies in numeric column.
    
    Methods:
    - iqr: Interquartile range method
    - zscore: Z-score method (>3 std dev)
    - isolation_forest: ML-based detection
    """
    try:
        # Parse CSV
        data = pd.read_csv(StringIO(data_csv))
        
        # Create agent
        agent = create_data_analyst_agent()
        
        # Detect anomalies
        result = await agent.detect_anomalies(data, column, method)
        
        return result
        
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
