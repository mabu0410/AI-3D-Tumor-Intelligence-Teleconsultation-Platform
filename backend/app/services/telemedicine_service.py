"""
Module 6 — Telemedicine Service
Handles consultation lifecycle: create, submit, review, annotate, sign.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import Case, Consultation, User


async def create_consultation(
    db: AsyncSession,
    case_id: str,
    requesting_hospital: str,
    specialist_id: Optional[str] = None,
) -> Consultation:
    """Create a new consultation request (from lower-level hospital)."""
    consultation = Consultation(
        case_id=uuid.UUID(case_id),
        requesting_hospital=requesting_hospital,
        specialist_id=uuid.UUID(specialist_id) if specialist_id else None,
        status="pending",
    )
    db.add(consultation)
    await db.commit()
    await db.refresh(consultation)
    return consultation


async def get_consultation(db: AsyncSession, consultation_id: str) -> Optional[Consultation]:
    q = await db.execute(
        select(Consultation).where(Consultation.id == uuid.UUID(consultation_id))
    )
    return q.scalar_one_or_none()


async def update_status(db: AsyncSession, consultation_id: str, status: str) -> Consultation:
    q = await db.execute(
        select(Consultation).where(Consultation.id == uuid.UUID(consultation_id))
    )
    c = q.scalar_one_or_none()
    if not c:
        raise ValueError(f"Consultation {consultation_id} not found")
    c.status = status
    await db.commit()
    return c


async def save_annotations(
    db: AsyncSession,
    consultation_id: str,
    annotations: dict,
    notes: str = "",
) -> Consultation:
    """
    Save doctor annotations and clinical notes.
    Annotations format (for 3D viewer):
    {
      "markers": [{"x": 10.5, "y": 3.2, "z": 7.1, "label": "Suspicious region"}],
      "measurements": [{"type": "distance", "points": [...], "value_mm": 12.3}],
      "highlight_faces": [100, 200, 305]  # mesh face indices
    }
    """
    c = await get_consultation(db, consultation_id)
    if not c:
        raise ValueError(f"Consultation {consultation_id} not found")

    c.annotations = annotations
    c.notes = notes
    c.status = "in_review"
    await db.commit()
    return c


async def sign_consultation(
    db: AsyncSession,
    consultation_id: str,
    specialist_id: str,
) -> Consultation:
    """Electronically sign a consultation (mark as completed)."""
    c = await get_consultation(db, consultation_id)
    if not c:
        raise ValueError(f"Consultation {consultation_id} not found")

    c.specialist_id = uuid.UUID(specialist_id)
    c.signed_at = datetime.utcnow()
    c.status = "completed"
    await db.commit()
    return c


async def list_consultations(
    db: AsyncSession,
    status: Optional[str] = None,
    specialist_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list:
    """List consultations with optional status and specialist filters."""
    q = select(Consultation).order_by(Consultation.created_at.desc())
    if status:
        q = q.where(Consultation.status == status)
    if specialist_id:
        q = q.where(Consultation.specialist_id == uuid.UUID(specialist_id))
    q = q.limit(limit).offset(offset)
    result = await db.execute(q)
    return result.scalars().all()
