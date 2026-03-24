"""
Module 1 — Full Segmentation API Endpoint
Handles DICOM upload, async inference trigger, and result retrieval.
"""
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.core.config import settings
from app.models.models import Case, SegmentationResult, Patient

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────────────

class SegmentationResponse(BaseModel):
    case_id: str
    task_id: Optional[str] = None
    status: str
    mask_path: Optional[str] = None
    tumor_voxels: Optional[int] = None
    dice_score: Optional[float] = None
    iou_score: Optional[float] = None
    hausdorff_distance: Optional[float] = None


# ─── Endpoints ────────────────────────────────────────────────────────────

@router.post("/upload-and-segment", response_model=SegmentationResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_dicom_and_segment(
    patient_id: str,
    scan_type: str = "CT",
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a DICOM .zip archive or single .dcm file and trigger async segmentation.
    - Creates a Case record
    - Saves DICOM files to storage
    - Dispatches Celery segmentation task
    """
    # Validate patient exists
    patient_result = await db.execute(select(Patient).where(Patient.id == uuid.UUID(patient_id)))
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    # Save uploaded file
    case_id = str(uuid.uuid4())
    dicom_dir = Path(settings.STORAGE_LOCAL_PATH) / "dicom" / case_id
    dicom_dir.mkdir(parents=True, exist_ok=True)

    file_path = dicom_dir / file.filename
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Extract zip if needed
    if str(file.filename).endswith(".zip"):
        import zipfile
        with zipfile.ZipFile(str(file_path), "r") as zf:
            zf.extractall(str(dicom_dir))
        os.remove(str(file_path))

    # Create Case record
    case = Case(
        id=uuid.UUID(case_id),
        patient_id=uuid.UUID(patient_id),
        dicom_path=str(dicom_dir),
        scan_type=scan_type.upper(),
        status="uploaded",
    )
    db.add(case)
    await db.commit()

    # Dispatch Celery task
    from app.workers.tasks.segmentation_tasks import run_segmentation_task
    task = run_segmentation_task.delay(case_id)

    return SegmentationResponse(case_id=case_id, task_id=task.id, status="queued")


@router.post("/run/{case_id}", response_model=SegmentationResponse)
async def trigger_segmentation(case_id: str, db: AsyncSession = Depends(get_db)):
    """Trigger segmentation for an already-uploaded case."""
    result = await db.execute(select(Case).where(Case.id == uuid.UUID(case_id)))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    from app.workers.tasks.segmentation_tasks import run_segmentation_task
    task = run_segmentation_task.delay(case_id)

    return SegmentationResponse(case_id=case_id, task_id=task.id, status="queued")


@router.get("/result/{case_id}", response_model=SegmentationResponse)
async def get_segmentation_result(case_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve segmentation result for a case."""
    case_result = await db.execute(select(Case).where(Case.id == uuid.UUID(case_id)))
    case = case_result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    seg_result = await db.execute(
        select(SegmentationResult).where(SegmentationResult.case_id == uuid.UUID(case_id))
    )
    seg = seg_result.scalar_one_or_none()

    if not seg:
        return SegmentationResponse(case_id=case_id, status=case.status)

    return SegmentationResponse(
        case_id=case_id,
        status=case.status,
        mask_path=seg.mask_path,
        dice_score=seg.dice_score,
        iou_score=seg.iou_score,
        hausdorff_distance=seg.hausdorff_distance,
    )


@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """Check Celery task status."""
    from celery.result import AsyncResult
    from app.workers.celery_app import celery_app
    result = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }
