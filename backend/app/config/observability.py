"""
Observability configuration for tracking user queries and system performance
"""

import os
from typing import Optional, Dict, Any
from functools import wraps
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import Langfuse, make it optional
try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    print("⚠️ Langfuse not available - observability disabled")
    LANGFUSE_AVAILABLE = False
    Langfuse = None

# Langfuse configuration
LANGFUSE_ENABLED = os.getenv("LANGFUSE_ENABLED", "true").lower() == "true"
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")  # Use cloud or self-hosted URL

# Privacy settings
TRACK_USER_QUERIES = os.getenv("TRACK_USER_QUERIES", "true").lower() == "true"
ANONYMIZE_USER_DATA = os.getenv("ANONYMIZE_USER_DATA", "false").lower() == "true"
EXCLUDE_PATTERNS = os.getenv("EXCLUDE_TRACKING_PATTERNS", "").split(",") if os.getenv("EXCLUDE_TRACKING_PATTERNS") else []

class ObservabilityManager:
    """Manages observability and tracking for the TMS chatbot"""
    
    def __init__(self):
        self.langfuse_client = None
        self.enabled = LANGFUSE_ENABLED and LANGFUSE_AVAILABLE
        
        if self.enabled and LANGFUSE_AVAILABLE:
            try:
                self.langfuse_client = Langfuse(
                    public_key=LANGFUSE_PUBLIC_KEY or None,
                    secret_key=LANGFUSE_SECRET_KEY or None,
                    host=LANGFUSE_HOST,
                    release=os.getenv("APP_VERSION", "1.0.0"),
                    debug=os.getenv("LANGFUSE_DEBUG", "false").lower() == "true"
                )
                logger.info(f"✅ Langfuse observability initialized (host: {LANGFUSE_HOST})")
            except Exception as e:
                logger.warning(f"⚠️ Langfuse initialization failed: {e}. Running without observability.")
                self.enabled = False
        else:
            logger.info("⚠️ Observability disabled (Langfuse not available or disabled)")
    
    def track_query(self, session_id: str, query: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """Track a user query"""
        if not self.enabled or not TRACK_USER_QUERIES:
            return None
        
        # Check if query should be excluded
        for pattern in EXCLUDE_PATTERNS:
            if pattern and pattern in query.lower():
                logger.debug(f"Skipping tracking for query matching excluded pattern: {pattern}")
                return None
        
        try:
            # Anonymize if configured
            tracked_query = self._anonymize_query(query) if ANONYMIZE_USER_DATA else query
            
            # Create trace for the query
            trace = self.langfuse_client.trace(
                name="user_query",
                user_id=session_id if not ANONYMIZE_USER_DATA else None,
                session_id=session_id,
                metadata={
                    "query_length": len(query),
                    "timestamp": datetime.utcnow().isoformat(),
                    **(metadata or {})
                }
            )
            
            # Create span for query processing
            trace.span(
                name="query_received",
                input=tracked_query,
                metadata={
                    "original_length": len(query),
                    "contains_sql": "select" in query.lower() or "from" in query.lower(),
                    "is_chart_request": any(word in query.lower() for word in ["chart", "graph", "plot", "visuali"])
                }
            )
            
            return trace
        except Exception as e:
            logger.error(f"Error tracking query: {e}")
            return None
    
    def track_response(self, trace: Any, response: str, agent_metrics: Optional[Dict[str, Any]] = None):
        """Track the response to a query"""
        if not self.enabled or not trace:
            return
        
        try:
            trace.span(
                name="response_generated",
                output=response[:1000] if ANONYMIZE_USER_DATA else response,  # Limit size if anonymizing
                metadata={
                    "response_length": len(response),
                    "agents_used": agent_metrics.get("agents_used", []) if agent_metrics else [],
                    "total_duration_ms": agent_metrics.get("duration_ms", 0) if agent_metrics else 0,
                    "has_chart": "/api/charts/" in response,
                    "has_error": "error" in response.lower() or "failed" in response.lower()
                }
            )
            
            # Track costs if available
            if agent_metrics and "token_usage" in agent_metrics:
                trace.score(
                    name="token_usage",
                    value=agent_metrics["token_usage"]
                )
            
            # Update trace status
            trace.update(
                output=response[:1000] if ANONYMIZE_USER_DATA else response,
                metadata={
                    "success": True,
                    "response_type": self._classify_response(response)
                }
            )
        except Exception as e:
            logger.error(f"Error tracking response: {e}")
    
    def track_agent_call(self, trace: Any, agent_name: str, input_data: str, output_data: str, duration_ms: float):
        """Track individual agent calls"""
        if not self.enabled or not trace:
            return
        
        try:
            trace.span(
                name=f"agent_{agent_name}",
                input=input_data[:500] if ANONYMIZE_USER_DATA else input_data,
                output=output_data[:500] if ANONYMIZE_USER_DATA else output_data,
                metadata={
                    "agent": agent_name,
                    "duration_ms": duration_ms,
                    "output_length": len(output_data)
                }
            )
        except Exception as e:
            logger.error(f"Error tracking agent call: {e}")
    
    def track_error(self, trace: Any, error: str, error_type: str = "unknown"):
        """Track errors in query processing"""
        if not self.enabled or not trace:
            return
        
        try:
            trace.score(
                name="error",
                value=1,
                comment=f"{error_type}: {error}"
            )
            
            trace.update(
                metadata={
                    "success": False,
                    "error_type": error_type,
                    "error_message": error[:500]
                }
            )
        except Exception as e:
            logger.error(f"Error tracking error: {e}")
    
    def flush(self):
        """Flush any pending tracking data"""
        if self.enabled and self.langfuse_client:
            try:
                self.langfuse_client.flush()
            except Exception as e:
                logger.error(f"Error flushing observability data: {e}")
    
    def _anonymize_query(self, query: str) -> str:
        """Basic anonymization of queries"""
        # This is a simple implementation - enhance based on requirements
        import re
        
        # Remove email addresses
        query = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', query)
        
        # Remove phone numbers (basic pattern)
        query = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', query)
        
        # Remove numbers that might be IDs
        query = re.sub(r'\b\d{5,}\b', '[ID]', query)
        
        return query
    
    def _classify_response(self, response: str) -> str:
        """Classify the type of response"""
        response_lower = response.lower()
        
        if "/api/charts/" in response:
            return "chart"
        elif "```python" in response:
            return "code"
        elif "error" in response_lower or "failed" in response_lower:
            return "error"
        elif any(word in response_lower for word in ["select", "from", "where"]):
            return "sql"
        elif len(response) > 500:
            return "detailed_analysis"
        else:
            return "simple_answer"

# Global observability manager instance
observability = ObservabilityManager()

# Decorator for tracking functions
def track_operation(operation_name: str):
    """Decorator to track function execution"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not observability.enabled:
                return await func(*args, **kwargs)
            
            trace = observability.langfuse_client.trace(name=operation_name)
            span = trace.span(name=f"{operation_name}_execution")
            
            try:
                result = await func(*args, **kwargs)
                span.end(output=str(result)[:500])
                return result
            except Exception as e:
                span.end(level="error", status_message=str(e))
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not observability.enabled:
                return func(*args, **kwargs)
            
            trace = observability.langfuse_client.trace(name=operation_name)
            span = trace.span(name=f"{operation_name}_execution")
            
            try:
                result = func(*args, **kwargs)
                span.end(output=str(result)[:500])
                return result
            except Exception as e:
                span.end(level="error", status_message=str(e))
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator