"""Module 4 — Celery Classification Task"""
from celery import shared_task
from loguru import logger


@shared_task(
    bind=True, max_retries=3, default_retry_delay=30,
    name="classification_tasks.run_classification_task",
)
def run_classification_task(self, case_id: str):
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    from app.services.classification_service import ClassificationService

    async def _run():
        from app.models.models import Case, SegmentationResult, FeatureResult, ClassificationResult
        from sqlalchemy import select
        import uuid

        engine = create_async_engine(settings.DATABASE_URL)
        session = async_sessionmaker(engine, expire_on_commit=False)

        async with session() as db:
            case_q = await db.execute(select(Case).where(Case.id == uuid.UUID(case_id)))
            case = case_q.scalar_one_or_none()
            if not case:
                raise ValueError(f"Case {case_id} not found")

            seg_q = await db.execute(
                select(SegmentationResult).where(SegmentationResult.case_id == uuid.UUID(case_id))
            )
            seg = seg_q.scalar_one_or_none()
            if not seg or not seg.mask_path:
                raise ValueError("Segmentation mask required for classification")

            # Optional: get feature vector from DB
            feat_q = await db.execute(
                select(FeatureResult).where(FeatureResult.case_id == uuid.UUID(case_id))
            )
            feat = feat_q.scalar_one_or_none()
            feature_vector = feat.feature_vector if feat else None

            case.status = "classifying"
            await db.commit()

            try:
                logger.info(f"[Classification] Starting for case {case_id}")
                result = ClassificationService.classify(
                    case_id=case_id,
                    mask_path=seg.mask_path,
                    feature_vector=feature_vector,
                )

                cls_record = ClassificationResult(
                    case_id=case.id,
                    label=result["label"],
                    malignancy_probability=result["malignancy_probability"],
                    risk_score=result["risk_score"],
                    model_used=f"ensemble_cnn+xgb",
                )
                db.add(cls_record)
                case.status = "classified"
                await db.commit()

                logger.info(
                    f"[Classification] Done: label={result['label']}, "
                    f"risk={result['risk_score']:.3f}"
                )
                return result

            except Exception as exc:
                case.status = "error"
                await db.commit()
                logger.error(f"[Classification] Failed for case {case_id}: {exc}")
                raise

    try:
        return asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc)
