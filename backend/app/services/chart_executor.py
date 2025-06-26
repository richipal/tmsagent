"""
Chart execution service for generating and serving visualization images.
"""

import os
import uuid
import tempfile
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Any, Optional
import base64
import io
import logging

# Use Agg backend for headless chart generation
matplotlib.use('Agg')

logger = logging.getLogger(__name__)


class ChartExecutor:
    """Executes Python chart code and returns image data."""
    
    def __init__(self):
        """Initialize chart executor."""
        self.chart_dir = os.path.join(os.getcwd(), "uploads", "charts")
        os.makedirs(self.chart_dir, exist_ok=True)
        
    def execute_chart_code(self, python_code: str) -> Dict[str, Any]:
        """
        Execute Python matplotlib code and return chart image.
        
        Args:
            python_code: Python code string containing matplotlib chart generation
            
        Returns:
            Dict containing image data and metadata
        """
        try:
            # Extract the actual Python code from markdown code blocks
            if "```python" in python_code:
                code_start = python_code.find("```python") + 9
                code_end = python_code.find("```", code_start)
                if code_end != -1:
                    clean_code = python_code[code_start:code_end].strip()
                else:
                    clean_code = python_code[code_start:].strip()
            else:
                clean_code = python_code.strip()
            
            # Replace plt.show() with plt.savefig() to capture the image
            chart_id = str(uuid.uuid4())
            chart_filename = f"chart_{chart_id}.png"
            chart_path = os.path.join(self.chart_dir, chart_filename)
            
            # Modify the code to save instead of show
            if "plt.show()" in clean_code:
                clean_code = clean_code.replace("plt.show()", f"plt.savefig('{chart_path}', dpi=150, bbox_inches='tight')")
            else:
                clean_code += f"\nplt.savefig('{chart_path}', dpi=150, bbox_inches='tight')"
            
            # Add plt.close() to prevent memory leaks
            clean_code += "\nplt.close()"
            
            logger.info(f"Executing chart code: {clean_code[:100]}...")
            
            # Execute the Python code in a controlled environment
            import pandas as pd
            try:
                import seaborn as sns
            except ImportError:
                sns = None
                
            exec_globals = {
                'matplotlib': matplotlib,
                'plt': plt,
                'np': np,
                'numpy': np,
                'pd': pd,
                'pandas': pd,
                '__builtins__': __builtins__
            }
            
            if sns:
                exec_globals['sns'] = sns
                exec_globals['seaborn'] = sns
            
            exec(clean_code, exec_globals)
            
            # Check if file was created
            if os.path.exists(chart_path):
                # Convert to base64 for embedding in response
                with open(chart_path, 'rb') as img_file:
                    img_data = base64.b64encode(img_file.read()).decode('utf-8')
                
                return {
                    "success": True,
                    "chart_id": chart_id,
                    "chart_path": chart_path,
                    "chart_url": f"/api/charts/{chart_filename}",
                    "image_data": img_data,
                    "message": "Chart generated successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Chart file was not created"
                }
                
        except Exception as e:
            logger.error(f"Error executing chart code: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_chart_path(self, chart_filename: str) -> Optional[str]:
        """Get the full path to a chart file."""
        chart_path = os.path.join(self.chart_dir, chart_filename)
        if os.path.exists(chart_path):
            return chart_path
        return None


# Global chart executor instance
chart_executor = ChartExecutor()