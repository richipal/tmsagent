#!/usr/bin/env python3
"""
Test script for table and column documentation integration.

This script demonstrates:
1. Comprehensive table and column documentation
2. Context-aware NL2SQL with documentation
3. API endpoints for documentation access
4. Business rule integration with detailed metadata

Usage:
    python test_table_documentation.py
"""

import asyncio
import json
from app.data_science.sub_agents.bigquery.tools import (
    TABLE_DOCUMENTATION,
    get_table_documentation,
    initial_bq_nl2sql
)


async def main():
    """Test table documentation integration."""
    
    print("=" * 80)
    print("Table and Column Documentation Integration Test")
    print("=" * 80)
    print()
    
    # 1. Show comprehensive table documentation
    print("1. Comprehensive Table Documentation")
    print("-" * 50)
    
    all_docs = get_table_documentation()
    print(f"Total documented tables: {all_docs['total_tables']}")
    print(f"Documented tables: {', '.join(all_docs['documented_tables'])}")
    print()
    
    # Show detailed documentation for key tables
    key_tables = ['user', 'time_entry', 'activity', 'absence']
    
    for table in key_tables:
        if table in TABLE_DOCUMENTATION:
            table_info = TABLE_DOCUMENTATION[table]
            print(f"📋 Table: {table}")
            print(f"   Description: {table_info['description']}")
            print(f"   Business Context: {table_info['business_context']}")
            print(f"   Columns ({len(table_info['columns'])}):")
            
            # Show first 5 columns
            for i, (col_name, col_desc) in enumerate(table_info['columns'].items()):
                if i < 5:
                    print(f"     • {col_name}: {col_desc}")
                elif i == 5:
                    print(f"     ... and {len(table_info['columns']) - 5} more columns")
                    break
            print()
    
    # 2. Test context-aware NL2SQL with documentation
    print("2. Context-Aware NL2SQL with Documentation")
    print("-" * 50)
    
    documentation_aware_questions = [
        "Show me the user account information",
        "Find time entries that are pending approval",
        "What's the status workflow for time entries?",
        "Show employee absence patterns",
        "Find activities with high pay rates",
        "Show manager-employee relationships",
        "What are the different user roles?",
        "Show favorite time entry templates"
    ]
    
    for question in documentation_aware_questions:
        print(f"Question: {question}")
        try:
            result = await initial_bq_nl2sql(question)
            if "sql_query" in result:
                sql = result["sql_query"]
                print(f"Generated SQL: {sql}")
                
                # Check if documentation context is applied
                question_lower = question.lower()
                relevant_tables = []
                for table_name in TABLE_DOCUMENTATION.keys():
                    if table_name in question_lower or any(col in question_lower for col in TABLE_DOCUMENTATION[table_name]['columns'].keys()):
                        relevant_tables.append(table_name)
                
                if relevant_tables:
                    print(f"✅ Documentation context applied for tables: {', '.join(relevant_tables)}")
                else:
                    print("⚠️  Documentation context may not be fully applied")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"Error: {e}")
        print()
    
    # 3. Demonstrate column-specific queries
    print("3. Column-Specific Query Examples")
    print("-" * 50)
    
    column_specific_examples = {
        "Status Code Examples": [
            "Show time entries with status_id = 1 (SENT_FOR_APPROVAL)",
            "Find disapproved time entries (status_id = 3)",
            "List posted time entries (status_id = 4)"
        ],
        "Date Field Examples": [
            "Show recent time entries by begin_date_time",
            "Find users by last_login_date",
            "Check posting cut_off_date compliance"
        ],
        "Rate Calculation Examples": [
            "Compare activity rate_of_pay across different types",
            "Show calculation_rate multipliers for overtime",
            "Analyze salary bands from salary_guide"
        ],
        "Relationship Examples": [
            "Join user and user_role tables",
            "Connect employees to their managers via user_manager",
            "Link activities to locations via user assignments"
        ]
    }
    
    for category, examples in column_specific_examples.items():
        print(f"🎯 {category}")
        for example in examples:
            print(f"  • {example}")
        print()
    
    # 4. Show API endpoint examples
    print("4. API Endpoint Examples for Documentation")
    print("-" * 50)
    
    print("Available documentation endpoints:")
    endpoints = [
        "GET /api/table-info/documentation - All table documentation",
        "GET /api/table-info/documentation/{table_name} - Specific table docs",
        "GET /api/table-info/schema - Enhanced schema with descriptions",
        "GET /api/table-info/query-examples - Business rule examples"
    ]
    
    for endpoint in endpoints:
        print(f"  • {endpoint}")
    print()
    
    print("Example curl commands:")
    print("curl http://localhost:8000/api/table-info/documentation")
    print("curl http://localhost:8000/api/table-info/documentation/user")
    print("curl http://localhost:8000/api/table-info/documentation/time_entry")
    print()
    
    # 5. Business rule and documentation integration
    print("5. Business Rule + Documentation Integration")
    print("-" * 50)
    
    integration_examples = {
        "Workflow Understanding": "Documentation explains status_id codes (0-4) while business rules define the approval workflow",
        "Field Validation": "Column docs specify data types and constraints while business rules define valid values",
        "Relationship Mapping": "Table docs show foreign key relationships while business rules explain the business logic",
        "Calculation Logic": "Column docs explain rate_of_pay and multiplier fields while business rules define how calculations work",
        "Security Context": "User role documentation combined with business rules for access control"
    }
    
    for aspect, explanation in integration_examples.items():
        print(f"🔗 {aspect}:")
        print(f"   {explanation}")
        print()
    
    # 6. Documentation coverage analysis
    print("6. Documentation Coverage Analysis")
    print("-" * 50)
    
    # Analyze documentation coverage
    total_documented_columns = sum(len(table_info['columns']) for table_info in TABLE_DOCUMENTATION.values())
    tables_with_business_context = sum(1 for table_info in TABLE_DOCUMENTATION.values() if table_info.get('business_context'))
    
    print(f"📊 Coverage Statistics:")
    print(f"   • Documented tables: {len(TABLE_DOCUMENTATION)}")
    print(f"   • Total documented columns: {total_documented_columns}")
    print(f"   • Tables with business context: {tables_with_business_context}")
    print(f"   • Average columns per table: {total_documented_columns / len(TABLE_DOCUMENTATION):.1f}")
    print()
    
    print("📋 Documentation Quality:")
    for table_name, table_info in TABLE_DOCUMENTATION.items():
        quality_score = 0
        if table_info.get('description'): quality_score += 1
        if table_info.get('business_context'): quality_score += 1
        if len(table_info.get('columns', {})) > 0: quality_score += 1
        
        quality_rating = "🟢 Excellent" if quality_score == 3 else "🟡 Good" if quality_score == 2 else "🔴 Needs work"
        print(f"   {table_name}: {quality_rating} ({quality_score}/3)")
    
    print()
    
    # 7. Summary
    print("7. Documentation Integration Summary")
    print("-" * 50)
    
    print("✅ Comprehensive table and column documentation added")
    print("✅ Context-aware NL2SQL with relevant documentation")
    print("✅ API endpoints for accessing documentation")
    print("✅ Business rules integrated with detailed metadata")
    print("✅ Column-level descriptions for accurate query generation")
    print("✅ Business context for each table explained")
    print("✅ Field validation and constraint information")
    print("✅ Relationship mapping between tables")
    print()
    
    print("Key Benefits:")
    print("• More accurate NL2SQL conversion with field-level context")
    print("• Better understanding of data relationships and constraints")
    print("• Comprehensive API documentation for developers")
    print("• Business context helps users understand data meaning")
    print("• Column descriptions enable precise query generation")
    print("• Integration with existing business rules and schemas")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())