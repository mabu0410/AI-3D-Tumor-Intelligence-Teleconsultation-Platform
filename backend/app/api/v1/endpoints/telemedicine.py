"""
Module 6 — Full Telemedicine API
REST endpoints + WebSocket real-time room.
"""
import json
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import Consultation, Case
from app.services.telemedicine_service import (
    create_consultation, get_consultation, update_status,
    save_annotations, sign_consultation, list_consultations,
)
from app.services.websocket_manager import ws_manager

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────────────

class ConsultationCreate(BaseModel):
    case_id: str
    requesting_hospital: str
    specialist_id: Optional[str] = None


class ConsultationResponse(BaseModel):
    id: str
    case_id: str
    requesting_hospital: Optional[str] = None
    specialist_id: Optional[str] = None
    status: str
    notes: Optional[str] = None
    annotations: Optional[dict] = None
    signed_at: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class AnnotationUpdate(BaseModel):
    annotations: dict   # 3D markers, measurements, face highlights
    notes: Optional[str] = ""


class SignRequest(BaseModel):
    specialist_id: str


# ─── REST Endpoints ───────────────────────────────────────────────────────

@router.post("/submit", response_model=ConsultationResponse, status_code=status.HTTP_201_CREATED)
async def submit_consultation(body: ConsultationCreate, db: AsyncSession = Depends(get_db)):
    """
    Step 1 (Lower hospital): Submit a case for expert consultation.
    Creates a Consultation record with status='pending'.
    """
    case_q = await db.execute(select(Case).where(Case.id == uuid.UUID(body.case_id)))
    case = case_q.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {body.case_id} not found")

    c = await create_consultation(
        db=db,
        case_id=body.case_id,
        requesting_hospital=body.requesting_hospital,
        specialist_id=body.specialist_id,
    )
    return _to_response(c)


@router.get("/list", response_model=List[ConsultationResponse])
async def list_all_consultations(
    status: Optional[str] = Query(None, description="Filter by status: pending|in_review|completed"),
    specialist_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List consultations with optional filters (for specialist dashboard)."""
    items = await list_consultations(db, status=status, specialist_id=specialist_id, limit=limit, offset=offset)
    return [_to_response(c) for c in items]


@router.get("/{consultation_id}", response_model=ConsultationResponse)
async def get_consultation_detail(consultation_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single consultation with all details."""
    c = await get_consultation(db, consultation_id)
    if not c:
        raise HTTPException(status_code=404, detail="Consultation not found")
    return _to_response(c)


@router.patch("/annotate/{consultation_id}", response_model=ConsultationResponse)
async def annotate_consultation(
    consultation_id: str,
    body: AnnotationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 2 (Specialist): Add 3D annotations and clinical notes.
    Annotations are saved and broadcast to all WS participants.
    """
    c = await save_annotations(db, consultation_id, body.annotations, body.notes or "")

    # Broadcast annotation update to all WS clients in this room
    await ws_manager.broadcast(
        consultation_id,
        {
            "type": "annotation",
            "user_id": "api",
            "data": body.annotations,
            "notes": body.notes,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )
    return _to_response(c)


@router.patch("/sign/{consultation_id}", response_model=ConsultationResponse)
async def sign_and_complete(
    consultation_id: str,
    body: SignRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 3 (Specialist): Electronically sign and complete the consultation.
    Sets signed_at timestamp and status='completed'.
    """
    c = await sign_consultation(db, consultation_id, body.specialist_id)

    # Notify WS participants that consultation is signed
    await ws_manager.broadcast(
        consultation_id,
        {
            "type": "signed",
            "specialist_id": body.specialist_id,
            "signed_at": c.signed_at.isoformat() if c.signed_at else None,
        },
    )
    return _to_response(c)


@router.get("/{consultation_id}/participants")
async def get_participants(consultation_id: str):
    """List currently connected WebSocket participants in a consultation room."""
    return {
        "consultation_id": consultation_id,
        "participants": ws_manager.get_room_users(consultation_id),
        "count": ws_manager.room_count(consultation_id),
    }


# ─── WebSocket Endpoint ────────────────────────────────────────────────────

@router.websocket("/ws/{consultation_id}")
async def consultation_websocket(
    websocket: WebSocket,
    consultation_id: str,
    user_id: str = "anonymous",
    role: str = "viewer",
):
    """
    Real-time WebSocket endpoint for consultation room.
    Messages are broadcast to all other participants.

    Supported message types: join, annotation, cursor, chat, leave
    """
    await ws_manager.connect(websocket, consultation_id, user_id, role)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")
            msg["user_id"] = user_id
            msg["timestamp"] = datetime.utcnow().isoformat()

            if msg_type in ("annotation", "cursor", "chat", "highlight"):
                # Forward to all other participants
                await ws_manager.broadcast(consultation_id, msg, exclude_user=user_id)

            elif msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, consultation_id, user_id)


# ─── Helper ────────────────────────────────────────────────────────────────

def _to_response(c: Consultation) -> ConsultationResponse:
    return ConsultationResponse(
        id=str(c.id),
        case_id=str(c.case_id),
        requesting_hospital=c.requesting_hospital,
        specialist_id=str(c.specialist_id) if c.specialist_id else None,
        status=c.status,
        notes=c.notes,
        annotations=c.annotations,
        signed_at=c.signed_at.isoformat() if c.signed_at else None,
        created_at=c.created_at.isoformat() if c.created_at else None,
    )
