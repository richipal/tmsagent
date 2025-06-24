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

"""API endpoints for BigQuery table information and query suggestions."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging

from app.services.table_info_service import table_info_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/table-info")
async def get_table_info() -> Dict[str, Any]:
    """Get comprehensive BigQuery table information."""
    try:
        table_info = table_info_service.get_comprehensive_table_info()
        
        if "error" in table_info:
            raise HTTPException(status_code=500, detail=table_info["error"])
        
        return {
            "success": True,
            "data": table_info
        }
        
    except Exception as e:
        logger.error(f"Error getting table info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/table-info/suggestions")
async def get_query_suggestions() -> Dict[str, Any]:
    """Get intelligent query suggestions based on table schemas."""
    try:
        result = await table_info_service.get_table_info_with_suggestions()
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error getting query suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/table-info/schema")
async def get_schema_only() -> Dict[str, Any]:
    """Get only the schema information for all tables."""
    try:
        table_info = table_info_service.get_comprehensive_table_info()
        
        if "error" in table_info:
            raise HTTPException(status_code=500, detail=table_info["error"])
        
        # Extract only schema information
        schema_info = {
            "database_info": table_info.get("database_info", {}),
            "schema_ddl": table_info.get("schema_ddl", ""),
            "tables": {}
        }
        
        for table_name, details in table_info.get("tables", {}).items():
            schema_info["tables"][table_name] = {
                "full_table_id": details.get("full_table_id"),
                "schema": details.get("schema", []),
                "description": details.get("description", ""),
                "num_rows": details.get("num_rows", 0)
            }
        
        return {
            "success": True,
            "data": schema_info
        }
        
    except Exception as e:
        logger.error(f"Error getting schema info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/table-info/sample-queries")
async def get_sample_queries() -> Dict[str, Any]:
    """Get sample queries categorized by type."""
    try:
        result = await table_info_service.get_table_info_with_suggestions()
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Organize queries by category and difficulty
        organized_queries = {
            "by_category": {},
            "by_difficulty": {
                "Beginner": [],
                "Intermediate": [],
                "Advanced": []
            },
            "total_queries": len(result.get("query_suggestions", []))
        }
        
        for suggestion in result.get("query_suggestions", []):
            category = suggestion.get("category", "General")
            difficulty = suggestion.get("difficulty", "Beginner")
            
            # Group by category
            if category not in organized_queries["by_category"]:
                organized_queries["by_category"][category] = []
            organized_queries["by_category"][category].append(suggestion)
            
            # Group by difficulty
            if difficulty in organized_queries["by_difficulty"]:
                organized_queries["by_difficulty"][difficulty].append(suggestion)
        
        return {
            "success": True,
            "data": organized_queries
        }
        
    except Exception as e:
        logger.error(f"Error getting sample queries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/table-info/table/{table_name}")
async def get_specific_table_info(table_name: str) -> Dict[str, Any]:
    """Get detailed information about a specific table."""
    try:
        table_info = table_info_service.get_comprehensive_table_info()
        
        if "error" in table_info:
            raise HTTPException(status_code=500, detail=table_info["error"])
        
        if table_name not in table_info.get("tables", {}):
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        
        specific_table = table_info["tables"][table_name]
        
        return {
            "success": True,
            "data": {
                "table_info": specific_table,
                "database_info": table_info.get("database_info", {})
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting specific table info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/table-info/query-examples")
async def get_categorized_query_examples() -> Dict[str, Any]:
    """Get query examples categorized by use case."""
    try:
        from app.data_science.sub_agents.bigquery.prompts_config import get_query_examples
        
        query_examples = get_query_examples()
        
        # Count total queries
        total_queries = sum(len(queries) for queries in query_examples.values())
        
        return {
            "success": True,
            "data": {
                "categories": list(query_examples.keys()),
                "total_queries": total_queries,
                "query_examples": query_examples
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting query examples: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/table-info/documentation")
async def get_table_documentation() -> Dict[str, Any]:
    """Get comprehensive table and column documentation."""
    try:
        from app.data_science.sub_agents.bigquery.prompts_config import get_table_documentation
        
        documentation = get_table_documentation()
        
        return {
            "success": True,
            "data": documentation
        }
        
    except Exception as e:
        logger.error(f"Error getting table documentation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/table-info/documentation/{table_name}")
async def get_specific_table_documentation(table_name: str) -> Dict[str, Any]:
    """Get detailed documentation for a specific table."""
    try:
        from app.data_science.sub_agents.bigquery.prompts_config import get_table_documentation
        
        documentation = get_table_documentation(table_name)
        
        if "error" in documentation:
            raise HTTPException(status_code=404, detail=documentation["error"])
        
        return {
            "success": True,
            "data": documentation
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting table documentation for {table_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/table-info/sql-examples")
async def get_sql_training_examples() -> Dict[str, Any]:
    """Get categorized SQL training examples for learning and reference."""
    try:
        from app.data_science.sub_agents.bigquery.prompts_config import get_sql_training_examples
        
        examples = get_sql_training_examples()
        
        return {
            "success": True,
            "data": examples
        }
        
    except Exception as e:
        logger.error(f"Error getting SQL training examples: {e}")
        raise HTTPException(status_code=500, detail=str(e))