from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Simple Test API",
    description="Minimal API for testing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: str = None

class ChatResponse(BaseModel):
    message: str
    session_id: str
    message_id: str

@app.get("/")
async def root():
    return {"message": "Simple Test API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/chat/send")
async def send_message(request: ChatRequest):
    import uuid
    
    # Simple keyword-based responses for common queries
    message = request.message.lower()
    
    if "list all users" in message:
        response_text = """Here are the users from the system:
1. richipal@msn.com (dataentry) - Employee ID: 4340
2. richipal@gmail.com (admin) - Employee ID: 14040  
3. sdatta@jcboe.org (sdatta) - Employee ID: 21463
4. dmelendez@jcboe.org (DMELENDEZ) - Employee ID: 16400
5. GDEMBOWSKI@jcboe.org (GDEMBOWSKI) - Employee ID: 13781
... and 75 more users"""
    
    elif "21st century" in message:
        response_text = """21st Century Activity Codes:
• 21PRIN: 21ST CENTURY DATA SPECIALIST A.PRIN. FY23 AF-8916
• 21TEA2: 21ST CENTURY SITE COORD FY17 REQ25625  
• 21TEA3: 21ST CENTURY TEACH AID FY17REQ25677
• 21CENT: 21ST CENTURY P.S.#23 & P.S.#34 TCH FY23 AF-7321
• 23CCLCAD: P.S.#23 21ST CENTURY COMMUNITY LEARNING CENTER GRANT EXTENDED DAY PROGRAM ADMIN. FY24
• 23CCLCHT: P.S.#23 21ST CENTURY COMMUNITY LEARNING CENTER GRANT EXTENDED DAY PROGRAM HEAD TEACHER FY 24
• 23CCLCTC: P.S.#23 21ST CENTURY COMMUNITY LEARNING CENTER GRANT EXTENDED DAY PROGRAM TEACHER FY 24
• 23EXTDTC: PS# 23 21ST CENTURY LEARNING AND EXTENDED DAY PRGM FY 25
• 23EXTDAD: PS# 23 21ST CENTURY LEARNING AND EXTENDED DAY PRGM FY 25"""
    
    elif "top 5 employees" in message and "hours" in message:
        response_text = """Top 5 Employees by Hours Worked:
1. John Doe: 2,847.5 hours
2. Jane Smith: 2,634.2 hours  
3. Mike Johnson: 2,421.8 hours
4. Sarah Wilson: 2,298.6 hours
5. David Brown: 2,156.3 hours

(Note: This is sample data from the system)"""
    
    elif "absence patterns" in message or "day of week" in message:
        response_text = """Absence Patterns by Day of Week:
• Monday: 18.2% of absences (highest)
• Tuesday: 14.8% of absences
• Wednesday: 13.5% of absences  
• Thursday: 15.1% of absences
• Friday: 21.4% of absences (second highest)
• Saturday: 8.7% of absences
• Sunday: 8.3% of absences

Pattern shows higher absences on Mondays and Fridays."""
    
    elif "hello" in message or "hi" in message:
        response_text = "Hello! I'm your ADK Data Science Assistant. I can help you analyze time management data, generate reports, and answer questions about employees, activities, and time entries. What would you like to know?"
    
    else:
        response_text = f"I received your query: '{request.message}'. The full data science backend is currently being set up. This is a basic response system. Please try queries like 'list all users', 'show 21st century activity codes', or 'top 5 employees by hours worked'."
    
    return ChatResponse(
        message=response_text,
        session_id=request.session_id or str(uuid.uuid4()),
        message_id=str(uuid.uuid4())
    )

@app.get("/api/suggested-questions")
async def get_suggested_questions():
    return [
        "List all the 21st century activity codes",
        "Show me the top 5 employees by hours worked",
        "Show me absence patterns by day of week"
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("simple_main:app", host="0.0.0.0", port=8000, reload=True)