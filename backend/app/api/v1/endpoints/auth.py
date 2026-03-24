"""Auth endpoint stubs"""
from fastapi import APIRouter
router = APIRouter()

@router.post("/login")
async def login(): return {"token": "placeholder"}

@router.post("/register")
async def register(): return {"status": "created"}
