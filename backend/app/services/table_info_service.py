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

"""Table Information Service for getting BigQuery table schemas and generating query suggestions."""

import os
import logging
from typing import Dict, List, Any, Optional
from google.cloud import bigquery
from google.cloud.exceptions import NotFound, GoogleCloudError
import google.generativeai as genai
from dotenv import load_dotenv

from app.data_science.sub_agents.bigquery.tools import bq_manager, get_database_settings

load_dotenv()
logger = logging.getLogger(__name__)


class TableInfoService:
    """Service for managing table information and query suggestions."""
    
    def __init__(self):
        self.bq_manager = bq_manager
        # Configure the generative AI model for query suggestions
        api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('ADK_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            logger.warning("No API key configured for query suggestions")
    
    def get_comprehensive_table_info(self) -> Dict[str, Any]:
        """Get comprehensive information about all tables in the dataset."""
        try:
            db_settings = get_database_settings()
            tables = self.bq_manager.get_tables()
            
            table_details = {}
            for table_name in tables:
                table_info = self._get_detailed_table_info(table_name)
                if table_info and "error" not in table_info:
                    table_details[table_name] = table_info
            
            return {
                "database_info": {
                    "type": "BigQuery",
                    "project_id": db_settings.get("project_id"),
                    "dataset_id": db_settings.get("dataset_id"),
                    "location": db_settings.get("location"),
                    "total_tables": len(table_details)
                },
                "tables": table_details,
                "schema_ddl": db_settings.get("bq_ddl_schema", ""),
                "available_datasets": db_settings.get("available_datasets", [])
            }
            
        except Exception as e:
            logger.error(f"Error getting comprehensive table info: {e}")
            return {"error": str(e)}
    
    def _get_detailed_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific table."""
        try:
            table_ref = self.bq_manager.client.dataset(self.bq_manager.dataset_id).table(table_name)
            table = self.bq_manager.client.get_table(table_ref)
            
            # Get schema information
            schema_fields = []
            for field in table.schema:
                field_info = {
                    "name": field.name,
                    "type": field.field_type,
                    "mode": field.mode,
                    "description": field.description or ""
                }
                schema_fields.append(field_info)
            
            # Get sample data (first 5 rows)
            sample_query = f"""
            SELECT * FROM `{self.bq_manager.project_id}.{self.bq_manager.dataset_id}.{table_name}` 
            LIMIT 5
            """
            sample_result = self.bq_manager.execute_query(sample_query)
            sample_data = sample_result.get("rows", []) if "error" not in sample_result else []
            
            return {
                "table_id": table.table_id,
                "full_table_id": f"{table.project}.{table.dataset_id}.{table.table_id}",
                "dataset_id": table.dataset_id,
                "project_id": table.project,
                "num_rows": table.num_rows,
                "num_bytes": table.num_bytes,
                "size_gb": round(table.num_bytes / (1024**3), 2) if table.num_bytes else 0,
                "created": table.created.isoformat() if table.created else None,
                "modified": table.modified.isoformat() if table.modified else None,
                "description": table.description or "",
                "schema": schema_fields,
                "sample_data": sample_data[:3] if sample_data else []  # Show only 3 sample rows
            }
            
        except NotFound:
            return {"error": f"Table {self.bq_manager.dataset_id}.{table_name} not found"}
        except Exception as e:
            logger.error(f"Error fetching detailed info for {table_name}: {e}")
            return {"error": str(e)}
    
    async def generate_query_suggestions(self, table_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate intelligent query suggestions based on table schemas."""
        if not self.model:
            return self._get_default_query_suggestions(table_info)
        
        try:
            # Create prompt for query suggestions
            tables_summary = []
            for table_name, details in table_info.get("tables", {}).items():
                schema_summary = ", ".join([f"{field['name']} ({field['type']})" for field in details.get("schema", [])])
                tables_summary.append(f"Table {table_name}: {schema_summary}")
            
            prompt = f"""Based on the following BigQuery database schema, generate 15-20 intelligent query suggestions that would be useful for data analysis.

Database: {table_info.get('database_info', {}).get('project_id')}.{table_info.get('database_info', {}).get('dataset_id')}

Tables and Schema:
{chr(10).join(tables_summary)}

Generate diverse query suggestions covering:
1. Basic data exploration (counts, distinct values, etc.)
2. Aggregation queries (sums, averages, grouping)
3. Filtering and sorting
4. Join operations between tables
5. Statistical analysis
6. Data quality checks
7. Business intelligence queries
8. Trend analysis
9. Comparison queries
10. Top/bottom N queries

For each suggestion, provide:
- A natural language description of what the query does
- The corresponding SQL query
- The difficulty level (Beginner/Intermediate/Advanced)
- The query category/type

Format as a JSON array of objects with fields: description, sql_query, difficulty, category.
Only return the JSON array, no additional text."""

            import asyncio
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            
            if response.candidates and response.candidates[0].content.parts:
                response_text = response.candidates[0].content.parts[0].text.strip()
                
                # Try to extract JSON from response
                import json
                try:
                    # Remove any markdown formatting
                    if "```json" in response_text:
                        json_start = response_text.find("```json") + 7
                        json_end = response_text.find("```", json_start)
                        if json_end != -1:
                            response_text = response_text[json_start:json_end]
                    
                    suggestions = json.loads(response_text)
                    if isinstance(suggestions, list):
                        return suggestions
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse AI response as JSON: {e}")
                    
            # Fallback to default suggestions
            return self._get_default_query_suggestions(table_info)
            
        except Exception as e:
            logger.error(f"Error generating AI query suggestions: {e}")
            return self._get_default_query_suggestions(table_info)
    
    def _get_default_query_suggestions(self, table_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate default query suggestions based on table schemas."""
        suggestions = []
        project_id = table_info.get('database_info', {}).get('project_id', 'your_project')
        dataset_id = table_info.get('database_info', {}).get('dataset_id', 'your_dataset')
        
        for table_name, details in table_info.get("tables", {}).items():
            full_table_name = f"`{project_id}.{dataset_id}.{table_name}`"
            schema = details.get("schema", [])
            
            # Basic exploration queries
            suggestions.append({
                "description": f"Get total number of records in {table_name}",
                "sql_query": f"SELECT COUNT(*) as total_records FROM {full_table_name}",
                "difficulty": "Beginner",
                "category": "Data Exploration"
            })
            
            suggestions.append({
                "description": f"Show first 10 records from {table_name}",
                "sql_query": f"SELECT * FROM {full_table_name} LIMIT 10",
                "difficulty": "Beginner",
                "category": "Data Exploration"
            })
            
            # Schema-specific queries
            for field in schema:
                field_name = field["name"]
                field_type = field["type"]
                
                if field_type in ["STRING", "TEXT"]:
                    suggestions.append({
                        "description": f"Get distinct values for {field_name} in {table_name}",
                        "sql_query": f"SELECT DISTINCT {field_name}, COUNT(*) as count FROM {full_table_name} GROUP BY {field_name} ORDER BY count DESC",
                        "difficulty": "Beginner",
                        "category": "Data Exploration"
                    })
                
                elif field_type in ["INTEGER", "FLOAT", "NUMERIC"]:
                    suggestions.append({
                        "description": f"Get statistical summary for {field_name} in {table_name}",
                        "sql_query": f"SELECT MIN({field_name}) as min_value, MAX({field_name}) as max_value, AVG({field_name}) as avg_value, COUNT({field_name}) as count FROM {full_table_name}",
                        "difficulty": "Intermediate",
                        "category": "Statistical Analysis"
                    })
                
                elif field_type in ["DATE", "DATETIME", "TIMESTAMP"]:
                    suggestions.append({
                        "description": f"Get date range for {field_name} in {table_name}",
                        "sql_query": f"SELECT MIN({field_name}) as earliest_date, MAX({field_name}) as latest_date FROM {full_table_name}",
                        "difficulty": "Beginner",
                        "category": "Data Exploration"
                    })
        
        # Cross-table queries if multiple tables exist
        tables = list(table_info.get("tables", {}).keys())
        if len(tables) > 1:
            suggestions.append({
                "description": f"Compare record counts across all tables",
                "sql_query": " UNION ALL ".join([f"SELECT '{table}' as table_name, COUNT(*) as record_count FROM `{project_id}.{dataset_id}.{table}`" for table in tables]),
                "difficulty": "Intermediate",
                "category": "Data Comparison"
            })
        
        return suggestions[:20]  # Limit to 20 suggestions
    
    async def get_table_info_with_suggestions(self) -> Dict[str, Any]:
        """Get comprehensive table information with query suggestions."""
        try:
            # Get table information
            table_info = self.get_comprehensive_table_info()
            
            if "error" in table_info:
                return table_info
            
            # Generate query suggestions
            query_suggestions = await self.generate_query_suggestions(table_info)
            
            # Combine results
            result = {
                **table_info,
                "query_suggestions": query_suggestions,
                "suggestion_categories": list(set(suggestion.get("category", "General") for suggestion in query_suggestions))
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting table info with suggestions: {e}")
            return {"error": str(e)}


# Global service instance
table_info_service = TableInfoService()