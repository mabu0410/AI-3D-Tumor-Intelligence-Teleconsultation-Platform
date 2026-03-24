"""
Module 2 — Mesh Generator
Converts a 3D binary mask to a triangle mesh using Marching Cubes,
then exports as OBJ or STL.
"""
import numpy as np
import nibabel as nib
from pathlib import Path
from skimage.measure import marching_cubes
from skimage.filters import gaussian
import trimesh
from typing import Tuple, Optional


def load_mask(mask_path: str) -> np.ndarray:
    """Load a binary NIfTI mask and return a 3D numpy array."""
    img = nib.load(mask_path)
    data = img.get_fdata().astype(np.uint8)
    return data


def mask_to_mesh(
    mask: np.ndarray,
    voxel_spacing: Tuple[float, float, float] = (1.5, 1.5, 1.5),
    step_size: int = 1,
    smooth_sigma: float = 1.0,
    threshold: float = 0.5,
) -> trimesh.Trimesh:
    """
    Convert a 3D binary mask to a watertight triangle mesh.

    Steps:
      1. Gaussian smoothing to reduce staircase artefacts
      2. Marching Cubes (scikit-image) → vertices & faces
      3. Scale vertices by voxel spacing (mm)
      4. Build trimesh, fix normals

    Args:
        mask: (D, H, W) binary numpy array
        voxel_spacing: (x, y, z) mm per voxel from DICOM metadata
        step_size: Marching Cubes step (1=finest, 2=faster)
        smooth_sigma: Gaussian blur sigma for surface smoothing
        threshold: Iso-surface level for marching cubes

    Returns:
        trimesh.Trimesh with vertices in mm coordinates
    """
    if mask.sum() == 0:
        raise ValueError("Empty mask — no tumor voxels to reconstruct.")

    # Smooth to reduce stepping artefacts
    mask_float = gaussian(mask.astype(np.float32), sigma=smooth_sigma)

    # Marching Cubes
    verts, faces, normals, _ = marching_cubes(
        mask_float,
        level=threshold,
        step_size=step_size,
        allow_degenerate=False,
    )

    # Scale by voxel spacing → physical mm coordinates
    # Marching Cubes gives voxel-space coords as (row, col, depth) = (D, H, W)
    # Map to (x=W, y=H, z=D) for standard 3D orientation
    verts_mm = verts * np.array([voxel_spacing[2], voxel_spacing[1], voxel_spacing[0]])

    mesh = trimesh.Trimesh(vertices=verts_mm, faces=faces, vertex_normals=normals)
    mesh.fix_normals()

    return mesh


def export_mesh(mesh: trimesh.Trimesh, output_path: str, format: str = "obj") -> str:
    """
    Export mesh to file.

    Args:
        mesh: trimesh.Trimesh object
        output_path: Output file path (without extension)
        format: 'obj' | 'stl' | 'glb'

    Returns:
        Full path to the exported file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if format == "obj":
        out = str(path.with_suffix(".obj"))
        mesh.export(out, file_type="obj")
    elif format == "stl":
        out = str(path.with_suffix(".stl"))
        mesh.export(out, file_type="stl")
    elif format == "glb":
        out = str(path.with_suffix(".glb"))
        mesh.export(out, file_type="glb")
    else:
        raise ValueError(f"Unsupported format: {format}")

    return out


def process_mask_to_mesh(
    mask_path: str,
    case_id: str,
    output_dir: str,
    voxel_spacing: Tuple[float, float, float] = (1.5, 1.5, 1.5),
    export_formats: list = ["obj", "glb"],
) -> dict:
    """
    Full pipeline: load mask → mesh → export → return paths.
    Exports both OBJ (for Python/VTK) and GLB (for Three.js).
    """
    mask = load_mask(mask_path)
    mesh = mask_to_mesh(mask, voxel_spacing=voxel_spacing)

    output_paths = {}
    base = str(Path(output_dir) / case_id)

    for fmt in export_formats:
        exported = export_mesh(mesh, base, format=fmt)
        output_paths[fmt] = exported

    return {
        "mesh_paths": output_paths,
        "vertex_count": len(mesh.vertices),
        "face_count": len(mesh.faces),
        "is_watertight": mesh.is_watertight,
        "mesh": mesh,   # pass to feature extractor
    }
