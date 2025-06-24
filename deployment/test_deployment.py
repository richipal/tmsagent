"""
Tests for deployment functionality
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from deployment.deploy import AgentDeploymentManager


@pytest.fixture
def temp_config():
    """Create a temporary configuration file."""
    config_data = {
        "agents": {
            "root_agent": {"enabled": True, "max_retries": 3, "timeout": 30},
            "db_agent": {"enabled": True, "max_retries": 2, "timeout": 15},
            "ds_agent": {"enabled": True, "max_retries": 2, "timeout": 20},
            "bqml_agent": {"enabled": True, "max_retries": 2, "timeout": 25}
        },
        "environment": {
            "log_level": "INFO",
            "enable_monitoring": True,
            "health_check_interval": 60
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(config_data, f)
        return f.name


@pytest.fixture
def deployment_manager(temp_config):
    """Create a deployment manager with test configuration."""
    return AgentDeploymentManager(temp_config)


def test_deployment_manager_initialization(deployment_manager):
    """Test that deployment manager initializes correctly."""
    assert deployment_manager.config is not None
    assert "agents" in deployment_manager.config
    assert "root_agent" in deployment_manager.config["agents"]


def test_default_config_loading():
    """Test loading default configuration when file doesn't exist."""
    manager = AgentDeploymentManager("nonexistent.yaml")
    assert manager.config is not None
    assert "agents" in manager.config
    assert manager.config["agents"]["root_agent"]["enabled"] is True


@pytest.mark.asyncio
async def test_health_check_agent_success(deployment_manager):
    """Test successful agent health check."""
    mock_agent = MagicMock()
    mock_agent.process_query = AsyncMock(return_value="Health check response")
    
    result = await deployment_manager._health_check_agent(mock_agent)
    
    assert result["healthy"] is True
    assert result["response_received"] is True
    assert result["response_length"] > 0


@pytest.mark.asyncio
async def test_health_check_agent_failure(deployment_manager):
    """Test failed agent health check."""
    mock_agent = MagicMock()
    mock_agent.process_query = AsyncMock(side_effect=Exception("Test error"))
    
    result = await deployment_manager._health_check_agent(mock_agent)
    
    assert result["healthy"] is False
    assert "error" in result
    assert "Test error" in result["error"]


@pytest.mark.asyncio
async def test_validate_agent_config_success(deployment_manager):
    """Test successful agent configuration validation."""
    mock_agent = MagicMock()
    mock_agent.process_query = AsyncMock()
    
    result = await deployment_manager._validate_agent_config("db_agent", mock_agent)
    
    assert result["valid"] is True


@pytest.mark.asyncio
async def test_validate_agent_config_missing_method(deployment_manager):
    """Test agent configuration validation with missing method."""
    mock_agent = MagicMock()
    # Don't add process_query method
    
    result = await deployment_manager._validate_agent_config("db_agent", mock_agent)
    
    assert result["valid"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_deploy_single_agent_success(deployment_manager):
    """Test successful single agent deployment."""
    mock_agent = MagicMock()
    mock_agent.process_query = AsyncMock(return_value="Test response")
    
    result = await deployment_manager._deploy_single_agent("db_agent", mock_agent)
    
    assert result["status"] == "success"
    assert "health_check" in result
    assert "config_validation" in result
    assert "deployment_time" in result


@pytest.mark.asyncio
async def test_deploy_single_agent_health_failure(deployment_manager):
    """Test single agent deployment with health check failure."""
    mock_agent = MagicMock()
    mock_agent.process_query = AsyncMock(side_effect=Exception("Health check failed"))
    
    with pytest.raises(Exception, match="Agent health check failed"):
        await deployment_manager._deploy_single_agent("db_agent", mock_agent)


@pytest.mark.asyncio
@patch('deployment.deploy.root_agent')
@patch('deployment.deploy.db_agent')
@patch('deployment.deploy.ds_agent')
@patch('deployment.deploy.bqml_agent')
async def test_deploy_agents_success(mock_bqml, mock_ds, mock_db, mock_root, deployment_manager):
    """Test successful deployment of all agents."""
    # Mock all agents
    for mock_agent in [mock_root, mock_db, mock_ds, mock_bqml]:
        mock_agent.process_query = AsyncMock(return_value="Mock response")
        mock_agent.process_message = AsyncMock(return_value="Mock response")
    
    with patch.object(deployment_manager, '_save_deployment_state'):
        result = await deployment_manager.deploy_agents()
    
    assert result["status"] == "success"
    assert "deployment_id" in result
    assert "agents" in result
    assert len(result["agents"]) == 4


@pytest.mark.asyncio
@patch('deployment.deploy.root_agent')
@patch('deployment.deploy.db_agent')
@patch('deployment.deploy.ds_agent')
@patch('deployment.deploy.bqml_agent')
async def test_deploy_agents_partial_failure(mock_bqml, mock_ds, mock_db, mock_root, deployment_manager):
    """Test deployment with some agent failures."""
    # Mock successful agents
    mock_root.process_message = AsyncMock(return_value="Mock response")
    mock_db.process_query = AsyncMock(return_value="Mock response")
    mock_ds.process_query = AsyncMock(return_value="Mock response")
    
    # Mock failing agent
    mock_bqml.process_query = AsyncMock(side_effect=Exception("BQML agent failed"))
    
    with patch.object(deployment_manager, '_save_deployment_state'):
        result = await deployment_manager.deploy_agents()
    
    assert result["status"] == "partial_failure"
    assert result["agents"]["bqml_agent"]["status"] == "failed"


@pytest.mark.asyncio
async def test_undeploy_agents(deployment_manager):
    """Test agent undeployment."""
    result = await deployment_manager.undeploy_agents("test-deployment-id")
    
    assert result["status"] == "success"
    assert "timestamp" in result


@pytest.mark.asyncio
@patch('deployment.deploy.root_agent')
@patch('deployment.deploy.db_agent')
@patch('deployment.deploy.ds_agent')
@patch('deployment.deploy.bqml_agent')
async def test_get_deployment_status(mock_bqml, mock_ds, mock_db, mock_root, deployment_manager):
    """Test getting deployment status."""
    # Mock all agents as healthy
    for mock_agent in [mock_root, mock_db, mock_ds, mock_bqml]:
        mock_agent.process_query = AsyncMock(return_value="Health check response")
        mock_agent.process_message = AsyncMock(return_value="Health check response")
    
    result = await deployment_manager.get_deployment_status()
    
    assert result["overall_status"] == "healthy"
    assert "agents" in result
    assert len(result["agents"]) == 4
    assert all(agent["status"] == "healthy" for agent in result["agents"].values())


@pytest.mark.asyncio
@patch('deployment.deploy.root_agent')
@patch('deployment.deploy.db_agent')
@patch('deployment.deploy.ds_agent')
@patch('deployment.deploy.bqml_agent')
async def test_get_deployment_status_with_unhealthy_agent(mock_bqml, mock_ds, mock_db, mock_root, deployment_manager):
    """Test getting deployment status with one unhealthy agent."""
    # Mock most agents as healthy
    mock_root.process_message = AsyncMock(return_value="Health check response")
    mock_db.process_query = AsyncMock(return_value="Health check response")
    mock_ds.process_query = AsyncMock(return_value="Health check response")
    
    # Mock one agent as unhealthy
    mock_bqml.process_query = AsyncMock(side_effect=Exception("BQML agent down"))
    
    result = await deployment_manager.get_deployment_status()
    
    assert result["overall_status"] == "degraded"
    assert result["agents"]["bqml_agent"]["status"] == "unhealthy"


def test_save_deployment_state(deployment_manager):
    """Test saving deployment state."""
    deployment_results = {
        "deployment_id": "test-deployment",
        "status": "success",
        "agents": {"test_agent": {"status": "success"}}
    }
    
    with patch('pathlib.Path.mkdir'), \
         patch('builtins.open', create=True) as mock_open:
        
        deployment_manager._save_deployment_state(deployment_results)
        
        # Verify file was opened for writing
        mock_open.assert_called_once()


@pytest.mark.integration
async def test_deployment_integration():
    """Integration test for full deployment workflow."""
    manager = AgentDeploymentManager()
    
    # Test that we can create a manager and get status
    # without actually deploying (to avoid dependencies)
    assert manager.config is not None
    
    # Test configuration loading
    default_config = manager._get_default_config()
    assert "agents" in default_config
    assert "environment" in default_config


@pytest.mark.asyncio
async def test_agent_method_detection(deployment_manager):
    """Test that deployment correctly detects agent methods."""
    # Test root agent (should have process_message)
    mock_root_agent = MagicMock()
    mock_root_agent.process_message = AsyncMock()
    
    result = await deployment_manager._validate_agent_config("root_agent", mock_root_agent)
    assert result["valid"] is True
    
    # Test sub-agent (should have process_query)
    mock_sub_agent = MagicMock()
    mock_sub_agent.process_query = AsyncMock()
    
    result = await deployment_manager._validate_agent_config("db_agent", mock_sub_agent)
    assert result["valid"] is True


@pytest.mark.asyncio
async def test_deployment_config_validation(deployment_manager):
    """Test deployment configuration validation."""
    # Test that all required config sections exist
    config = deployment_manager.config
    
    assert "agents" in config
    assert "root_agent" in config["agents"]
    assert "db_agent" in config["agents"]
    assert "ds_agent" in config["agents"]
    assert "bqml_agent" in config["agents"]
    
    # Test that each agent has required config
    for agent_name, agent_config in config["agents"].items():
        assert "enabled" in agent_config
        assert "max_retries" in agent_config
        assert "timeout" in agent_config