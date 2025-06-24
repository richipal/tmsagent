"""
Pytest configuration and fixtures for the Data Science Multi-Agent System tests
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.data_science.agent import root_agent
from app.data_science.tools import ToolContext
from app.data_science.sub_agents import db_agent, ds_agent, bqml_agent


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def data_science_agent():
    """Fixture for the root data science agent."""
    return root_agent


@pytest.fixture
async def database_agent():
    """Fixture for the database sub-agent."""
    return db_agent


@pytest.fixture
async def analytics_agent():
    """Fixture for the analytics sub-agent."""
    return ds_agent


@pytest.fixture
async def bqml_agent_fixture():
    """Fixture for the BQML sub-agent."""
    return bqml_agent


@pytest.fixture
def tool_context():
    """Fixture for tool context."""
    return ToolContext()


@pytest.fixture
def sample_data_context():
    """Fixture with sample data context for testing."""
    return {
        "current_dataset": {
            "filename": "test_sales_data.csv",
            "shape": "1000 rows × 8 columns",
            "columns": ["customer_id", "product_id", "quantity", "price", "date"],
            "file_type": ".csv"
        },
        "schema": """
        CREATE TABLE `project.dataset.sales_data` (
            customer_id STRING,
            product_id STRING,
            quantity INT64,
            price FLOAT64,
            transaction_date DATE
        );
        """
    }


@pytest.fixture
def sample_sql_queries():
    """Fixture with sample SQL queries for testing."""
    return {
        "basic_select": "SELECT * FROM sales_data LIMIT 10;",
        "aggregation": "SELECT customer_id, SUM(quantity * price) as total_spent FROM sales_data GROUP BY customer_id;",
        "join": """
        SELECT c.customer_name, SUM(s.quantity * s.price) as total_spent
        FROM sales_data s
        JOIN customers c ON s.customer_id = c.customer_id
        GROUP BY c.customer_name;
        """
    }


@pytest.fixture
def sample_ml_requests():
    """Fixture with sample ML requests for testing."""
    return {
        "classification": "Build a model to predict customer churn",
        "regression": "Create a model to predict customer lifetime value",
        "clustering": "Segment customers based on purchase behavior",
        "time_series": "Forecast monthly sales for the next quarter"
    }


@pytest.fixture
def mock_environment_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("GOOGLE_API_KEY", "mock_api_key_for_testing")
    monkeypatch.setenv("ADK_API_KEY", "mock_adk_key_for_testing")
    monkeypatch.setenv("DEBUG", "true")


@pytest.fixture
def sample_file_upload():
    """Fixture for testing file upload scenarios."""
    return {
        "file_name": "test_dataset.csv",
        "file_size": 1024,
        "file_type": ".csv",
        "content": "customer_id,product_id,quantity,price\n1,A001,2,29.99\n2,B002,1,15.50"
    }


# Test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.slow = pytest.mark.slow