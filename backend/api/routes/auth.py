from fastapi import APIRouter, HTTPException, Header, Depends
from backend.services.auth_service import AuthService
from typing import Optional
import json

router = APIRouter(prefix="/auth", tags=["authentication"])

async def get_auth_service():
    return AuthService()

async def get_current_user(
    authorization: Optional[str] = Header(None),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Dependency to get current authenticated user"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    user_data = await auth_service.verify_token(token)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user_data

@router.post("/verify")
async def verify_token(
    authorization: Optional[str] = Header(None),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Verify JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    token = authorization.split(" ")[1]
    user_data = await auth_service.verify_token(token)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {"user": user_data}

@router.get("/profile")
async def get_profile(
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get user profile"""
    profile = await auth_service.get_user_profile(current_user["user_id"])
    return {"profile": profile}