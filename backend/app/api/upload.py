from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import aiofiles
import os
import uuid
from typing import Optional
import pandas as pd
import json
from app.models.chat import FileUploadResponse
from app.data_science.agent import root_agent as data_science_agent
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".csv", ".json", ".xlsx", ".txt", ".parquet"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a file for data analysis"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(contents)
        
        # Process file with Data Science Multi-Agent System
        # Create analysis context for the uploaded file
        file_context = {
            "file_id": file_id,
            "original_filename": file.filename,
            "file_size": len(contents),
            "file_type": file_ext
        }
        
        # Generate analysis prompt for the data science agents
        analysis_prompt = f"""I've uploaded a {file_ext} file named '{file.filename}' ({len(contents)} bytes). 
        Please analyze this dataset and provide comprehensive insights including:
        1. Data structure and quality assessment
        2. Key statistics and patterns
        3. Recommended analyses and visualizations
        4. Data cleaning suggestions if needed
        5. Potential machine learning opportunities"""
        
        result = await data_science_agent.process_message(analysis_prompt, file_context)
        
        logger.info(f"File uploaded and processed: {filename}")
        
        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            size=len(contents),
            status="completed",
            message="File uploaded and processed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/file/{file_id}")
async def get_file_info(file_id: str):
    """Get information about an uploaded file"""
    try:
        # Find file in upload directory
        for filename in os.listdir(UPLOAD_DIR):
            if filename.startswith(file_id):
                file_path = os.path.join(UPLOAD_DIR, filename)
                file_size = os.path.getsize(file_path)
                
                return {
                    "file_id": file_id,
                    "filename": filename.split("_", 1)[1],  # Remove UUID prefix
                    "size": file_size,
                    "path": file_path
                }
        
        raise HTTPException(status_code=404, detail="File not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/{session_id}")
async def export_chat(session_id: str, format: str = "json"):
    """Export chat history in various formats"""
    try:
        from app.core.session_manager import session_manager
        
        messages = session_manager.get_messages(session_id)
        
        if format.lower() == "json":
            data = json.dumps([
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in messages
            ], indent=2)
            
            return StreamingResponse(
                iter([data]),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=chat_{session_id}.json"}
            )
        
        elif format.lower() == "csv":
            df = pd.DataFrame([
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in messages
            ])
            
            csv_data = df.to_csv(index=False)
            
            return StreamingResponse(
                iter([csv_data]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=chat_{session_id}.csv"}
            )
        
        elif format.lower() == "txt":
            text_data = "\n".join([
                f"[{msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {msg.role.upper()}: {msg.content}\n"
                for msg in messages
            ])
            
            return StreamingResponse(
                iter([text_data]),
                media_type="text/plain",
                headers={"Content-Disposition": f"attachment; filename=chat_{session_id}.txt"}
            )
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))