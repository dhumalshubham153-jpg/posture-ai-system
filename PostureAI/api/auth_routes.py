import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from modules.supabase_client import get_client, get_admin_client

router = APIRouter()


class RegisterData(BaseModel):
    email          : str
    password       : str
    name           : str = ""
    role           : str = "user"
    # Patient fields
    age            : Optional[int]   = None
    body_weight    : Optional[float] = None
    height         : Optional[float] = None
    # Physiotherapist fields
    experience     : Optional[str]   = None
    license_number : Optional[str]   = None
    speciality     : Optional[str]   = None


class LoginData(BaseModel):
    email   : str
    password: str


@router.post("/register")
async def register(data: RegisterData):
    try:
        sb  = get_client()
        res = sb.auth.sign_up({
            "email"   : data.email,
            "password": data.password,
            "options" : {
                "data": {
                    "name": data.name,
                    "role": data.role,
                }
            }
        })
        if res.user:
            # Update profile with extra details using admin client
            sb_admin = get_admin_client()
            update_data = {
                "name" : data.name,
                "role" : data.role,
                "email": data.email,
            }
            if data.role == "user":
                if data.age:           update_data["age"]         = data.age
                if data.body_weight:   update_data["body_weight"]  = data.body_weight
                if data.height:        update_data["height"]       = data.height
            else:
                if data.experience:    update_data["experience"]    = data.experience
                if data.license_number:update_data["license_number"]= data.license_number
                if data.speciality:    update_data["speciality"]    = data.speciality

            # Wait a moment for trigger to create profile then update
            import time
            time.sleep(1)
            sb_admin.table("profiles").upsert({
                "id": str(res.user.id),
                **update_data
            }).execute()

            return {
                "success": True,
                "message": "Registration successful!",
                "user_id": str(res.user.id),
                "email"  : res.user.email,
            }
        raise HTTPException(status_code=400, detail="Registration failed")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(data: LoginData):
    try:
        sb  = get_client()
        res = sb.auth.sign_in_with_password({
            "email"   : data.email,
            "password": data.password,
        })
        if res.user and res.session:
            # Get profile for role
            sb_admin = get_admin_client()
            profile  = sb_admin.table("profiles").select("*").eq("id", str(res.user.id)).single().execute()
            role     = profile.data.get("role", "user") if profile.data else "user"

            return {
                "success"     : True,
                "access_token": res.session.access_token,
                "user_id"     : str(res.user.id),
                "email"       : res.user.email,
                "name"        : res.user.user_metadata.get("name", ""),
                "role"        : role,
            }
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def logout():
    try:
        sb = get_client()
        sb.auth.sign_out()
        return {"success": True}
    except Exception as e:
        return {"success": False}


@router.get("/me")
async def get_me(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        token = authorization.replace("Bearer ", "")
        sb    = get_client()
        user  = sb.auth.get_user(token)
        if user.user:
            sb_admin = get_admin_client()
            profile  = sb_admin.table("profiles").select("*").eq("id", str(user.user.id)).single().execute()
            role     = profile.data.get("role","user") if profile.data else "user"
            return {
                "user_id": str(user.user.id),
                "email"  : user.user.email,
                "name"   : user.user.user_metadata.get("name",""),
                "role"   : role,
            }
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))