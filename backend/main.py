from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.api.upload import router as upload_router
from app.api.auth import router as auth_router
# WebSocket support removed - using HTTP REST API
from app.api.charts import router as charts_router
from app.api.table_info import router as table_info_router
from app.api.suggested_questions import router as suggested_questions_router
from app.api.database import router as database_router

# Import authentication middleware
from app.middleware.auth_middleware import auth_middleware

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

# Add authentication middleware
app.middleware("http")(auth_middleware)

app.include_router(auth_router)  # Auth routes don't need /api prefix
app.include_router(chat_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
# WebSocket router removed
app.include_router(charts_router, prefix="/api")
app.include_router(table_info_router, prefix="/api")
app.include_router(suggested_questions_router, prefix="/api")
app.include_router(database_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "ADK Data Science Chatbot API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """Initialize database and other resources on startup"""
    from app.database.models import db_manager
    
    try:
        # Force database initialization
        db_manager.init_database()
        
        # Test database connectivity
        sessions = db_manager.list_sessions()
        print(f"✅ Database initialized at: data/conversations.db")
        print(f"📊 Found {len(sessions)} existing sessions")
        
        # Initialize session manager to ensure it connects to the database
        from app.core.persistent_session_manager import persistent_session_manager
        print("✅ Session manager initialized")
        
        # Initialize observability
        from app.config.observability import observability
        if observability.enabled:
            print("✅ Observability (Langfuse) initialized")
        else:
            print("⚠️ Observability disabled or not configured")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    try:
        # Flush observability data
        from app.config.observability import observability
        observability.flush()
        print("✅ Observability data flushed")
    except Exception as e:
        print(f"⚠️ Error flushing observability data: {e}")

def serve():
    """Entry point for poetry script"""
    import uvicorn
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)

if __name__ == "__main__":
    serve()