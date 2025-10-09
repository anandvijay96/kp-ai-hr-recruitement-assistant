"""
Simple authentication endpoints for MVP demo
No complex OAuth - just basic session-based auth
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class SimpleLoginRequest(BaseModel):
    email: str
    password: str


@router.post("/simple-login")
async def simple_login(login_data: SimpleLoginRequest, request: Request):
    """
    Simple MVP login - creates session for demo purposes
    
    For MVP demo:
    - Email: hr@example.com
    - Password: demo123
    """
    # For MVP, accept demo credentials
    if login_data.email == "hr@example.com" and login_data.password == "demo123":
        # Create session
        request.session["user_id"] = "1"
        request.session["user_email"] = "hr@example.com"
        request.session["user_name"] = "HR Manager"
        request.session["user_role"] = "recruiter"
        
        logger.info(f"User logged in: {login_data.email}")
        
        return {
            "success": True,
            "message": "Login successful",
            "user": {
                "id": "1",
                "email": "hr@example.com",
                "name": "HR Manager",
                "role": "recruiter"
            }
        }
    
    # Invalid credentials
    logger.warning(f"Failed login attempt: {login_data.email}")
    raise HTTPException(status_code=401, detail="Invalid email or password")


@router.post("/logout")
async def logout(request: Request):
    """Logout - clear session"""
    request.session.clear()
    logger.info("User logged out")
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me")
async def get_current_user_info(request: Request):
    """Get current user information from session"""
    user_id = request.session.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "id": user_id,
        "email": request.session.get("user_email"),
        "name": request.session.get("user_name"),
        "role": request.session.get("user_role")
    }
