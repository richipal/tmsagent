"""
Chart serving API endpoints.
"""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
import os
import logging
from app.services.chart_executor import chart_executor

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/charts/{chart_filename}")
async def get_chart(chart_filename: str):
    """Serve a chart image file."""
    try:
        chart_path = chart_executor.get_chart_path(chart_filename)
        
        if not chart_path:
            raise HTTPException(status_code=404, detail="Chart not found")
        
        return FileResponse(
            chart_path,
            media_type="image/png",
            filename=chart_filename
        )
        
    except Exception as e:
        logger.error(f"Error serving chart {chart_filename}: {e}")
        raise HTTPException(status_code=500, detail="Error serving chart")