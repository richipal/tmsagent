from fastapi import APIRouter
from typing import List, Dict, Any
import random

router = APIRouter()

def get_comprehensive_question_categories() -> Dict[str, List[str]]:
    """Get comprehensive question suggestions based on TMS data model."""
    return {
        "Employee Performance & Hours": [
            "Show me the top 10 employees by total hours worked",
            "Which employees worked the most overtime last month?",
            "What's the average hours worked per employee this year?",
            "Show me employees with the highest productivity rates",
            "Which employees haven't submitted time entries recently?",
            "Compare hours worked between departments",
            "Show me part-time vs full-time employee hour patterns"
        ],
        
        "Time Tracking & Payroll": [
            "How many time entries are pending approval?",
            "Show me all time entries that need manager approval",
            "What's the current payroll period cut-off date?",
            "Which time entries were posted to payroll last week?",
            "Show me disapproved time entries and reasons",
            "What's the average time between entry creation and approval?",
            "How many hours are awaiting payroll processing?"
        ],
        
        "Location Analytics": [
            "Which locations have the most employee time entries?",
            "Show me overtime patterns by location",
            "Compare productivity across different work sites",
            "Which locations have the highest absence rates?",
            "Show me time entry distribution by location",
            "Which work sites have the most active employees?",
            "Compare average hours worked per location"
        ],
        
        "Activity & Task Analysis": [
            "What are the most frequently used activity codes?",
            "Show me time spent on different types of activities",
            "Which activities generate the most overtime?",
            "Compare regular vs overtime activity usage",
            "Show me inactive or expired activities",
            "Which activities have the highest pay rates?",
            "How much time is spent on administrative vs operational tasks?"
        ],
        
        "Absence & Leave Management": [
            "Show me vacation usage patterns by employee",
            "Which employees have the most sick leave taken?",
            "What are the most common absence reasons?",
            "Show me absence trends over the past 6 months",
            "Which departments have the highest absence rates?",
            "Compare personal time vs vacation usage",
            "Show me employees approaching leave limits"
        ],
        
        "Management Reports": [
            "Show me manager approval patterns and response times",
            "Which managers have the most direct reports?",
            "Compare approval rates between different managers",
            "Show me department-level time tracking summaries",
            "Which teams are most efficient with time entry submissions?",
            "Show me cost analysis by department and activity",
            "Generate executive summary of workforce productivity"
        ],
        
        "Compliance & Data Quality": [
            "Show me time entries with missing or incomplete data",
            "Which employees haven't updated their time sheets?",
            "Show me potential duplicate time entries",
            "Which time entries exceed normal working hours?",
            "Show me gaps in employee time tracking",
            "Identify employees with unusual work patterns",
            "Show me time entries that may need review"
        ],
        
        "Trends & Forecasting": [
            "Show me seasonal patterns in employee hours",
            "Compare this month's productivity to last month",
            "What are the busiest days/times for time entry submissions?",
            "Show me year-over-year absence trends",
            "Predict next month's overtime requirements",
            "Show me employee retention patterns",
            "Analyze workload distribution trends"
        ]
    }

def mask_pii_in_question(question: str) -> str:
    """Mask personally identifiable information in questions."""
    # Replace specific names and codes with generic placeholders
    masked_question = question
    
    # Replace common names with generic ones
    masked_question = masked_question.replace("Rosalinda Rodriguez", "John Doe")
    masked_question = masked_question.replace("rosalinda rodriguez", "john doe")
    
    # Replace specific location codes
    masked_question = masked_question.replace("location 061", "location ABC")
    masked_question = masked_question.replace("location 075", "location XYZ")
    
    # Replace specific activity codes
    masked_question = masked_question.replace("DBOUTM", "ACTCODE")
    
    return masked_question

@router.get("/suggested-questions", response_model=List[str])
async def get_suggested_questions():
    """Get 6 diverse questions covering different aspects of the TMS system."""
    categories = get_comprehensive_question_categories()
    
    # Select one question from each of 6 different categories
    selected_questions = []
    category_names = list(categories.keys())
    
    # Randomly select 6 categories (or all if less than 6)
    num_categories = min(6, len(category_names))
    selected_categories = random.sample(category_names, num_categories)
    
    for category in selected_categories:
        questions = categories[category]
        if questions:
            question = random.choice(questions)
            masked_question = mask_pii_in_question(question)
            selected_questions.append(masked_question)
    
    return selected_questions

@router.get("/suggested-questions/categories", response_model=Dict[str, List[str]])
async def get_question_categories():
    """Get all available question categories and their questions."""
    categories = get_comprehensive_question_categories()
    
    # Mask PII in all questions
    masked_categories = {}
    for category, questions in categories.items():
        masked_categories[category] = [mask_pii_in_question(q) for q in questions]
    
    return masked_categories

@router.get("/suggested-questions/category/{category_name}", response_model=List[str])
async def get_questions_by_category(category_name: str):
    """Get questions for a specific category."""
    categories = get_comprehensive_question_categories()
    
    # Find category (case-insensitive)
    for cat_name, questions in categories.items():
        if cat_name.lower().replace(" ", "").replace("&", "") == category_name.lower().replace(" ", "").replace("&", ""):
            return [mask_pii_in_question(q) for q in questions]
    
    return []