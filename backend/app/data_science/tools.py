"""
Tools for the Data Science Multi-Agent System
Based on Google ADK samples structure
"""

import asyncio
from typing import Dict, Any, Optional
import json


class ToolContext:
    """Context object to maintain state across agent calls"""
    
    def __init__(self):
        self.state = {}
        self.history = []
    
    def update_state(self, key: str, value: Any):
        """Update the context state"""
        self.state[key] = value
    
    def get_state(self, key: str, default=None):
        """Get value from context state"""
        return self.state.get(key, default)
    
    def add_to_history(self, agent: str, query: str, response: str):
        """Add interaction to history"""
        self.history.append({
            "agent": agent,
            "query": query,
            "response": response,
            "timestamp": asyncio.get_event_loop().time()
        })


def call_db_agent(question: str, tool_context: ToolContext = None) -> dict:
    """Tool to query the database using natural language.
    
    Args:
        question: Natural language question to be converted to SQL and executed
        tool_context: Context object for maintaining state across agent calls
        
    Returns:
        dict: Response with status, report, and optional data
    """
    from .sub_agents import db_agent
    
    print(f"\n🗄️  Calling Database Agent with question: {question[:100]}...")
    
    try:
        import asyncio
        
        # Create tool_context if not provided
        if tool_context is None:
            tool_context = ToolContext()
            
        # Handle async call with proper event loop management
        try:
            # Check if we're in an async context
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context - need to use a thread
                import concurrent.futures
                import threading
                
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(db_agent.process_query(question, tool_context))
                    finally:
                        new_loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    db_agent_output = future.result()
                    
            except RuntimeError:
                # No running loop - we can use asyncio.run directly
                db_agent_output = asyncio.run(db_agent.process_query(question, tool_context))
        except Exception as inner_e:
            print(f"Error in async handling: {inner_e}")
            # Fallback for debugging
            db_agent_output = f"Database agent temporarily unavailable: {str(inner_e)}"
            
        tool_context.update_state("db_agent_output", db_agent_output)
        tool_context.add_to_history("database", question, db_agent_output)
        
        return {
            "status": "success",
            "report": db_agent_output,
            "data": tool_context.get_state("query_result")  # Include structured data if available
        }
    except Exception as e:
        error_msg = f"Database Agent error: {str(e)}"
        tool_context.update_state("db_agent_error", error_msg) if tool_context else None
        
        return {
            "status": "error", 
            "report": error_msg
        }


def call_ds_agent(question: str, tool_context: ToolContext = None) -> dict:
    """Tool to perform data analysis and statistical operations.
    
    Args:
        question: Question requiring data analysis or statistical computation
        tool_context: Context object for maintaining state across agent calls
        
    Returns:
        dict: Response with status, report, and analysis results
    """
    from .sub_agents import ds_agent
    
    print(f"\n📊 Calling Analytics Agent with question: {question[:100]}...")
    
    try:
        # Create tool_context if not provided
        if tool_context is None:
            tool_context = ToolContext()
        
        # Check if we have data from previous database query
        input_data = tool_context.get_state("query_result")
        if input_data and question != "N/A":
            question_with_data = f"""
Question to answer: {question}

Available data from previous query:
{input_data}

Please analyze this data to answer the question.
"""
        else:
            question_with_data = question
        
        # Handle async call with proper event loop management
        try:
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context - need to use a thread
                import concurrent.futures
                
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(ds_agent.process_query(question_with_data, tool_context))
                    finally:
                        new_loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    ds_agent_output = future.result()
                    
            except RuntimeError:
                # No running loop - we can use asyncio.run directly
                ds_agent_output = asyncio.run(ds_agent.process_query(question_with_data, tool_context))
        except Exception as inner_e:
            print(f"Error in async handling: {inner_e}")
            ds_agent_output = f"Analytics agent temporarily unavailable: {str(inner_e)}"
            
        tool_context.update_state("ds_agent_output", ds_agent_output)
        tool_context.add_to_history("analytics", question, ds_agent_output)
        
        return {
            "status": "success",
            "report": ds_agent_output,
            "analysis_type": "statistical_analysis"
        }
    except Exception as e:
        error_msg = f"Analytics Agent error: {str(e)}"
        tool_context.update_state("ds_agent_error", error_msg) if tool_context else None
        
        return {
            "status": "error",
            "report": error_msg
        }


def call_bqml_agent(question: str, tool_context: ToolContext = None) -> dict:
    """Tool to create and manage machine learning models using BigQuery ML.
    
    Args:
        question: Question about ML model creation, training, or prediction
        tool_context: Context object for maintaining state across agent calls
        
    Returns:
        dict: Response with status, report, and ML recommendations
    """
    from .sub_agents import bqml_agent
    
    print(f"\n🤖 Calling BQML Agent with question: {question[:100]}...")
    
    try:
        # Create tool_context if not provided
        if tool_context is None:
            tool_context = ToolContext()
        
        # Add context about available data if relevant
        dataset_info = tool_context.get_state("current_dataset")
        if dataset_info:
            question_with_context = f"""
Question: {question}

Dataset context:
{dataset_info}

Please provide BQML recommendations and implementation.
"""
        else:
            question_with_context = question
        
        # Handle async call with proper event loop management
        try:
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context - need to use a thread
                import concurrent.futures
                
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(bqml_agent.process_query(question_with_context, tool_context))
                    finally:
                        new_loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    bqml_agent_output = future.result()
                    
            except RuntimeError:
                # No running loop - we can use asyncio.run directly
                bqml_agent_output = asyncio.run(bqml_agent.process_query(question_with_context, tool_context))
        except Exception as inner_e:
            print(f"Error in async handling: {inner_e}")
            bqml_agent_output = f"BQML agent temporarily unavailable: {str(inner_e)}"
            
        tool_context.update_state("bqml_agent_output", bqml_agent_output)
        tool_context.add_to_history("bqml", question, bqml_agent_output)
        
        return {
            "status": "success",
            "report": bqml_agent_output,
            "model_type": "bqml_recommendation"
        }
    except Exception as e:
        error_msg = f"BQML Agent error: {str(e)}"
        tool_context.update_state("bqml_agent_error", error_msg) if tool_context else None
        
        return {
            "status": "error",
            "report": error_msg
        }


def load_artifacts(tool_context: ToolContext) -> Dict[str, Any]:
    """Load and return available artifacts from context"""
    artifacts = {
        "db_output": tool_context.get_state("db_agent_output"),
        "ds_output": tool_context.get_state("ds_agent_output"),
        "bqml_output": tool_context.get_state("bqml_agent_output"),
        "current_dataset": tool_context.get_state("current_dataset"),
        "query_result": tool_context.get_state("query_result"),
        "history": tool_context.history
    }
    
    # Filter out None values
    return {k: v for k, v in artifacts.items() if v is not None}