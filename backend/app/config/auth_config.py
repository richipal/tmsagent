"""
Google OAuth Authentication Configuration
Handles Google OAuth2 setup and JWT token management for user authentication
"""

import os
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

import jwt
from google.oauth2 import id_token
from google.auth.transport import requests
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv

load_dotenv()


@dataclass
class GoogleUser:
    """Represents an authenticated Google user"""
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    verified_email: bool = False


class AuthConfig:
    """Configuration for Google OAuth authentication"""
    
    def __init__(self):
        # Google OAuth Configuration
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
        
        # JWT Configuration
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.jwt_algorithm = "HS256"
        self.jwt_expiration_hours = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
        
        # OAuth Setup
        self.oauth = OAuth()
        self._setup_google_oauth()
        
        # Validate configuration
        self._validate_config()
    
    def _setup_google_oauth(self):
        """Setup Google OAuth client"""
        if self.google_client_id and self.google_client_secret:
            self.oauth.register(
                name='google',
                client_id=self.google_client_id,
                client_secret=self.google_client_secret,
                server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
                client_kwargs={
                    'scope': 'openid email profile'
                }
            )
    
    def _validate_config(self):
        """Validate authentication configuration"""
        missing_vars = []
        
        if not self.google_client_id:
            missing_vars.append("GOOGLE_CLIENT_ID")
        if not self.google_client_secret:
            missing_vars.append("GOOGLE_CLIENT_SECRET")
        
        if missing_vars:
            print(f"⚠️ Missing environment variables for Google OAuth: {', '.join(missing_vars)}")
            print("Authentication will be disabled until these are configured.")
            self.enabled = False
        else:
            self.enabled = True
            print("✅ Google OAuth authentication configured")
            print(f"   Client ID: {self.google_client_id[:20]}...")
            print(f"   Redirect URI: {self.google_redirect_uri}")
    
    def create_jwt_token(self, user: GoogleUser) -> str:
        """Create a JWT token for an authenticated user"""
        payload = {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "verified_email": user.verified_email,
            "exp": datetime.utcnow() + timedelta(hours=self.jwt_expiration_hours),
            "iat": datetime.utcnow(),
            "iss": "tms-chatbot"
        }
        
        return jwt.encode(payload, self.jwt_secret_key, algorithm=self.jwt_algorithm)
    
    def verify_jwt_token(self, token: str) -> Optional[GoogleUser]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret_key, algorithms=[self.jwt_algorithm])
            
            return GoogleUser(
                id=payload.get("user_id"),
                email=payload.get("email"),
                name=payload.get("name"),
                picture=payload.get("picture"),
                verified_email=payload.get("verified_email", False)
            )
        
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None
    
    def verify_google_token(self, id_token_str: str) -> Optional[GoogleUser]:
        """Verify Google ID token and extract user information"""
        try:
            # Verify the token
            id_info = id_token.verify_oauth2_token(
                id_token_str, 
                requests.Request(), 
                self.google_client_id
            )
            
            # Extract user information
            if id_info.get('iss') not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
            
            return GoogleUser(
                id=id_info['sub'],
                email=id_info['email'],
                name=id_info.get('name', ''),
                picture=id_info.get('picture'),
                verified_email=id_info.get('email_verified', False)
            )
            
        except ValueError as e:
            print(f"Token verification failed: {e}")
            return None


class MockAuthConfig:
    """Mock authentication for development when Google OAuth is not configured"""
    
    def __init__(self):
        self.enabled = True
        print("🔧 Using mock authentication for development")
    
    def create_jwt_token(self, user: GoogleUser) -> str:
        """Create a mock JWT token"""
        return f"mock_token_{user.id}"
    
    def verify_jwt_token(self, token: str) -> Optional[GoogleUser]:
        """Verify mock token"""
        if token.startswith("mock_token_"):
            user_id = token.replace("mock_token_", "")
            return GoogleUser(
                id=user_id,
                email=f"user{user_id}@example.com",
                name=f"Test User {user_id}",
                picture=None,
                verified_email=True
            )
        return None
    
    def get_mock_user(self, user_id: str = "dev_user") -> GoogleUser:
        """Get a mock user for development"""
        return GoogleUser(
            id=user_id,
            email=f"{user_id}@example.com",
            name=f"Development User",
            picture=None,
            verified_email=True
        )


# Global auth configuration instance
auth_config = AuthConfig()

# Use mock auth if Google OAuth is not configured
if not auth_config.enabled:
    auth_config = MockAuthConfig()


def get_auth_config() -> AuthConfig:
    """Get the global authentication configuration"""
    return auth_config