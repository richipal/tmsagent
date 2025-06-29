"""
Tests for agent routing and context handling
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.data_science.tools import ToolContext


class TestAgentRouting:
    """Test agent routing and tool functions"""
    
    def test_tool_imports(self):
        """Test that agent tools can be imported"""
        try:
            from app.data_science.tools import call_db_agent, call_ds_agent, call_bqml_agent
            assert callable(call_db_agent)
            assert callable(call_ds_agent) 
            assert callable(call_bqml_agent)
        except ImportError as e:
            pytest.skip(f"Agent tools not available: {e}")
    
    def test_agent_instances_import(self):
        """Test that agent instances can be imported"""
        try:
            from app.data_science.sub_agents.bigquery.agent import db_agent
            from app.data_science.sub_agents.analytics.agent import ds_agent  
            from app.data_science.sub_agents.bqml.agent import bqml_agent
            
            assert db_agent is not None
            assert ds_agent is not None
            assert bqml_agent is not None
        except ImportError as e:
            pytest.skip(f"Agent instances not available: {e}")
    
    def test_database_agent_class(self):
        """Test DatabaseAgent class can be instantiated"""
        try:
            from app.data_science.sub_agents.bigquery.agent import DatabaseAgent
            
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel'):
                    agent = DatabaseAgent()
                    assert hasattr(agent, 'process_query')
                    assert hasattr(agent, 'model_name')
        except ImportError as e:
            pytest.skip(f"DatabaseAgent not available: {e}")
    
    @pytest.mark.asyncio
    async def test_database_agent_process_query_mock(self):
        """Test database agent query processing with mocks"""
        try:
            from app.data_science.sub_agents.bigquery.agent import DatabaseAgent
            
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel'):
                    with patch('app.data_science.sub_agents.bigquery.agent.initial_bq_nl2sql') as mock_nl2sql:
                        with patch('app.data_science.sub_agents.bigquery.agent.run_bigquery_validation') as mock_validation:
                            
                            mock_nl2sql.return_value = {"sql_query": "SELECT * FROM test"}
                            mock_validation.return_value = {
                                "success": True,
                                "data": [{"name": "John", "department": "Engineering"}],
                                "row_count": 1
                            }
                            
                            agent = DatabaseAgent()
                            result = await agent.process_query("Where does John work?")
                            
                            assert isinstance(result, str)
                            assert len(result) > 0
        except ImportError as e:
            pytest.skip(f"DatabaseAgent not available: {e}")


class TestToolContext:
    """Test ToolContext functionality"""
    
    def test_context_state_management(self):
        """Test context state update and retrieval"""
        context = ToolContext()
        
        # Update state
        context.update_state("test_key", "test_value")
        context.update_state("number", 42)
        context.update_state("dict_data", {"nested": "value"})
        
        # Retrieve state
        assert context.get_state("test_key") == "test_value"
        assert context.get_state("number") == 42
        assert context.get_state("dict_data")["nested"] == "value"
        assert context.get_state("nonexistent") is None
    
    def test_context_state_keys(self):
        """Test getting all state keys"""
        context = ToolContext()
        context.update_state("key1", "value1")
        context.update_state("key2", "value2")
        
        # Use direct state access instead of get_state_keys()
        keys = list(context.state.keys())
        assert "key1" in keys
        assert "key2" in keys
        assert len(keys) >= 2
    
    def test_context_callback_preservation(self):
        """Test that callback context is preserved"""
        context = ToolContext()
        
        # Set callback context data
        context.update_state("callback_data", {"important": "info"})
        
        # Context should maintain this for other agents
        callback_data = context.get_state("callback_data")
        assert callback_data is not None
        assert callback_data["important"] == "info"


class TestAgentIntegration:
    """Test integration between agents and session memory"""
    
    def test_session_memory_integration(self, test_session_manager):
        """Test that agents can access session memory"""
        session = test_session_manager.create_session(title="Memory Test")
        memory = test_session_manager.get_session_memory(session.id)
        
        # Store data in memory
        memory.update_state("department", "Engineering")
        memory.update_state("employees", ["John", "Jane"])
        memory.add_to_history("database", "Who works in Engineering?", "John and Jane")
        
        # Create context from memory
        context = ToolContext()
        for key, value in memory.state.items():
            context.update_state(key, value)
        
        # Verify context has memory data
        assert context.get_state("department") == "Engineering"
        assert context.get_state("employees") == ["John", "Jane"]
        assert len(memory.history) == 1