import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt

# Secret key to sign JWT token
# In a real app, generate a strong random key and keep it secret!
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hours

# Read credentials from environment variables or use defaults
# API_USERNAME and API_PASSWORD removed as we use UserAccount DB model

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

from sqlalchemy.orm import Session
from database import get_db
import models

async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    Dependency to check if the user is authenticated via X-API-Key header or cookie.
    If anything fails, raises 401.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    
    # Check for API Key first
    api_key_header = request.headers.get("X-API-Key")
    if api_key_header:
        # Validate against database
        db_key = db.query(models.ApiKey).filter(models.ApiKey.key_value == api_key_header).first()
        if db_key and db_key.active == 1:
            # RBAC Scope Check
            if not db_key.allow_admin:
                method = request.method.upper()
                if method == "GET" and not db_key.allow_get:
                    raise HTTPException(status_code=403, detail="Forbidden: Missing GET permission")
                if method == "POST" and not db_key.allow_post:
                    raise HTTPException(status_code=403, detail="Forbidden: Missing POST permission")
                if method == "PUT" and not db_key.allow_put:
                    raise HTTPException(status_code=403, detail="Forbidden: Missing PUT permission")
                if method == "DELETE" and not db_key.allow_delete:
                    raise HTTPException(status_code=403, detail="Forbidden: Missing DELETE permission")
                
            return db_key.name # Return the key name as the "user"
        raise credentials_exception

    # If no API key, fallback to cookie
    token = request.cookies.get("session_token")
    if not token:
        raise credentials_exception
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    return username

