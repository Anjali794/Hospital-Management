from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Literal
from pydantic import BaseModel, EmailStr, Field

from database import get_db
from models import DBUser
from security import hash_password, verify_password, create_access_token, RoleChecker, verify_token
from datetime import timedelta
from email_utils import send_email

router = APIRouter(prefix="/auth", tags=["Auth"])

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
optional_bearer = HTTPBearer(auto_error=False)

class SignupRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: Literal["admin", "doctor", "patient", "master_admin"]

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)

def register_user(payload: SignupRequest, role: str, db: Session):
    user_email = str(payload.email).lower()
    existing_user = db.query(DBUser).filter(DBUser.email == user_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = DBUser(
        name=payload.name,
        email=user_email,
        role=role,
        password_hash=hash_password(payload.password)
    )
    db.add(new_user)
    db.commit()
    return {"message": f"{role} signed up successfully", "email": new_user.email}

@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(
    payload: SignupRequest, 
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer)
):
    if payload.role in ["admin", "doctor", "master_admin"]:
        # Allow bypassing auth ONLY if there are absolutely 0 users in the database (First Setup)
        if db.query(DBUser).count() == 0:
            pass # Bootstrap the first super admin
        else:
            if not credentials:
                raise HTTPException(status_code=401, detail="Authentication required for this role")
            
            checker = RoleChecker(["admin", "master_admin"])
            checker(credentials)
        
    return register_user(payload, payload.role, db)

@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user_email = str(payload.email).lower()
    user = db.query(DBUser).filter(DBUser.email == user_email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "role": user.role}

@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user_email = str(payload.email).lower()
    user = db.query(DBUser).filter(DBUser.email == user_email).first()
    
    if not user:
        return {"message": "If that email is in our database, we will send a password reset link."}
        
    reset_token = create_access_token(
        data={"sub": user.email, "type": "reset"}, 
        expires_delta=timedelta(minutes=15)
    )
    
    # Since you don't have a frontend yet, we'll just send the raw token
    # You can copy this token and use it in the Swagger UI (/docs) or Postman
    body = f"Hello {user.name},\n\nPlease use the following token in the /reset-password API to reset your password:\n\n{reset_token}\n\nThis token will expire in 15 minutes."
    
    success = send_email(user.email, "Password Reset Request", body)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send password reset email")
        
    return {"message": "If that email is in our database, we will send a password reset link."}

@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    token_data = verify_token(payload.token)
    
    if token_data.get("type") != "reset":
        raise HTTPException(status_code=400, detail="Invalid token type")
        
    user_email = token_data.get("sub")
    user = db.query(DBUser).filter(DBUser.email == user_email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    
    return {"message": "Password has been reset successfully"}