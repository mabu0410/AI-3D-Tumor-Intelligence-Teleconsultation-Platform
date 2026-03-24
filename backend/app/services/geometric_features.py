"""
Module 2 — Geometric Feature Extractor
Computes shape features from a 3D mesh and binary mask:
  - Volume (mm³)          → from voxel count × spacing³
  - Surface Area (mm²)    → from mesh
  - Sphericity            → (π^(1/3) * (6V)^(2/3)) / A
  - Surface Roughness     → mean abs deviation of vertex normals
  - Compactness           → V / (A^1.5)
  - Bounding Box Dimensions
  - Elongation            → ratio of bounding box axes
"""
import numpy as np
import trimesh
from scipy.spatial import ConvexHull
from typing import Tuple


def compute_volume_from_mask(
    mask: np.ndarray,
    voxel_spacing: Tuple[float, float, float] = (1.5, 1.5, 1.5),
) -> float:
    """
    Compute tumor volume in mm³ from binary mask.
    More accurate than mesh-based volume for irregular shapes.
    """
    voxel_volume_mm3 = voxel_spacing[0] * voxel_spacing[1] * voxel_spacing[2]
    tumor_voxels = int(mask.sum())
    return tumor_voxels * voxel_volume_mm3


def compute_surface_area(mesh: trimesh.Trimesh) -> float:
    """Mesh surface area in mm²."""
    return float(mesh.area)


def compute_sphericity(volume_mm3: float, surface_area_mm2: float) -> float:
    """
    Sphericity = (π^(1/3) × (6V)^(2/3)) / A
    Range: (0, 1] — 1 = perfect sphere, lower = more irregular
    """
    if surface_area_mm2 <= 0:
        return 0.0
    sphere_area = (np.pi ** (1 / 3)) * ((6 * volume_mm3) ** (2 / 3))
    return float(sphere_area / surface_area_mm2)


def compute_roughness_index(mesh: trimesh.Trimesh) -> float:
    """
    Surface Roughness Index:
    Mean absolute deviation of vertex normal vectors from the mean normal.
    Higher value = more irregular/spiky surface (malignant indicator).
    """
    normals = mesh.vertex_normals  # (N, 3) unit vectors
    mean_normal = normals.mean(axis=0)
    mean_normal /= np.linalg.norm(mean_normal) + 1e-8
    deviations = np.abs(normals - mean_normal).mean(axis=1)
    return float(deviations.mean())


def compute_compactness(volume_mm3: float, surface_area_mm2: float) -> float:
    """
    Compactness = V / A^1.5
    Normalized compact shape descriptor.
    """
    if surface_area_mm2 <= 0:
        return 0.0
    return float(volume_mm3 / (surface_area_mm2 ** 1.5))


def compute_bounding_box(mesh: trimesh.Trimesh) -> dict:
    """Axis-aligned bounding box dimensions in mm."""
    bounds = mesh.bounds  # (2, 3): [[min_x, min_y, min_z], [max_x, max_y, max_z]]
    dims = bounds[1] - bounds[0]
    return {
        "x_mm": float(dims[0]),
        "y_mm": float(dims[1]),
        "z_mm": float(dims[2]),
        "max_diameter_mm": float(dims.max()),
    }


def compute_elongation(mesh: trimesh.Trimesh) -> float:
    """
    Elongation = min(dim) / max(dim)
    Range: (0, 1] — 1 = isotropic, lower = elongated
    """
    bounds = mesh.bounds
    dims = bounds[1] - bounds[0]
    if dims.max() == 0:
        return 0.0
    return float(dims.min() / dims.max())


def compute_convexity(mesh: trimesh.Trimesh, volume_mm3: float) -> float:
    """
    Convexity = Volume / Convex Hull Volume
    Range: (0, 1] — 1 = convex shape, lower = concave/lobulated
    """
    try:
        hull = ConvexHull(mesh.vertices)
        convex_volume = hull.volume
        if convex_volume <= 0:
            return 0.0
        return float(volume_mm3 / convex_volume)
    except Exception:
        return 0.0


def extract_geometric_features(
    mesh: trimesh.Trimesh,
    mask: np.ndarray,
    voxel_spacing: Tuple[float, float, float] = (1.5, 1.5, 1.5),
) -> dict:
    """
    Extract all geometric features from a mesh and its source mask.

    Returns:
        dict with all geometric metrics (serializable for JSON/DB storage)
    """
    volume_mm3 = compute_volume_from_mask(mask, voxel_spacing)
    surface_area_mm2 = compute_surface_area(mesh)
    sphericity = compute_sphericity(volume_mm3, surface_area_mm2)
    roughness = compute_roughness_index(mesh)
    compactness = compute_compactness(volume_mm3, surface_area_mm2)
    bbox = compute_bounding_box(mesh)
    elongation = compute_elongation(mesh)
    convexity = compute_convexity(mesh, volume_mm3)

    return {
        "volume_mm3": round(volume_mm3, 3),
        "surface_area_mm2": round(surface_area_mm2, 3),
        "sphericity": round(sphericity, 6),
        "roughness_index": round(roughness, 6),
        "compactness": round(compactness, 9),
        "elongation": round(elongation, 6),
        "convexity": round(convexity, 6),
        "bounding_box": bbox,
        "max_diameter_mm": bbox["max_diameter_mm"],
        "vertex_count": len(mesh.vertices),
        "face_count": len(mesh.faces),
        "is_watertight": bool(mesh.is_watertight),
    }
