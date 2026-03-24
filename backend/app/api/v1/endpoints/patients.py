"""Patients & Cases endpoint stubs"""
from fastapi import APIRouter
router = APIRouter()

@router.get("/")
async def list_patients(): return {"patients": []}

@router.post("/")
async def create_patient(): return {"status": "created"}

@router.get("/{patient_id}")
async def get_patient(patient_id: str): return {"patient_id": patient_id}
