"""Module 3 — Celery Feature Extraction Task"""
from celery import shared_task
from loguru import logger


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="feature_tasks.run_feature_extraction_task",
)
def run_feature_extraction_task(self, case_id: str):
    """
    Extract all features for a case (requires segmentation mask to exist).
    Looks up the original DICOM/NIfTI image path from the Case record.
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    from app.services.feature_service import extract_all_features
    import json

    async def _run():
        from app.models.models import Case, SegmentationResult, FeatureResult
        from sqlalchemy import select
        import uuid

        engine = create_async_engine(settings.DATABASE_URL)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as db:
            case_q = await db.execute(select(Case).where(Case.id == uuid.UUID(case_id)))
            case = case_q.scalar_one_or_none()
            if not case:
                raise ValueError(f"Case {case_id} not found")

            seg_q = await db.execute(
                select(SegmentationResult).where(SegmentationResult.case_id == uuid.UUID(case_id))
            )
            seg = seg_q.scalar_one_or_none()
            if not seg or not seg.mask_path:
                raise ValueError(f"Segmentation mask not found for case {case_id}")

            case.status = "extracting_features"
            await db.commit()

            try:
                logger.info(f"[Features] Starting extraction for case {case_id}")

                # Try to find a NIfTI image in the DICOM directory
                from pathlib import Path
                dicom_dir = Path(case.dicom_path)
                nii_files = list(dicom_dir.glob("*.nii*"))
                image_path = str(nii_files[0]) if nii_files else None

                result = extract_all_features(
                    image_path=image_path,
                    mask_path=seg.mask_path,
                    case_id=case_id,
                )

                feat_record = FeatureResult(
                    case_id=case.id,
                    feature_vector=result["feature_vector"],
                    radiomics_features=result["radiomics_features"],
                    fractal_dimension=result.get("fractal_dimension"),
                    surface_irregularity=result["advanced_features"].get("asymmetry_index"),
                )
                db.add(feat_record)
                case.status = "features_extracted"
                await db.commit()

                logger.info(f"[Features] Done: {result['feature_count']} features extracted")
                return result

            except Exception as exc:
                case.status = "error"
                await db.commit()
                logger.error(f"[Features] Failed for case {case_id}: {exc}")
                raise

    try:
        return asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc)
