"""
Authentication middleware for the API.
"""

from fastapi import Request, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional, Dict, Any
import jwt
from datetime import datetime, timedelta
import os

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Secret key for JWT - in production, this should be stored securely
# and loaded from environment variables
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "development_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Mock user database - in production, this would be a real database
fake_users_db = {
    "testuser": {
        "username": "testuser",
        "full_name": "Test User",
        "email": "testuser@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "disabled": False,
    }
}

class User:
    def __init__(self, username: str, email: str, full_name: str = None, disabled: bool = False):
        self.username = username
        self.email = email
        self.full_name = full_name
        self.disabled = disabled

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None):
    """
    Create a JWT access token.
    
    Parameters:
    - data: Data to encode in the token
    - expires_delta: Optional expiration time
    
    Returns:
    - JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get the current user from the JWT token.
    
    Parameters:
    - token: JWT token
    
    Returns:
    - User object
    
    Raises:
    - HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    # In production, this would query a database
    user_dict = fake_users_db.get(username)
    if user_dict is None:
        raise credentials_exception
    
    return User(
        username=user_dict["username"],
        email=user_dict["email"],
        full_name=user_dict.get("full_name"),
        disabled=user_dict.get("disabled", False)
    )

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """
    Get the current active user.
    
    Parameters:
    - current_user: User object from get_current_user
    
    Returns:
    - User object if active
    
    Raises:
    - HTTPException: If user is disabled
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Authentication dependency to use in routes
async def authenticate(request: Request, token: str = Depends(oauth2_scheme)):
    """
    Authenticate a request.
    
    Parameters:
    - request: FastAPI request object
    - token: JWT token
    
    Returns:
    - User object
    
    Raises:
    - HTTPException: If authentication fails
    """
    user = await get_current_active_user(await get_current_user(token))
    return user