# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""BigQuery Database Agent for Natural Language to SQL conversion."""

import os
from typing import Any, Dict

# Note: In a real ADK implementation, these would be:
# from google.adk.agents import Agent
# from google.adk.context import CallbackContext
# For our implementation, we'll simulate the ADK patterns

import google.generativeai as genai
from dotenv import load_dotenv

from .tools import initial_bq_nl2sql, run_bigquery_validation
from ...prompts import return_instructions_bigquery

load_dotenv()


def setup_before_agent_call(callback_context: Any) -> None:
    """Setup database settings before agent call."""
    if "database_settings" not in callback_context.state:
        from .tools import get_database_settings
        database_settings = get_database_settings()
        callback_context.update_state("database_settings", database_settings)


class DatabaseAgent:
    """BigQuery Database Agent using ADK patterns."""
    
    def __init__(self):
        """Initialize the database agent."""
        self.model_name = os.getenv("BIGQUERY_AGENT_MODEL", "gemini-1.5-flash")
        self.nl2sql_method = os.getenv("NL2SQL_METHOD", "BASELINE")
        
        # Configure the generative AI model
        api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('ADK_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY or ADK_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=genai.GenerationConfig(temperature=0.01)
        )
        
        # Set up tools based on NL2SQL method
        self.tools = {
            "nl2sql": initial_bq_nl2sql,
            "validation": run_bigquery_validation
        }
        
        self.instructions = return_instructions_bigquery()
    
    async def process_query(self, query: str, callback_context: Any = None) -> str:
        """Process a natural language query through the database agent."""
        try:
            # Setup database settings if needed
            if callback_context:
                setup_before_agent_call(callback_context)
            
            # Step 1: Convert natural language to SQL
            sql_result = await self.tools["nl2sql"](query, callback_context)
            
            if "error" in sql_result:
                return f"I don't know the answer to that question. Could not generate SQL: {sql_result['error']}"
            
            sql_query = sql_result.get("sql_query", "")
            if not sql_query:
                return "I don't know the answer to that question. Could not generate a SQL query from your question."
            
            # Log the SQL query at agent level for easy tracking
            print(f"\n{'='*80}")
            print(f"🗄️ DATABASE AGENT PROCESSING")
            print(f"User Query: {query}")
            print(f"Generated SQL: {sql_query}")
            print(f"{'='*80}\n")
            
            # Step 2: Validate and execute the SQL
            validation_result = await self.tools["validation"](sql_query, callback_context)
            
            if "error" in validation_result:
                # Return clear "I don't know" response for validation failures
                error_msg = validation_result['error']
                return f"I don't know the answer to that question. The database query failed: {error_msg}"
            
            # Store structured data for other agents (following official ADK pattern)
            if callback_context:
                callback_context.update_state("query_result", validation_result)
                print(f"Database Agent stored query_result: {validation_result.get('rows', [])[:2]}...")  # Debug
            
            # Format the response
            return self._format_response(validation_result, query)
            
        except Exception as e:
            return f"Database agent error: {str(e)}"
    
    def _format_response(self, result: Dict[str, Any], original_query: str) -> str:
        """Format the query response based on the original question."""
        # BigQuery returns data in "data" field, not "rows"
        rows = result.get("data") or result.get("rows", [])
        if not rows:
            return "No results found for your query."
        original_query_lower = original_query.lower()
        
        # Handle employee queries with first_name, last_name, and metric (3 columns)
        if (len(rows) > 1 and all(len(row) == 3 for row in rows) and 
            any(key in ['first_name', 'last_name'] for row in rows for key in row.keys())):
            result_parts = []
            for i, row in enumerate(rows, 1):
                # Extract name and metric value
                first_name = row.get('first_name', '')
                last_name = row.get('last_name', '')
                
                # Find the metric column (not first_name or last_name)
                metric_value = None
                metric_name = None
                for key, value in row.items():
                    if key not in ['first_name', 'last_name']:
                        metric_value = value
                        metric_name = key
                        break
                
                if metric_value is not None:
                    # Convert string numbers to int/float for formatting
                    try:
                        if isinstance(metric_value, str) and metric_value.isdigit():
                            metric_value = int(metric_value)
                        elif isinstance(metric_value, str):
                            metric_value = float(metric_value)
                    except:
                        pass
                    
                    if isinstance(metric_value, (int, float)):
                        result_parts.append(f"{i}. {first_name} {last_name}: {metric_value:,.0f}")
                    else:
                        result_parts.append(f"{i}. {first_name} {last_name}: {metric_value}")
            
            # Format based on query type
            if "hours" in original_query_lower:
                return f"Top employees by hours worked:\n" + "\n".join(result_parts)
            elif "top" in original_query_lower and "employee" in original_query_lower:
                return f"Top employees:\n" + "\n".join(result_parts)
            else:
                return "\n".join(result_parts)
        
        # Handle single value results (like simple aggregations)
        if len(rows) == 1 and len(rows[0]) == 1:
            value = list(rows[0].values())[0]
            if isinstance(value, (int, float)):
                return f"Result: {value:,.2f}"
            else:
                return f"Result: {value}"
        
        # Handle category/group comparisons (multiple rows with name-value pairs)
        elif len(rows) > 1 and all(len(row) == 2 for row in rows):
            # This is likely a GROUP BY result (categories, regions, etc.)
            result_parts = []
            for row in rows:
                values = list(row.values())
                if isinstance(values[1], (int, float)):
                    result_parts.append(f"{values[0]}: {values[1]:,.2f}")
                else:
                    result_parts.append(f"{values[0]}: {values[1]}")
            
            # Format based on the type of comparison
            if any(phrase in original_query_lower for phrase in ["compare", "between", "categories", "category"]):
                return f"The total sales for each product category are: {', and '.join(result_parts)}."
            else:
                # Generic formatting for group by results
                return "\n".join(result_parts)
        
        # Handle single row with two columns
        elif len(rows) == 1 and len(rows[0]) == 2:
            values = list(rows[0].values())
            if isinstance(values[1], (int, float)):
                return f"{values[0]}: {values[1]:,.2f}"
            else:
                return f"{values[0]}: {values[1]}"
        
        else:
            # Multiple rows or complex results - show detailed format
            response_lines = []
            for i, row in enumerate(rows[:5], 1):  # Show first 5 results
                if len(row) == 2:
                    values = list(row.values())
                    if isinstance(values[1], (int, float)):
                        response_lines.append(f"{i}. {values[0]}: {values[1]:,.2f}")
                    else:
                        response_lines.append(f"{i}. {values[0]}: {values[1]}")
                else:
                    # Multiple columns
                    row_str = " | ".join([f"{k}: {v}" for k, v in row.items()])
                    response_lines.append(f"{i}. {row_str}")
            
            if len(rows) > 5:
                response_lines.append(f"... and {len(rows) - 5} more results")
            
            return "\n".join(response_lines)


# Create the database agent instance following ADK pattern
database_agent = DatabaseAgent()

# For compatibility with existing code
db_agent = database_agent