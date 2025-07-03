"""
Authentication API Routes
Handles Google OAuth login, callback, and logout
"""

from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel

from app.config.auth_config import get_auth_config, GoogleUser
from app.middleware.auth_middleware import get_current_user, require_auth


router = APIRouter()


class LoginRequest(BaseModel):
    """Request model for login with Google ID token"""
    id_token: str


class UserResponse(BaseModel):
    """Response model for user information"""
    id: str
    email: str
    name: str
    picture: str = None
    verified_email: bool = False


@router.get("/auth/google/login")
async def google_login(request: Request):
    """Initiate Google OAuth login"""
    auth_config = get_auth_config()
    
    if not hasattr(auth_config, 'oauth') or not auth_config.enabled:
        # For development without OAuth configured
        return JSONResponse({
            "login_url": "/auth/dev-login",
            "message": "Development mode - use mock authentication"
        })
    
    try:
        # Build Google OAuth URL manually for better error handling
        google_auth_url = (
            f"https://accounts.google.com/o/oauth2/auth?"
            f"client_id={auth_config.google_client_id}&"
            f"redirect_uri={auth_config.google_redirect_uri}&"
            f"scope=openid email profile&"
            f"response_type=code&"
            f"access_type=offline"
        )
        
        # Redirect directly to Google
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=google_auth_url)
        
    except Exception as e:
        print(f"Google OAuth login error: {e}")
        return JSONResponse({
            "error": "OAuth configuration error",
            "message": "Please check Google OAuth credentials"
        }, status_code=500)


@router.get("/auth/google/callback")
async def google_callback(request: Request):
    """Handle Google OAuth callback"""
    auth_config = get_auth_config()
    
    if not hasattr(auth_config, 'google_client_id') or not auth_config.enabled:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="OAuth not configured"
        )
    
    try:
        # Get authorization code from callback
        code = request.query_params.get('code')
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code not found"
            )
        
        # Exchange code for token using requests
        import requests as requests_lib
        
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'client_id': auth_config.google_client_id,
            'client_secret': auth_config.google_client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': auth_config.google_redirect_uri,
        }
        
        token_response = requests_lib.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if 'access_token' not in token_json:
            raise Exception(f"Token exchange failed: {token_json}")
        
        # Get user info from Google
        user_info_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={token_json['access_token']}"
        user_response = requests_lib.get(user_info_url)
        user_info = user_response.json()
        
        # Create user object
        user = GoogleUser(
            id=user_info['id'],
            email=user_info['email'],
            name=user_info.get('name', ''),
            picture=user_info.get('picture'),
            verified_email=user_info.get('verified_email', False)
        )
        
        # Generate JWT token
        jwt_token = auth_config.create_jwt_token(user)
        
        # Redirect to frontend with token
        from fastapi.responses import RedirectResponse
        frontend_url = f"http://localhost:5174/?token={jwt_token}"
        print(f"OAuth success! Redirecting to: {frontend_url[:50]}...")
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        print(f"OAuth callback error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/auth/login")
async def login_with_id_token(login_request: LoginRequest):
    """Login with Google ID token (for frontend integration)"""
    auth_config = get_auth_config()
    
    try:
        # Verify Google ID token
        user = auth_config.verify_google_token(login_request.id_token)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Generate JWT token
        jwt_token = auth_config.create_jwt_token(user)
        
        return {
            "access_token": jwt_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture": user.picture,
                "verified_email": user.verified_email
            }
        }
        
    except Exception as e:
        print(f"ID token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


@router.get("/auth/dev-login")
async def dev_login(user_id: str = "dev_user"):
    """Development login (when OAuth is not configured)"""
    auth_config = get_auth_config()
    
    if hasattr(auth_config, 'get_mock_user'):
        user = auth_config.get_mock_user(user_id)
        jwt_token = auth_config.create_jwt_token(user)
        
        return {
            "access_token": jwt_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture": user.picture,
                "verified_email": user.verified_email
            },
            "message": "Development authentication"
        }
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication not configured"
    )


@router.post("/auth/logout")
async def logout():
    """Logout user"""
    response = JSONResponse({"message": "Logged out successfully"})
    response.delete_cookie("access_token")
    return response


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(request: Request):
    """Get current authenticated user information"""
    user = require_auth(request)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        picture=user.picture,
        verified_email=user.verified_email
    )


@router.get("/auth/status")
async def auth_status(request: Request):
    """Get authentication status"""
    auth_config = get_auth_config()
    
    # Check if authorization header is present
    auth_header = request.headers.get("Authorization")
    
    # First try to get user from middleware
    user = get_current_user(request)
    authenticated = getattr(request.state, 'authenticated', False)
    
    # If middleware didn't authenticate, try manual verification
    if not user and auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        user = auth_config.verify_jwt_token(token)
        authenticated = user is not None
    
    if user and authenticated:
        return {
            "authenticated": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture": user.picture
            },
            "oauth_enabled": auth_config.enabled if hasattr(auth_config, 'enabled') else False
        }
    
    return {
        "authenticated": False,
        "user": None,
        "oauth_enabled": auth_config.enabled if hasattr(auth_config, 'enabled') else False
    }

@router.get("/auth/config")
async def auth_config_status():
    """Get OAuth configuration status for debugging"""
    auth_config = get_auth_config()
    
    return {
        "oauth_enabled": auth_config.enabled if hasattr(auth_config, 'enabled') else False,
        "has_client_id": bool(getattr(auth_config, 'google_client_id', None)),
        "has_client_secret": bool(getattr(auth_config, 'google_client_secret', None)),
        "redirect_uri": getattr(auth_config, 'google_redirect_uri', None),
        "config_type": type(auth_config).__name__
    }

@router.get("/auth/debug")
async def debug_auth():
    """Debug endpoint to test authentication flow"""
    try:
        auth_config = get_auth_config()
        
        # Test OAuth URL generation
        google_auth_url = (
            f"https://accounts.google.com/o/oauth2/auth?"
            f"client_id={auth_config.google_client_id}&"
            f"redirect_uri={auth_config.google_redirect_uri}&"
            f"scope=openid email profile&"
            f"response_type=code&"
            f"access_type=offline"
        )
        
        return {
            "status": "success",
            "oauth_url": google_auth_url,
            "config_type": type(auth_config).__name__,
            "enabled": getattr(auth_config, 'enabled', False)
        }
    except Exception as e:
        import traceback
        return {
            "status": "error", 
            "error": str(e),
            "traceback": traceback.format_exc()
        }