"""
Module 3 — Radiomics Feature Extractor
Uses PyRadiomics to extract standardized radiomic features from
3D image + binary mask pairs.

Feature groups extracted:
  - firstorder:  intensity statistics (mean, std, skewness, kurtosis, entropy…)
  - shape:       geometric shape descriptors (elongation, flatness, mesh volume…)
  - glcm:        Gray Level Co-occurrence Matrix (texture)
  - glrlm:       Gray Level Run Length Matrix (texture)
  - gldm:        Gray Level Dependence Matrix (texture)
  - ngtdm:       Neighbourhood Gray-Tone Difference Matrix (texture)
"""
import os
import logging
import numpy as np
import SimpleITK as sitk
from pathlib import Path
from typing import Optional
import six

# Suppress PyRadiomics verbose output
logging.getLogger("radiomics").setLevel(logging.ERROR)

try:
    import radiomics
    from radiomics import featureextractor
    RADIOMICS_AVAILABLE = True
except ImportError:
    RADIOMICS_AVAILABLE = False


# ─── PyRadiomics settings ─────────────────────────────────────────────────

RADIOMICS_PARAMS = {
    "setting": {
        "binWidth": 25,
        "resampledPixelSpacing": [1.5, 1.5, 1.5],
        "interpolator": "sitkBSpline",
        "normalizeScale": 100,
        "removeOutliers": 3.0,
        "preCrop": True,
        "force2D": False,
    },
    "featureClass": {
        "firstorder": [],        # All first-order statistics
        "shape": [],             # All shape features
        "glcm": [                # Texture — selected subset
            "Autocorrelation",
            "ClusterProminence",
            "ClusterShade",
            "Contrast",
            "Correlation",
            "DifferenceEntropy",
            "Idm",
            "Idn",
            "JointEntropy",
        ],
        "glrlm": [],
        "gldm": [],
        "ngtdm": [],
    },
}


def extract_radiomics(
    image_path: str,
    mask_path: str,
    label: int = 1,
) -> dict:
    """
    Extract PyRadiomics features from a NIfTI image + mask pair.

    Args:
        image_path: Path to preprocessed NIfTI image (.nii.gz)
        mask_path:  Path to binary NIfTI mask (.nii.gz)
        label:      Mask label value to extract (default=1 for tumor)

    Returns:
        dict of feature_name → float value (diagnostic keys filtered out)
    """
    if not RADIOMICS_AVAILABLE:
        return _dummy_radiomics_features()

    extractor = featureextractor.RadiomicsFeatureExtractor()
    extractor.disableAllFeatures()

    for feature_class, features in RADIOMICS_PARAMS["featureClass"].items():
        if features:
            extractor.enableFeaturesByName(**{feature_class: features})
        else:
            extractor.enableFeatureClassByName(feature_class)

    # Apply settings
    for key, val in RADIOMICS_PARAMS["setting"].items():
        extractor.settings[key] = val

    result = extractor.execute(image_path, mask_path, label=label)

    # Filter diagnostic metadata, keep only numeric features
    features = {}
    for key, val in result.items():
        if key.startswith("diagnostics_"):
            continue
        try:
            features[key] = float(val)
        except (TypeError, ValueError):
            pass

    return features


def _dummy_radiomics_features() -> dict:
    """Return zeros when PyRadiomics is unavailable (testing/demo mode)."""
    keys = [
        "original_firstorder_Energy", "original_firstorder_Entropy",
        "original_firstorder_Kurtosis", "original_firstorder_Mean",
        "original_firstorder_Skewness", "original_firstorder_Variance",
        "original_shape_Elongation", "original_shape_Flatness",
        "original_shape_LeastAxisLength", "original_shape_MajorAxisLength",
        "original_shape_MeshVolume", "original_shape_MinorAxisLength",
        "original_shape_Sphericity", "original_shape_SurfaceArea",
        "original_shape_SurfaceVolumeRatio", "original_shape_Maximum2DDiameterSlice",
        "original_glcm_Autocorrelation", "original_glcm_Contrast",
        "original_glcm_Correlation", "original_glcm_JointEntropy",
    ]
    return {k: 0.0 for k in keys}
