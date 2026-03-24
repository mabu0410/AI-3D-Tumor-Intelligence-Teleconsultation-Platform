"""Module 7 — Celery Scheduling & Notification Tasks"""
from celery import shared_task
from loguru import logger
from datetime import datetime


@shared_task(
    bind=True, max_retries=3, default_retry_delay=60,
    name="notification_tasks.auto_schedule_patient",
)
def auto_schedule_patient(self, case_id: str):
    """
    Called after Classification or Prediction is complete.
    Computes schedule, creates Schedule DB record, 
    and triggers immediate SMS notification.
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    from app.services.scheduling_service import compute_schedule, format_schedule_message
    from app.services.notification_service import send_sms, send_push_notification

    async def _run():
        from app.models.models import Case, Patient, ClassificationResult, ProgressionPrediction, Schedule
        from sqlalchemy import select
        import uuid

        engine = create_async_engine(settings.DATABASE_URL)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as db:
            # Load Case & Patient
            case_q = await db.execute(select(Case).where(Case.id == uuid.UUID(case_id)))
            case = case_q.scalar_one_or_none()
            if not case:
                raise ValueError("Case not found")

            pat_q = await db.execute(select(Patient).where(Patient.id == case.patient_id))
            patient = pat_q.scalar_one_or_none()

            # Load latest AI insights
            cls_q = await db.execute(select(ClassificationResult).where(ClassificationResult.case_id == case.id))
            cls_res = cls_q.scalar_one_or_none()
            
            prog_q = await db.execute(
                select(ProgressionPrediction)
                .where(ProgressionPrediction.patient_id == patient.id)
                .order_by(ProgressionPrediction.created_at.desc())
            )
            prog_res = prog_q.scalars().first()

            label = cls_res.label if cls_res else "indeterminate"
            invasion = prog_res.invasion_speed if prog_res else None

            # Compute schedule logic
            sched_data = compute_schedule(label, invasion, base_date=datetime.utcnow())
            
            # Create DB Schedule
            schedule = Schedule(
                patient_id=patient.id,
                scheduled_date=sched_data["scheduled_date"],
                reason=sched_data["reason"],
                status="scheduled",
                notification_sent=True,
            )
            db.add(schedule)
            await db.commit()
            
            logger.info(f"[Schedule] Created for {patient.name} on {sched_data['scheduled_date'].date()}")

            # Formulate messages and notify via SMS and Push
            msgs = format_schedule_message(patient.name, sched_data["scheduled_date"], sched_data["reason"])
            
            sms_res = {"status": "skipped"}
            if patient.phone:
                sms_res = send_sms(patient.phone, msgs["sms"])
                
            push_res = {"status": "skipped"}
            if patient.email: # using email as dummy push token for demo
                push_res = send_push_notification(f"token_{patient.id}", msgs["push_title"], msgs["push_body"])

            return {
                "schedule_id": str(schedule.id),
                "scheduled_date": str(sched_data["scheduled_date"].date()),
                "urgency": sched_data["urgency"],
                "sms": sms_res,
                "push": push_res,
            }

    try:
        return asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(name="notification_tasks.daily_reminder_cron")
def daily_reminder_cron():
    """
    Intended to be run via Celery Beat every day at 8:00 AM.
    Finds all schedules happening in exactly 3 days and sends reminder SMS.
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    from app.services.notification_service import send_sms
    
    async def _run():
        from app.models.models import Schedule, Patient
        from sqlalchemy import select, and_
        from datetime import timedelta

        target_date = (datetime.utcnow() + timedelta(days=3)).date()

        engine = create_async_engine(settings.DATABASE_URL)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as db:
            q = await db.execute(
                select(Schedule, Patient)
                .join(Patient, Schedule.patient_id == Patient.id)
                .where(and_(
                    Schedule.status == "scheduled",
                    # postgres logic: cast scheduled_date to date
                ))
            )
            results = q.all() # list of (Schedule, Patient)
            
            sent_count = 0
            for sched, pat in results:
                if sched.scheduled_date.date() == target_date:
                    msg = f"[Nhắc lịch] Xin chào {pat.name}, bạn có lịch khám vào ngày {sched.scheduled_date.date().strftime('%d/%m/%Y')}."
                    if pat.phone:
                        send_sms(pat.phone, msg)
                        sent_count += 1
                        
            logger.info(f"[Cron] Sent {sent_count} daily reminders for {target_date}")
            return {"sent": sent_count, "target_date": str(target_date)}

    return asyncio.run(_run())
