"""
Root Data Science Agent
Based on Google ADK samples structure
"""

import os
import json
import asyncio
from datetime import date
from typing import Dict, Any, Optional

import google.generativeai as genai
from dotenv import load_dotenv

from .sub_agents import bqml_agent, ds_agent, db_agent
from .sub_agents.bigquery.tools import get_database_settings
from .prompts import return_instructions_root
from .tools import call_db_agent, call_ds_agent, call_bqml_agent, load_artifacts, ToolContext

load_dotenv()

date_today = date.today()


def setup_before_agent_call(tool_context: ToolContext):
    """Setup the agent before processing"""
    
    # Setting up database settings in context state
    if "database_settings" not in tool_context.state:
        db_settings = dict()
        db_settings["use_database"] = "BigQuery"
        tool_context.update_state("all_db_settings", db_settings)

    # Setting up schema in context
    if tool_context.get_state("all_db_settings", {}).get("use_database") == "BigQuery":
        database_settings = get_database_settings()
        tool_context.update_state("database_settings", database_settings)
        schema = database_settings["bq_ddl_schema"]
        tool_context.update_state("schema", schema)


class DataScienceRootAgent:
    """
    Root agent that orchestrates the multi-agent data science system
    Following Google ADK samples structure
    """
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('ADK_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY or ADK_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        
        # Initialize the root model
        self.model = genai.GenerativeModel(
            model_name='gemini-1.5-flash'
        )
        
        # Sub-agents are already initialized in sub_agents/__init__.py
        self.sub_agents = [bqml_agent, ds_agent, db_agent]
        
        # Tools available to the root agent
        self.tools = {
            "call_db_agent": call_db_agent,
            "call_ds_agent": call_ds_agent,
            "call_bqml_agent": call_bqml_agent,
            "load_artifacts": load_artifacts
        }
        
    def _get_global_instruction(self) -> str:
        """Get the global instruction for the root agent"""
        return f"""
        You are a Data Science and Data Analytics Multi Agent System.
        Today's date: {date_today}
        
        {return_instructions_root()}
        """
    
    async def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process a message through the multi-agent system"""
        try:
            print(f"🚀 Processing message: {message[:100]}...")
            
            # Use provided context or create new one
            if context and isinstance(context, ToolContext):
                tool_context = context
                print(f"📥 RECEIVED TOOL CONTEXT with state keys: {list(tool_context.state.keys())}")
            else:
                tool_context = ToolContext()
                print(f"📦 CREATED NEW TOOL CONTEXT")
                # Add any provided context if it's a dictionary
                if context and hasattr(context, 'items'):
                    for key, value in context.items():
                        tool_context.update_state(key, value)
                    print(f"📥 Added context from dict: {list(context.keys())}")
            
            # Setup before agent call
            setup_before_agent_call(tool_context)
            print("✅ Setup completed")
            
            # Classify the intent and determine agent routing
            intent = await self._classify_intent(message, tool_context)
            print(f"🎯 Intent classified: {intent}")
            print(f"   Primary: {intent.get('primary_agent')}, Secondary: {intent.get('secondary_agents')}")
            
            # Route to appropriate agent(s) based on intent
            response = await self._route_to_agents(message, intent, tool_context)
            print(f"📤 Response generated: {len(response) if response else 0} characters")
            print(f"📤 Final context state: {list(tool_context.state.keys())}")
            
            return response
            
        except Exception as e:
            print(f"❌ Error in DataScienceRootAgent: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._get_error_response(str(e))
    
    async def _classify_intent(self, message: str, tool_context: ToolContext) -> Dict[str, Any]:
        """Classify the user's intent and determine agent routing using AI classification"""
        
        # Get conversation history for context
        history = tool_context.history[-5:] if tool_context.history else []
        history_text = ""
        if history:
            history_text = "\nRecent conversation history:\n"
            for h in history:
                history_text += f"- {h['agent']}: {h['query'][:100]}...\n"
        
        # Get last query result for context
        last_result = tool_context.get_state("query_result")
        result_context = ""
        if last_result:
            result_context = f"\n\nLast query result available: {str(last_result)[:200]}..."
        
        classification_prompt = f"""
You are a routing agent that determines which specialized agent should handle a query.

Current Query: {message}
{history_text}
{result_context}

IMPORTANT CONTEXT AWARENESS:
- If there are previous query results in the conversation, consider if the current query references them
- Look for pronouns (it, they, these, those) or references to "the data", "results", etc.
- If the query seems to reference previous data, include that context in your routing decision

ROUTING RULES:

1. DATABASE AGENT - Use when the user wants ACTUAL DATA from the database:
   - Questions starting with: "Which", "What", "How many", "List", "Show me", "Get", "Find"
   - Questions about specific people, locations, departments, counts, or records
   - Questions requiring SQL queries to retrieve data
   - Examples:
     * "Which location does [person] work at?" → database
     * "How many employees work in location X?" → database
     * "Which locations have the most time entries?" → database
     * "What is the total hours for department X?" → database
     * "List all users in the system" → database
     * "Show me absence patterns" → database

2. ANALYTICS AGENT - Use ONLY when the user wants:
   - Python code examples or scripts
   - Instructions on HOW to analyze data
   - Statistical analysis methodology (not actual results)
   - Examples:
     * "How do I analyze employee turnover?" → analytics
     * "Write a Python script to calculate correlations" → analytics
     * "What statistical methods should I use?" → analytics

3. BOTH DATABASE + ANALYTICS - Use when the user wants data AND visualization:
   - Questions asking for charts, graphs, or visualizations of data
   - Examples:
     * "Show me chart of top 5 employees by hours" → database + analytics
     * "Create a bar chart of absence patterns" → database + analytics
     * "Show me a graph of overtime by location" → database + analytics
     * "Visualize time entries by department" → database + analytics

4. ML AGENT - Use for machine learning tasks:
   - Model creation, training, predictions
   - ML algorithm recommendations

IMPORTANT: 
- If the query asks for BOTH data AND a chart/graph/visualization, use "database" as primary_agent and ["analytics"] as secondary_agents
- If the query asks for specific data only, use "database"
- When in doubt, if the query asks for specific data or information that exists in the database, ALWAYS choose "database".

The query "{message}" is asking for: [analyze the query]

Based on the routing rules above, this should go to:

Consider the schema context:
{tool_context.get_state('schema', 'No schema available')}

Return a JSON object with:
{{
  "primary_agent": "agent_name",
  "secondary_agents": ["list", "of", "additional", "agents"],
  "reasoning": "explanation of routing decision",
  "sub_tasks": ["specific", "tasks", "for", "each", "agent"]
}}
"""
        
        try:
            response = await asyncio.to_thread(self.model.generate_content, classification_prompt)
            
            # Extract text from response parts
            text = ""
            if response.candidates and response.candidates[0].content.parts:
                text = response.candidates[0].content.parts[0].text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            intent = json.loads(text.strip())
            tool_context.update_state("intent_classification", intent)
            
            return intent
            
        except Exception as e:
            print(f"Intent classification error: {e}")
            # Default to complex routing
            return {
                "primary_agent": "analytics",
                "secondary_agents": [],
                "reasoning": "Classification failed, defaulting to analytics agent",
                "sub_tasks": [message]
            }
    
    async def _route_to_agents(self, message: str, intent: Dict[str, Any], tool_context: ToolContext) -> str:
        """Route the message to appropriate agents based on intent"""
        
        primary_agent = intent.get("primary_agent", "analytics")
        secondary_agents = intent.get("secondary_agents", [])
        
        responses = []
        
        # Call primary agent
        try:
            # Normalize agent names for comparison
            primary_agent_normalized = primary_agent.lower()
            
            if "database" in primary_agent_normalized or "bigquery" in primary_agent_normalized or "call_db_agent" in primary_agent_normalized or "db_agent" in primary_agent_normalized:
                tool_response = call_db_agent(message, tool_context)
                if tool_response["status"] == "success":
                    response = tool_response["report"]
                else:
                    response = f"Error: {tool_response['report']}"
                
                # For single-agent responses, don't add the agent prefix
                if len(secondary_agents) == 0:
                    responses.append(response)
                else:
                    responses.append(f"🗄️ **Database Agent Response:**\n{response}")
                
            elif "analytics" in primary_agent_normalized or "call_ds_agent" in primary_agent_normalized or "ds_agent" in primary_agent_normalized:
                tool_response = call_ds_agent(message, tool_context)
                if tool_response["status"] == "success":
                    response = tool_response["report"]
                else:
                    response = f"Error: {tool_response['report']}"
                responses.append(f"📊 **Analytics Agent Response:**\n{response}")
                
            elif "ml" in primary_agent_normalized or "bqml" in primary_agent_normalized:
                tool_response = call_bqml_agent(message, tool_context)
                if tool_response["status"] == "success":
                    response = tool_response["report"]
                else:
                    response = f"Error: {tool_response['report']}"
                responses.append(f"🤖 **BQML Agent Response:**\n{response}")
            else:
                # Default to analytics if unknown primary agent
                tool_response = call_ds_agent(message, tool_context)
                if tool_response["status"] == "success":
                    response = tool_response["report"]
                else:
                    response = f"Error: {tool_response['report']}"
                responses.append(f"📊 **Analytics Agent Response:**\n{response}")
        except Exception as e:
            print(f"Error calling primary agent {primary_agent}: {e}")
            # Fallback to direct response
            chat = self.model.start_chat(history=[])
            response = await asyncio.to_thread(chat.send_message, f"{self._get_global_instruction()}\n\nUser Query: {message}")
            responses.append(response.text)
        
        # Call secondary agents if needed
        for agent in secondary_agents:
            agent_normalized = agent.lower()
            primary_normalized = primary_agent.lower()
            
            if ("database" in agent_normalized or "bigquery" in agent_normalized or "call_db_agent" in agent_normalized or "db_agent" in agent_normalized) and agent_normalized != primary_normalized:
                tool_response = call_db_agent(message, tool_context)
                response = tool_response["report"] if tool_response["status"] == "success" else f"Error: {tool_response['report']}"
                responses.append(f"🗄️ **Additional Database Analysis:**\n{response}")
                
            elif ("analytics" in agent_normalized or "call_ds_agent" in agent_normalized or "ds_agent" in agent_normalized) and agent_normalized != primary_normalized:
                tool_response = call_ds_agent(message, tool_context)
                response = tool_response["report"] if tool_response["status"] == "success" else f"Error: {tool_response['report']}"
                responses.append(f"📊 **Additional Analytics:**\n{response}")
                
            elif "ml" in agent_normalized and agent_normalized != primary_normalized:
                tool_response = call_bqml_agent(message, tool_context)
                response = tool_response["report"] if tool_response["status"] == "success" else f"Error: {tool_response['report']}"
                responses.append(f"🤖 **Additional ML Recommendations:**\n{response}")
        
        # If complex workflow, synthesize responses
        if len(responses) > 1:
            # Check if any response contains Python code or chart URLs - if so, preserve it
            chart_or_code_response = None
            for response in responses:
                if "```python" in response or "/api/charts/" in response or "![Bar Chart]" in response:
                    chart_or_code_response = response
                    break
            
            if chart_or_code_response:
                # For visualization requests, return the chart/code directly
                print(f"Found chart/code response, returning it directly: {chart_or_code_response[:100]}...")
                return chart_or_code_response
            else:
                # Normal synthesis for non-code responses
                synthesis_prompt = f"""
Synthesize the following agent responses into a coherent answer for the user:

Original Query: {message}

Agent Responses:
{chr(10).join(responses)}

IMPORTANT: Provide a DIRECT and CONCISE unified answer. Focus on the key findings and actionable insights without lengthy explanations.
"""
                
                chat = self.model.start_chat(history=[])
                synthesis = await asyncio.to_thread(chat.send_message, synthesis_prompt)
                return synthesis.text
        
        return responses[0] if responses else "No response generated."
    
    def _get_error_response(self, error: str) -> str:
        """Generate a helpful error response"""
        if "SERVICE_DISABLED" in error:
            return "The Google Generative AI service needs to be enabled. Please check your API configuration."
        return f"I encountered an error while processing your request: {error}. Please try rephrasing your question."


# Create the root agent instance following ADK pattern
root_agent = DataScienceRootAgent()