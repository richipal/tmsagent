"""
Tests for Sub-Agents (Database, Analytics, BQML)
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_database_agent_initialization(database_agent):
    """Test database agent initialization."""
    assert database_agent is not None
    assert hasattr(database_agent, 'model')
    assert hasattr(database_agent, 'system_prompt')


@pytest.mark.asyncio
async def test_database_agent_sql_generation(database_agent, tool_context):
    """Test SQL query generation by database agent."""
    query = "Find the top 10 customers by total sales"
    
    response = await database_agent.process_query(query, tool_context)
    
    assert isinstance(response, str)
    assert len(response) > 0
    # Check if response contains SQL-like keywords
    assert any(keyword in response.upper() for keyword in ['SELECT', 'FROM', 'GROUP BY', 'ORDER BY'])


@pytest.mark.asyncio
async def test_database_agent_with_context(database_agent, tool_context, sample_data_context):
    """Test database agent with dataset context."""
    # Add context to tool_context
    for key, value in sample_data_context.items():
        tool_context.update_state(key, value)
    
    query = "Get sales data for analysis"
    response = await database_agent.process_query(query, tool_context)
    
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_analytics_agent_initialization(analytics_agent):
    """Test analytics agent initialization."""
    assert analytics_agent is not None
    assert hasattr(analytics_agent, 'model')
    assert hasattr(analytics_agent, 'system_prompt')


@pytest.mark.asyncio
async def test_analytics_agent_statistical_analysis(analytics_agent, tool_context):
    """Test statistical analysis by analytics agent."""
    query = "Calculate correlation between customer age and purchase amount"
    
    response = await analytics_agent.process_query(query, tool_context)
    
    assert isinstance(response, str)
    assert len(response) > 0
    # Check if response contains statistical keywords
    assert any(keyword in response.lower() for keyword in ['correlation', 'analysis', 'statistical', 'data'])


@pytest.mark.asyncio
async def test_analytics_agent_visualization(analytics_agent, tool_context):
    """Test visualization recommendations by analytics agent."""
    query = "Create visualizations for sales data trends"
    
    response = await analytics_agent.process_query(query, tool_context)
    
    assert isinstance(response, str)
    assert len(response) > 0
    # Check if response contains visualization keywords
    assert any(keyword in response.lower() for keyword in ['plot', 'chart', 'graph', 'visualization'])


@pytest.mark.asyncio
async def test_bqml_agent_initialization(bqml_agent_fixture):
    """Test BQML agent initialization."""
    assert bqml_agent_fixture is not None
    assert hasattr(bqml_agent_fixture, 'model')
    assert hasattr(bqml_agent_fixture, 'system_prompt')


@pytest.mark.asyncio
async def test_bqml_agent_model_recommendation(bqml_agent_fixture, tool_context, sample_ml_requests):
    """Test ML model recommendations by BQML agent."""
    query = sample_ml_requests["classification"]
    
    response = await bqml_agent_fixture.process_query(query, tool_context)
    
    assert isinstance(response, str)
    assert len(response) > 0
    # Check if response contains ML keywords
    assert any(keyword in response.lower() for keyword in ['model', 'machine learning', 'classification', 'bqml'])


@pytest.mark.asyncio
async def test_bqml_agent_clustering(bqml_agent_fixture, tool_context, sample_ml_requests):
    """Test clustering recommendations by BQML agent."""
    query = sample_ml_requests["clustering"]
    
    response = await bqml_agent_fixture.process_query(query, tool_context)
    
    assert isinstance(response, str)
    assert len(response) > 0
    assert any(keyword in response.lower() for keyword in ['cluster', 'segment', 'kmeans'])


@pytest.mark.asyncio
async def test_database_agent_error_handling(database_agent, tool_context):
    """Test database agent error handling."""
    # Test with invalid or problematic query
    invalid_query = ""
    
    response = await database_agent.process_query(invalid_query, tool_context)
    
    assert isinstance(response, str)
    # Should handle gracefully without crashing


@pytest.mark.asyncio
async def test_analytics_agent_error_handling(analytics_agent, tool_context):
    """Test analytics agent error handling."""
    # Test with invalid query
    invalid_query = "xyz123invalid"
    
    response = await analytics_agent.process_query(invalid_query, tool_context)
    
    assert isinstance(response, str)
    # Should handle gracefully


@pytest.mark.asyncio
async def test_bqml_agent_error_handling(bqml_agent_fixture, tool_context):
    """Test BQML agent error handling."""
    # Test with invalid query
    invalid_query = ""
    
    response = await bqml_agent_fixture.process_query(invalid_query, tool_context)
    
    assert isinstance(response, str)
    # Should handle gracefully


@pytest.mark.asyncio
async def test_agent_context_enhancement(database_agent, tool_context, sample_data_context):
    """Test that agents properly enhance queries with context."""
    # Set up context
    for key, value in sample_data_context.items():
        tool_context.update_state(key, value)
    
    query = "Analyze the data"
    
    # Mock the _enhance_query_with_context method
    enhanced_query = database_agent._enhance_query_with_context(query, tool_context)
    
    assert len(enhanced_query) > len(query)
    assert "test_sales_data.csv" in enhanced_query or "sales_data" in enhanced_query


@pytest.mark.asyncio
async def test_analytics_agent_with_previous_results(analytics_agent, tool_context):
    """Test analytics agent using results from previous database query."""
    # Simulate previous database results
    tool_context.update_state("db_agent_output", "SELECT customer_id, SUM(amount) FROM sales GROUP BY customer_id")
    
    query = "Analyze the customer spending patterns"
    response = await analytics_agent.process_query(query, tool_context)
    
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_bqml_agent_with_analysis_context(bqml_agent_fixture, tool_context):
    """Test BQML agent using context from previous analysis."""
    # Simulate previous analysis results
    tool_context.update_state("analysis_result", "Customer segments identified: High, Medium, Low value")
    
    query = "Build a model to predict customer segments"
    response = await bqml_agent_fixture.process_query(query, tool_context)
    
    assert isinstance(response, str)
    assert len(response) > 0