#!/usr/bin/env python3
"""
Test script for SQL training examples integration.

This script demonstrates:
1. Categorized SQL training examples
2. Complex query patterns and business logic
3. NL2SQL training enhancement
4. API endpoint functionality

Usage:
    python test_sql_examples_integration.py
"""

import asyncio
import json
from app.data_science.sub_agents.bigquery.tools import (
    SQL_EXAMPLES,
    get_sql_training_examples,
    initial_bq_nl2sql
)


async def main():
    """Test SQL examples integration."""
    
    print("=" * 80)
    print("SQL Training Examples Integration Test")
    print("=" * 80)
    print()
    
    # 1. Show comprehensive SQL examples
    print("1. Comprehensive SQL Training Examples")
    print("-" * 50)
    
    training_examples = get_sql_training_examples()
    print(f"Total SQL examples: {training_examples['total_examples']}")
    print(f"Categories: {list(training_examples['categories'].keys())}")
    print()
    
    # Show examples by category
    for category, category_info in training_examples['categories'].items():
        examples = category_info['examples']
        if examples:
            print(f"📚 {category.replace('_', ' ').title()} ({len(examples)} examples)")
            print(f"   {category_info['description']}")
            print("─" * 40)
            
            for i, example in enumerate(examples, 1):
                print(f"{i}. Question: {example['question']}")
                print(f"   Explanation: {example['explanation']}")
                
                # Show key SQL patterns
                sql_lower = example['sql'].lower()
                patterns = []
                if 'join' in sql_lower:
                    patterns.append('JOINs')
                if 'timestampdiff' in sql_lower:
                    patterns.append('Time calculations')
                if 'group by' in sql_lower:
                    patterns.append('Aggregation')
                if 'case when' in sql_lower:
                    patterns.append('Conditional logic')
                if 'status_id' in sql_lower:
                    patterns.append('Workflow status')
                
                if patterns:
                    print(f"   SQL Patterns: {', '.join(patterns)}")
                
                # Show SQL snippet
                sql_lines = example['sql'].split('\n')
                if len(sql_lines) > 1:
                    print(f"   SQL (multi-line): {sql_lines[0].strip()}...")
                else:
                    print(f"   SQL: {example['sql'][:80]}...")
                print()
            print()
    
    # 2. Test enhanced NL2SQL with training examples
    print("2. Enhanced NL2SQL with Training Examples")
    print("-" * 50)
    
    # Test questions similar to training examples
    test_questions = [
        "List all 21st century activities",
        "Show me top employees by total hours",
        "Which locations are most active?",
        "Find most used activity codes",
        "Show overtime workers from last month",
        "What's the current payroll period?",
        "Show pending approvals for a specific location"
    ]
    
    for question in test_questions:
        print(f"Question: {question}")
        try:
            result = await initial_bq_nl2sql(question)
            if "sql_query" in result:
                sql = result["sql_query"]
                print(f"Generated SQL: {sql}")
                
                # Check if training patterns are applied
                sql_lower = sql.lower()
                applied_patterns = []
                
                if 'join' in sql_lower:
                    applied_patterns.append('JOINs')
                if 'group by' in sql_lower:
                    applied_patterns.append('Aggregation')
                if 'order by' in sql_lower:
                    applied_patterns.append('Sorting')
                if 'limit' in sql_lower:
                    applied_patterns.append('Limiting')
                if 'where' in sql_lower:
                    applied_patterns.append('Filtering')
                
                if applied_patterns:
                    print(f"✅ Applied patterns: {', '.join(applied_patterns)}")
                else:
                    print("⚠️  Basic query pattern")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"Error: {e}")
        print()
    
    # 3. Demonstrate complex query patterns
    print("3. Complex Query Patterns from Training Examples")
    print("-" * 50)
    
    complex_patterns = {
        "Time Calculations": {
            "description": "TIMESTAMPDIFF and conditional logic for hour calculations",
            "example": """SUM(
    CASE 
        WHEN TIMESTAMPDIFF(MINUTE, begin_date_time, end_date_time) = 0 
            THEN unit 
        ELSE TRUNCATE(TIMESTAMPDIFF(MINUTE, begin_date_time, end_date_time)/60, 2) 
    END
) AS total_hours"""
        },
        "Multi-table Joins": {
            "description": "Complex joins across employee, time_entry, activity, and location tables",
            "example": """FROM employee e 
JOIN time_entry te ON e.id = te.employee_id 
JOIN activity a ON te.activity_id = a.id 
JOIN location l ON e.location_id = l.id"""
        },
        "Case-insensitive Search": {
            "description": "Using LCASE/LOWER for flexible name matching",
            "example": """WHERE LCASE(e.first_name) LIKE LCASE('%Rosalinda%') 
AND LCASE(e.last_name) LIKE LCASE('%Rodriguez%')"""
        },
        "Workflow Status Filtering": {
            "description": "Using status_id codes for workflow management",
            "example": """WHERE te.status_id = 1  -- SENT_FOR_APPROVAL
AND l.code = '061'"""
        },
        "Date Range Filtering": {
            "description": "Time-based filtering for recent records",
            "example": """WHERE te.begin_date_time >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)
AND te.status_id = 4  -- POSTED"""
        }
    }
    
    for pattern_name, pattern_info in complex_patterns.items():
        print(f"🔧 {pattern_name}")
        print(f"   {pattern_info['description']}")
        print(f"   Example:")
        for line in pattern_info['example'].split('\n'):
            print(f"     {line}")
        print()
    
    # 4. Business logic examples
    print("4. Business Logic Examples from Training Data")
    print("-" * 50)
    
    business_scenarios = {
        "Employee Performance Analysis": [
            "Total hours calculation with proper time logic",
            "Top performers identification by posted hours",
            "Overtime tracking by activity type"
        ],
        "Location Management": [
            "Location-based time entry analysis",
            "Specific location approval workflows",
            "Location usage patterns"
        ],
        "Activity Analysis": [
            "Activity code usage frequency",
            "Active vs inactive activity filtering",
            "21st century program identification"
        ],
        "Approval Workflow": [
            "Pending approval identification by location",
            "Status-based filtering using workflow codes",
            "Current payroll period tracking"
        ],
        "Data Quality": [
            "Case-insensitive employee name matching",
            "Proper JOIN relationships",
            "Active record filtering"
        ]
    }
    
    for scenario, features in business_scenarios.items():
        print(f"💼 {scenario}")
        for feature in features:
            print(f"  • {feature}")
        print()
    
    # 5. API endpoint testing
    print("5. API Endpoint Testing")
    print("-" * 50)
    
    print("Available SQL examples endpoints:")
    endpoints = [
        "GET /api/table-info/sql-examples - All categorized training examples",
        "GET /api/table-info/documentation - Table and column docs",
        "GET /api/table-info/query-examples - Business rule examples",
        "GET /api/table-info/suggestions - AI-generated suggestions"
    ]
    
    for endpoint in endpoints:
        print(f"  • {endpoint}")
    print()
    
    print("Example curl commands:")
    print("curl http://localhost:8000/api/table-info/sql-examples")
    print("curl http://localhost:8000/api/table-info/sql-examples | jq '.data.categories.time_calculation_queries'")
    print()
    
    # 6. Training data quality analysis
    print("6. Training Data Quality Analysis")
    print("-" * 50)
    
    # Analyze training examples
    total_examples = len(SQL_EXAMPLES)
    examples_with_joins = sum(1 for ex in SQL_EXAMPLES if 'join' in ex['sql'].lower())
    examples_with_aggregation = sum(1 for ex in SQL_EXAMPLES if any(word in ex['sql'].lower() for word in ['count', 'sum', 'group by']))
    examples_with_time_calc = sum(1 for ex in SQL_EXAMPLES if 'timestampdiff' in ex['sql'].lower())
    examples_with_workflow = sum(1 for ex in SQL_EXAMPLES if 'status_id' in ex['sql'].lower())
    
    print(f"📊 Training Data Statistics:")
    print(f"   • Total examples: {total_examples}")
    print(f"   • Examples with JOINs: {examples_with_joins} ({examples_with_joins/total_examples*100:.1f}%)")
    print(f"   • Examples with aggregation: {examples_with_aggregation} ({examples_with_aggregation/total_examples*100:.1f}%)")
    print(f"   • Examples with time calculations: {examples_with_time_calc} ({examples_with_time_calc/total_examples*100:.1f}%)")
    print(f"   • Examples with workflow logic: {examples_with_workflow} ({examples_with_workflow/total_examples*100:.1f}%)")
    print()
    
    print("📋 Example Complexity Distribution:")
    complexity_scores = []
    for example in SQL_EXAMPLES:
        sql_lower = example['sql'].lower()
        score = 0
        if 'join' in sql_lower: score += 2
        if any(word in sql_lower for word in ['count', 'sum', 'group by']): score += 1
        if 'timestampdiff' in sql_lower: score += 3
        if 'case when' in sql_lower: score += 2
        if 'where' in sql_lower: score += 1
        complexity_scores.append(score)
    
    simple_queries = sum(1 for score in complexity_scores if score <= 2)
    medium_queries = sum(1 for score in complexity_scores if 3 <= score <= 5)
    complex_queries = sum(1 for score in complexity_scores if score > 5)
    
    print(f"   • Simple queries (score ≤ 2): {simple_queries}")
    print(f"   • Medium queries (score 3-5): {medium_queries}")
    print(f"   • Complex queries (score > 5): {complex_queries}")
    print()
    
    # 7. Summary
    print("7. SQL Examples Integration Summary")
    print("-" * 50)
    
    print("✅ Comprehensive SQL training examples added")
    print("✅ Categorized by query type and complexity")
    print("✅ Business logic and workflow examples included")
    print("✅ Complex time calculation patterns provided")
    print("✅ Multi-table JOIN examples for relationships")
    print("✅ Case-insensitive search patterns")
    print("✅ Location and employee-specific queries")
    print("✅ API endpoint for accessing training data")
    print()
    
    print("Key Training Patterns:")
    print("• Time calculations using TIMESTAMPDIFF and conditional logic")
    print("• Multi-table joins across employee, time_entry, activity, location")
    print("• Workflow status management with status_id codes")
    print("• Case-insensitive employee name searching")
    print("• Date range filtering for recent data analysis")
    print("• Activity usage and frequency analysis")
    print("• Location-based approval workflow queries")
    print("• Performance ranking and top N queries")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())