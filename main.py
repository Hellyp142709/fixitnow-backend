from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import hashlib
import secrets
import json
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="FixitNow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Models ───────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class BookingRequest(BaseModel):
    pro_id: int
    pro_name: str
    pro_avatar: str
    pro_rating: float
    pro_price: str
    service_id: str
    service_label: str
    date: str
    time: str
    address: str
    emergency: bool
    notes: Optional[str] = ""
    eta: str

class SavedProRequest(BaseModel):
    pro_id: int
    pro_name: str
    pro_avatar: str
    pro_rating: float
    pro_price: str
    pro_service: str

# ─── Helpers ──────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    return secrets.token_hex(32)

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    result = supabase.table("sessions").select("user_id").eq("token", token).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return result.data[0]["user_id"]

# ─── Auth Routes ──────────────────────────────────────────────────────────────

@app.post("/api/signup")
async def signup(req: SignupRequest):
    existing = supabase.table("users").select("id").eq("email", req.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Account already exists with this email")
    
    user_data = {
        "name": req.name,
        "email": req.email,
        "phone": req.phone,
        "password_hash": hash_password(req.password),
        "joined_at": datetime.utcnow().isoformat(),
    }
    result = supabase.table("users").insert(user_data).execute()
    user = result.data[0]
    
    token = generate_token()
    supabase.table("sessions").insert({"user_id": user["id"], "token": token}).execute()
    
    return {
        "token": token,
        "user": {"id": user["id"], "name": user["name"], "email": user["email"], "phone": user["phone"]}
    }

@app.post("/api/login")
async def login(req: LoginRequest):
    result = supabase.table("users").select("*").eq("email", req.email).execute()
    if not result.data:
        raise HTTPException(status_code=400, detail="No account found with this email")
    
    user = result.data[0]
    if user["password_hash"] != hash_password(req.password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    token = generate_token()
    supabase.table("sessions").insert({"user_id": user["id"], "token": token}).execute()
    
    return {
        "token": token,
        "user": {"id": user["id"], "name": user["name"], "email": user["email"], "phone": user["phone"]}
    }

@app.post("/api/logout")
async def logout(user_id: str = Depends(get_current_user), authorization: str = Header(None)):
    token = authorization.split(" ")[1]
    supabase.table("sessions").delete().eq("token", token).execute()
    return {"message": "Logged out successfully"}

@app.get("/api/me")
async def get_me(user_id: str = Depends(get_current_user)):
    result = supabase.table("users").select("id, name, email, phone, joined_at").eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    return result.data[0]

# ─── Booking Routes ───────────────────────────────────────────────────────────

@app.post("/api/bookings")
async def create_booking(req: BookingRequest, user_id: str = Depends(get_current_user)):
    booking_data = {
        "user_id": user_id,
        "pro_id": req.pro_id,
        "pro_name": req.pro_name,
        "pro_avatar": req.pro_avatar,
        "pro_rating": req.pro_rating,
        "pro_price": req.pro_price,
        "service_id": req.service_id,
        "service_label": req.service_label,
        "date": req.date,
        "time": req.time,
        "address": req.address,
        "emergency": req.emergency,
        "notes": req.notes,
        "eta": req.eta,
        "status": "upcoming",
        "created_at": datetime.utcnow().isoformat(),
    }
    result = supabase.table("bookings").insert(booking_data).execute()
    return result.data[0]

@app.get("/api/bookings")
async def get_bookings(user_id: str = Depends(get_current_user)):
    result = supabase.table("bookings").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return result.data

@app.patch("/api/bookings/{booking_id}/cancel")
async def cancel_booking(booking_id: str, user_id: str = Depends(get_current_user)):
    existing = supabase.table("bookings").select("id").eq("id", booking_id).eq("user_id", user_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Booking not found")
    result = supabase.table("bookings").update({"status": "cancelled"}).eq("id", booking_id).execute()
    return result.data[0]

# ─── Saved Pros Routes ────────────────────────────────────────────────────────

@app.get("/api/saved")
async def get_saved(user_id: str = Depends(get_current_user)):
    result = supabase.table("saved_pros").select("*").eq("user_id", user_id).execute()
    return result.data

@app.post("/api/saved")
async def save_pro(req: SavedProRequest, user_id: str = Depends(get_current_user)):
    existing = supabase.table("saved_pros").select("id").eq("user_id", user_id).eq("pro_id", req.pro_id).execute()
    if existing.data:
        supabase.table("saved_pros").delete().eq("user_id", user_id).eq("pro_id", req.pro_id).execute()
        return {"saved": False}
    
    data = {
        "user_id": user_id,
        "pro_id": req.pro_id,
        "pro_name": req.pro_name,
        "pro_avatar": req.pro_avatar,
        "pro_rating": req.pro_rating,
        "pro_price": req.pro_price,
        "pro_service": req.pro_service,
    }
    supabase.table("saved_pros").insert(data).execute()
    return {"saved": True}

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "FixitNow API"}
