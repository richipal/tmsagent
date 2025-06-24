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


# Business rules and other constants are now imported from prompts_config module


# Table and Column Documentation
TABLE_DOCUMENTATION = {
    "user": {
        "description": "System users who can access the time management application",
        "columns": {
            "id": "Unique identifier for each user",
            "email": "User's email address for login and notifications",
            "enabled": "Whether the user account is active (1=enabled, 0=disabled)",
            "password": "Encrypted password for authentication",
            "username": "Unique username for login",
            "employee_id": "Links to the employee record if the user is an employee",
            "created_date": "When the user account was created",
            "last_modified_date": "When the user account was last updated",
            "last_login_date": "Last time the user logged into the system"
        },
        "business_context": "Users can be employees, managers, HR staff, or administrators. Each user has specific permissions based on their role."
    },
    
    "employee": {
        "description": "Employee master data including personal information and employment details",
        "columns": {
            "id": "Unique identifier for each employee",
            "account_number": "Employee's account/payroll number (FLOAT type)",
            "active": "Whether the employee is currently active ('true'/'false' string)",
            "first_name": "Employee's first name",
            "last_name": "Employee's last name", 
            "middle_name": "Employee's middle name or initial",
            "num_workday_hours": "Standard number of hours per workday (FLOAT)",
            "num_workdays": "Number of workdays per year for salary calculations (STRING)",
            "salary": "Annual salary amount (FLOAT)",
            "scname": "Job title or position description",
            "location_id": "Primary work location for the employee",
            "created_date": "When the employee record was created",
            "last_modified_date": "When the employee record was last updated",
            "created_by_user_id": "User who created this employee record",
            "last_modified_by_user_id": "User who last modified this employee record"
        },
        "business_context": "Employees are the core entities who submit time entries. Active employees can log time, while inactive employees are historical records."
    },
    
    "location": {
        "description": "Physical work locations where employees can log time",
        "columns": {
            "id": "Unique identifier for each location",
            "code": "Short code identifier for the location",
            "name": "Full descriptive name of the location"
        },
        "business_context": "Locations represent schools, offices, or work sites. Time entries must be associated with a location for proper cost allocation."
    },
    
    "activity": {
        "description": "Work activities or tasks that employees can log time against",
        "columns": {
            "id": "Unique identifier for each activity",
            "account_number": "Account number for financial reporting",
            "active": "Whether the activity is currently available for use",
            "code": "Short code identifier for the activity",
            "description": "Full description of the work activity",
            "earn_code": "Payroll earning code for this activity",
            "expiration_date": "When this activity expires and becomes unavailable",
            "rate_of_pay": "Hourly rate for this activity",
            "type": "Category of activity (REGULAR, OVERTIME, DOUBLE-TIME, etc.)",
            "job_code": "Job classification code"
        },
        "business_context": "Activities define what type of work was performed. Different activities may have different pay rates and reporting requirements."
    },
    
    "time_entry": {
        "description": "Individual time records submitted by employees for payroll processing",
        "columns": {
            "id": "Unique identifier for each time entry record",
            "activity_id": "Foreign key to activity table - type of work performed",
            "employee_id": "Foreign key to employee table - employee who performed the work",
            "begin_date_time": "Start date and time of work period (DATETIME)",
            "end_date_time": "End date and time of work period (DATETIME)",
            "unit": "Hours worked (FLOAT) - if time difference is 0, use this value; otherwise calculate from time difference",
            "status_id": "Approval workflow status (INTEGER: 0=NEW, 1=SENT_FOR_APPROVAL, 2=APPROVED, 3=DISAPPROVED, 4=POSTED)",
            "created_date": "When the time entry was originally created (DATETIME)",
            "last_modified_date": "When the time entry was last updated (DATETIME)",
            "user_id": "ID of user who created this time entry",
            "description": "Optional description or notes about the work performed",
            "location_id": "Foreign key to location table - where the work was performed",
            "project_id": "Foreign key to project if work is project-specific",
            "rate_id": "Foreign key to rate table for pay calculation",
            "overtime_flag": "Boolean flag indicating if this is overtime work",
            "break_time": "Break time in minutes deducted from total time",
            "approved_by": "User ID of manager who approved this entry",
            "posted_date": "Date when entry was posted to payroll",
            "comments": "Additional comments or approval notes from managers"
        },
        "business_context": "Time entries are the core records for employee time tracking and payroll processing. They flow through a complete approval workflow (NEW → SENT_FOR_APPROVAL → APPROVED/DISAPPROVED → POSTED) before being included in payroll calculations. Each entry captures detailed work information including location, activity type, and overtime status for accurate compensation."
    },
    
    "absence": {
        "description": "Employee absence records for vacation, sick leave, etc.",
        "columns": {
            "id": "Unique identifier for each absence record",
            "absence_reason": "Type of absence (vacation, sick, personal, etc.)",
            "amt_used": "Amount of time taken (usually in days or hours)",
            "out_date": "Date of the absence",
            "employee_id": "Employee who was absent"
        },
        "business_context": "Absence tracking is important for leave management and payroll processing."
    },
    
    "posting_date": {
        "description": "Payroll periods defining when time entries are processed",
        "columns": {
            "id": "Unique identifier for each payroll period",
            "posting_date": "Date when payroll is processed",
            "cut_off_date": "Last date for submitting time entries for this period",
            "is_lunch_fifths": "Whether lunch deductions are calculated in fifths",
            "active": "Whether this payroll period is currently active"
        },
        "business_context": "Payroll periods control when time entries are collected and processed for payment."
    },
    
    "user_role": {
        "description": "Role assignments defining user permissions",
        "columns": {
            "id": "Unique identifier for each role assignment",
            "role": "Role name (ADMIN, MANAGER, EMPLOYEE, SECRETARY, etc.)",
            "user_id": "User who has this role"
        },
        "business_context": "Roles determine what actions users can perform in the system."
    },
    
    "user_manager": {
        "description": "Manager-employee relationships for approval workflows",
        "columns": {
            "id": "Unique identifier for each manager relationship",
            "manager_id": "User ID of the manager",
            "user_id": "User ID of the employee reporting to this manager"
        },
        "business_context": "Manager relationships determine who can approve time entries and access employee data."
    },
    
    "user_activities": {
        "description": "Many-to-many relationship between users and activities they can work on",
        "columns": {
            "user_id": "User who can work on the activity",
            "activity_id": "Activity the user is authorized to work on"
        },
        "business_context": "Controls which activities users can select when creating time entries."
    },
    
    "user_locations": {
        "description": "Many-to-many relationship between users and locations they can work at",
        "columns": {
            "user_id": "User who can work at the location",
            "location_id": "Location the user is authorized to work at"
        },
        "business_context": "Controls which locations users can select when creating time entries."
    },
    
    "calculation_rate": {
        "description": "Pay rate configurations for payroll calculations",
        "columns": {
            "id": "Unique identifier for each rate configuration",
            "multiplier": "Multiplier applied to base rate (e.g., 1.5 for overtime)",
            "num_work_day_hours": "Standard number of hours per work day",
            "num_work_days": "Number of work days in the calculation period",
            "rate": "Hourly rate amount",
            "salary": "Salary classification or band",
            "type": "Type of rate calculation",
            "value": "Additional value used in calculations"
        },
        "business_context": "Rate configurations determine how different types of time are compensated."
    },
    
    "salary_guide": {
        "description": "Salary guide reference data for cost calculations",
        "columns": {
            "scname": "Job title or position description",
            "num_workday_hours": "Standard hours per workday for this position",
            "num_workdays": "Number of workdays per year for this position"
        },
        "business_context": "Provides standard work schedules for different job classifications."
    },
    
    "favorite": {
        "description": "User favorites/bookmarks for quick time entry access",
        "columns": {
            "id": "Unique identifier for each favorite",
            "name": "User-defined name for the favorite",
            "created_by_user_id": "User who created this favorite"
        },
        "business_context": "Allows users to save commonly used time entry combinations for faster data entry."
    },
    
    "favorite_entry": {
        "description": "Favorite entry details for quick time entry templates",
        "columns": {
            "id": "Unique identifier for each favorite entry",
            "begin_date_time": "Default start time for this favorite",
            "end_date_time": "Default end time for this favorite",
            "unit": "Default unit/hours for this favorite",
            "activity_id": "Default activity for this favorite",
            "location_id": "Default location for this favorite",
            "employee_id": "Employee this favorite belongs to"
        },
        "business_context": "Pre-configured time entry templates that users can quickly apply."
    },
    
    "favorite_days": {
        "description": "Favorite days configuration for recurring time entries",
        "columns": {
            "id": "Unique identifier for each day configuration",
            "day": "Day of the week (1=Monday, 7=Sunday)",
            "favorite_id": "Associated favorite record"
        },
        "business_context": "Defines which days of the week a favorite template applies to."
    }
}


# SQL Examples for Training
SQL_EXAMPLES = [
    {
        "question": "List all the 21st century activity codes",
        "sql": "select a.code, a.description from activity a where a.description like '%21st century%';",
        "explanation": "Lists all activity code and their descriptions that match 21st century"
    },
    
    {
        "question": "Which location does Rosalinda Rodriguez work at?",
        "sql": """Select l.code,l.name
                  From employee e 
                  JOIN location l on e.location_id =l.id
                  Where LCASE(e.first_name ) like LCASE('%Rosalinda%') and 
                  LCASE(e.last_name) like LCASE('%Rodriguez%');""",
        "explanation": "Returns location code and name where an employee Rosalinda Rodriguez works"
    },
    
    {
        "question": "How many hours did Rosalinda Rodriguez work in total throught years?",
        "sql": """SELECT 
    SUM(
        CASE 
            WHEN TIMESTAMPDIFF(MINUTE, begin_date_time, te.end_date_time) = 0 
                THEN unit 
            ELSE ROUND(TIMESTAMPDIFF(MINUTE, begin_date_time, te.end_date_time)/60, 2) 
        END
    ) AS total_hours
    FROM employee e
    JOIN time_entry te ON te.employee_id = e.id
    WHERE LCASE(e.first_name) LIKE LCASE('%Rosalinda%') 
    AND LCASE(e.last_name) LIKE LCASE('%Rodriguez%');;""",
        "explanation": "Gets the total number of hours for an employee over all the years"
    },
    
    {
        "question": "Show me the top 5 employees by hours worked",
        "sql": """SELECT e.first_name, e.last_name,
    SUM(
        CASE 
            WHEN TIMESTAMPDIFF(MINUTE, begin_date_time, te.end_date_time) = 0 
                THEN unit 
            ELSE ROUND(TIMESTAMPDIFF(MINUTE, begin_date_time, te.end_date_time)/60, 2) 
        END
    ) AS total_hours
    FROM employee e
    JOIN time_entry te ON te.employee_id = e.id
    WHERE te.status_id = 4 
                 GROUP BY e.id, e.first_name, e.last_name 
                 ORDER BY total_hours DESC 
                 LIMIT 5;""",
        "explanation": "Shows employees with most posted hours worked"
    },
    
    {
        "question": "Which locations have the most time entries?",
        "sql": """SELECT l.name, l.code, COUNT(te.id) as time_entry_count 
                 FROM location l 
                 JOIN time_entry te ON l.id = te.location_id 
                 GROUP BY l.id, l.name, l.code 
                 ORDER BY time_entry_count DESC;""",
        "explanation": "Ranks locations by number of time entries submitted"
    },
    
    {
        "question": "What are the most used activity codes?",
        "sql": """SELECT a.code, a.description, COUNT(te.id) as usage_count 
                 FROM activity a 
                 JOIN time_entry te ON a.id = te.activity_id 
                 WHERE a.active = 1 
                 GROUP BY a.id, a.code, a.description 
                 ORDER BY usage_count DESC;""",
        "explanation": "Shows which activities are used most frequently in time entries"
    },
    
    {
        "question": "Show me employees who worked overtime last month",
        "sql": """SELECT DISTINCT e.first_name, e.last_name, l.name as location 
                 FROM employee e 
                 JOIN time_entry te ON e.id = te.employee_id 
                 JOIN activity a ON te.activity_id = a.id 
                 JOIN location l ON e.location_id = l.id 
                 WHERE a.type IN ('OVERTIME', 'DOUBLE-TIME') 
                 AND te.begin_date_time >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH) 
                 AND te.status_id = 4 
                 ORDER BY e.last_name, e.first_name;""",
        "explanation": "Finds employees who worked overtime in the past month"
    },
    
    {
        "question": "Show me pending time entries for approval for location 061",
        "sql": """SELECT e.first_name, e.last_name, te.begin_date_time, te.end_date_time, 
                        te.total as hours, a.description as activity
                 FROM time_entry te 
                 JOIN employee e ON te.employee_id = e.id 
                 JOIN activity a ON te.activity_id = a.id
                 JOIN location l ON l.id =te.location_id
                 WHERE te.status_id = 1 and l.code='061'
                 ORDER BY te.begin_date_time DESC;""",
        "explanation": "Lists time entries that are pending manager approval for location 061"
    },
    
    {
        "question": "What is the current payroll period?",
        "sql": """SELECT posting_date, cut_off_date 
                 FROM posting_date 
                 WHERE active = 1 
                 ORDER BY posting_date DESC 
                 LIMIT 1;""",
        "explanation": "Shows the currently active payroll period"
    }
]


class BigQueryManager:
    """Manages BigQuery connections and operations."""
    
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.dataset_id = os.getenv('BIGQUERY_DATASET_ID', 'data_science_agents')
        self.location = os.getenv('BIGQUERY_LOCATION', 'US')
        
        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required")
        
        try:
            self.client = bigquery.Client(project=self.project_id)
            logger.info(f"Initialized BigQuery client for project: {self.project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
            raise
    
    def get_datasets(self) -> List[str]:
        """Get list of available datasets."""
        try:
            datasets = list(self.client.list_datasets())
            return [dataset.dataset_id for dataset in datasets]
        except Exception as e:
            logger.error(f"Error fetching datasets: {e}")
            return []
    
    def get_tables(self, dataset_id: Optional[str] = None) -> List[str]:
        """Get list of tables in a dataset."""
        dataset_id = dataset_id or self.dataset_id
        try:
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
            job_config.use_query_cache = True
            
            if dry_run:
                query_job = self.client.query(query, job_config=job_config)
                return {
                    "valid": True,
                    "bytes_processed": query_job.total_bytes_processed,
                    "bytes_billed": query_job.total_bytes_billed
                }
            else:
                query_job = self.client.query(query, job_config=job_config)
                results = query_job.result()
                
                rows = []
                for row in results:
                    rows.append(dict(row))
                
                return {
                    "rows": rows,
                    "total_rows": len(rows),
                    "bytes_processed": query_job.total_bytes_processed,
                    "bytes_billed": query_job.total_bytes_billed,
                    "job_id": query_job.job_id
                }
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return {"error": str(e)}


# Global BigQuery manager instance
bq_manager = BigQueryManager()


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
            "location": bq_manager.location,
            "available_datasets": datasets,
            "tables": tables,
            "bq_ddl_schema": schema_ddl,
            "connection_info": {
                "type": "BigQuery",
                "authentication": "application_default_credentials",
                "location": bq_manager.location
            }
        }
    except Exception as e:
        logger.error(f"Error getting database settings: {e}")
        return {
            "use_database": "BigQuery",
            "project_id": bq_manager.project_id,
            "dataset_id": bq_manager.dataset_id,
            "location": bq_manager.location,
            "available_datasets": [],
            "tables": [],
            "bq_ddl_schema": "-- Error fetching schema",
            "connection_info": {
                "type": "BigQuery",
                "authentication": "application_default_credentials",
                "location": bq_manager.location
            },
            "error": str(e)
        }


async def initial_bq_nl2sql(question: str, callback_context: Any = None) -> Dict[str, Any]:
    """Convert natural language to SQL using the baseline method."""
    try:
        # Get database settings
        db_settings = get_database_settings()
        
        # Configure the generative AI model
        api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('ADK_API_KEY')
        if not api_key:
            return {"error": "API key not configured"}
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Get relevant table documentation for the query
        def get_relevant_documentation(question_text):
            """Extract relevant table documentation based on the question."""
            question_lower = question_text.lower()
            relevant_docs = []
            
            for table_name, table_info in TABLE_DOCUMENTATION.items():
                # Check if table name or related terms are mentioned
                if (table_name in question_lower or 
                    any(keyword in question_lower for keyword in table_info.get('keywords', [])) or
                    any(col_name in question_lower for col_name in table_info['columns'].keys())):
                    
                    doc_section = f"\nTable: {table_name}\n"
                    doc_section += f"Description: {table_info['description']}\n"
                    doc_section += f"Business Context: {table_info['business_context']}\n"
                    doc_section += "Key Columns:\n"
                    
                    for col_name, col_desc in table_info['columns'].items():
                        doc_section += f"  - {col_name}: {col_desc}\n"
                    
                    relevant_docs.append(doc_section)
            
            return "\n".join(relevant_docs) if relevant_docs else ""
        
        relevant_table_docs = get_relevant_documentation(question)
        
        # Create the NL2SQL prompt with business context and table documentation
        prompt = f"""You are a BigQuery SQL expert for a Time Management System. Convert the following natural language question to a valid BigQuery SQL query.

Database Schema:
{db_settings.get('bq_ddl_schema', '')}

Business Context:
{BUSINESS_RULES}

Relevant Table Documentation:
{relevant_table_docs}

Question: {question}

Guidelines:
1. Use fully qualified table names: `{db_settings.get('project_id')}.{db_settings.get('dataset_id')}.table_name`
2. Limit results to maximum 80 rows using LIMIT clause
3. Use appropriate BigQuery functions and syntax
4. For aggregations, use proper GROUP BY clauses
5. Apply business rules when relevant (e.g., status codes, activity types, workflow states)
6. Return only the SQL query, no explanations

Examples based on available tables and business rules:
- "count total users" → SELECT COUNT(*) as total_users FROM `project.dataset.user`
- "show active users" → SELECT * FROM `project.dataset.user` WHERE enabled = 'true'
- "users by location" → SELECT l.name as location, COUNT(ul.user_id) as user_count FROM `project.dataset.location` l JOIN `project.dataset.user_locations` ul ON l.id = ul.location_id GROUP BY l.name ORDER BY user_count DESC
- "total absences by reason" → SELECT absence_reason, COUNT(*) as count FROM `project.dataset.absence` GROUP BY absence_reason ORDER BY count DESC
- "PI absences" → SELECT COUNT(*) as pi_count FROM `project.dataset.absence` WHERE absence_reason = 'PI'
- "vacation absences" → SELECT employee_id, COUNT(*) as vacation_count FROM `project.dataset.absence` WHERE absence_reason = 'VACATION' GROUP BY employee_id
- "active activities" → SELECT * FROM `project.dataset.activity` WHERE active = 'true'
- "activities by type" → SELECT type, COUNT(*) as count FROM `project.dataset.activity` GROUP BY type ORDER BY count DESC
- "user activity assignments" → SELECT u.username, COUNT(ua.activity_id) as activity_count FROM `project.dataset.user` u JOIN `project.dataset.user_activities` ua ON u.id = ua.user_id GROUP BY u.username
- "favorite entries by user" → SELECT created_by_user_id, COUNT(*) as favorite_count FROM `project.dataset.favorite_entry` GROUP BY created_by_user_id
- "calculation rates summary" → SELECT type, MIN(rate) as min_rate, MAX(rate) as max_rate, AVG(rate) as avg_rate FROM `project.dataset.calculation_rate` GROUP BY type
- "payroll posting periods" → SELECT posting_date, cut_off_date FROM `project.dataset.posting_date` ORDER BY posting_date DESC
- "manager relationships" → SELECT manager_id, COUNT(user_id) as direct_reports FROM `project.dataset.user_manager` GROUP BY manager_id
- "user roles distribution" → SELECT role, COUNT(*) as user_count FROM `project.dataset.user_role` GROUP BY role ORDER BY user_count DESC

Advanced Training Examples:
- "List all the 21st century activity codes" → SELECT a.code, a.description FROM `project.dataset.activity` a WHERE a.description LIKE '%21st century%'
- "Which location does Rosalinda Rodriguez work at?" → SELECT l.code, l.name FROM `project.dataset.employee` e JOIN `project.dataset.location` l ON e.location_id = l.id WHERE LOWER(e.first_name) LIKE '%rosalinda%' AND LOWER(e.last_name) LIKE '%rodriguez%'
- "Show me the top 5 employees by hours worked" → SELECT e.first_name, e.last_name, SUM(CASE WHEN TIMESTAMPDIFF(MINUTE, te.begin_date_time, te.end_date_time) = 0 THEN te.unit ELSE ROUND(TIMESTAMPDIFF(MINUTE, te.begin_date_time, te.end_date_time)/60, 2) END) AS total_hours FROM `project.dataset.employee` e JOIN `project.dataset.time_entry` te ON te.employee_id = e.id WHERE te.status_id = 4 GROUP BY e.id, e.first_name, e.last_name ORDER BY total_hours DESC LIMIT 5
- "Which locations have the most time entries?" → SELECT l.name, l.code, COUNT(te.id) as time_entry_count FROM `project.dataset.location` l JOIN `project.dataset.time_entry` te ON l.id = te.location_id GROUP BY l.id, l.name, l.code ORDER BY time_entry_count DESC
- "What are the most used activity codes?" → SELECT a.code, a.description, COUNT(te.id) as usage_count FROM `project.dataset.activity` a JOIN `project.dataset.time_entry` te ON a.id = te.activity_id WHERE a.active = 1 GROUP BY a.id, a.code, a.description ORDER BY usage_count DESC
- "Show me employees who worked overtime last month" → SELECT DISTINCT e.first_name, e.last_name, l.name as location FROM `project.dataset.employee` e JOIN `project.dataset.time_entry` te ON e.id = te.employee_id JOIN `project.dataset.activity` a ON te.activity_id = a.id JOIN `project.dataset.location` l ON e.location_id = l.id WHERE a.type IN ('OVERTIME', 'DOUBLE-TIME') AND te.begin_date_time >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH) AND te.status_id = 4 ORDER BY e.last_name, e.first_name
- "Show me pending time entries for approval for location 061" → SELECT e.first_name, e.last_name, te.begin_date_time, te.end_date_time, te.total as hours, a.description as activity FROM `project.dataset.time_entry` te JOIN `project.dataset.employee` e ON te.employee_id = e.id JOIN `project.dataset.activity` a ON te.activity_id = a.id JOIN `project.dataset.location` l ON l.id = te.location_id WHERE te.status_id = 1 AND l.code = '061' ORDER BY te.begin_date_time DESC
- "What is the current payroll period?" → SELECT posting_date, cut_off_date FROM `project.dataset.posting_date` WHERE active = 1 ORDER BY posting_date DESC LIMIT 1

SQL Query:"""
        
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
        
        # Check for destructive operations
        destructive_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER', 'ROUND']
        sql_upper = sql_query.upper()
        
        for keyword in destructive_keywords:
            if keyword in sql_upper:
                return {"error": f"Destructive operation '{keyword}' not allowed"}
        
        # First, validate with dry run
        validation_result = bq_manager.execute_query(sql_query, dry_run=True)
        
        if "error" in validation_result:
            return {"error": f"Query validation failed: {validation_result['error']}"}
        
        # If validation passes, execute the query
        execution_result = bq_manager.execute_query(sql_query, dry_run=False)
        
        if "error" in execution_result:
            return {"error": f"Query execution failed: {execution_result['error']}"}
        
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


def get_available_tables(dataset_id: Optional[str] = None) -> List[str]:
    """Get list of available tables in a dataset."""
    return bq_manager.get_tables(dataset_id)


def get_table_documentation(table_name: Optional[str] = None) -> Dict[str, Any]:
    """Get detailed documentation for tables and columns."""
    if table_name:
        # Return documentation for specific table
        if table_name in TABLE_DOCUMENTATION:
            return {
                "table": table_name,
                "documentation": TABLE_DOCUMENTATION[table_name]
            }
        else:
            return {"error": f"Documentation not found for table: {table_name}"}
    else:
        # Return all table documentation
        return {
            "total_tables": len(TABLE_DOCUMENTATION),
            "documented_tables": list(TABLE_DOCUMENTATION.keys()),
            "documentation": TABLE_DOCUMENTATION
        }


def get_sql_training_examples() -> Dict[str, Any]:
    """Get SQL training examples for learning and reference."""
    # Categorize examples by complexity and use case
    categorized_examples = {
        "basic_queries": [],
        "join_queries": [],
        "aggregation_queries": [],
        "time_calculation_queries": [],
        "workflow_queries": [],
        "location_queries": []
    }
    
    for example in SQL_EXAMPLES:
        question_lower = example["question"].lower()
        sql_lower = example["sql"].lower()
        
        # Categorize based on query characteristics
        if "join" in sql_lower:
            if "time_entry" in sql_lower and ("timestampdiff" in sql_lower or "unit" in sql_lower):
                categorized_examples["time_calculation_queries"].append(example)
            else:
                categorized_examples["join_queries"].append(example)
        elif "count" in sql_lower or "sum" in sql_lower or "group by" in sql_lower:
            categorized_examples["aggregation_queries"].append(example)
        elif "status_id" in sql_lower or "approval" in question_lower or "pending" in question_lower:
            categorized_examples["workflow_queries"].append(example)
        elif "location" in question_lower or "location" in sql_lower:
            categorized_examples["location_queries"].append(example)
        else:
            categorized_examples["basic_queries"].append(example)
    
    return {
        "total_examples": len(SQL_EXAMPLES),
        "categories": {
            "basic_queries": {
                "description": "Simple SELECT queries with basic filtering",
                "examples": categorized_examples["basic_queries"]
            },
            "join_queries": {
                "description": "Queries involving joins between multiple tables",
                "examples": categorized_examples["join_queries"]
            },
            "aggregation_queries": {
                "description": "Queries with GROUP BY, COUNT, SUM, and other aggregations",
                "examples": categorized_examples["aggregation_queries"]
            },
            "time_calculation_queries": {
                "description": "Complex time calculations using TIMESTAMPDIFF and business logic",
                "examples": categorized_examples["time_calculation_queries"]
            },
            "workflow_queries": {
                "description": "Queries related to approval workflow and status management",
                "examples": categorized_examples["workflow_queries"]
            },
            "location_queries": {
                "description": "Queries focused on location-based analysis",
                "examples": categorized_examples["location_queries"]
            }
        },
        "all_examples": SQL_EXAMPLES
    }


def get_query_examples() -> Dict[str, List[Dict[str, str]]]:
    """Get categorized query examples based on available tables."""
    project = bq_manager.project_id
    dataset = bq_manager.dataset_id
    
    return {
        "user_management": [
            {
                "description": "Count total active users",
                "query": f"SELECT COUNT(*) as active_users FROM `{project}.{dataset}.user` WHERE enabled = 'true'"
            },
            {
                "description": "Find users who haven't logged in recently",
                "query": f"SELECT username, email, last_login_date FROM `{project}.{dataset}.user` WHERE last_login_date < DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)"
            },
            {
                "description": "User activity summary",
                "query": f"""SELECT u.username, u.email, COUNT(DISTINCT ua.activity_id) as activities, 
                            COUNT(DISTINCT ul.location_id) as locations 
                            FROM `{project}.{dataset}.user` u 
                            LEFT JOIN `{project}.{dataset}.user_activities` ua ON u.id = ua.user_id 
                            LEFT JOIN `{project}.{dataset}.user_locations` ul ON u.id = ul.user_id 
                            GROUP BY u.username, u.email 
                            ORDER BY activities DESC"""
            }
        ],
        "absence_tracking": [
            {
                "description": "Absence summary by reason",
                "query": f"SELECT absence_reason, COUNT(*) as count, SUM(amt_used) as total_hours FROM `{project}.{dataset}.absence` GROUP BY absence_reason ORDER BY count DESC"
            },
            {
                "description": "Employee absence patterns",
                "query": f"""SELECT employee_id, COUNT(*) as absence_count, AVG(amt_used) as avg_duration 
                            FROM `{project}.{dataset}.absence` 
                            GROUP BY employee_id 
                            HAVING COUNT(*) > 5 
                            ORDER BY absence_count DESC"""
            },
            {
                "description": "Monthly absence trends",
                "query": f"""SELECT DATE_TRUNC(out_date, MONTH) as month, COUNT(*) as absences, 
                            SUM(amt_used) as total_hours 
                            FROM `{project}.{dataset}.absence` 
                            WHERE out_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
                            GROUP BY month 
                            ORDER BY month DESC"""
            }
        ],
        "activity_management": [
            {
                "description": "Active activities by type",
                "query": f"SELECT type, COUNT(*) as count FROM `{project}.{dataset}.activity` WHERE active = 'true' GROUP BY type"
            },
            {
                "description": "Activities with high thresholds",
                "query": f"""SELECT a.code, a.description, at.threshold, l.name as location
                            FROM `{project}.{dataset}.activity` a
                            JOIN `{project}.{dataset}.activity_threshold` at ON a.id = at.activity_id
                            JOIN `{project}.{dataset}.location` l ON at.location_id = l.id
                            WHERE at.active = 'true' AND at.threshold > 100
                            ORDER BY at.threshold DESC"""
            }
        ],
        "location_analytics": [
            {
                "description": "User distribution by location",
                "query": f"""SELECT l.name as location, l.code, COUNT(ul.user_id) as user_count 
                            FROM `{project}.{dataset}.location` l 
                            LEFT JOIN `{project}.{dataset}.user_locations` ul ON l.id = ul.location_id 
                            GROUP BY l.name, l.code 
                            ORDER BY user_count DESC"""
            },
            {
                "description": "Location activity summary",
                "query": f"""SELECT l.name, COUNT(DISTINCT u.id) as users, COUNT(DISTINCT a.id) as activities
                            FROM `{project}.{dataset}.location` l
                            LEFT JOIN `{project}.{dataset}.user_locations` ul ON l.id = ul.location_id
                            LEFT JOIN `{project}.{dataset}.user` u ON ul.user_id = u.id
                            LEFT JOIN `{project}.{dataset}.user_activities` ua ON u.id = ua.user_id
                            LEFT JOIN `{project}.{dataset}.activity` a ON ua.activity_id = a.id
                            GROUP BY l.name"""
            }
        ],
        "favorites_and_templates": [
            {
                "description": "Favorite entries by user (template usage)",
                "query": f"""SELECT fe.created_by_user_id, u.username, COUNT(*) as favorite_count
                            FROM `{project}.{dataset}.favorite_entry` fe 
                            JOIN `{project}.{dataset}.user` u ON fe.created_by_user_id = u.id
                            GROUP BY fe.created_by_user_id, u.username 
                            ORDER BY favorite_count DESC"""
            },
            {
                "description": "Favorite days configuration analysis",
                "query": f"""SELECT fd.day, COUNT(*) as usage_count
                            FROM `{project}.{dataset}.favorite_days` fd 
                            GROUP BY fd.day 
                            ORDER BY fd.day"""
            },
            {
                "description": "Recent favorite entries by location",
                "query": f"""SELECT l.name as location, COUNT(fe.id) as entry_count
                            FROM `{project}.{dataset}.favorite_entry` fe 
                            JOIN `{project}.{dataset}.location` l ON fe.location_id = l.id
                            WHERE DATE(fe.created_date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                            GROUP BY l.name 
                            ORDER BY entry_count DESC"""
            }
        ],
        "activity_analysis": [
            {
                "description": "Activities by type and status",
                "query": f"""SELECT a.type, a.active, COUNT(*) as activity_count, AVG(a.rate_of_pay) as avg_rate
                            FROM `{project}.{dataset}.activity` a 
                            GROUP BY a.type, a.active 
                            ORDER BY activity_count DESC"""
            },
            {
                "description": "Activity usage by users",
                "query": f"""SELECT a.code, a.description, COUNT(ua.user_id) as user_count
                            FROM `{project}.{dataset}.activity` a 
                            LEFT JOIN `{project}.{dataset}.user_activities` ua ON a.id = ua.activity_id
                            WHERE a.active = 'true'
                            GROUP BY a.code, a.description 
                            ORDER BY user_count DESC"""
            }
        ],
        "payroll_analysis": [
            {
                "description": "Pay rate analysis by activity type",
                "query": f"""SELECT a.type, MIN(a.rate_of_pay) as min_rate, MAX(a.rate_of_pay) as max_rate, 
                            AVG(a.rate_of_pay) as avg_rate, COUNT(*) as activity_count
                            FROM `{project}.{dataset}.activity` a 
                            WHERE a.rate_of_pay IS NOT NULL 
                            GROUP BY a.type"""
            },
            {
                "description": "Calculation rates by type and salary band",
                "query": f"""SELECT cr.type, cr.salary, MIN(cr.rate) as min_rate, MAX(cr.rate) as max_rate, 
                            AVG(cr.rate) as avg_rate, COUNT(*) as rate_count
                            FROM `{project}.{dataset}.calculation_rate` cr 
                            GROUP BY cr.type, cr.salary 
                            ORDER BY avg_rate DESC"""
            }
        ],
        "compliance_reporting": [
            {
                "description": "Posting date compliance tracking",
                "query": f"""SELECT pd.posting_date, pd.cut_off_date, pd.active,
                            CASE WHEN pd.cut_off_date < CURRENT_DATE() THEN 'Past Due' ELSE 'Open' END as status
                            FROM `{project}.{dataset}.posting_date` pd 
                            ORDER BY pd.posting_date DESC"""
            },
            {
                "description": "Manager workload distribution",
                "query": f"""SELECT um.manager_id, COUNT(um.user_id) as direct_reports,
                            (SELECT username FROM `{project}.{dataset}.user` WHERE id = um.manager_id) as manager_name
                            FROM `{project}.{dataset}.user_manager` um 
                            GROUP BY um.manager_id 
                            ORDER BY direct_reports DESC"""
            },
            {
                "description": "User access audit by location",
                "query": f"""SELECT l.name as location, COUNT(ul.user_id) as user_count,
                            COUNT(CASE WHEN u.enabled = 'true' THEN 1 END) as active_users
                            FROM `{project}.{dataset}.location` l 
                            LEFT JOIN `{project}.{dataset}.user_locations` ul ON l.id = ul.location_id
                            LEFT JOIN `{project}.{dataset}.user` u ON ul.user_id = u.id
                            GROUP BY l.name 
                            ORDER BY user_count DESC"""
            }
        ],
        "data_quality": [
            {
                "description": "Check for users without locations",
                "query": f"""SELECT u.username, u.email 
                            FROM `{project}.{dataset}.user` u 
                            LEFT JOIN `{project}.{dataset}.user_locations` ul ON u.id = ul.user_id 
                            WHERE ul.user_id IS NULL AND u.enabled = 'true'"""
            },
            {
                "description": "Activities without valid rate information",
                "query": f"""SELECT a.code, a.description, a.type 
                            FROM `{project}.{dataset}.activity` a 
                            WHERE a.active = 'true' AND (a.rate_of_pay IS NULL OR a.rate_of_pay = 0)"""
            },
            {
                "description": "Orphaned favorite entries",
                "query": f"""SELECT fe.id, fe.activity_id, fe.location_id
                            FROM `{project}.{dataset}.favorite_entry` fe 
                            LEFT JOIN `{project}.{dataset}.activity` a ON fe.activity_id = a.id 
                            LEFT JOIN `{project}.{dataset}.location` l ON fe.location_id = l.id
                            WHERE a.id IS NULL OR l.id IS NULL"""
            }
        ]
    }