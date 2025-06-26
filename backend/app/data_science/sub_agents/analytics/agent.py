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

"""Analytics/Data Science Agent for statistical analysis and data science tasks."""

import os
from typing import Any, Dict
import google.generativeai as genai
from dotenv import load_dotenv

from ...prompts import return_instructions_analytics

load_dotenv()


class AnalyticsAgent:
    """Analytics Agent using ADK patterns for data science tasks."""
    
    def __init__(self):
        """Initialize the analytics agent."""
        self.model_name = os.getenv("ANALYTICS_AGENT_MODEL", "gemini-1.5-flash")
        
        # Configure the generative AI model
        api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('ADK_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY or ADK_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=genai.GenerationConfig(temperature=0.1)
        )
        
        self.instructions = return_instructions_analytics()
    
    async def process_query(self, query: str, callback_context: Any = None) -> str:
        """Process an analytics/data science query."""
        try:
            # Check if we have data context from previous operations
            context_info = ""
            db_agent_data = None
            
            if callback_context:
                # Get database settings if available
                db_settings = callback_context.get_state("database_settings")
                if db_settings:
                    context_info += f"\nAvailable tables: {', '.join(db_settings.get('tables', []))}"
                
                # Get database agent output (this contains the actual data)
                db_agent_output = callback_context.get_state("db_agent_output")
                if db_agent_output:
                    context_info += f"\nDatabase Agent Results: {db_agent_output}"
                    db_agent_data = db_agent_output
                    print(f"Analytics Agent received DB data: {db_agent_output[:200]}...")  # Debug log
                
                # Get previous query results if available (prioritize structured data)
                query_result = callback_context.get_state("query_result")
                if query_result and query_result.get("rows"):
                    context_info += f"\nStructured Data: {query_result.get('rows', [])[:3]}..."  # Show first 3 rows
                    db_agent_data = query_result  # Use structured data
                    print(f"Analytics Agent using structured query_result: {query_result.get('rows', [])[:2]}...")  # Debug
            
            # Check if database agent returned an error/don't know response
            if db_agent_data and isinstance(db_agent_data, str) and "I don't know" in db_agent_data:
                return db_agent_data  # Pass through the "I don't know" response
            
            # Check if this is a visualization request
            is_visualization = any(word in query.lower() for word in ['chart', 'graph', 'plot', 'visuali', 'bar', 'line', 'pie', 'histogram'])
            print(f"Analytics Agent: is_visualization={is_visualization}, has_db_data={bool(db_agent_data)}")  # Debug
            
            # Create enhanced prompt with context
            if is_visualization and db_agent_data:
                # Check if data contains error messages or is empty
                if isinstance(db_agent_data, str) and ("error" in db_agent_data.lower() or "failed" in db_agent_data.lower()):
                    return "I don't know how to create that chart. The data query failed."
                
                # Extract data for visualization
                if isinstance(db_agent_data, dict) and db_agent_data.get("rows"):
                    # Structured data from query_result
                    rows = db_agent_data.get("rows", [])
                    if not rows:
                        return "I don't know how to create that chart. No data was returned from the query."
                    data_summary = f"Query returned {len(rows)} rows: {rows[:3]}..." if len(rows) > 3 else f"Query returned {len(rows)} rows: {rows}"
                else:
                    # Text data from db_agent_output
                    data_summary = str(db_agent_data)
                    # Check if the text data looks like an error
                    if not data_summary or "no results" in data_summary.lower() or len(data_summary.strip()) < 10:
                        return "I don't know how to create that chart. Insufficient data was provided."
                
                # Generate and execute visualization code for ANY data structure
                print(f"Generating dynamic visualization for: {query}")
                
                # Generate visualization code using AI (no hardcoded patterns)
                chart_result = await self._generate_and_execute_chart(query, db_agent_data, data_summary)
                return chart_result
            else:
                # If analytics agent was called without database data for a chart request, return "I don't know"
                if is_visualization and not db_agent_data:
                    return "I don't know how to create that chart. No data was provided by the database."
                
                # Check if this is a statistical analysis request with actual data
                is_statistical_analysis = any(word in query.lower() for word in ['statistical', 'statistics', 'summary', 'correlation', 'distribution', 'analysis', 'outlier', 'outliers', 'anomal', 'detect'])
                
                if is_statistical_analysis and db_agent_data:
                    # Execute actual statistical analysis on the provided data
                    analysis_result = await self._execute_statistical_analysis(query, db_agent_data, context_info)
                    return analysis_result
                else:
                    # For general analytics requests without specific data
                    enhanced_prompt = f"""{self.instructions}

User Query: {query}

{context_info if context_info else ""}

Provide a comprehensive analysis with:
1. Approach and methodology
2. Python code using pandas, numpy, matplotlib/seaborn if applicable
3. Statistical interpretation
4. Actionable insights and recommendations
5. Next steps for deeper analysis

Keep the response practical and focused on delivering value to the user."""
            
            # Generate response using the model
            import asyncio
            response = await asyncio.to_thread(
                self.model.generate_content,
                enhanced_prompt
            )
            
            # Extract text from response parts
            response_text = ""
            if response.candidates and response.candidates[0].content.parts:
                response_text = response.candidates[0].content.parts[0].text
            
            # Store analysis results in context if available
            if callback_context:
                callback_context.update_state("analytics_result", response_text)
            
            return response_text
            
        except Exception as e:
            return f"Analytics agent error: {str(e)}"
    
    async def _execute_statistical_analysis(self, query: str, db_data: Any, context_info: str) -> str:
        """Execute statistical analysis on actual data following Google ADK patterns."""
        try:
            # Generate Python code to analyze the data
            code_prompt = f"""Generate Python code to analyze the data provided. 

User Query: {query}
Data: {context_info}

Generate Python code that:
1. Creates a pandas DataFrame from the provided data
2. Performs the requested analysis (outlier detection, statistical summary, etc.)
3. Prints clear, specific results with actual numbers
4. Returns meaningful insights

Use pandas, numpy, and appropriate statistical methods. Print all key findings."""

            import asyncio
            response = await asyncio.to_thread(
                self.model.generate_content,
                code_prompt
            )
            
            # Extract code from response
            response_text = ""
            if response.candidates and response.candidates[0].content.parts:
                response_text = response.candidates[0].content.parts[0].text
            
            # Extract Python code
            python_code = response_text
            if "```python" in python_code:
                code_start = python_code.find("```python") + 9
                code_end = python_code.find("```", code_start)
                if code_end != -1:
                    python_code = python_code[code_start:code_end].strip()
                else:
                    python_code = python_code[code_start:].strip()
            
            # Execute the code and capture output
            result = self._execute_analysis_code(python_code, db_data)
            return result
            
        except Exception as e:
            print(f"Error in statistical analysis execution: {e}")
            return f"Error performing statistical analysis: {str(e)}"
    
    def _execute_analysis_code(self, python_code: str, db_data: Any) -> str:
        """Execute Python analysis code and return results."""
        try:
            import pandas as pd
            import numpy as np
            from io import StringIO
            import sys
            
            # Prepare data for analysis
            if isinstance(db_data, dict) and db_data.get("rows"):
                # Convert structured data to DataFrame
                df = pd.DataFrame(db_data["rows"])
            else:
                # Try to parse text data dynamically
                data_str = str(db_data)
                # Generic data parsing - try to extract key-value pairs
                try:
                    lines = data_str.split(", ")
                    data = []
                    for line in lines:
                        if ":" in line:
                            parts = line.split(": ", 1)  # Split only on first colon
                            if len(parts) == 2:
                                key = parts[0].strip()
                                value = parts[1].strip()
                                # Try to convert to appropriate type
                                try:
                                    # Try numeric conversion
                                    if "." in value:
                                        value = float(value.replace(",", "").replace("$", ""))
                                    elif value.isdigit():
                                        value = int(value)
                                except ValueError:
                                    pass  # Keep as string
                                
                                # Create or update record
                                if not data or key in data[-1]:
                                    data.append({key: value})
                                else:
                                    data[-1][key] = value
                    
                    if data:
                        df = pd.DataFrame(data)
                    else:
                        return "Unable to parse data for analysis"
                except Exception as e:
                    return f"Unable to parse data for analysis: {str(e)}"
            
            # Capture stdout to get printed results
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()
            
            # Create execution environment
            exec_globals = {
                'pd': pd,
                'np': np,
                'df': df,
                'print': print,
                '__builtins__': __builtins__
            }
            
            # Execute the code
            exec(python_code, exec_globals)
            
            # Restore stdout and get output
            sys.stdout = old_stdout
            output = captured_output.getvalue()
            
            return output if output.strip() else "Analysis completed but no output generated."
            
        except Exception as e:
            return f"Error executing analysis: {str(e)}"
    
    async def _generate_and_execute_chart(self, query: str, db_data: Any, data_summary: str) -> str:
        """Generate and execute chart code for any visualization request following Google ADK patterns."""
        try:
            # Generate Python visualization code using AI
            chart_prompt = f"""Generate Python matplotlib code to create a visualization based on this request:

User Query: {query}
Available Data: {data_summary}

Requirements:
1. Create a pandas DataFrame from the provided data
2. Generate appropriate matplotlib visualization based on the query
3. Use proper chart type (bar, line, pie, etc.) based on the request
4. Add meaningful titles, labels, and styling
5. Include data value labels when appropriate
6. Use plt.show() at the end

Data structure: {db_data if isinstance(db_data, dict) and db_data.get('rows') else 'Text format data'}

Generate complete executable Python code."""

            import asyncio
            response = await asyncio.to_thread(
                self.model.generate_content,
                chart_prompt
            )
            
            # Extract code from response
            response_text = ""
            if response.candidates and response.candidates[0].content.parts:
                response_text = response.candidates[0].content.parts[0].text
            
            # Extract Python code
            chart_code = response_text
            if "```python" in chart_code:
                code_start = chart_code.find("```python") + 9
                code_end = chart_code.find("```", code_start)
                if code_end != -1:
                    chart_code = chart_code[code_start:code_end].strip()
                else:
                    chart_code = chart_code[code_start:].strip()
            
            print(f"Generated chart code: {chart_code[:200]}...")
            
            # Execute the chart code using chart executor
            try:
                from app.services.chart_executor import chart_executor
                chart_result = chart_executor.execute_chart_code(chart_code)
                
                if chart_result["success"]:
                    print(f"Chart generated successfully: {chart_result['chart_url']}")
                    
                    # Generate summary of the data
                    summary_text = self._generate_data_summary(db_data, query)
                    
                    return f"""{summary_text}

![Chart]({chart_result['chart_url']})

**Chart URL:** {chart_result['chart_url']}"""
                else:
                    print(f"Chart generation failed: {chart_result.get('error', 'Unknown error')}")
                    return f"""Chart generation failed: {chart_result.get('error', 'Unknown error')}

```python
{chart_code}
```

*Note: Chart execution failed*"""
            
            except Exception as e:
                print(f"Error executing chart: {e}")
                return f"""Error executing chart: {str(e)}

```python
{chart_code}
```

*Note: Chart execution failed*"""
                
        except Exception as e:
            print(f"Error generating chart: {e}")
            return f"Error generating visualization: {str(e)}"
    
    def _generate_data_summary(self, db_data: Any, query: str) -> str:
        """Generate a textual summary of the data."""
        try:
            if isinstance(db_data, dict) and db_data.get("rows"):
                rows = db_data["rows"]
                
                # Extract key information from the data
                if len(rows) > 0:
                    keys = list(rows[0].keys())
                    
                    # Generate dynamic summary based on data structure and query
                    # Look for categorical fields that could be used for distribution analysis
                    categorical_fields = []
                    for key in keys:
                        # Check if this field contains categorical data
                        unique_values = set(row.get(key) for row in rows[:10])  # Sample first 10 rows
                        if len(unique_values) <= len(rows) * 0.8 and len(unique_values) > 1:  # Categorical if unique values < 80% of total
                            categorical_fields.append(key)
                    
                    # Find the most relevant field based on query
                    target_field = None
                    for field in categorical_fields:
                        if field.lower() in query.lower() or any(word in query.lower() for word in ["distribution", "breakdown", "by"]):
                            target_field = field
                            break
                    
                    # If no specific field found, use the first categorical field
                    if not target_field and categorical_fields:
                        target_field = categorical_fields[0]
                    
                    if target_field:
                        # Generate distribution summary for the target field
                        field_counts = {}
                        for row in rows:
                            value = row.get(target_field, "Unknown")
                            field_counts[value] = field_counts.get(value, 0) + 1
                        
                        total = sum(field_counts.values())
                        summary_parts = []
                        for value, count in sorted(field_counts.items(), key=lambda x: x[1], reverse=True):
                            percentage = (count / total) * 100
                            summary_parts.append(f"{value}: {count} ({percentage:.1f}%)")
                        
                        field_name = target_field.replace("_", " ").title()
                        return f"{field_name} distribution: {', '.join(summary_parts)}"
                    
                    else:
                        # Generic summary
                        return f"Data analysis complete with {len(rows)} records across {len(keys)} fields: {', '.join(keys[:3])}{'...' if len(keys) > 3 else ''}"
                        
            return "Data analysis complete."
            
        except Exception as e:
            return f"Analysis of {len(db_data.get('rows', [])) if isinstance(db_data, dict) else 'available'} records."


# Create the analytics agent instance following ADK pattern
analytics_agent = AnalyticsAgent()

# For compatibility with existing code
ds_agent = analytics_agent