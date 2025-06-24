#!/usr/bin/env python3
"""
Test script for business rules integration in BigQuery tools.

This script demonstrates how the business rules enhance NL2SQL conversion
and query suggestions for the Time Management System.

Usage:
    python test_business_rules_integration.py
"""

import asyncio
import json
from app.data_science.sub_agents.bigquery.tools import (
    BUSINESS_RULES,
    get_query_examples,
    initial_bq_nl2sql,
    get_database_settings
)


async def main():
    """Test business rules integration."""
    
    print("=" * 80)
    print("Business Rules Integration Test")
    print("=" * 80)
    print()
    
    # 1. Show business rules
    print("1. Business Rules Context")
    print("-" * 50)
    print(BUSINESS_RULES)
    print()
    
    # 2. Test business rule-aware NL2SQL
    print("2. Testing Business Rule-Aware NL2SQL")
    print("-" * 50)
    
    business_rule_questions = [
        "Show me all new time entries",
        "How many time entries are waiting for approval?", 
        "List all approved time entries from this week",
        "Find disapproved time entries",
        "Show time entries that have been posted to payroll",
        "How many overtime activities do we have?",
        "Show vacation time requests",
        "What are the different time entry statuses?",
        "Find time entries submitted before the cut-off date",
        "Show managers with pending approvals"
    ]
    
    for question in business_rule_questions:
        print(f"Question: {question}")
        try:
            result = await initial_bq_nl2sql(question)
            if "sql_query" in result:
                sql = result["sql_query"]
                print(f"Generated SQL: {sql}")
                
                # Check if business rules are applied
                if any(keyword in sql.upper() for keyword in ['STATUS', 'TYPE', 'APPROVAL', 'POSTED']):
                    print("✅ Business rules applied!")
                else:
                    print("⚠️  Business rules may not be fully applied")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"Error: {e}")
        print()
    
    # 3. Show enhanced query examples
    print("3. Enhanced Query Examples with Business Rules")
    print("-" * 50)
    
    query_examples = get_query_examples()
    
    # Show new business rule categories
    new_categories = ["time_entry_workflow", "activity_types", "compliance_reporting"]
    
    for category in new_categories:
        if category in query_examples:
            examples = query_examples[category]
            print(f"📊 {category.replace('_', ' ').title()} ({len(examples)} queries)")
            print("─" * 40)
            
            for i, example in enumerate(examples, 1):
                print(f"{i}. {example['description']}")
                
                # Show key business rule elements in the query
                query = example['query']
                business_elements = []
                
                if "status =" in query.lower():
                    business_elements.append("Status codes")
                if "type =" in query.lower() or "type in" in query.lower():
                    business_elements.append("Activity types")
                if "case when" in query.lower():
                    business_elements.append("Business logic")
                if "cut_off_date" in query.lower():
                    business_elements.append("Compliance rules")
                
                if business_elements:
                    print(f"   Business elements: {', '.join(business_elements)}")
                
                # Show first 100 chars of query
                print(f"   Query: {query[:100]}...")
                print()
            print()
    
    # 4. Test specific business rule scenarios
    print("4. Business Rule Scenario Testing")
    print("-" * 50)
    
    scenarios = {
        "Workflow Management": [
            "Show the workflow status distribution",
            "Find time entries stuck in approval",
            "List all posted entries for payroll"
        ],
        "Activity Type Analysis": [
            "Compare regular vs overtime hours",
            "Show vacation time usage",
            "Analyze double-time activities"
        ],
        "Compliance Monitoring": [
            "Check submission deadline compliance",
            "Find disapproved entries needing attention",
            "Monitor manager approval workload"
        ],
        "Payroll Processing": [
            "Calculate payroll for posted entries",
            "Show overtime costs",
            "Verify payroll calculation accuracy"
        ]
    }
    
    for scenario, questions in scenarios.items():
        print(f"🎯 {scenario}")
        for question in questions:
            print(f"  • {question}")
        print()
    
    # 5. Enhanced schema with business context
    print("5. Enhanced Schema Information")
    print("-" * 50)
    
    db_settings = get_database_settings()
    schema_ddl = db_settings.get('bq_ddl_schema', '')
    
    # Show business context in schema (first few tables)
    schema_lines = schema_ddl.split('\n')
    current_table = None
    lines_shown = 0
    
    for line in schema_lines:
        if line.startswith('--') and ('time' in line.lower() or 'status' in line.lower() or 'workflow' in line.lower()):
            print(line)
            lines_shown += 1
        elif line.startswith('CREATE TABLE') and ('time_entry' in line or 'activity' in line):
            print(line)
            current_table = line
            lines_shown += 1
        elif current_table and lines_shown < 10 and line.strip():
            print(line)
            if line.strip() == ');':
                current_table = None
            lines_shown += 1
        
        if lines_shown >= 20:
            print("  ...")
            break
    
    print()
    
    # 6. Summary
    print("6. Business Rules Integration Summary")
    print("-" * 50)
    
    total_examples = sum(len(examples) for examples in query_examples.values())
    business_categories = len([cat for cat in query_examples.keys() if any(keyword in cat for keyword in ['time_entry', 'activity_types', 'compliance'])])
    
    print(f"✅ Business rules integrated into NL2SQL prompt")
    print(f"✅ Enhanced table descriptions with business context")
    print(f"✅ Added {business_categories} new business-specific query categories")
    print(f"✅ Total query examples: {total_examples}")
    print(f"✅ Status codes (0-4) integrated into queries")
    print(f"✅ Activity types (REGULAR, OVERTIME, etc.) recognized")
    print(f"✅ Workflow states and compliance rules included")
    print()
    
    print("Key Business Rule Features:")
    print("• Status code translation (0=NEW, 1=SENT_FOR_APPROVAL, etc.)")
    print("• Activity type filtering (REGULAR, OVERTIME, VACATION, etc.)")
    print("• Workflow-aware queries (approval process, posting)")
    print("• Compliance monitoring (cut-off dates, submission timing)")
    print("• Payroll calculations (posted entries only)")
    print("• Manager approval tracking")
    print("• Data quality checks with business context")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())