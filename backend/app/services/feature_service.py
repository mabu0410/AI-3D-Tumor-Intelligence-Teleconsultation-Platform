"""
Module 3 — Feature Service
Combines PyRadiomics + Advanced features into a unified feature vector
ready for classification (Module 4) and progression prediction (Module 5).
"""
import numpy as np
import nibabel as nib
import SimpleITK as sitk
from pathlib import Path
from typing import Optional

from app.services.radiomics_extractor import extract_radiomics
from app.services.advanced_features import extract_advanced_features


def load_nifti_volume(path: str) -> np.ndarray:
    """Load a NIfTI file as numpy array."""
    return nib.load(path).get_fdata().astype(np.float32)


def load_nifti_mask(path: str) -> np.ndarray:
    """Load a NIfTI binary mask as uint8."""
    return (nib.load(path).get_fdata() > 0.5).astype(np.uint8)


def extract_all_features(
    image_path: Optional[str],
    mask_path: str,
    case_id: str,
) -> dict:
    """
    Master feature extraction pipeline combining:
      1. PyRadiomics features (firstorder, shape, texture)
      2. Advanced features (fractal, gradient, asymmetry, intensity)
      3. Combined normalized feature vector for ML models

    Args:
        image_path: Path to original NIfTI image (optional — required for radiomics & gradient features)
        mask_path:  Path to binary NIfTI mask (required)
        case_id:    Case identifier for traceability

    Returns:
        dict with keys: radiomics_features, advanced_features, feature_vector, feature_names
    """
    mask = load_nifti_mask(mask_path)

    # Advanced features (only requires mask, image optional)
    if image_path and Path(image_path).exists():
        image = load_nifti_volume(image_path)
        advanced = extract_advanced_features(image, mask)
    else:
        # Fallback: compute from mask intensity only
        advanced = extract_advanced_features(mask.astype(np.float32), mask)

    # PyRadiomics features (requires both image and mask as NIfTI)
    radiomics = {}
    if image_path and Path(image_path).exists():
        try:
            radiomics = extract_radiomics(
                image_path=image_path,
                mask_path=mask_path,
                label=1,
            )
        except Exception as e:
            # Non-fatal — fall back to empty dict
            radiomics = {"_radiomics_error": str(e)}

    # Build flat feature vector (for ML models)
    combined = {**radiomics, **advanced}
    # Remove non-numeric entries
    numeric_features = {
        k: v for k, v in combined.items()
        if isinstance(v, (int, float)) and not (v != v)  # exclude NaN
    }

    feature_vector = list(numeric_features.values())
    feature_names = list(numeric_features.keys())

    return {
        "case_id": case_id,
        "radiomics_features": radiomics,
        "advanced_features": advanced,
        "feature_vector": feature_vector,
        "feature_names": feature_names,
        "feature_count": len(feature_vector),
        "fractal_dimension": advanced.get("fractal_dimension"),
        "asymmetry_index": advanced.get("asymmetry_index"),
        "gradient_entropy": advanced.get("gradient_entropy"),
    }
