"""Cases endpoint stubs"""
from fastapi import APIRouter, UploadFile, File
router = APIRouter()

@router.post("/upload")
async def upload_dicom(file: UploadFile = File(...)): return {"case_id": "uuid-placeholder"}

@router.get("/{case_id}")
async def get_case(case_id: str): return {"case_id": case_id}

@router.get("/patient/{patient_id}")
async def get_cases_by_patient(patient_id: str): return {"cases": []}
