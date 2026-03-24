"""
Module 2 — Full 3D Reconstruction API Endpoint
Handles mesh generation, feature retrieval, and mesh file serving.
"""
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.core.config import settings
from app.models.models import Case, SegmentationResult, ReconstructionResult

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────────────

class GeometricFeaturesResponse(BaseModel):
    case_id: str
    status: str
    volume_mm3: Optional[float] = None
    surface_area_mm2: Optional[float] = None
    sphericity: Optional[float] = None
    roughness_index: Optional[float] = None
    compactness: Optional[float] = None
    elongation: Optional[float] = None
    convexity: Optional[float] = None
    max_diameter_mm: Optional[float] = None
    mesh_glb_url: Optional[str] = None
    mesh_obj_url: Optional[str] = None
    vertex_count: Optional[int] = None
    face_count: Optional[int] = None


# ─── Endpoints ────────────────────────────────────────────────────────────

@router.post("/run/{case_id}", status_code=status.HTTP_202_ACCEPTED)
async def run_reconstruction(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    Trigger 3D reconstruction for a segmented case.
    Requires segmentation to be completed first.
    """
    # Check segmentation exists
    seg_q = await db.execute(
        select(SegmentationResult).where(SegmentationResult.case_id == uuid.UUID(case_id))
    )
    seg = seg_q.scalar_one_or_none()
    if not seg or not seg.mask_path:
        raise HTTPException(
            status_code=400,
            detail="Segmentation mask not found. Run segmentation first.",
        )

    from app.workers.tasks.reconstruction_tasks import run_reconstruction_task
    task = run_reconstruction_task.delay(case_id)

    return {"case_id": case_id, "task_id": task.id, "status": "queued"}


@router.get("/features/{case_id}", response_model=GeometricFeaturesResponse)
async def get_geometric_features(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve all geometric features for a reconstructed case.
    """
    case_q = await db.execute(select(Case).where(Case.id == uuid.UUID(case_id)))
    case = case_q.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    recon_q = await db.execute(
        select(ReconstructionResult).where(ReconstructionResult.case_id == uuid.UUID(case_id))
    )
    recon = recon_q.scalar_one_or_none()

    if not recon:
        return GeometricFeaturesResponse(case_id=case_id, status=case.status)

    return GeometricFeaturesResponse(
        case_id=case_id,
        status=case.status,
        volume_mm3=recon.volume_mm3,
        surface_area_mm2=recon.surface_area_mm2,
        sphericity=recon.sphericity,
        roughness_index=recon.roughness_index,
        mesh_glb_url=f"/api/v1/reconstruction/mesh/{case_id}/glb",
        mesh_obj_url=f"/api/v1/reconstruction/mesh/{case_id}/obj",
    )


@router.get("/mesh/{case_id}/glb")
async def serve_mesh_glb(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    Serve the GLB mesh file for Three.js rendering.
    GLB = binary glTF, natively supported by Three.js GLTFLoader.
    """
    mesh_path = Path(settings.STORAGE_LOCAL_PATH) / "meshes" / f"{case_id}.glb"
    if not mesh_path.exists():
        raise HTTPException(status_code=404, detail="GLB mesh not found. Run reconstruction first.")
    return FileResponse(str(mesh_path), media_type="model/gltf-binary", filename=f"{case_id}.glb")


@router.get("/mesh/{case_id}/obj")
async def serve_mesh_obj(case_id: str):
    """Serve the OBJ mesh file for download / VTK."""
    mesh_path = Path(settings.STORAGE_LOCAL_PATH) / "meshes" / f"{case_id}.obj"
    if not mesh_path.exists():
        raise HTTPException(status_code=404, detail="OBJ mesh not found. Run reconstruction first.")
    return FileResponse(str(mesh_path), media_type="text/plain", filename=f"{case_id}.obj")


@router.get("/mesh/{case_id}/stl")
async def serve_mesh_stl(case_id: str):
    """Serve the STL mesh file for 3D printing / download."""
    mesh_path = Path(settings.STORAGE_LOCAL_PATH) / "meshes" / f"{case_id}.stl"
    if not mesh_path.exists():
        raise HTTPException(status_code=404, detail="STL mesh not found.")
    return FileResponse(str(mesh_path), media_type="application/octet-stream", filename=f"{case_id}.stl")


@router.post("/export-stl/{case_id}")
async def export_stl(case_id: str, db: AsyncSession = Depends(get_db)):
    """
    On-demand STL export from existing OBJ mesh.
    Useful for 3D printing or surgical planning.
    """
    import trimesh
    obj_path = Path(settings.STORAGE_LOCAL_PATH) / "meshes" / f"{case_id}.obj"
    if not obj_path.exists():
        raise HTTPException(status_code=404, detail="OBJ mesh not found.")

    mesh = trimesh.load(str(obj_path))
    stl_path = Path(settings.STORAGE_LOCAL_PATH) / "meshes" / f"{case_id}.stl"
    mesh.export(str(stl_path), file_type="stl")

    return {"case_id": case_id, "stl_url": f"/api/v1/reconstruction/mesh/{case_id}/stl"}
