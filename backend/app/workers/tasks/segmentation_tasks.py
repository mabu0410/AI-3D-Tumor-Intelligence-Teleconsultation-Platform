"""
Module 1 — Celery Segmentation Task
Async wrapper for the SegmentationService to run inference in background.
"""
from celery import shared_task
from loguru import logger


@shared_task(bind=True, max_retries=3, default_retry_delay=30, name="segmentation_tasks.run_segmentation_task")
def run_segmentation_task(self, case_id: str):
    """
    Celery task to run 3D tumor segmentation for a given case_id.
    Fetches DICOM path from DB, runs inference, and saves result.
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.core.config import settings
    from app.services.segmentation_inference import SegmentationService

    async def _run():
        from app.models.models import Case, SegmentationResult
        from sqlalchemy import select
        import uuid

        engine = create_async_engine(settings.DATABASE_URL)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as db:
            # Fetch case
            result = await db.execute(select(Case).where(Case.id == uuid.UUID(case_id)))
            case = result.scalar_one_or_none()
            if not case:
                raise ValueError(f"Case {case_id} not found")

            # Update status
            case.status = "processing"
            await db.commit()

            try:
                logger.info(f"[Segmentation] Starting for case {case_id}")
                seg_result = SegmentationService.segment(
                    dicom_dir=case.dicom_path,
                    case_id=case_id,
                )

                # Save result
                seg_record = SegmentationResult(
                    case_id=case.id,
                    mask_path=seg_result["mask_path"],
                    dice_score=seg_result.get("dice_score"),
                    iou_score=seg_result.get("iou_score"),
                    hausdorff_distance=seg_result.get("hausdorff_distance"),
                )
                db.add(seg_record)
                case.status = "segmented"
                await db.commit()
                logger.info(f"[Segmentation] Done for case {case_id}: {seg_result['mask_path']}")
                return seg_result

            except Exception as exc:
                case.status = "error"
                await db.commit()
                logger.error(f"[Segmentation] Failed for case {case_id}: {exc}")
                raise

    try:
        return asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc)
