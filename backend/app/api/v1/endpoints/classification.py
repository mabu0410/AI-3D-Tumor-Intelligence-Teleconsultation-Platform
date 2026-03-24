"""
Module 4 — Full Classification API Endpoint
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import Case, SegmentationResult, FeatureResult, ClassificationResult

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────────────

class ClassificationResponse(BaseModel):
    case_id: str
    status: str
    label: Optional[str] = None                  # benign | malignant | indeterminate
    malignancy_probability: Optional[float] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None              # Low | Moderate | High
    recommendation: Optional[str] = None
    color: Optional[str] = None
    model_used: Optional[str] = None
    cnn_result: Optional[dict] = None
    xgboost_result: Optional[dict] = None


# ─── Endpoints ────────────────────────────────────────────────────────────

@router.post("/run/{case_id}", status_code=status.HTTP_202_ACCEPTED)
async def run_classification(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    Trigger classification for a case.
    Requires segmentation mask. Feature vector is optional but improves accuracy.
    """
    seg_q = await db.execute(
        select(SegmentationResult).where(SegmentationResult.case_id == uuid.UUID(case_id))
    )
    seg = seg_q.scalar_one_or_none()
    if not seg or not seg.mask_path:
        raise HTTPException(
            status_code=400,
            detail="Segmentation mask required. Run segmentation first.",
        )

    from app.workers.tasks.classification_tasks import run_classification_task
    task = run_classification_task.delay(case_id)
    return {"case_id": case_id, "task_id": task.id, "status": "queued"}


@router.post("/run-sync/{case_id}", response_model=ClassificationResponse)
async def run_classification_sync(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    Synchronous classification (for testing/small cases).
    Runs inline — not recommended for production.
    """
    from app.services.classification_service import ClassificationService

    case_q = await db.execute(select(Case).where(Case.id == uuid.UUID(case_id)))
    case = case_q.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    seg_q = await db.execute(
        select(SegmentationResult).where(SegmentationResult.case_id == uuid.UUID(case_id))
    )
    seg = seg_q.scalar_one_or_none()
    if not seg:
        raise HTTPException(status_code=400, detail="Segmentation mask required.")

    feat_q = await db.execute(
        select(FeatureResult).where(FeatureResult.case_id == uuid.UUID(case_id))
    )
    feat = feat_q.scalar_one_or_none()

    result = ClassificationService.classify(
        case_id=case_id,
        mask_path=seg.mask_path,
        feature_vector=feat.feature_vector if feat else None,
    )

    # Persist
    cls_record = ClassificationResult(
        case_id=case.id,
        label=result["label"],
        malignancy_probability=result["malignancy_probability"],
        risk_score=result["risk_score"],
        model_used="ensemble_cnn+xgb",
    )
    db.add(cls_record)
    case.status = "classified"
    await db.commit()

    return ClassificationResponse(
        case_id=case_id,
        status="classified",
        **{k: v for k, v in result.items() if k != "case_id"},
        cnn_result=result.get("cnn"),
        xgboost_result=result.get("xgboost"),
    )


@router.get("/result/{case_id}", response_model=ClassificationResponse)
async def get_classification_result(case_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve classification result from DB."""
    case_q = await db.execute(select(Case).where(Case.id == uuid.UUID(case_id)))
    case = case_q.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    cls_q = await db.execute(
        select(ClassificationResult).where(ClassificationResult.case_id == uuid.UUID(case_id))
    )
    cls_rec = cls_q.scalar_one_or_none()

    if not cls_rec:
        return ClassificationResponse(case_id=case_id, status=case.status)

    from app.services.classification_service import interpret_risk_score
    interpretation = interpret_risk_score(cls_rec.risk_score or 0.0)

    return ClassificationResponse(
        case_id=case_id,
        status=case.status,
        label=cls_rec.label,
        malignancy_probability=cls_rec.malignancy_probability,
        risk_score=cls_rec.risk_score,
        risk_level=interpretation["risk_level"],
        recommendation=interpretation["recommendation"],
        color=interpretation["color"],
        model_used=cls_rec.model_used,
    )


@router.get("/feature-importance/{case_id}")
async def get_feature_importance(case_id: str, db: AsyncSession = Depends(get_db)):
    """XGBoost feature importance for this classification."""
    from app.services.xgboost_classifier import get_xgb_classifier
    from app.core.config import settings
    import os

    xgb = get_xgb_classifier(
        model_path=os.path.join(settings.MODEL_WEIGHTS_DIR, "xgb_classifier.joblib")
    )
    importance = xgb.get_feature_importance(top_n=15)
    return {"case_id": case_id, "feature_importance": importance}
