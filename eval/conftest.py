"""
Pytest configuration for evaluation tests
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def evaluation_scenarios():
    """Standard evaluation scenarios for testing agent capabilities."""
    return {
        "sql_generation": [
            {
                "query": "Find the top 10 customers by total sales amount",
                "expected_keywords": ["SELECT", "TOP", "ORDER BY", "SUM", "GROUP BY"],
                "category": "aggregation"
            },
            {
                "query": "Get all orders from the last 30 days",
                "expected_keywords": ["SELECT", "WHERE", "DATE", "INTERVAL"],
                "category": "filtering"
            },
            {
                "query": "Calculate monthly revenue trends",
                "expected_keywords": ["SELECT", "DATE_TRUNC", "SUM", "GROUP BY"],
                "category": "time_series"
            }
        ],
        "analytics": [
            {
                "query": "Analyze correlation between customer age and purchase amount",
                "expected_keywords": ["correlation", "analysis", "statistical", "relationship"],
                "category": "statistical_analysis"
            },
            {
                "query": "Create visualizations for sales trends",
                "expected_keywords": ["plot", "chart", "visualization", "matplotlib", "seaborn"],
                "category": "visualization"
            },
            {
                "query": "Perform customer segmentation analysis",
                "expected_keywords": ["segment", "cluster", "group", "analysis"],
                "category": "segmentation"
            }
        ],
        "machine_learning": [
            {
                "query": "Build a model to predict customer churn",
                "expected_keywords": ["model", "predict", "churn", "classification", "machine learning"],
                "category": "classification"
            },
            {
                "query": "Create a recommendation system for products",
                "expected_keywords": ["recommendation", "collaborative", "model", "algorithm"],
                "category": "recommendation"
            },
            {
                "query": "Forecast sales for the next quarter",
                "expected_keywords": ["forecast", "time series", "prediction", "model"],
                "category": "forecasting"
            }
        ]
    }


@pytest.fixture
def performance_benchmarks():
    """Performance benchmarks for evaluation."""
    return {
        "response_time": {
            "excellent": 2.0,  # seconds
            "good": 5.0,
            "acceptable": 10.0
        },
        "response_length": {
            "minimum": 50,  # characters
            "optimal_min": 200,
            "optimal_max": 2000,
            "maximum": 5000
        },
        "keyword_coverage": {
            "excellent": 0.8,  # 80% of expected keywords present
            "good": 0.6,
            "acceptable": 0.4
        }
    }


@pytest.fixture
def complex_scenarios():
    """Complex multi-agent scenarios for evaluation."""
    return [
        {
            "name": "End-to-End Data Analysis",
            "description": "Complete data analysis workflow from SQL to insights",
            "query": "Analyze customer purchase patterns and build a predictive model for customer lifetime value",
            "expected_agents": ["database", "analytics", "ml"],
            "expected_workflow": [
                "data_extraction",
                "exploratory_analysis", 
                "feature_engineering",
                "model_building",
                "evaluation",
                "insights"
            ]
        },
        {
            "name": "Business Intelligence Dashboard",
            "description": "Create comprehensive business intelligence solution",
            "query": "Create a dashboard showing sales performance, customer segments, and revenue forecasts",
            "expected_agents": ["database", "analytics"],
            "expected_workflow": [
                "data_aggregation",
                "visualization_design",
                "dashboard_layout",
                "insights_summary"
            ]
        },
        {
            "name": "Real-time Analytics",
            "description": "Design real-time analytics solution",
            "query": "Set up real-time monitoring of sales metrics with automated alerts",
            "expected_agents": ["database", "analytics"],
            "expected_workflow": [
                "streaming_setup",
                "metric_calculation",
                "alert_configuration",
                "monitoring_dashboard"
            ]
        }
    ]