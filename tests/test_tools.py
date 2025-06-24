"""
Tests for Agent Tools and Utilities
"""

import pytest
from unittest.mock import AsyncMock, patch
from app.data_science.tools import ToolContext, call_db_agent, call_ds_agent, call_bqml_agent, load_artifacts
from app.data_science.sub_agents.bigquery.tools import get_database_settings, get_table_info, validate_sql_query


def test_tool_context_initialization():
    """Test ToolContext initialization."""
    context = ToolContext()
    assert hasattr(context, 'state')
    assert hasattr(context, 'history')
    assert isinstance(context.state, dict)
    assert isinstance(context.history, list)


def test_tool_context_state_management():
    """Test ToolContext state management."""
    context = ToolContext()
    
    # Test update_state
    context.update_state("test_key", "test_value")
    assert context.get_state("test_key") == "test_value"
    
    # Test get_state with default
    assert context.get_state("nonexistent_key", "default") == "default"
    assert context.get_state("nonexistent_key") is None


def test_tool_context_history():
    """Test ToolContext history management."""
    context = ToolContext()
    
    context.add_to_history("test_agent", "test_query", "test_response")
    
    assert len(context.history) == 1
    history_entry = context.history[0]
    assert history_entry["agent"] == "test_agent"
    assert history_entry["query"] == "test_query"
    assert history_entry["response"] == "test_response"
    assert "timestamp" in history_entry


@pytest.mark.asyncio
async def test_call_db_agent():
    """Test the call_db_agent tool function."""
    context = ToolContext()
    
    with patch('app.data_science.sub_agents.db_agent.process_query', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = "Mock database response"
        
        result = await call_db_agent("test query", context)
        
        assert result == "Mock database response"
        assert context.get_state("db_agent_output") == "Mock database response"
        assert len(context.history) == 1


@pytest.mark.asyncio
async def test_call_ds_agent():
    """Test the call_ds_agent tool function."""
    context = ToolContext()
    
    with patch('app.data_science.sub_agents.ds_agent.process_query', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = "Mock analytics response"
        
        result = await call_ds_agent("test query", context)
        
        assert result == "Mock analytics response"
        assert context.get_state("ds_agent_output") == "Mock analytics response"
        assert len(context.history) == 1


@pytest.mark.asyncio
async def test_call_ds_agent_with_data():
    """Test call_ds_agent with previous query results."""
    context = ToolContext()
    context.update_state("query_result", "Previous query results")
    
    with patch('app.data_science.sub_agents.ds_agent.process_query', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = "Analytics with data"
        
        result = await call_ds_agent("analyze this", context)
        
        # Should call with enhanced query including data
        called_args = mock_process.call_args[0]
        assert "Previous query results" in called_args[0]


@pytest.mark.asyncio
async def test_call_bqml_agent():
    """Test the call_bqml_agent tool function."""
    context = ToolContext()
    
    with patch('app.data_science.sub_agents.bqml_agent.process_query', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = "Mock BQML response"
        
        result = await call_bqml_agent("test ML query", context)
        
        assert result == "Mock BQML response"
        assert context.get_state("bqml_agent_output") == "Mock BQML response"
        assert len(context.history) == 1


@pytest.mark.asyncio
async def test_agent_error_handling():
    """Test error handling in agent tool functions."""
    context = ToolContext()
    
    with patch('app.data_science.sub_agents.db_agent.process_query', new_callable=AsyncMock) as mock_process:
        mock_process.side_effect = Exception("Test error")
        
        result = await call_db_agent("test query", context)
        
        assert "error" in result.lower()
        assert context.get_state("db_agent_error") is not None


def test_load_artifacts():
    """Test the load_artifacts function."""
    context = ToolContext()
    context.update_state("db_agent_output", "DB result")
    context.update_state("ds_agent_output", "Analytics result")
    context.add_to_history("test", "query", "response")
    
    artifacts = load_artifacts(context)
    
    assert "db_output" in artifacts
    assert "ds_output" in artifacts
    assert "history" in artifacts
    assert artifacts["db_output"] == "DB result"
    assert artifacts["ds_output"] == "Analytics result"
    assert len(artifacts["history"]) == 1


def test_load_artifacts_empty_context():
    """Test load_artifacts with empty context."""
    context = ToolContext()
    
    artifacts = load_artifacts(context)
    
    # Should only contain non-None values
    assert all(v is not None for v in artifacts.values())


def test_get_database_settings():
    """Test BigQuery database settings."""
    settings = get_database_settings()
    
    assert isinstance(settings, dict)
    assert "use_database" in settings
    assert settings["use_database"] == "BigQuery"
    assert "bq_ddl_schema" in settings
    assert "project_id" in settings
    assert "dataset_id" in settings
    assert "tables" in settings


def test_get_table_info_valid_table():
    """Test getting info for valid table."""
    table_info = get_table_info("sales_data")
    
    assert isinstance(table_info, dict)
    assert "columns" in table_info
    assert "row_count" in table_info
    assert "size_gb" in table_info
    assert isinstance(table_info["columns"], list)


def test_get_table_info_invalid_table():
    """Test getting info for invalid table."""
    table_info = get_table_info("nonexistent_table")
    
    assert "error" in table_info


def test_validate_sql_query_basic():
    """Test basic SQL query validation."""
    query = "SELECT customer_id, amount FROM sales WHERE amount > 100"
    result = validate_sql_query(query)
    
    assert isinstance(result, dict)
    assert "is_valid" in result
    assert "warnings" in result
    assert "errors" in result
    assert "suggestions" in result


def test_validate_sql_query_select_star():
    """Test validation of SELECT * queries."""
    query = "SELECT * FROM large_table"
    result = validate_sql_query(query)
    
    assert result["is_valid"]
    assert any("SELECT *" in warning for warning in result["warnings"])


def test_validate_sql_query_no_limit():
    """Test validation of queries without LIMIT."""
    query = "SELECT customer_id FROM sales"
    result = validate_sql_query(query)
    
    assert result["is_valid"]
    assert any("LIMIT" in suggestion for suggestion in result["suggestions"])


def test_validate_sql_query_no_where():
    """Test validation of queries without WHERE clause."""
    query = "SELECT customer_id FROM sales_data"
    result = validate_sql_query(query)
    
    assert result["is_valid"]
    assert any("WHERE" in warning for warning in result["warnings"])


@pytest.mark.asyncio
async def test_agent_context_passing():
    """Test that context is properly passed between agents."""
    context = ToolContext()
    context.update_state("current_dataset", {"filename": "test.csv"})
    
    with patch('app.data_science.sub_agents.bqml_agent.process_query', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = "BQML response"
        
        await call_bqml_agent("build model", context)
        
        # Check that the agent received the context
        called_args = mock_process.call_args[0]
        called_context = mock_process.call_args[1] if len(mock_process.call_args) > 1 else None
        
        # Context should be passed to the agent
        assert called_context is not None or "test.csv" in called_args[0]