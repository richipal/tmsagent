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

"""BigQuery tools for Natural Language to SQL conversion and execution."""

import os
import re
import logging
from typing import Dict, Any, List, Optional
from google.cloud import bigquery
from google.cloud.exceptions import NotFound, GoogleCloudError
import google.generativeai as genai
from dotenv import load_dotenv

# Import modular components
from .prompts_config import (
    BUSINESS_RULES,
    TABLE_DOCUMENTATION,
    SQL_EXAMPLES,
    get_nl2sql_prompt_template,
    get_query_examples,
    get_table_documentation,
    get_sql_training_examples,
    get_relevant_documentation
)

load_dotenv()
logger = logging.getLogger(__name__)


class BigQueryManager:
    """Manages BigQuery connections and operations."""
    
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.dataset_id = os.getenv('BIGQUERY_DATASET_ID') or os.getenv('BQ_DATASET_ID', 'tms_dataset')
        
        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required")
        
        try:
            self.client = bigquery.Client(project=self.project_id)
            logger.info(f"BigQuery client initialized for project: {self.project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
            raise

    def get_datasets(self) -> List[str]:
        """Get list of available datasets in the project."""
        try:
            datasets = list(self.client.list_datasets())
            return [dataset.dataset_id for dataset in datasets]
        except Exception as e:
            logger.error(f"Error fetching datasets: {e}")
            return []

    def get_tables(self, dataset_id: str = None) -> List[str]:
        """Get list of tables in the specified dataset."""
        try:
            dataset_id = dataset_id or self.dataset_id
            dataset_ref = self.client.dataset(dataset_id)
            tables = list(self.client.list_tables(dataset_ref))
            return [table.table_id for table in tables]
        except NotFound:
            logger.warning(f"Dataset {dataset_id} not found")
            return []
        except Exception as e:
            logger.error(f"Error fetching tables from {dataset_id}: {e}")
            return []
    
    def get_schema_ddl(self) -> str:
        """Get DDL schema for available tables with table descriptions."""
        tables = self.get_tables()
        schema_parts = []
        
        # Add helpful table descriptions with business context
        table_descriptions = {
            "user": "User accounts and authentication information for the time management system",
            "employee": "Employee master data including personal information, employment details, and location assignments",
            "activity": "Activities and tasks - includes types like REGULAR, OVERTIME, VACATION, SICK, etc.",
            "absence": "Employee absence records and leave tracking",
            "location": "Physical locations or offices where work is performed",
            "pay_rate": "Payment rate configurations for different activity types",
            "time_entry": "Core time tracking records with status workflow (0=NEW, 1=SENT_FOR_APPROVAL, 2=APPROVED, 3=DISAPPROVED, 4=POSTED)",
            "user_activities": "Many-to-many relationship between users and activities they can work on",
            "user_locations": "Many-to-many relationship between users and locations they can work at",
            "user_role": "User role assignments for security and access control",
            "user_manager": "Manager-employee relationships for approval workflow",
            "calculation_rate": "Rate calculation configurations for payroll processing",
            "time_entry_calculation_rates": "Links time entries to their calculation rates",
            "salary_guide": "Salary guide reference data for cost calculations",
            "posting_date": "Payroll posting periods with cut-off dates for time entry submission",
            "favorite": "User favorites/bookmarks for quick time entry access",
            "activity_threshold": "Activity threshold configurations by location",
            "terminal_pay": "Terminal pay configurations for employee separations",
            "stipend": "Stipend configurations for special payments",
            "favorite_days": "Favorite days configuration for recurring time entries",
            "favorite_entry": "Favorite entry details for quick time entry templates"
        }
        
        for table_id in tables:
            try:
                table_ref = self.client.dataset(self.dataset_id).table(table_id)
                table = self.client.get_table(table_ref)
                
                # Add table description comment
                if table_id in table_descriptions:
                    schema_parts.append(f"-- {table_descriptions[table_id]}")
                
                schema_parts.append(f"CREATE TABLE `{self.project_id}.{self.dataset_id}.{table_id}` (")
                for field in table.schema:
                    field_def = f"  {field.name} {field.field_type}"
                    if field.mode == "REQUIRED":
                        field_def += " NOT NULL"
                    if field.description:
                        field_def += f" -- {field.description}"
                    schema_parts.append(field_def + ",")
                
                # Remove last comma and close table definition
                if schema_parts[-1].endswith(","):
                    schema_parts[-1] = schema_parts[-1][:-1]
                schema_parts.append(");")
                schema_parts.append("")  # Empty line between tables
                
            except Exception as e:
                logger.error(f"Error getting schema for {table_id}: {e}")
                continue
        
        return "\n".join(schema_parts)
    
    def execute_query(self, query: str, dry_run: bool = False) -> Dict[str, Any]:
        """Execute a BigQuery SQL query."""
        try:
            job_config = bigquery.QueryJobConfig()
            job_config.dry_run = dry_run
            job_config.use_query_cache = False
            
            query_job = self.client.query(query, job_config=job_config)
            
            if dry_run:
                return {
                    "success": True,
                    "message": "Query validation successful",
                    "bytes_processed": query_job.total_bytes_processed,
                    "bytes_billed": query_job.total_bytes_billed
                }
            
            results = query_job.result()
            
            # Convert results to list of dictionaries
            rows = []
            for row in results:
                row_dict = {}
                for key, value in row.items():
                    # Handle BigQuery types that aren't JSON serializable
                    if hasattr(value, 'isoformat'):  # datetime objects
                        row_dict[key] = value.isoformat()
                    elif hasattr(value, '__str__'):  # other objects
                        row_dict[key] = str(value)
                    else:
                        row_dict[key] = value
                rows.append(row_dict)
            
            return {
                "success": True,
                "data": rows,
                "row_count": len(rows),
                "bytes_processed": query_job.total_bytes_processed,
                "bytes_billed": query_job.total_bytes_billed,
                "job_id": query_job.job_id
            }
            
        except Exception as e:
            logger.error(f"BigQuery execution error: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global BigQuery manager instance
bq_manager = BigQueryManager()

# Initialize Gemini for NL2SQL
try:
    api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('ADK_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY or ADK_API_KEY environment variable is required")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    logger.info("Gemini model initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Gemini model: {e}")
    model = None


async def initial_bq_nl2sql(question: str, callback_context: Any = None) -> Dict[str, Any]:
    """Convert natural language to BigQuery SQL using Gemini with entity resolution."""
    try:
        if not model:
            return {"error": "Gemini model not initialized"}
        
        # Step 1: Entity resolution using vector search (with fallback)
        enhanced_question = question
        entity_resolution_context = ""
        
        try:
            from app.services.entity_resolver import entity_resolver
            
            logger.info(f"🔍 Starting NL2SQL with entity resolution for: '{question}'")
            print(f"🔍 Entity Resolution: Processing query '{question}'")
            
            # First, let's see what entities are extracted
            test_entities = entity_resolver.vector_service.extract_entities(question)
            print(f"🔍 Entity Extraction Test:")
            print(f"   Query: '{question}'")
            print(f"   Extracted entities: {len(test_entities)}")
            for ent in test_entities:
                print(f"     - '{ent['text']}' (type: {ent['label']}, confidence: {ent.get('confidence', 'N/A')})")
            
            # Perform entity resolution on the question
            resolution_result = entity_resolver.enhance_query(question, callback_context)
            
            # Use the enhanced query for SQL generation
            enhanced_question = resolution_result.enhanced_query
            
            print(f"🔍 Entity Resolution Results:")
            print(f"   Original: '{question}'")
            print(f"   Enhanced: '{enhanced_question}'")
            print(f"   Confidence: {resolution_result.confidence_score:.3f}")
            print(f"   Fallback: {resolution_result.fallback_to_original}")
            
            # Log entity resolution results
            if resolution_result.resolved_entities:
                logger.info(f"Entity resolution applied: {len(resolution_result.resolved_entities)} entities resolved")
                print(f"   ✅ {len(resolution_result.resolved_entities)} entities resolved:")
                for entity in resolution_result.resolved_entities:
                    logger.info(f"  '{entity.original_text}' → '{entity.resolved_text}' (confidence: {entity.confidence:.3f})")
                    print(f"      '{entity.original_text}' → '{entity.resolved_text}' (confidence: {entity.confidence:.3f})")
                
                # Get entity resolution context for the prompt
                entity_resolution_context = entity_resolver.get_resolution_context_for_prompt(resolution_result)
            else:
                logger.info("No entities resolved, using original query")
                print("   ❌ No entities resolved")
                
        except ImportError as e:
            logger.warning(f"Entity resolution not available (missing dependencies): {e}")
            print(f"❌ Entity resolution not available: {e}")
            logger.info("Falling back to standard NL2SQL without entity resolution")
        except Exception as e:
            logger.error(f"Entity resolution failed: {e}")
            print(f"❌ Entity resolution error: {e}")
            logger.info("Falling back to original query")
        
        # Get database settings
        db_settings = {
            'project_id': bq_manager.project_id,
            'dataset_id': bq_manager.dataset_id,
            'bq_ddl_schema': bq_manager.get_schema_ddl()
        }
        
        # Get relevant documentation for the question
        relevant_table_docs = get_relevant_documentation(enhanced_question)
        
        # Get the modular prompt template
        prompt_template = get_nl2sql_prompt_template(
            db_settings['project_id'], 
            db_settings['dataset_id']
        )
        
        # Build context information for the prompt if available
        context_info = ""
        if callback_context:
            last_query = callback_context.get_state("last_query")
            last_response = callback_context.get_state("last_response")
            query_result = callback_context.get_state("query_result")
            
            if last_query and last_response:
                context_info = f"\n\nCONVERSATION CONTEXT:\nPrevious Question: {last_query}\nPrevious Answer: {last_response}\n"
                
                if query_result and query_result.get("data"):
                    # Include a sample of the actual data for better context understanding
                    sample_data = query_result.get("data", [])[:2]  # First 2 rows
                    context_info += f"Previous Query Data Sample: {sample_data}\n"
        
        # Format the prompt with actual data and context
        final_question = enhanced_question + context_info
        if entity_resolution_context:
            final_question = entity_resolution_context + final_question
        
        prompt = prompt_template.format(
            schema=db_settings['bq_ddl_schema'],
            documentation=relevant_table_docs,
            question=final_question
        )
        
        
        # Generate SQL using the model
        import asyncio
        response = await asyncio.to_thread(model.generate_content, prompt)
        
        if response.candidates and response.candidates[0].content.parts:
            sql_query = response.candidates[0].content.parts[0].text.strip()
            
            # Clean up the SQL query
            sql_query = re.sub(r'^```sql\s*', '', sql_query, flags=re.IGNORECASE)
            sql_query = re.sub(r'\s*```$', '', sql_query)
            sql_query = sql_query.strip()
            
            # Add LIMIT if not present and it's a SELECT query
            if sql_query.upper().startswith('SELECT') and 'LIMIT' not in sql_query.upper():
                sql_query += " LIMIT 80"
            
            # Log the generated SQL for validation
            logger.info(f"\n{'='*60}")
            logger.info(f"NL2SQL Generated Query:")
            logger.info(f"User Question: {question}")
            logger.info(f"Generated SQL:\n{sql_query}")
            logger.info(f"{'='*60}\n")
            print(f"\n🔍 NL2SQL Generated SQL:\n{sql_query}\n")
            
            return {
                "sql_query": sql_query,
                "method": "baseline"
            }
        else:
            return {"error": "Failed to generate SQL query"}
            
    except Exception as e:
        logger.error(f"Error in NL2SQL conversion: {e}")
        return {"error": str(e)}


async def run_bigquery_validation(sql_query: str, callback_context: Any = None) -> Dict[str, Any]:
    """Validate and execute a BigQuery SQL query."""
    try:
        # Clean the SQL query
        sql_query = sql_query.strip()
        if sql_query.startswith('```sql'):
            sql_query = sql_query[6:]
        if sql_query.endswith('```'):
            sql_query = sql_query[:-3]
        sql_query = sql_query.strip()
        
        # Check for destructive operations (removed ROUND as it's not destructive)
        destructive_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER', 'TRUNCATE']
        sql_upper = sql_query.upper()
        
        for keyword in destructive_keywords:
            if keyword in sql_upper:
                return {"error": f"Destructive operation '{keyword}' not allowed"}
        
        # Log the SQL being validated and executed
        logger.info(f"\n{'='*60}")
        logger.info(f"BigQuery Validation & Execution:")
        logger.info(f"SQL Query:\n{sql_query}")
        logger.info(f"{'='*60}\n")
        print(f"\n📊 BigQuery Executing SQL:\n{sql_query}\n")
        
        # First, validate with dry run
        validation_result = bq_manager.execute_query(sql_query, dry_run=True)
        
        if "error" in validation_result:
            logger.error(f"Query validation failed: {validation_result['error']}")
            print(f"❌ Query validation failed: {validation_result['error']}")
            return {"error": f"Query validation failed: {validation_result['error']}"}
        
        # If validation passes, execute the query
        print(f"✅ Query validation passed, executing...")
        execution_result = bq_manager.execute_query(sql_query, dry_run=False)
        
        if "error" in execution_result:
            logger.error(f"Query execution failed: {execution_result['error']}")
            print(f"❌ Query execution failed: {execution_result['error']}")
            return {"error": f"Query execution failed: {execution_result['error']}"}
        
        # Log successful execution
        rows = execution_result.get("data", []) or execution_result.get("rows", [])
        print(f"✅ Query executed successfully!")
        print(f"   Returned {len(rows)} rows")
        if rows:
            print(f"   First row: {rows[0]}")
        logger.info(f"Query executed successfully. Returned {len(rows)} rows.")
        
        # If no results returned, suggest entity corrections
        if not rows and callback_context:
            try:
                from app.services.entity_resolver import entity_resolver
                
                # Get the original user query from context
                original_query = callback_context.get_state("last_query") or "unknown query"
                
                # Analyze the no-results case and get suggestions
                analysis = entity_resolver.handle_no_results_case(original_query, sql_query)
                
                if analysis.get("suggestions"):
                    logger.info(f"No results found. Entity resolution suggestions available: {len(analysis['suggestions'])}")
                    
                    # Add suggestions to the execution result for the agent to handle
                    execution_result["entity_suggestions"] = analysis
                    execution_result["no_results_analysis"] = True
                    
            except ImportError:
                logger.debug("Entity resolution not available for no-results suggestions")
            except Exception as e:
                logger.error(f"Error generating entity suggestions: {e}")
        
        return execution_result
        
    except Exception as e:
        logger.error(f"Error in query validation: {e}")
        return {"error": str(e)}


# Legacy compatibility functions
def get_table_info(table_name: str) -> Dict[str, Any]:
    """Get detailed information about a specific table."""
    try:
        table_ref = bq_manager.client.dataset(bq_manager.dataset_id).table(table_name)
        table = bq_manager.client.get_table(table_ref)
        
        return {
            "table_id": table.table_id,
            "dataset_id": table.dataset_id,
            "project_id": table.project,
            "num_rows": table.num_rows,
            "num_bytes": table.num_bytes,
            "created": table.created.isoformat() if table.created else None,
            "modified": table.modified.isoformat() if table.modified else None,
            "description": table.description or "",
            "size_gb": round(table.num_bytes / (1024**3), 2) if table.num_bytes else 0
        }
    except NotFound:
        return {"error": f"Table {bq_manager.dataset_id}.{table_name} not found"}
    except Exception as e:
        logger.error(f"Error fetching info for {bq_manager.dataset_id}.{table_name}: {e}")
        return {"error": str(e)}


def validate_sql_query(query: str) -> Dict[str, Any]:
    """Validate a SQL query without executing it."""
    try:
        validation_result = bq_manager.execute_query(query, dry_run=True)
        if "error" in validation_result:
            return {
                "is_valid": False,
                "errors": [validation_result["error"]],
                "warnings": [],
                "suggestions": []
            }
        else:
            return {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "suggestions": []
            }
    except Exception as e:
        return {
            "is_valid": False,
            "errors": [str(e)],
            "warnings": [],
            "suggestions": []
        }


def execute_bigquery_sql(query: str) -> Dict[str, Any]:
    """Execute a BigQuery SQL query and return results."""
    return bq_manager.execute_query(query)


def get_available_datasets() -> List[str]:
    """Get list of available datasets in the project."""
    return bq_manager.get_datasets()


def get_database_settings() -> Dict[str, Any]:
    """Get BigQuery database settings and configuration."""
    try:
        datasets = bq_manager.get_datasets()
        tables = bq_manager.get_tables()
        schema_ddl = bq_manager.get_schema_ddl()
        
        return {
            "use_database": "BigQuery",
            "project_id": bq_manager.project_id,
            "dataset_id": bq_manager.dataset_id,
            "available_datasets": datasets,
            "tables": tables,
            "bq_ddl_schema": schema_ddl,
            "connection_info": {
                "type": "BigQuery",
                "authentication": "application_default_credentials"
            }
        }
    except Exception as e:
        logger.error(f"Error getting database settings: {e}")
        return {
            "use_database": "BigQuery",
            "error": str(e)
        }