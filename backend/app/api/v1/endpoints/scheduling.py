"""
Module 7 — Scheduling & Patient Management API
Endpoints to fetch patient details, schedules, and trigger manual reminders.
"""
import uuid
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import Patient, Schedule

router = APIRouter()


class ScheduleResponse(BaseModel):
    id: str
    patient_id: str
    scheduled_date: str
    reason: str
    status: str
    notification_sent: bool
    created_at: str

    class Config:
        from_attributes = True


class PatientDashboardResponse(BaseModel):
    id: str
    name: str
    dicom_id: Optional[str]
    gender: str
    age: int
    phone: Optional[str]
    email: Optional[str]
    schedules: List[ScheduleResponse]


@router.get("/patient/{patient_id}", response_model=PatientDashboardResponse)
async def get_patient_dashboard(patient_id: str, db: AsyncSession = Depends(get_db)):
    """Get full patient profile along with all their scheduled follow-ups."""
    p_q = await db.execute(select(Patient).where(Patient.id == uuid.UUID(patient_id)))
    pat = p_q.scalar_one_or_none()
    if not pat:
        raise HTTPException(status_code=404, detail="Patient not found")

    s_q = await db.execute(
        select(Schedule)
        .where(Schedule.patient_id == uuid.UUID(patient_id))
        .order_by(Schedule.scheduled_date.desc())
    )
    schedules = s_q.scalars().all()

    return {
        "id": str(pat.id),
        "name": pat.name,
        "dicom_id": pat.dicom_id,
        "gender": pat.gender,
        "age": pat.age,
        "phone": pat.phone,
        "email": pat.email,
        "schedules": [
            {
                "id": str(s.id),
                "patient_id": str(s.patient_id),
                "scheduled_date": s.scheduled_date.isoformat(),
                "reason": s.reason,
                "status": s.status,
                "notification_sent": s.notification_sent,
                "created_at": s.created_at.isoformat(),
            }
            for s in schedules
        ]
    }


@router.post("/trigger-auto/{case_id}", status_code=status.HTTP_202_ACCEPTED)
async def trigger_auto_schedule(case_id: str):
    """
    Manually trigger the auto-scheduling background task for a specific case.
    Normally called automatically by the post-classification hook.
    """
    from app.workers.tasks.notification_tasks import auto_schedule_patient
    task = auto_schedule_patient.delay(case_id)
    return {"case_id": case_id, "task_id": task.id, "message": "Auto-schedule task queued"}


@router.post("/send-manual-reminder/{schedule_id}")
async def send_manual_reminder(schedule_id: str, db: AsyncSession = Depends(get_db)):
    """Manually send an SMS reminder for a specific schedule."""
    from app.services.notification_service import send_sms

    s_q = await db.execute(select(Schedule).where(Schedule.id == uuid.UUID(schedule_id)))
    sched = s_q.scalar_one_or_none()
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")

    p_q = await db.execute(select(Patient).where(Patient.id == sched.patient_id))
    pat = p_q.scalar_one_or_none()

    if not pat or not pat.phone:
        raise HTTPException(status_code=400, detail="Patient phone number missing")

    date_str = sched.scheduled_date.strftime("%d/%m/%Y")
    body = f"[Nhắc Lịch] Bệnh viện xin nhắc {pat.name} lịch tái khám định kỳ vào {date_str}."
    
    res = send_sms(pat.phone, body)
    
    if res["status"] in ("sent", "mock"):
        sched.notification_sent = True
        await db.commit()
    
    return {"schedule_id": schedule_id, "notification_result": res}


@router.patch("/status/{schedule_id}")
async def update_schedule(schedule_id: str, new_status: str, db: AsyncSession = Depends(get_db)):
    """Update schedule status (scheduled -> completed | cancelled)."""
    if new_status not in ("scheduled", "completed", "cancelled"):
        raise HTTPException(status_code=400, detail="Invalid status")
        
    s_q = await db.execute(select(Schedule).where(Schedule.id == uuid.UUID(schedule_id)))
    sched = s_q.scalar_one_or_none()
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
        
    sched.status = new_status
    await db.commit()
    return {"id": schedule_id, "status": new_status}
