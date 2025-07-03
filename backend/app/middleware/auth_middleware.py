"""
Authentication Middleware
Handles JWT token validation and user context injection
"""

from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse

from app.config.auth_config import get_auth_config, GoogleUser


security = HTTPBearer(auto_error=False)


class AuthMiddleware:
    """Middleware to handle authentication for protected routes"""
    
    def __init__(self):
        self.auth_config = get_auth_config()
    
    async def __call__(self, request: Request, call_next: Callable):
        """Process request with authentication"""
        
        # Skip authentication for public routes
        if self._is_public_route(request.url.path):
            return await call_next(request)
        
        # Extract and verify token
        user = await self._get_authenticated_user(request)
        
        if user:
            # Add user to request state for use in route handlers
            request.state.user = user
            request.state.authenticated = True
        else:
            # For development, allow unauthenticated access with mock user
            if isinstance(self.auth_config, type(self.auth_config)) and hasattr(self.auth_config, 'get_mock_user'):
                mock_user = self.auth_config.get_mock_user()
                request.state.user = mock_user
                request.state.authenticated = True
            else:
                request.state.user = None
                request.state.authenticated = False
        
        return await call_next(request)
    
    def _is_public_route(self, path: str) -> bool:
        """Check if a route is public and doesn't require authentication"""
        public_routes = [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/google/login",
            "/auth/google/callback",
            "/auth/logout",
            "/auth/status",
            "/auth/config",
            "/auth/debug"
        ]
        
        # Check exact matches and specific prefixes
        if path in public_routes:
            return True
        
        # Check for specific path prefixes that should be public
        if path.startswith("/api/suggested-questions"):
            return True
        
        # Allow favicon and other static assets
        if path.endswith(('.ico', '.png', '.jpg', '.jpeg', '.css', '.js', '.map')):
            return True
        
        return False
    
    async def _get_authenticated_user(self, request: Request) -> Optional[GoogleUser]:
        """Extract and verify user from request"""
        
        # Try to get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            return self.auth_config.verify_jwt_token(token)
        
        # Try to get token from cookie
        token = request.cookies.get("access_token")
        if token:
            return self.auth_config.verify_jwt_token(token)
        
        # Try to get token from query parameter (for development)
        token = request.query_params.get("token")
        if token:
            return self.auth_config.verify_jwt_token(token)
        
        return None


def get_current_user(request: Request) -> Optional[GoogleUser]:
    """Get the current authenticated user from request state"""
    return getattr(request.state, 'user', None)


def require_auth(request: Request) -> GoogleUser:
    """Require authentication and return the current user"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user


def get_user_id(request: Request) -> str:
    """Get the current user ID or return a default for unauthenticated requests"""
    user = get_current_user(request)
    if user:
        return user.id
    
    # For development/testing, return a default user ID
    return "anonymous_user"


# Global middleware instance
auth_middleware = AuthMiddleware()