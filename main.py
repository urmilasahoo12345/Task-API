import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# --- Supabase Setup ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://axzjxppjdvndgrbwycrf.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY must be set in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Enables Bearer token auth & Lock button in Swagger UI (/docs)
security_scheme = HTTPBearer()

# --- App Initialization ---
app = FastAPI(
    title="Auth - Login & Protect API",
    description="BE-03 Assignment with FastAPI and Supabase Auth",
    version="1.0"
)

# --- Models ---
class AuthPayload(BaseModel):
    email: EmailStr
    password: str

class TaskPayload(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

# --- Middleware / Dependency for Token Verification ---
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    """Verifies the Bearer JWT token against Supabase."""
    token = credentials.credentials
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Invalid or expired token"}
            )
        return user_response.user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid or expired token"}
        )

# --- Auth Routes ---
@app.post("/auth/signup", status_code=status.HTTP_201_CREATED, summary="Create account")
def signup(payload: AuthPayload):
    try:
        response = supabase.auth.sign_up({
            "email": payload.email,
            "password": payload.password
        })
        return {
            "message": "User created successfully",
            "user": {
                "id": response.user.id if response.user else None,
                "email": payload.email
            }
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@app.post("/auth/login", status_code=status.HTTP_200_OK, summary="Log in & get JWT")
def login(payload: AuthPayload):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password
        })
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "token_type": "bearer"
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid login credentials"}
        )

@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    try:
        supabase.auth.sign_out(credentials.credentials)
    except Exception:
        pass
    return None

# --- Public & Protected Gates ---
@app.get("/public/info", summary="Public Info")
def public_info():
    return {"message": "Welcome! This information is publicly accessible."}

@app.get("/protected/profile", summary="Protected User Profile")
def get_profile(user=Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "created_at": str(user.created_at)
    }

# --- Base Info Routes ---
@app.get("/", summary="Root API Info")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/auth/signup", "/auth/login", "/protected/profile", "/tasks"]}

@app.get("/health", summary="Health Check")
def health_check():
    return {"status": "ok"}