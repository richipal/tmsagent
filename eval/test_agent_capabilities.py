"""
Evaluation tests for individual agent capabilities
"""

import pytest
import time
import asyncio
from app.data_science.agent import root_agent
from app.data_science.sub_agents import db_agent, ds_agent, bqml_agent
from app.data_science.tools import ToolContext


@pytest.mark.asyncio
async def test_sql_generation_capabilities(evaluation_scenarios, performance_benchmarks):
    """Evaluate SQL generation capabilities of the database agent."""
    sql_scenarios = evaluation_scenarios["sql_generation"]
    results = []
    
    for scenario in sql_scenarios:
        start_time = time.time()
        
        # Test the database agent
        context = ToolContext()
        response = await db_agent.process_query(scenario["query"], context)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Check response quality
        keyword_matches = sum(1 for keyword in scenario["expected_keywords"] 
                             if keyword.lower() in response.lower())
        keyword_coverage = keyword_matches / len(scenario["expected_keywords"])
        
        result = {
            "scenario": scenario["category"],
            "query": scenario["query"],
            "response_time": response_time,
            "response_length": len(response),
            "keyword_coverage": keyword_coverage,
            "response": response[:200] + "..." if len(response) > 200 else response
        }
        results.append(result)
        
        # Assertions for quality
        assert response_time <= performance_benchmarks["response_time"]["acceptable"]
        assert len(response) >= performance_benchmarks["response_length"]["minimum"]
        assert keyword_coverage >= performance_benchmarks["keyword_coverage"]["acceptable"]
    
    # Print results for analysis
    print("\n=== SQL Generation Evaluation Results ===")
    for result in results:
        print(f"Category: {result['scenario']}")
        print(f"Response Time: {result['response_time']:.2f}s")
        print(f"Keyword Coverage: {result['keyword_coverage']:.1%}")
        print(f"Response Length: {result['response_length']} chars")
        print("---")


@pytest.mark.asyncio
async def test_analytics_capabilities(evaluation_scenarios, performance_benchmarks):
    """Evaluate analytics capabilities of the analytics agent."""
    analytics_scenarios = evaluation_scenarios["analytics"]
    results = []
    
    for scenario in analytics_scenarios:
        start_time = time.time()
        
        context = ToolContext()
        # Add some mock data context
        context.update_state("current_dataset", {
            "filename": "test_data.csv",
            "columns": ["customer_id", "age", "purchase_amount", "category"]
        })
        
        response = await ds_agent.process_query(scenario["query"], context)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Check response quality
        keyword_matches = sum(1 for keyword in scenario["expected_keywords"] 
                             if keyword.lower() in response.lower())
        keyword_coverage = keyword_matches / len(scenario["expected_keywords"])
        
        result = {
            "scenario": scenario["category"],
            "query": scenario["query"],
            "response_time": response_time,
            "response_length": len(response),
            "keyword_coverage": keyword_coverage,
            "contains_code": "```" in response or "import" in response
        }
        results.append(result)
        
        # Assertions
        assert response_time <= performance_benchmarks["response_time"]["acceptable"]
        assert len(response) >= performance_benchmarks["response_length"]["minimum"]
        assert keyword_coverage >= performance_benchmarks["keyword_coverage"]["acceptable"]
    
    print("\n=== Analytics Evaluation Results ===")
    for result in results:
        print(f"Category: {result['scenario']}")
        print(f"Response Time: {result['response_time']:.2f}s")
        print(f"Keyword Coverage: {result['keyword_coverage']:.1%}")
        print(f"Contains Code: {result['contains_code']}")
        print("---")


@pytest.mark.asyncio
async def test_ml_capabilities(evaluation_scenarios, performance_benchmarks):
    """Evaluate machine learning capabilities of the BQML agent."""
    ml_scenarios = evaluation_scenarios["machine_learning"]
    results = []
    
    for scenario in ml_scenarios:
        start_time = time.time()
        
        context = ToolContext()
        # Add ML-relevant context
        context.update_state("current_dataset", {
            "filename": "customer_data.csv",
            "columns": ["customer_id", "features", "target"],
            "task_type": scenario["category"]
        })
        
        response = await bqml_agent.process_query(scenario["query"], context)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        keyword_matches = sum(1 for keyword in scenario["expected_keywords"] 
                             if keyword.lower() in response.lower())
        keyword_coverage = keyword_matches / len(scenario["expected_keywords"])
        
        result = {
            "scenario": scenario["category"],
            "query": scenario["query"],
            "response_time": response_time,
            "response_length": len(response),
            "keyword_coverage": keyword_coverage,
            "mentions_bqml": "bqml" in response.lower() or "bigquery ml" in response.lower()
        }
        results.append(result)
        
        # Assertions
        assert response_time <= performance_benchmarks["response_time"]["acceptable"]
        assert len(response) >= performance_benchmarks["response_length"]["minimum"]
        assert keyword_coverage >= performance_benchmarks["keyword_coverage"]["acceptable"]
    
    print("\n=== ML Capabilities Evaluation Results ===")
    for result in results:
        print(f"Category: {result['scenario']}")
        print(f"Response Time: {result['response_time']:.2f}s")
        print(f"Keyword Coverage: {result['keyword_coverage']:.1%}")
        print(f"Mentions BQML: {result['mentions_bqml']}")
        print("---")


@pytest.mark.asyncio
async def test_intent_classification_accuracy():
    """Evaluate the accuracy of intent classification."""
    test_cases = [
        ("SELECT * FROM customers", "database"),
        ("Show me the top customers by sales", "database"),
        ("Analyze correlation between variables", "analytics"),
        ("Create a scatter plot of the data", "analytics"),
        ("Build a machine learning model", "ml"),
        ("Predict customer churn using historical data", "ml"),
        ("What is the best algorithm for classification?", "ml"),
        ("Calculate statistical significance", "analytics")
    ]
    
    correct_classifications = 0
    total_tests = len(test_cases)
    
    for query, expected_category in test_cases:
        context = ToolContext()
        intent = await root_agent._classify_intent(query, context)
        
        primary_agent = intent.get("primary_agent", "").lower()
        
        # Check if the classification is correct
        if expected_category in primary_agent:
            correct_classifications += 1
        else:
            print(f"Misclassification: '{query}' -> Expected: {expected_category}, Got: {primary_agent}")
    
    accuracy = correct_classifications / total_tests
    print(f"\n=== Intent Classification Accuracy ===")
    print(f"Correct: {correct_classifications}/{total_tests}")
    print(f"Accuracy: {accuracy:.1%}")
    
    # Expect at least 70% accuracy
    assert accuracy >= 0.7, f"Intent classification accuracy too low: {accuracy:.1%}"


@pytest.mark.asyncio
async def test_response_consistency():
    """Test that agents provide consistent responses to similar queries."""
    similar_queries = [
        "Find top customers by sales",
        "Show me the highest spending customers",
        "List customers with most revenue"
    ]
    
    responses = []
    for query in similar_queries:
        context = ToolContext()
        response = await db_agent.process_query(query, context)
        responses.append(response)
    
    # Check that all responses contain SQL keywords
    for response in responses:
        assert any(keyword in response.upper() for keyword in ['SELECT', 'FROM', 'ORDER BY'])
    
    # Check that responses have similar structure/length
    lengths = [len(response) for response in responses]
    avg_length = sum(lengths) / len(lengths)
    
    # All responses should be within 50% of average length
    for length in lengths:
        assert abs(length - avg_length) / avg_length <= 0.5


@pytest.mark.asyncio
async def test_error_recovery():
    """Test how agents handle and recover from errors."""
    problematic_queries = [
        "",  # Empty query
        "xyz123invalid",  # Nonsensical query
        "A" * 1000,  # Very long query
        "SELECT * FROM nonexistent_table_xyz",  # Invalid SQL
    ]
    
    for query in problematic_queries:
        context = ToolContext()
        
        # Test each agent with problematic input
        for agent in [db_agent, ds_agent, bqml_agent]:
            response = await agent.process_query(query, context)
            
            # Should not crash and should return some response
            assert isinstance(response, str)
            assert len(response) > 0
            
            # Should not contain stack traces or raw error messages
            assert "Traceback" not in response
            assert "Exception" not in response


@pytest.mark.asyncio 
async def test_context_utilization():
    """Test how well agents utilize provided context."""
    context = ToolContext()
    context.update_state("current_dataset", {
        "filename": "sales_data.csv",
        "columns": ["customer_id", "product_id", "sales_amount", "date"],
        "shape": "10000 rows × 4 columns"
    })
    
    query = "Analyze this dataset"
    
    # Test analytics agent with context
    response = await ds_agent.process_query(query, context)
    
    # Should reference the dataset information
    assert "sales_data" in response or "customer_id" in response or "10000" in response
    
    # Should provide specific analysis relevant to the columns
    assert any(col in response for col in ["customer_id", "product_id", "sales_amount", "date"])