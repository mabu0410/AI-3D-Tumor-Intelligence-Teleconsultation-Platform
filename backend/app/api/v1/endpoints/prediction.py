"""
Module 5 — Full Progression Prediction API
"""
import uuid
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import Patient, ProgressionPrediction

router = APIRouter()


class PredictionResponse(BaseModel):
    patient_id: str
    status: str
    data_points: Optional[int] = None
    invasion_speed: Optional[str] = None
    invasion_confidence: Optional[float] = None
    invasion_probabilities: Optional[dict] = None
    current: Optional[dict] = None
    prediction_3m: Optional[dict] = None
    prediction_6m: Optional[dict] = None
    model: Optional[str] = None


@router.post("/run/{patient_id}", status_code=status.HTTP_202_ACCEPTED)
async def run_prediction(patient_id: str, db: AsyncSession = Depends(get_db)):
    """
    Trigger progression prediction for a patient.
    Requires at least 2 cases with classification results completed.
    """
    patient_q = await db.execute(select(Patient).where(Patient.id == uuid.UUID(patient_id)))
    patient = patient_q.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    from app.workers.tasks.prediction_tasks import run_prediction_task
    task = run_prediction_task.delay(patient_id)
    return {"patient_id": patient_id, "task_id": task.id, "status": "queued"}


@router.post("/run-sync/{patient_id}", response_model=PredictionResponse)
async def run_prediction_sync(patient_id: str, db: AsyncSession = Depends(get_db)):
    """
    Synchronous prediction for testing (small datasets).
    """
    from app.services.prediction_service import PredictionService
    from app.services.temporal_dataset import snapshots_from_db_records
    from app.models.models import (
        Case, SegmentationResult, ReconstructionResult,
        FeatureResult, ClassificationResult,
    )

    patient_q = await db.execute(select(Patient).where(Patient.id == uuid.UUID(patient_id)))
    patient = patient_q.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    cases_q = await db.execute(
        select(Case).where(Case.patient_id == uuid.UUID(patient_id)).order_by(Case.scan_date)
    )
    cases = cases_q.scalars().all()

    if not cases:
        raise HTTPException(status_code=400, detail="No cases found for this patient")

    records = []
    for case in cases:
        record = {"case_id": str(case.id), "scan_date": str(case.scan_date or "")}
        for Model, key_map in [
            (ReconstructionResult, {"volume_mm3": "volume_mm3", "surface_area_mm2": "surface_area_mm2",
                                    "sphericity": "sphericity", "roughness_index": "roughness_index"}),
            (FeatureResult, {"fractal_dimension": "fractal_dimension",
                             "surface_irregularity": "surface_irregularity",
                             "feature_vector": "feature_vector"}),
            (ClassificationResult, {"malignancy_probability": "malignancy_probability"}),
        ]:
            res_q = await db.execute(select(Model).where(Model.case_id == case.id))
            res = res_q.scalar_one_or_none()
            if res:
                for k, v in key_map.items():
                    record[v] = getattr(res, k, None)
        records.append(record)

    snapshots = snapshots_from_db_records(records)
    result = PredictionService.predict(snapshots)

    # Persist
    pred_3m = result.get("prediction_3m", {})
    pred_6m = result.get("prediction_6m", {})
    prog = ProgressionPrediction(
        patient_id=uuid.UUID(patient_id),
        volume_change_3m=pred_3m.get("volume_change_pct"),
        volume_change_6m=pred_6m.get("volume_change_pct"),
        malignancy_risk_3m=pred_3m.get("malignancy_probability"),
        malignancy_risk_6m=pred_6m.get("malignancy_probability"),
        invasion_speed=result.get("invasion_speed"),
    )
    db.add(prog)
    await db.commit()

    return PredictionResponse(patient_id=patient_id, status="completed", **result)


@router.get("/result/{patient_id}", response_model=PredictionResponse)
async def get_latest_prediction(patient_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve the most recent progression prediction for a patient."""
    prog_q = await db.execute(
        select(ProgressionPrediction)
        .where(ProgressionPrediction.patient_id == uuid.UUID(patient_id))
        .order_by(ProgressionPrediction.created_at.desc())
    )
    prog = prog_q.scalars().first()

    if not prog:
        return PredictionResponse(patient_id=patient_id, status="not_run")

    return PredictionResponse(
        patient_id=patient_id,
        status="completed",
        invasion_speed=prog.invasion_speed,
        prediction_3m={
            "volume_change_pct": prog.volume_change_3m,
            "malignancy_probability": prog.malignancy_risk_3m,
            "risk_level": _risk(prog.malignancy_risk_3m),
        },
        prediction_6m={
            "volume_change_pct": prog.volume_change_6m,
            "malignancy_probability": prog.malignancy_risk_6m,
            "risk_level": _risk(prog.malignancy_risk_6m),
        },
    )


@router.get("/history/{patient_id}")
async def get_prediction_history(patient_id: str, db: AsyncSession = Depends(get_db)):
    """Return all prediction records for charting."""
    q = await db.execute(
        select(ProgressionPrediction)
        .where(ProgressionPrediction.patient_id == uuid.UUID(patient_id))
        .order_by(ProgressionPrediction.created_at)
    )
    items = q.scalars().all()
    return {
        "patient_id": patient_id,
        "history": [
            {
                "date": str(p.created_at),
                "volume_change_3m": p.volume_change_3m,
                "volume_change_6m": p.volume_change_6m,
                "malignancy_risk_3m": p.malignancy_risk_3m,
                "malignancy_risk_6m": p.malignancy_risk_6m,
                "invasion_speed": p.invasion_speed,
            }
            for p in items
        ],
    }


def _risk(p):
    if p is None:
        return None
    if p < 0.35:
        return "Low"
    if p < 0.65:
        return "Moderate"
    return "High"
