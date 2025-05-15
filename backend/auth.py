# backend/auth.py
from fastapi import APIRouter, HTTPException
from passlib.hash import bcrypt
from pydantic import BaseModel

router = APIRouter(prefix="/auth")

class LoginIn(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(data: LoginIn):
    user = await db["users"].find_one({"email": data.email})
    if not user or not bcrypt.verify(data.password, user["passwordHash"]):
        raise HTTPException(401, "Invalid credentials")
    # create JWT...
    return {"token": jwt_token}