from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.api.upload import router as upload_router
from app.api.websocket import router as websocket_router
from app.api.charts import router as charts_router
from app.api.table_info import router as table_info_router

app = FastAPI(
    title="ADK Data Science Chatbot API",
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

app.include_router(chat_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(websocket_router)
app.include_router(charts_router, prefix="/api")
app.include_router(table_info_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "ADK Data Science Chatbot API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    uvicorn.run("main:app", host=host, port=port, reload=True)