#!/usr/bin/env python3
"""
Example script demonstrating the enhanced BigQuery tools with real table examples.

This script shows:
1. Updated NL2SQL examples based on actual tables
2. Categorized query examples for different use cases
3. Enhanced schema information with table descriptions
4. Practical query patterns for the discovered data

Usage:
    python example_enhanced_bigquery_tools.py
"""

import asyncio
import json
from app.data_science.sub_agents.bigquery.tools import (
    get_database_settings, 
    get_query_examples,
    initial_bq_nl2sql,
    run_bigquery_validation
)


async def main():
    """Main function demonstrating enhanced BigQuery tools."""
    
    print("=" * 80)
    print("Enhanced BigQuery Tools - Real Table Examples")
    print("=" * 80)
    print()
    
    # 1. Show database settings with enhanced schema
    print("1. Enhanced Database Schema Information")
    print("-" * 50)
    
    db_settings = get_database_settings()
    print(f"Project: {db_settings.get('project_id')}")
    print(f"Dataset: {db_settings.get('dataset_id')}")
    print(f"Tables: {len(db_settings.get('tables', []))}")
    print()
    
    # Show enhanced schema with descriptions (first few lines)
    schema_ddl = db_settings.get('bq_ddl_schema', '')
    schema_lines = schema_ddl.split('\n')[:30]
    print("Enhanced Schema (sample):")
    for line in schema_lines:
        if line.strip():
            print(f"  {line}")
    print("  ...")
    print()
    
    # 2. Categorized Query Examples
    print("2. Categorized Query Examples")
    print("-" * 50)
    
    query_examples = get_query_examples()
    
    for category, examples in query_examples.items():
        print(f"📊 {category.replace('_', ' ').title()} ({len(examples)} queries)")
        print("─" * 40)
        
        for i, example in enumerate(examples, 1):
            print(f"{i}. {example['description']}")
            # Show query with proper formatting
            query = example['query']
            if len(query) > 100:
                # Format multi-line queries nicely
                lines = query.split('\n')
                if len(lines) > 1:
                    print(f"   Query:")
                    for line in lines:
                        print(f"     {line.strip()}")
                else:
                    print(f"   Query: {query[:80]}...")
            else:
                print(f"   Query: {query}")
            print()
        print()
    
    # 3. Test NL2SQL with real examples
    print("3. Testing NL2SQL with Real Examples")
    print("-" * 50)
    
    test_questions = [
        "How many active users do we have?",
        "Show me the top 5 users with most activities",
        "What are the most common absence reasons?",
        "Which locations have the most users?",
        "Show me pay rate statistics",
        "Find users who haven't logged in recently"
    ]
    
    for question in test_questions:
        print(f"Question: {question}")
        try:
            nl2sql_result = await initial_bq_nl2sql(question)
            if "sql_query" in nl2sql_result:
                generated_sql = nl2sql_result["sql_query"]
                print(f"Generated SQL: {generated_sql}")
                
                # Validate the query
                validation_result = await run_bigquery_validation(generated_sql)
                if "error" in validation_result:
                    print(f"Validation Error: {validation_result['error']}")
                else:
                    rows = validation_result.get("rows", [])
                    print(f"Query executed successfully, returned {len(rows)} rows")
                    if rows:
                        # Show first row as example
                        first_row = rows[0]
                        print(f"Sample result: {first_row}")
            else:
                print(f"Error: {nl2sql_result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"Error: {e}")
        print()
    
    # 4. Show practical business scenarios
    print("4. Practical Business Analysis Scenarios")
    print("-" * 50)
    
    scenarios = {
        "Employee Performance Dashboard": [
            "User activity levels across different locations",
            "Absence patterns and trends",
            "Role distribution and assignments"
        ],
        "Operational Analytics": [
            "Location utilization analysis",
            "Activity threshold monitoring", 
            "Pay rate and cost analysis"
        ],
        "Data Quality Monitoring": [
            "Users without location assignments",
            "Duplicate or inconsistent activity records",
            "Missing or invalid data patterns"
        ],
        "Workforce Planning": [
            "Staffing levels by location",
            "Activity capacity vs demand",
            "Salary cost projections"
        ]
    }
    
    for scenario, analyses in scenarios.items():
        print(f"🎯 {scenario}")
        for analysis in analyses:
            print(f"  • {analysis}")
        print()
    
    # 5. API Integration Examples
    print("5. API Integration Examples")
    print("-" * 50)
    
    print("Available enhanced endpoints:")
    endpoints = [
        "GET /api/table-info - Complete table information with descriptions",
        "GET /api/table-info/suggestions - AI-generated query suggestions",
        "GET /api/table-info/query-examples - Categorized real-world examples",
        "GET /api/table-info/schema - Enhanced schema with table descriptions"
    ]
    
    for endpoint in endpoints:
        print(f"  • {endpoint}")
    print()
    
    print("Example usage in applications:")
    print("""
    # Frontend: Get query examples for autocomplete
    const examples = await fetch('/api/table-info/query-examples');
    
    # Data Analysis: Execute common queries
    const userStats = await queryDatabase(`
        SELECT l.name, COUNT(ul.user_id) as users 
        FROM location l 
        LEFT JOIN user_locations ul ON l.id = ul.location_id 
        GROUP BY l.name
    `);
    
    # Reporting: Generate absence reports
    const absenceReport = await queryDatabase(`
        SELECT absence_reason, COUNT(*) as incidents, 
               SUM(amt_used) as total_hours 
        FROM absence 
        WHERE out_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)
        GROUP BY absence_reason
    `);
    """)
    
    # 6. Summary
    print("6. Summary of Enhancements")
    print("-" * 50)
    
    total_examples = sum(len(examples) for examples in query_examples.values())
    
    print(f"✅ Updated NL2SQL examples based on {len(db_settings.get('tables', []))} real tables")
    print(f"✅ Added {total_examples} categorized query examples across {len(query_examples)} use cases")
    print("✅ Enhanced schema information with table descriptions")
    print("✅ Improved query pattern recognition for business scenarios")
    print("✅ Better integration with actual data structure")
    print()
    
    print("Key improvements:")
    print("• Real table names and fields in all examples")
    print("• Business-relevant query categories")
    print("• Enhanced schema documentation")
    print("• Practical use case scenarios")
    print("• Better NL2SQL conversion accuracy")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())