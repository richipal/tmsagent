"""
Tests for the Root Data Science Agent
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_root_agent_initialization(data_science_agent):
    """Test that the root agent initializes correctly."""
    assert data_science_agent is not None
    assert hasattr(data_science_agent, 'model')
    assert hasattr(data_science_agent, 'sub_agents')
    assert hasattr(data_science_agent, 'tools')


@pytest.mark.asyncio
async def test_intent_classification_database_query(data_science_agent, tool_context):
    """Test intent classification for database queries."""
    database_query = "SELECT * FROM sales_data WHERE customer_id = '12345'"
    
    intent = await data_science_agent._classify_intent(database_query, tool_context)
    
    assert isinstance(intent, dict)
    assert "primary_agent" in intent
    assert "reasoning" in intent


@pytest.mark.asyncio
async def test_intent_classification_analytics_query(data_science_agent, tool_context):
    """Test intent classification for analytics queries."""
    analytics_query = "What is the correlation between customer age and purchase amount?"
    
    intent = await data_science_agent._classify_intent(analytics_query, tool_context)
    
    assert isinstance(intent, dict)
    assert "primary_agent" in intent
    assert "reasoning" in intent


@pytest.mark.asyncio
async def test_intent_classification_ml_query(data_science_agent, tool_context):
    """Test intent classification for ML queries."""
    ml_query = "Build a model to predict customer churn using historical data"
    
    intent = await data_science_agent._classify_intent(ml_query, tool_context)
    
    assert isinstance(intent, dict)
    assert "primary_agent" in intent
    assert "reasoning" in intent


@pytest.mark.asyncio
async def test_process_message_with_context(data_science_agent, sample_data_context):
    """Test processing a message with context."""
    message = "Analyze the sales trends in our dataset"
    
    response = await data_science_agent.process_message(message, sample_data_context)
    
    assert isinstance(response, str)
    assert len(response) > 0
    assert response != "No response generated."


@pytest.mark.asyncio
async def test_process_message_without_context(data_science_agent):
    """Test processing a message without context."""
    message = "What is machine learning?"
    
    response = await data_science_agent.process_message(message)
    
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_error_handling(data_science_agent):
    """Test error handling in the root agent."""
    # Test with an extremely long message that might cause issues
    long_message = "A" * 10000
    
    response = await data_science_agent.process_message(long_message)
    
    assert isinstance(response, str)
    # Should not crash and should return some response


@pytest.mark.asyncio
async def test_agent_routing_database(data_science_agent, tool_context, sample_sql_queries):
    """Test that database queries are routed correctly."""
    sql_query = sample_sql_queries["basic_select"]
    
    with patch('app.data_science.tools.call_db_agent', new_callable=AsyncMock) as mock_db:
        mock_db.return_value = "Mocked database response"
        
        # Create a mock intent that routes to database
        mock_intent = {
            "primary_agent": "database",
            "secondary_agents": [],
            "reasoning": "SQL query should go to database agent"
        }
        
        response = await data_science_agent._route_to_agents(sql_query, mock_intent, tool_context)
        
        assert "database" in response.lower() or "sql" in response.lower()


@pytest.mark.asyncio
async def test_agent_routing_analytics(data_science_agent, tool_context):
    """Test that analytics queries are routed correctly."""
    analytics_query = "Calculate correlation between variables"
    
    with patch('app.data_science.tools.call_ds_agent', new_callable=AsyncMock) as mock_analytics:
        mock_analytics.return_value = "Mocked analytics response"
        
        mock_intent = {
            "primary_agent": "analytics",
            "secondary_agents": [],
            "reasoning": "Statistical analysis should go to analytics agent"
        }
        
        response = await data_science_agent._route_to_agents(analytics_query, mock_intent, tool_context)
        
        assert "analytics" in response.lower() or "mocked" in response.lower()


@pytest.mark.asyncio
async def test_agent_routing_ml(data_science_agent, tool_context):
    """Test that ML queries are routed correctly."""
    ml_query = "Build a classification model"
    
    with patch('app.data_science.tools.call_bqml_agent', new_callable=AsyncMock) as mock_ml:
        mock_ml.return_value = "Mocked ML response"
        
        mock_intent = {
            "primary_agent": "ml",
            "secondary_agents": [],
            "reasoning": "ML task should go to BQML agent"
        }
        
        response = await data_science_agent._route_to_agents(ml_query, mock_intent, tool_context)
        
        assert "ml" in response.lower() or "mocked" in response.lower()


@pytest.mark.asyncio
async def test_multi_agent_workflow(data_science_agent, tool_context):
    """Test a complex workflow involving multiple agents."""
    complex_query = "Analyze customer data and build a predictive model"
    
    with patch('app.data_science.tools.call_db_agent', new_callable=AsyncMock) as mock_db, \
         patch('app.data_science.tools.call_ds_agent', new_callable=AsyncMock) as mock_analytics, \
         patch('app.data_science.tools.call_bqml_agent', new_callable=AsyncMock) as mock_ml:
        
        mock_db.return_value = "Database analysis complete"
        mock_analytics.return_value = "Analytics complete"
        mock_ml.return_value = "ML model built"
        
        mock_intent = {
            "primary_agent": "analytics",
            "secondary_agents": ["database", "ml"],
            "reasoning": "Complex task requires multiple agents"
        }
        
        response = await data_science_agent._route_to_agents(complex_query, mock_intent, tool_context)
        
        assert isinstance(response, str)
        assert len(response) > 0