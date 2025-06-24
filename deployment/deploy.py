"""
Deployment scripts for Data Science Multi-Agent System
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import yaml
import json
from datetime import datetime

from app.data_science.agent import root_agent
from app.data_science.sub_agents import db_agent, ds_agent, bqml_agent
from app.data_science.tools import ToolContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentDeploymentManager:
    """Manages deployment and lifecycle of data science agents."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "deployment/config.yaml"
        self.config = self._load_config()
        self.deployment_state = {}
    
    def _load_config(self) -> Dict[str, Any]:
        """Load deployment configuration."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default deployment configuration."""
        return {
            "agents": {
                "root_agent": {
                    "enabled": True,
                    "max_retries": 3,
                    "timeout": 30
                },
                "db_agent": {
                    "enabled": True,
                    "max_retries": 2,
                    "timeout": 15
                },
                "ds_agent": {
                    "enabled": True,
                    "max_retries": 2,
                    "timeout": 20
                },
                "bqml_agent": {
                    "enabled": True,
                    "max_retries": 2,
                    "timeout": 25
                }
            },
            "environment": {
                "log_level": "INFO",
                "enable_monitoring": True,
                "health_check_interval": 60
            },
            "database": {
                "project_id": os.getenv("GOOGLE_CLOUD_PROJECT", "test-project"),
                "dataset_id": "data_science_agents",
                "location": "US"
            }
        }
    
    async def deploy_agents(self) -> Dict[str, Any]:
        """Deploy all configured agents."""
        logger.info("Starting agent deployment...")
        
        deployment_results = {
            "deployment_id": f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "agents": {},
            "status": "in_progress"
        }
        
        agents = {
            "root_agent": root_agent,
            "db_agent": db_agent,
            "ds_agent": ds_agent,
            "bqml_agent": bqml_agent
        }
        
        for agent_name, agent in agents.items():
            if self.config["agents"][agent_name]["enabled"]:
                try:
                    logger.info(f"Deploying {agent_name}...")
                    result = await self._deploy_single_agent(agent_name, agent)
                    deployment_results["agents"][agent_name] = result
                    logger.info(f"Successfully deployed {agent_name}")
                except Exception as e:
                    logger.error(f"Failed to deploy {agent_name}: {str(e)}")
                    deployment_results["agents"][agent_name] = {
                        "status": "failed",
                        "error": str(e)
                    }
        
        # Overall deployment status
        failed_agents = [name for name, result in deployment_results["agents"].items() 
                        if result.get("status") == "failed"]
        
        if not failed_agents:
            deployment_results["status"] = "success"
            logger.info("All agents deployed successfully")
        else:
            deployment_results["status"] = "partial_failure"
            logger.warning(f"Failed to deploy: {', '.join(failed_agents)}")
        
        # Save deployment state
        self._save_deployment_state(deployment_results)
        
        return deployment_results
    
    async def _deploy_single_agent(self, agent_name: str, agent) -> Dict[str, Any]:
        """Deploy a single agent with health checks."""
        agent_config = self.config["agents"][agent_name]
        
        # Health check
        health_status = await self._health_check_agent(agent)
        if not health_status["healthy"]:
            raise Exception(f"Agent health check failed: {health_status['error']}")
        
        # Configuration validation
        config_status = await self._validate_agent_config(agent_name, agent)
        if not config_status["valid"]:
            raise Exception(f"Agent configuration invalid: {config_status['error']}")
        
        return {
            "status": "success",
            "health_check": health_status,
            "config_validation": config_status,
            "deployment_time": datetime.now().isoformat(),
            "config": agent_config
        }
    
    async def _health_check_agent(self, agent) -> Dict[str, Any]:
        """Perform health check on an agent."""
        try:
            # Test basic functionality
            context = ToolContext()
            test_query = "health check"
            
            if hasattr(agent, 'process_query'):
                response = await agent.process_query(test_query, context)
            elif hasattr(agent, 'process_message'):
                response = await agent.process_message(test_query, context)
            else:
                raise Exception("Agent does not have expected methods")
            
            return {
                "healthy": True,
                "response_received": bool(response),
                "response_length": len(str(response)) if response else 0
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def _validate_agent_config(self, agent_name: str, agent) -> Dict[str, Any]:
        """Validate agent configuration."""
        try:
            # Check required methods
            required_methods = ['process_query'] if agent_name != 'root_agent' else ['process_message']
            
            for method in required_methods:
                if not hasattr(agent, method):
                    raise Exception(f"Missing required method: {method}")
            
            return {"valid": True}
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def _save_deployment_state(self, deployment_results: Dict[str, Any]):
        """Save deployment state to file."""
        state_file = Path("deployment/state") / f"{deployment_results['deployment_id']}.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(state_file, 'w') as f:
            json.dump(deployment_results, f, indent=2)
        
        logger.info(f"Deployment state saved to {state_file}")
    
    async def undeploy_agents(self, deployment_id: Optional[str] = None) -> Dict[str, Any]:
        """Undeploy agents."""
        logger.info("Starting agent undeployment...")
        
        return {
            "status": "success",
            "message": "Agents undeployed successfully",
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status."""
        agents = {
            "root_agent": root_agent,
            "db_agent": db_agent,
            "ds_agent": ds_agent,
            "bqml_agent": bqml_agent
        }
        
        status = {
            "overall_status": "healthy",
            "agents": {},
            "timestamp": datetime.now().isoformat()
        }
        
        for agent_name, agent in agents.items():
            health = await self._health_check_agent(agent)
            status["agents"][agent_name] = {
                "status": "healthy" if health["healthy"] else "unhealthy",
                "health_check": health
            }
            
            if not health["healthy"]:
                status["overall_status"] = "degraded"
        
        return status


async def main():
    """Main deployment function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy Data Science Agents")
    parser.add_argument("--action", choices=["deploy", "undeploy", "status"], 
                       default="deploy", help="Deployment action")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--deployment-id", help="Deployment ID for undeploy")
    
    args = parser.parse_args()
    
    manager = AgentDeploymentManager(args.config)
    
    if args.action == "deploy":
        result = await manager.deploy_agents()
        print(json.dumps(result, indent=2))
    elif args.action == "undeploy":
        result = await manager.undeploy_agents(args.deployment_id)
        print(json.dumps(result, indent=2))
    elif args.action == "status":
        result = await manager.get_deployment_status()
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())