from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.config import DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_USERNAME
from backend.core.security import generate_token, verify_password
from backend.database.database import get_db
from backend.database.models import AdminUser

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate administrator credentials."""
    # First check database for registered admin user
    user = db.query(AdminUser).filter(AdminUser.username == request.username).first()

    authenticated = False
    role = "ADMIN"

    if user:
        if verify_password(request.password, user.password_hash):
            authenticated = True
            role = user.role
    else:
        # Fallback to default admin credentials from config
        if request.username == DEFAULT_ADMIN_USERNAME and request.password == DEFAULT_ADMIN_PASSWORD:
            authenticated = True

    if not authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrator credentials."
        )

    token = generate_token()

    return {
        "status": "success",
        "message": "Authentication successful",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": request.username,
            "role": role
        }
    }


@router.get("/status")
def auth_status():
    """Health status of authentication service."""
    return {
        "auth_service": "online",
        "method": "bearer"
    }
