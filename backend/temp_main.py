"""
Temporary main.py without authentication dependencies
For testing basic functionality
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="TMS AI Chatbot Assistant",
    description="Backend API for the ADK-powered data science chatbot",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "TMS AI Chatbot API is running (temp version without auth)"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "auth": "disabled"}

# Simple auth endpoints for development
@app.get("/auth/status")
async def auth_status():
    return {
        "authenticated": True,
        "user": {
            "id": "temp_user",
            "email": "temp@example.com", 
            "name": "Temporary User"
        }
    }

@app.get("/auth/dev-login")
async def dev_login():
    return {
        "access_token": "temp_token_123",
        "user": {
            "id": "temp_user",
            "email": "temp@example.com",
            "name": "Temporary User"
        },
        "message": "Temporary authentication"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("temp_main:app", host="0.0.0.0", port=8000, reload=True)