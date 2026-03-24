"""
Module 3 — Full Feature Extraction API Endpoint
"""
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import Case, SegmentationResult, FeatureResult

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────────────

class FeatureResultResponse(BaseModel):
    case_id: str
    status: str
    feature_count: Optional[int] = None
    fractal_dimension: Optional[float] = None
    surface_irregularity: Optional[float] = None     # = asymmetry_index
    gradient_entropy: Optional[float] = None
    radiomics_features: Optional[dict] = None
    advanced_features: Optional[dict] = None
    feature_vector: Optional[List[float]] = None
    feature_names: Optional[List[str]] = None

    class Config:
        from_attributes = True


class FeatureSummaryResponse(BaseModel):
    case_id: str
    status: str
    feature_count: Optional[int] = None
    fractal_dimension: Optional[float] = None
    surface_irregularity: Optional[float] = None
    asymmetry_index: Optional[float] = None
    gradient_entropy: Optional[float] = None
    key_radiomics: Optional[dict] = None    # Subset of important radiomics


# ─── Endpoints ────────────────────────────────────────────────────────────

@router.post("/run/{case_id}", status_code=status.HTTP_202_ACCEPTED)
async def run_feature_extraction(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    Trigger feature extraction for a case.
    Requires segmentation mask to be available.
    """
    seg_q = await db.execute(
        select(SegmentationResult).where(SegmentationResult.case_id == uuid.UUID(case_id))
    )
    seg = seg_q.scalar_one_or_none()
    if not seg or not seg.mask_path:
        raise HTTPException(
            status_code=400,
            detail="Segmentation mask not found. Run segmentation first.",
        )

    from app.workers.tasks.feature_tasks import run_feature_extraction_task
    task = run_feature_extraction_task.delay(case_id)

    return {"case_id": case_id, "task_id": task.id, "status": "queued"}


@router.get("/result/{case_id}", response_model=FeatureResultResponse)
async def get_feature_result(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve full feature vector and all extracted features for a case.
    Includes radiomics_features dict and ML-ready feature_vector list.
    """
    case_q = await db.execute(select(Case).where(Case.id == uuid.UUID(case_id)))
    case = case_q.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    feat_q = await db.execute(
        select(FeatureResult).where(FeatureResult.case_id == uuid.UUID(case_id))
    )
    feat = feat_q.scalar_one_or_none()

    if not feat:
        return FeatureResultResponse(case_id=case_id, status=case.status)

    return FeatureResultResponse(
        case_id=case_id,
        status=case.status,
        feature_count=len(feat.feature_vector) if feat.feature_vector else 0,
        fractal_dimension=feat.fractal_dimension,
        surface_irregularity=feat.surface_irregularity,
        radiomics_features=feat.radiomics_features,
        feature_vector=feat.feature_vector,
    )


@router.get("/summary/{case_id}", response_model=FeatureSummaryResponse)
async def get_feature_summary(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get a concise summary of the most clinically relevant features.
    Used by the dashboard to show key indicators without large payload.
    """
    case_q = await db.execute(select(Case).where(Case.id == uuid.UUID(case_id)))
    case = case_q.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    feat_q = await db.execute(
        select(FeatureResult).where(FeatureResult.case_id == uuid.UUID(case_id))
    )
    feat = feat_q.scalar_one_or_none()
    if not feat:
        return FeatureSummaryResponse(case_id=case_id, status=case.status)

    # Extract key radiomics subset for summary
    key_radiomics = {}
    if feat.radiomics_features:
        important_keys = [
            "original_firstorder_Entropy",
            "original_firstorder_Skewness",
            "original_shape_Sphericity",
            "original_shape_Elongation",
            "original_shape_SurfaceVolumeRatio",
            "original_glcm_Contrast",
            "original_glcm_Correlation",
        ]
        key_radiomics = {
            k.split("original_")[-1]: v
            for k, v in feat.radiomics_features.items()
            if k in important_keys
        }

    return FeatureSummaryResponse(
        case_id=case_id,
        status=case.status,
        feature_count=len(feat.feature_vector) if feat.feature_vector else 0,
        fractal_dimension=feat.fractal_dimension,
        surface_irregularity=feat.surface_irregularity,
        asymmetry_index=feat.surface_irregularity,
        key_radiomics=key_radiomics,
    )


@router.get("/vector/{case_id}")
async def get_feature_vector(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    Return only the raw ML feature vector (list of floats) and feature names.
    Used directly by classification (Module 4).
    """
    feat_q = await db.execute(
        select(FeatureResult).where(FeatureResult.case_id == uuid.UUID(case_id))
    )
    feat = feat_q.scalar_one_or_none()
    if not feat:
        raise HTTPException(status_code=404, detail="Features not yet extracted.")

    return {
        "case_id": case_id,
        "feature_vector": feat.feature_vector,
        "feature_count": len(feat.feature_vector) if feat.feature_vector else 0,
    }
