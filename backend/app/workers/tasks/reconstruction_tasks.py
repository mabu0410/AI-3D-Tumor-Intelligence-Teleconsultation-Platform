"""
Module 2 — Celery Reconstruction Task
Async pipeline: load mask → generate mesh → extract features → persist to DB.
"""
from celery import shared_task
from loguru import logger


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="reconstruction_tasks.run_reconstruction_task",
)
def run_reconstruction_task(self, case_id: str):
    """
    Celery task to run 3D reconstruction for a given case_id.
    Depends on segmentation having been completed first (mask must exist).
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    from app.services.mesh_generator import process_mask_to_mesh
    from app.services.geometric_features import extract_geometric_features
    from app.services.mesh_generator import load_mask
    import nibabel as nib

    async def _run():
        from app.models.models import Case, SegmentationResult, ReconstructionResult
        from sqlalchemy import select
        import uuid

        engine = create_async_engine(settings.DATABASE_URL)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as db:
            # Fetch segmentation result
            seg_q = await db.execute(
                select(SegmentationResult).where(SegmentationResult.case_id == uuid.UUID(case_id))
            )
            seg = seg_q.scalar_one_or_none()
            if not seg or not seg.mask_path:
                raise ValueError(f"No segmentation mask found for case {case_id}")

            # Fetch case for status update
            case_q = await db.execute(select(Case).where(Case.id == uuid.UUID(case_id)))
            case = case_q.scalar_one_or_none()
            if not case:
                raise ValueError(f"Case {case_id} not found")

            case.status = "reconstructing"
            await db.commit()

            try:
                logger.info(f"[Reconstruction] Starting for case {case_id}")

                output_dir = f"{settings.STORAGE_LOCAL_PATH}/meshes"

                # Generate mesh (OBJ + GLB)
                mesh_result = process_mask_to_mesh(
                    mask_path=seg.mask_path,
                    case_id=case_id,
                    output_dir=output_dir,
                    voxel_spacing=(1.5, 1.5, 1.5),
                    export_formats=["obj", "glb"],
                )

                # Extract geometric features
                mask = load_mask(seg.mask_path)
                geo_features = extract_geometric_features(
                    mesh=mesh_result["mesh"],
                    mask=mask,
                    voxel_spacing=(1.5, 1.5, 1.5),
                )

                # Save to DB
                recon = ReconstructionResult(
                    case_id=case.id,
                    mesh_path=mesh_result["mesh_paths"].get("glb"),
                    volume_mm3=geo_features["volume_mm3"],
                    surface_area_mm2=geo_features["surface_area_mm2"],
                    sphericity=geo_features["sphericity"],
                    roughness_index=geo_features["roughness_index"],
                )
                db.add(recon)
                case.status = "reconstructed"
                await db.commit()

                logger.info(f"[Reconstruction] Done for case {case_id}: vol={geo_features['volume_mm3']:.2f} mm³")
                return {**geo_features, "mesh_paths": mesh_result["mesh_paths"]}

            except Exception as exc:
                case.status = "error"
                await db.commit()
                logger.error(f"[Reconstruction] Failed for case {case_id}: {exc}")
                raise

    try:
        return asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc)
