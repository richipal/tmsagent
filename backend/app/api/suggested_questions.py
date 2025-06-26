from fastapi import APIRouter
from typing import List
from app.data_science.sub_agents.bigquery.prompts_config import SQL_EXAMPLES
import random

router = APIRouter()

def mask_pii_in_question(question: str) -> str:
    """Mask personally identifiable information in questions."""
    # Replace specific employee names with generic placeholders
    masked_question = question
    
    # Replace "Rosalinda Rodriguez" with "John Doe"
    masked_question = masked_question.replace("Rosalinda Rodriguez", "John Doe")
    masked_question = masked_question.replace("rosalinda rodriguez", "john doe")
    
    # Replace specific location codes with generic ones
    masked_question = masked_question.replace("location 061", "location ABC")
    
    return masked_question

@router.get("/suggested-questions", response_model=List[str])
async def get_suggested_questions():
    """Get 3 random questions from the SQL examples for suggested queries."""
    # Extract questions from SQL_EXAMPLES and mask PII
    all_questions = []
    for example in SQL_EXAMPLES:
        if "question" in example:
            masked_question = mask_pii_in_question(example["question"])
            all_questions.append(masked_question)
    
    # Return 3 random questions
    if len(all_questions) >= 3:
        return random.sample(all_questions, 3)
    else:
        return all_questions