#!/usr/bin/env python3
"""
Example script demonstrating how to get table information and query suggestions from BigQuery.

This script shows how to:
1. Get comprehensive table information
2. Generate intelligent query suggestions
3. Access specific table details
4. Use the table info API endpoints

Usage:
    python example_table_info_usage.py
"""

import asyncio
import json
from app.services.table_info_service import table_info_service


async def main():
    """Main function demonstrating table info and query suggestions."""
    
    print("=" * 80)
    print("ADK Data Science Chatbot - BigQuery Table Information & Query Suggestions")
    print("=" * 80)
    print()
    
    # 1. Get comprehensive table information
    print("1. Getting comprehensive table information...")
    print("-" * 50)
    
    table_info = table_info_service.get_comprehensive_table_info()
    
    if "error" in table_info:
        print(f"Error: {table_info['error']}")
        return
    
    # Display database information
    db_info = table_info.get("database_info", {})
    print(f"Database Type: {db_info.get('type')}")
    print(f"Project ID: {db_info.get('project_id')}")
    print(f"Dataset ID: {db_info.get('dataset_id')}")
    print(f"Location: {db_info.get('location')}")
    print(f"Total Tables: {db_info.get('total_tables')}")
    print()
    
    # Display table summaries
    print("Available Tables:")
    for table_name, details in table_info.get("tables", {}).items():
        print(f"  • {table_name}")
        print(f"    - Rows: {details.get('num_rows', 0):,}")
        print(f"    - Size: {details.get('size_gb', 0):.2f} GB")
        print(f"    - Fields: {len(details.get('schema', []))}")
        if details.get('description'):
            print(f"    - Description: {details.get('description')}")
    print()
    
    # 2. Generate query suggestions
    print("2. Generating intelligent query suggestions...")
    print("-" * 50)
    
    result = await table_info_service.get_table_info_with_suggestions()
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    
    query_suggestions = result.get("query_suggestions", [])
    categories = result.get("suggestion_categories", [])
    
    print(f"Generated {len(query_suggestions)} query suggestions across {len(categories)} categories")
    print(f"Categories: {', '.join(categories)}")
    print()
    
    # Display suggestions by category
    suggestions_by_category = {}
    for suggestion in query_suggestions:
        category = suggestion.get("category", "General")
        if category not in suggestions_by_category:
            suggestions_by_category[category] = []
        suggestions_by_category[category].append(suggestion)
    
    for category, suggestions in suggestions_by_category.items():
        print(f"📊 {category} ({len(suggestions)} queries)")
        print("─" * 40)
        
        for i, suggestion in enumerate(suggestions[:3], 1):  # Show top 3 per category
            difficulty = suggestion.get("difficulty", "Unknown")
            print(f"{i}. {suggestion.get('description', 'No description')}")
            print(f"   Difficulty: {difficulty}")
            print(f"   SQL: {suggestion.get('sql_query', 'No query')}")
            print()
        
        if len(suggestions) > 3:
            print(f"   ... and {len(suggestions) - 3} more {category.lower()} queries")
        print()
    
    # 3. Show example queries for different use cases
    print("3. Example Queries by Use Case")
    print("-" * 50)
    
    use_cases = {
        "Data Exploration": [
            "SELECT COUNT(*) as total_records FROM `adk-rag-462901.data_science_agents.user`",
            "SELECT * FROM `adk-rag-462901.data_science_agents.activity` LIMIT 10",
            "SELECT DISTINCT user_id, COUNT(*) as activity_count FROM `adk-rag-462901.data_science_agents.user_activities` GROUP BY user_id ORDER BY activity_count DESC LIMIT 5"
        ],
        "Statistical Analysis": [
            "SELECT MIN(rate) as min_rate, MAX(rate) as max_rate, AVG(rate) as avg_rate FROM `adk-rag-462901.data_science_agents.pay_rate`",
            "SELECT activity_id, COUNT(*) as threshold_count FROM `adk-rag-462901.data_science_agents.activity_threshold` GROUP BY activity_id ORDER BY threshold_count DESC",
            "SELECT location_id, COUNT(*) as user_count FROM `adk-rag-462901.data_science_agents.user_locations` GROUP BY location_id"
        ],
        "Business Intelligence": [
            "SELECT u.user_id, u.email, COUNT(ua.activity_id) as total_activities FROM `adk-rag-462901.data_science_agents.user` u LEFT JOIN `adk-rag-462901.data_science_agents.user_activities` ua ON u.user_id = ua.user_id GROUP BY u.user_id, u.email ORDER BY total_activities DESC",
            "SELECT l.name as location_name, COUNT(ul.user_id) as user_count FROM `adk-rag-462901.data_science_agents.location` l LEFT JOIN `adk-rag-462901.data_science_agents.user_locations` ul ON l.location_id = ul.location_id GROUP BY l.location_id, l.name ORDER BY user_count DESC",
            "SELECT DATE(posting_date) as date, COUNT(*) as posts_count FROM `adk-rag-462901.data_science_agents.posting_date` GROUP BY DATE(posting_date) ORDER BY date DESC LIMIT 30"
        ]
    }
    
    for use_case, queries in use_cases.items():
        print(f"🎯 {use_case}")
        for i, query in enumerate(queries, 1):
            print(f"{i}. {query}")
        print()
    
    # 4. Schema information
    print("4. Detailed Schema Information")
    print("-" * 50)
    
    # Show schema for a few key tables
    key_tables = ['user', 'activity', 'pay_rate']
    for table_name in key_tables:
        if table_name in table_info.get("tables", {}):
            table_details = table_info["tables"][table_name]
            schema = table_details.get("schema", [])
            
            print(f"📋 Table: {table_name}")
            print(f"   Full ID: {table_details.get('full_table_id')}")
            print(f"   Rows: {table_details.get('num_rows', 0):,}")
            print(f"   Schema:")
            
            for field in schema:
                field_info = f"     • {field['name']} ({field['type']})"
                if field['mode'] == 'REQUIRED':
                    field_info += " NOT NULL"
                if field.get('description'):
                    field_info += f" - {field['description']}"
                print(field_info)
            print()
    
    # 5. API endpoint examples
    print("5. API Endpoint Usage Examples")
    print("-" * 50)
    
    print("Available API endpoints:")
    print("• GET /api/table-info - Get comprehensive table information")
    print("• GET /api/table-info/suggestions - Get table info with query suggestions")
    print("• GET /api/table-info/schema - Get schema-only information")
    print("• GET /api/table-info/sample-queries - Get organized sample queries")
    print("• GET /api/table-info/table/{table_name} - Get specific table details")
    print()
    
    print("Example curl commands:")
    print("curl http://localhost:8000/api/table-info")
    print("curl http://localhost:8000/api/table-info/suggestions")
    print("curl http://localhost:8000/api/table-info/schema")
    print("curl http://localhost:8000/api/table-info/sample-queries")
    print("curl http://localhost:8000/api/table-info/table/user")
    print()
    
    print("=" * 80)
    print("Summary:")
    print(f"✅ Found {db_info.get('total_tables', 0)} tables in BigQuery dataset")
    print(f"✅ Generated {len(query_suggestions)} intelligent query suggestions")
    print(f"✅ Created {len(categories)} different query categories")
    print("✅ API endpoints ready for frontend integration")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())