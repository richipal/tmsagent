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

"""BigQuery ML Agent for machine learning tasks using BQML."""

import os
from typing import Any, Dict
import google.generativeai as genai
from dotenv import load_dotenv

from ...prompts import return_instructions_bqml

load_dotenv()


class BQMLAgent:
    """BigQuery ML Agent using ADK patterns for machine learning tasks."""
    
    def __init__(self):
        """Initialize the BQML agent."""
        self.model_name = os.getenv("BQML_AGENT_MODEL", "gemini-1.5-flash")
        
        # Configure the generative AI model
        api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('ADK_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY or ADK_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=genai.GenerationConfig(temperature=0.1)
        )
        
        self.instructions = return_instructions_bqml()
    
    async def process_query(self, query: str, callback_context: Any = None) -> str:
        """Process a BigQuery ML query."""
        try:
            # Get database context for ML model recommendations
            context_info = ""
            if callback_context:
                # Get database settings if available
                db_settings = callback_context.get_state("database_settings")
                if db_settings:
                    context_info += f"\nAvailable tables: {', '.join(db_settings.get('tables', []))}"
                    context_info += f"\nProject: {db_settings.get('project_id', '')}"
                    context_info += f"\nDataset: {db_settings.get('dataset_id', '')}"
                
                # Get previous query results that might be used for ML
                query_result = callback_context.get_state("query_result")
                if query_result and query_result.get("rows"):
                    context_info += f"\nData available: {len(query_result['rows'])} rows"
                    context_info += f"\nColumns: {', '.join(query_result.get('columns', []))}"
            
            # Create enhanced prompt for BQML recommendations
            enhanced_prompt = f"""{self.instructions}

User Query: {query}

{context_info if context_info else ""}

Provide comprehensive BQML guidance including:
1. Recommended ML approach and model type for the use case
2. Feature engineering considerations and SQL queries
3. BQML CREATE MODEL statement with appropriate parameters
4. Model training and evaluation queries
5. Prediction and deployment recommendations
6. Performance monitoring and model improvement strategies

Focus on practical BQML implementation that the user can execute directly."""
            
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
            
            # Store BQML recommendations in context if available
            if callback_context:
                callback_context.update_state("bqml_result", response_text)
            
            return response_text
            
        except Exception as e:
            return f"BQML agent error: {str(e)}"


# Create the BQML agent instance following ADK pattern
bqml_agent = BQMLAgent()

# For compatibility with existing code
root_agent = bqml_agent