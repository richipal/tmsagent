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

"""BigQuery prompts, templates, and configuration constants."""

from typing import Dict, List, Any


# Business Rules and Context for Time Management System
BUSINESS_RULES = """
Time Management System Business Rules:

1. ABSENCE REASONS (from absence table):
   - PI = Personal time off
   - SICK = Sick leave  
   - VACATION = Vacation time
   - Various other absence codes in the system

2. ACTIVITY TYPES (from activity table):
   - Activities have 'type' field indicating purpose
   - Activities have 'active' field ('true'/'false') for status
   - Activities have rate_of_pay for compensation calculations
   - Activities are linked to users via user_activities table

3. USER MANAGEMENT:
   - Users have enabled field ('true'/'false') for active status
   - User-manager relationships tracked in user_manager table
   - User locations tracked in user_locations table
   - User roles tracked in user_role table

4. CALCULATION SYSTEM:
   - calculation_rate table contains pay rate configurations
   - time_entry_calculation_rates links entries to rates
   - salary_guide provides reference salary data
   - pay_rate table has rate structures

5. FAVORITES SYSTEM:
   - favorite table stores user bookmark preferences
   - favorite_entry table stores templated time entries
   - favorite_days table configures recurring patterns

6. POSTING AND DATES:
   - posting_date table manages payroll periods
   - cut_off_date field indicates submission deadlines
   - Various date fields track creation and modification times

7. SECURITY AND ACCESS:
   - Users can only see their own data unless they have manager role
   - Managers can view data for their direct reports
   - Location-based access control via user_locations
"""


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
            "hire_date": "Date when employee was hired (DATE)",
            "termination_date": "Date when employee was terminated (DATE, null if active)",
            "employee_number": "Employee's unique number/ID",
            "location_id": "Foreign key to location table - employee's primary work location",
            "department": "Department or division the employee belongs to",
            "job_title": "Employee's job title or position",
            "salary": "Employee's current salary (FLOAT)",
            "pay_type": "Payment type (hourly, salary, etc.)",
            "supervisor_id": "Foreign key to employee table - employee's direct supervisor"
        },
        "business_context": "Employees are the core workforce. They create time entries, take absences, and are managed through the approval workflow."
    },
    
    "location": {
        "description": "Physical locations or work sites where employees can work",
        "columns": {
            "id": "Unique identifier for each location",
            "code": "Short location code for easy reference",
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


# SQL Examples for Training (Fixed for BigQuery compatibility)
SQL_EXAMPLES = [
    {
        "question": "List all the 21st century activity codes",
        "sql": "SELECT code, description FROM activity  WHERE LOWER(description) LIKE '%21st century%'",
        "explanation": "Lists all activity codes and their descriptions that match 21st century"
    },
    
    {
        "question": "Which location does Rosalinda Rodriguez work at?",
        "sql": """SELECT l.code, l.name
                  FROM employee e 
                  JOIN location l ON e.location_id = l.id
                  WHERE LOWER(e.first_name) LIKE LOWER('%Rosalinda%') 
                  AND LOWER(e.last_name) LIKE LOWER('%Rodriguez%')""",
        "explanation": "Gets the location information for employee Rosalinda Rodriguez using case-insensitive name matching"
    },
    
    {
        "question": "Which locations have the most time entries?",
        "sql": """SELECT l.name, l.code, COUNT(te.id) as time_entry_count
                  FROM location l
                  JOIN time_entry te ON l.id = te.location_id
                  GROUP BY l.id, l.name, l.code
                  ORDER BY time_entry_count DESC""",
        "explanation": "Shows locations ordered by the number of time entries recorded"
    },
    
    {
        "question": "What are the most used activity codes?",
        "sql": """SELECT a.code, a.description, COUNT(te.id) as usage_count
                  FROM activity a
                  JOIN time_entry te ON a.id = te.activity_id
                  WHERE a.active = 'true'
                  GROUP BY a.id, a.code, a.description
                  ORDER BY usage_count DESC""",
        "explanation": "Lists activity codes by frequency of use in time entries, for active activities only"
    },
    
    {
        "question": "Show me employees who worked overtime last month",
        "sql": """SELECT DISTINCT e.first_name, e.last_name, l.name as location
                  FROM employee e
                  JOIN time_entry te ON e.id = te.employee_id
                  JOIN activity a ON te.activity_id = a.id
                  JOIN location l ON e.location_id = l.id
                  WHERE a.type IN ('OVERTIME', 'DOUBLE-TIME')
                  AND te.begin_date_time >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)
                  AND te.status_id = 4
                  ORDER BY e.last_name, e.first_name""",
        "explanation": "Finds employees who worked overtime activities in the last month with posted status"
    },
    
    {
        "question": "Show me pending time entries for approval for location 061",
        "sql": """SELECT e.first_name, e.last_name, te.begin_date_time, te.end_date_time, 
                         te.unit as hours, a.description as activity
                  FROM time_entry te
                  JOIN employee e ON te.employee_id = e.id
                  JOIN activity a ON te.activity_id = a.id
                  JOIN location l ON l.id = te.location_id
                  WHERE te.status_id = 1
                  AND l.code = '061'
                  ORDER BY te.begin_date_time DESC""",
        "explanation": "Shows pending time entries for a specific location that need approval"
    },
    
    {
        "question": "What is the current payroll period?",
        "sql": """SELECT posting_date, cut_off_date
                  FROM posting_date
                  WHERE active = 'true'
                  ORDER BY posting_date DESC
                  LIMIT 1""",
        "explanation": "Gets the current active payroll period with posting and cut-off dates"
    },
    
    {
        "question": "How many hours did Rosalinda Rodriguez work in total throughout years?",
        "sql": """
        SELECT
  SUM(
    CASE
      WHEN DATETIME_DIFF(te.end_date_time, te.begin_date_time, MINUTE) = 0
        THEN CAST(te.unit AS FLOAT64)
      ELSE
        ROUND(DATETIME_DIFF(te.end_date_time, te.begin_date_time, MINUTE) / 60.0, 2)
    END
  ) AS total_hours
FROM `adk-rag-462901.data_science_agents.time_entry` AS te
JOIN  `adk-rag-462901.data_science_agents.employee` AS e
ON te.employee_id = e.id
WHERE
  LOWER(e.first_name) LIKE '%rosalinda%'
  AND LOWER(e.last_name) LIKE '%rodriguez%'
  AND te.status_id = 4;  

        """,
        "explanation": "Gets the total number of hours for an employee over all years using BigQuery DATETIME_DIFF function"
    },
    
    {
        "question": "Show me the top 5 employees by hours worked",
        "sql": """SELECT 
  e.first_name, 
  e.last_name,
  SUM(
    CASE 
      WHEN DATETIME_DIFF(te.end_date_time, te.begin_date_time, MINUTE) = 0 
        THEN CAST(te.unit AS FLOAT64)
      ELSE ROUND(DATETIME_DIFF(te.end_date_time, te.begin_date_time, MINUTE)/60.0, 2) 
    END
  ) AS total_hours
FROM 
  `adk-rag-462901.data_science_agents.employee` e
JOIN 
  `adk-rag-462901.data_science_agents.time_entry` te 
ON 
  te.employee_id = e.id
WHERE 
  te.status_id = 4 
GROUP BY 
  e.id, e.first_name, e.last_name 
ORDER BY 
  total_hours DESC 
LIMIT 5;
""",
        "explanation": "Shows top 5 employees by total posted hours worked using BigQuery time functions"
    },

     {
        "question": "Show me employees who worked overtime last month",
        "sql": """SELECT DISTINCT e.first_name, e.last_name, l.name AS location
FROM `adk-rag-462901.data_science_agents.employee` AS e
JOIN `adk-rag-462901.data_science_agents.time_entry` AS te ON e.id = te.employee_id
JOIN `adk-rag-462901.data_science_agents.activity` AS a ON te.activity_id = a.id
JOIN `adk-rag-462901.data_science_agents.location` AS l ON e.location_id = l.id
WHERE a.type = 'OVERTIME'
  AND DATE(te.begin_date_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)
  AND te.status_id = 4
ORDER BY e.last_name, e.first_name
LIMIT 80
""",
        "explanation": "Shows employees who worked overtime last month, this is identified by checking type column in table activity"
    },

     {
        "question": "Show me employees who worked activity code DBOUTM last month at location 075",
        "sql": """SELECT DISTINCT e.first_name, e.last_name, l.name AS location
FROM `adk-rag-462901.data_science_agents.employee` AS e
JOIN `adk-rag-462901.data_science_agents.time_entry` AS te ON e.id = te.employee_id
JOIN `adk-rag-462901.data_science_agents.activity` AS a ON te.activity_id = a.id
JOIN `adk-rag-462901.data_science_agents.location` AS l ON e.location_id = l.id
WHERE a.code = 'DBOUTM'
  AND DATE(te.begin_date_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)
  AND l.code= '075'
  AND te.status_id = 4 
ORDER BY e.last_name, e.first_name
LIMIT 80
""",
        "explanation": "Shows employees who worked activity code DBOUTM last month at location 075, uses code column in table activity"
    }

]


# NL2SQL Prompt Template
def get_nl2sql_prompt_template(project_id: str, dataset_id: str) -> str:
    """Generate the NL2SQL prompt template with project-specific information."""
    return f"""You are a BigQuery SQL expert for a Time Management System. Convert the following natural language question to a valid BigQuery SQL query.

Database Schema:
{{schema}}

Business Context:
{BUSINESS_RULES}

Relevant Table Documentation:
{{documentation}}

Question: {{question}}

Guidelines:
1. Use fully qualified table names: `{project_id}.{dataset_id}.table_name`
2. Limit results to maximum 80 rows using LIMIT clause
3. Use appropriate BigQuery functions and syntax
4. For aggregations, use proper GROUP BY clauses
5. Apply business rules when relevant (e.g., status codes, activity types, workflow states)
6. Use BigQuery-specific functions like DATETIME_DIFF instead of MySQL TIMESTAMPDIFF
7. Use LOWER() instead of LCASE() for case-insensitive comparisons
8. Return only the SQL query, no explanations

Examples based on available tables and business rules:
- "count total users" → SELECT COUNT(*) as total_users FROM `{project_id}.{dataset_id}.user`
- "show active users" → SELECT * FROM `{project_id}.{dataset_id}.user` WHERE enabled = 'true'
- "users by location" → SELECT l.name as location, COUNT(ul.user_id) as user_count FROM `{project_id}.{dataset_id}.location` l JOIN `{project_id}.{dataset_id}.user_locations` ul ON l.id = ul.location_id GROUP BY l.name ORDER BY user_count DESC
- "total absences by reason" → SELECT absence_reason, COUNT(*) as count FROM `{project_id}.{dataset_id}.absence` GROUP BY absence_reason ORDER BY count DESC
- "PI absences" → SELECT COUNT(*) as pi_count FROM `{project_id}.{dataset_id}.absence` WHERE absence_reason = 'PI'
- "vacation absences" → SELECT employee_id, COUNT(*) as vacation_count FROM `{project_id}.{dataset_id}.absence` WHERE absence_reason = 'VACATION' GROUP BY employee_id
- "active activities" → SELECT * FROM `{project_id}.{dataset_id}.activity` WHERE active = 'true'
- "activities by type" → SELECT type, COUNT(*) as count FROM `{project_id}.{dataset_id}.activity` GROUP BY type ORDER BY count DESC
- "user activity assignments" → SELECT u.username, COUNT(ua.activity_id) as activity_count FROM `{project_id}.{dataset_id}.user` u JOIN `{project_id}.{dataset_id}.user_activities` ua ON u.id = ua.user_id GROUP BY u.username
- "favorite entries by user" → SELECT created_by_user_id, COUNT(*) as favorite_count FROM `{project_id}.{dataset_id}.favorite_entry` GROUP BY created_by_user_id
- "calculation rates summary" → SELECT type, MIN(rate) as min_rate, MAX(rate) as max_rate, AVG(rate) as avg_rate FROM `{project_id}.{dataset_id}.calculation_rate` GROUP BY type
- "payroll posting periods" → SELECT posting_date, cut_off_date FROM `{project_id}.{dataset_id}.posting_date` ORDER BY posting_date DESC
- "manager relationships" → SELECT manager_id, COUNT(user_id) as direct_reports FROM `{project_id}.{dataset_id}.user_manager` GROUP BY manager_id
- "user roles distribution" → SELECT role, COUNT(*) as user_count FROM `{project_id}.{dataset_id}.user_role` GROUP BY role ORDER BY user_count DESC

Advanced Training Examples:
- "List all the 21st century activity codes" → SELECT a.code, a.description FROM `{project_id}.{dataset_id}.activity` a WHERE a.description LIKE '%21st century%'
- "Which location does Rosalinda Rodriguez work at?" → SELECT l.code, l.name FROM `{project_id}.{dataset_id}.employee` e JOIN `{project_id}.{dataset_id}.location` l ON e.location_id = l.id WHERE LOWER(e.first_name) LIKE '%rosalinda%' AND LOWER(e.last_name) LIKE '%rodriguez%'
- "Show me the top 5 employees by hours worked" → SELECT e.first_name, e.last_name, SUM(CASE WHEN DATETIME_DIFF(te.end_date_time, te.begin_date_time, MINUTE) = 0 THEN te.unit ELSE ROUND(DATETIME_DIFF(te.end_date_time, te.begin_date_time, MINUTE)/60, 2) END) AS total_hours FROM `{project_id}.{dataset_id}.employee` e JOIN `{project_id}.{dataset_id}.time_entry` te ON te.employee_id = e.id WHERE te.status_id = 4 GROUP BY e.id, e.first_name, e.last_name ORDER BY total_hours DESC LIMIT 5
- "Which locations have the most time entries?" → SELECT l.name, l.code, COUNT(te.id) as time_entry_count FROM `{project_id}.{dataset_id}.location` l JOIN `{project_id}.{dataset_id}.time_entry` te ON l.id = te.location_id GROUP BY l.id, l.name, l.code ORDER BY time_entry_count DESC
- "What are the most used activity codes?" → SELECT a.code, a.description, COUNT(te.id) as usage_count FROM `{project_id}.{dataset_id}.activity` a JOIN `{project_id}.{dataset_id}.time_entry` te ON a.id = te.activity_id WHERE a.active = 'true' GROUP BY a.id, a.code, a.description ORDER BY usage_count DESC
- "Show me employees who worked overtime last month" → SELECT DISTINCT e.first_name, e.last_name, l.name as location FROM `{project_id}.{dataset_id}.employee` e JOIN `{project_id}.{dataset_id}.time_entry` te ON e.id = te.employee_id JOIN `{project_id}.{dataset_id}.activity` a ON te.activity_id = a.id JOIN `{project_id}.{dataset_id}.location` l ON e.location_id = l.id WHERE a.type IN ('OVERTIME', 'DOUBLE-TIME') AND te.begin_date_time >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH) AND te.status_id = 4 ORDER BY e.last_name, e.first_name
- "Show me pending time entries for approval for location 061" → SELECT e.first_name, e.last_name, te.begin_date_time, te.end_date_time, te.unit as hours, a.description as activity FROM `{project_id}.{dataset_id}.time_entry` te JOIN `{project_id}.{dataset_id}.employee` e ON te.employee_id = e.id JOIN `{project_id}.{dataset_id}.activity` a ON te.activity_id = a.id JOIN `{project_id}.{dataset_id}.location` l ON l.id = te.location_id WHERE te.status_id = 1 AND l.code = '061' ORDER BY te.begin_date_time DESC
- "What is the current payroll period?" → SELECT posting_date, cut_off_date FROM `{project_id}.{dataset_id}.posting_date` WHERE active = 'true' ORDER BY posting_date DESC LIMIT 1

SQL Query:"""


# Query examples for different use cases
def get_query_examples() -> Dict[str, List[Dict[str, str]]]:
    """Get categorized query examples for the API."""
    return {
        "Basic Queries": [
            {"question": "List all users", "sql": "SELECT * FROM user LIMIT 80", "difficulty": "Beginner"},
            {"question": "Show active employees", "sql": "SELECT * FROM employee WHERE active = 'true' LIMIT 80", "difficulty": "Beginner"},
            {"question": "List all locations", "sql": "SELECT * FROM location LIMIT 80", "difficulty": "Beginner"}
        ],
        "Time Tracking": [
            {"question": "Show recent time entries", "sql": "SELECT * FROM time_entry ORDER BY created_date DESC LIMIT 80", "difficulty": "Intermediate"},
            {"question": "Time entries pending approval", "sql": "SELECT * FROM time_entry WHERE status_id = 1 LIMIT 80", "difficulty": "Intermediate"},
            {"question": "Posted time entries", "sql": "SELECT * FROM time_entry WHERE status_id = 4 LIMIT 80", "difficulty": "Intermediate"}
        ],
        "Analytics": [
            {"question": "Hours by employee", "sql": "SELECT employee_id, SUM(unit) as total_hours FROM time_entry WHERE status_id = 4 GROUP BY employee_id ORDER BY total_hours DESC LIMIT 80", "difficulty": "Advanced"},
            {"question": "Activity usage frequency", "sql": "SELECT activity_id, COUNT(*) as usage_count FROM time_entry GROUP BY activity_id ORDER BY usage_count DESC LIMIT 80", "difficulty": "Advanced"},
            {"question": "Location time tracking", "sql": "SELECT location_id, COUNT(*) as entry_count FROM time_entry GROUP BY location_id ORDER BY entry_count DESC LIMIT 80", "difficulty": "Advanced"}
        ]
    }


# Helper functions for documentation
def get_table_documentation(table_name: str = None) -> Dict[str, Any]:
    """Get table documentation, optionally for a specific table."""
    if table_name:
        if table_name in TABLE_DOCUMENTATION:
            return {
                "table": table_name,
                "documentation": TABLE_DOCUMENTATION[table_name]
            }
        else:
            return {"error": f"Table '{table_name}' not found in documentation"}
    
    return {
        "total_tables": len(TABLE_DOCUMENTATION),
        "documented_tables": list(TABLE_DOCUMENTATION.keys()),
        "documentation": TABLE_DOCUMENTATION
    }


def get_sql_training_examples() -> Dict[str, Any]:
    """Get categorized SQL training examples."""
    # Categorize examples
    categories = {
        "basic_queries": {
            "description": "Simple SELECT queries with basic filtering",
            "examples": []
        },
        "join_queries": {
            "description": "Multi-table joins and relationship queries",
            "examples": []
        },
        "time_calculation_queries": {
            "description": "Complex time calculations using DATETIME_DIFF and business logic",
            "examples": []
        },
        "workflow_queries": {
            "description": "Status-based and approval workflow queries",
            "examples": []
        },
        "aggregation_queries": {
            "description": "GROUP BY and statistical analysis queries",
            "examples": []
        },
        "location_queries": {
            "description": "Location-based filtering and analysis",
            "examples": []
        }
    }
    
    # Categorize each example
    for example in SQL_EXAMPLES:
        sql_lower = example['sql'].lower()
        
        if 'datetime_diff' in sql_lower or 'case when' in sql_lower:
            categories["time_calculation_queries"]["examples"].append(example)
        elif 'join' in sql_lower:
            categories["join_queries"]["examples"].append(example)
        elif 'status_id' in sql_lower:
            categories["workflow_queries"]["examples"].append(example)
        elif 'location' in sql_lower:
            categories["location_queries"]["examples"].append(example)
        elif 'group by' in sql_lower or 'count(' in sql_lower:
            categories["aggregation_queries"]["examples"].append(example)
        else:
            categories["basic_queries"]["examples"].append(example)
    
    return {
        "total_examples": len(SQL_EXAMPLES),
        "categories": categories,
        "all_examples": SQL_EXAMPLES
    }


def get_relevant_documentation(question_text: str) -> str:
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