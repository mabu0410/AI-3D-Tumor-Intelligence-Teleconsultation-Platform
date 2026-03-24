"""Module 5 — Celery Prediction Task"""
from celery import shared_task
from loguru import logger


@shared_task(
    bind=True, max_retries=3, default_retry_delay=30,
    name="prediction_tasks.run_prediction_task",
)
def run_prediction_task(self, patient_id: str):
    """
    Fetch all cases for a patient (sorted by scan date),
    build TumorSnapshot sequence, run prediction, persist to DB.
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    from app.services.prediction_service import PredictionService
    from app.services.temporal_dataset import snapshots_from_db_records

    async def _run():
        from app.models.models import (
            Case, SegmentationResult, ReconstructionResult,
            FeatureResult, ClassificationResult, ProgressionPrediction,
        )
        from sqlalchemy import select
        import uuid

        engine = create_async_engine(settings.DATABASE_URL)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as db:
            # Load all cases for this patient (ordered)
            cases_q = await db.execute(
                select(Case)
                .where(Case.patient_id == uuid.UUID(patient_id))
                .order_by(Case.scan_date)
            )
            cases = cases_q.scalars().all()

            if not cases:
                raise ValueError(f"No cases found for patient {patient_id}")

            logger.info(f"[Prediction] {len(cases)} cases found for patient {patient_id}")

            # Build records list
            records = []
            for case in cases:
                record = {"case_id": str(case.id), "scan_date": str(case.scan_date or "")}

                recon_q = await db.execute(
                    select(ReconstructionResult).where(ReconstructionResult.case_id == case.id)
                )
                recon = recon_q.scalar_one_or_none()
                if recon:
                    record.update({
                        "volume_mm3": recon.volume_mm3,
                        "surface_area_mm2": recon.surface_area_mm2,
                        "sphericity": recon.sphericity,
                        "roughness_index": recon.roughness_index,
                    })

                feat_q = await db.execute(
                    select(FeatureResult).where(FeatureResult.case_id == case.id)
                )
                feat = feat_q.scalar_one_or_none()
                if feat:
                    record.update({
                        "fractal_dimension": feat.fractal_dimension,
                        "surface_irregularity": feat.surface_irregularity,
                        "feature_vector": feat.feature_vector,
                    })

                cls_q = await db.execute(
                    select(ClassificationResult).where(ClassificationResult.case_id == case.id)
                )
                cls_rec = cls_q.scalar_one_or_none()
                if cls_rec:
                    record["malignancy_probability"] = cls_rec.malignancy_probability

                records.append(record)

            snapshots = snapshots_from_db_records(records)
            result = PredictionService.predict(snapshots)

            # Persist
            pred_3m = result["prediction_3m"]
            pred_6m = result["prediction_6m"]

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

            logger.info(f"[Prediction] Done: 3m vol_change={pred_3m.get('volume_change_pct'):.2f}%")
            return result

    try:
        return asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc)
