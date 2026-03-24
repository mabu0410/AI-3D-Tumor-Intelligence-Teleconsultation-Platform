"""
Module 1 — DICOM Preprocessor
Loads DICOM series and returns normalized 3D NumPy volumes.
"""
import os
import numpy as np
import SimpleITK as sitk
from pathlib import Path
from typing import Tuple
import pydicom
from pydicom.errors import InvalidDicomError
import monai.transforms as T


def load_dicom_series(dicom_dir: str) -> Tuple[np.ndarray, dict]:
    """
    Load a DICOM series from a directory into a 3D numpy array.

    Returns:
        volume (np.ndarray): Shape (D, H, W) in HU values for CT, or raw for MRI
        metadata (dict): Spacing, origin, direction, modality
    """
    reader = sitk.ImageSeriesReader()
    series_ids = reader.GetGDCMSeriesIDs(dicom_dir)
    if not series_ids:
        raise ValueError(f"No DICOM series found in {dicom_dir}")

    dicom_files = reader.GetGDCMSeriesFileNames(dicom_dir, series_ids[0])
    reader.SetFileNames(dicom_files)
    image = reader.Execute()

    volume = sitk.GetArrayFromImage(image)  # (D, H, W)
    metadata = {
        "spacing": image.GetSpacing(),         # (x, y, z) mm per voxel
        "origin": image.GetOrigin(),
        "direction": image.GetDirection(),
        "size": image.GetSize(),
        "modality": _get_modality(dicom_dir),
    }
    return volume, metadata


def _get_modality(dicom_dir: str) -> str:
    """Read modality (CT or MRI) from first DICOM file."""
    try:
        dcm_files = sorted(Path(dicom_dir).glob("*.dcm"))
        if not dcm_files:
            return "UNKNOWN"
        ds = pydicom.dcmread(str(dcm_files[0]), stop_before_pixels=True)
        return str(getattr(ds, "Modality", "UNKNOWN"))
    except (InvalidDicomError, Exception):
        return "UNKNOWN"


def get_monai_transforms(
    target_spacing: Tuple[float, float, float] = (1.5, 1.5, 1.5),
    roi_size: Tuple[int, int, int] = (128, 128, 128),
    intensity_min: float = -1000.0,
    intensity_max: float = 400.0,
    normalize: bool = True,
) -> T.Compose:
    """
    MONAI transform pipeline for CT volumes:
    1. LoadImaged → EnsureChannelFirst
    2. Orientation (RAS)
    3. Spacing resampling
    4. Intensity windowing + normalization
    5. Random crop (training) or CropForeground (inference)
    """
    transforms = [
        T.LoadImaged(keys=["image"], image_only=False),
        T.EnsureChannelFirstd(keys=["image"]),
        T.Orientationd(keys=["image"], axcodes="RAS"),
        T.Spacingd(keys=["image"], pixdim=target_spacing, mode="bilinear"),
        T.ScaleIntensityRanged(
            keys=["image"],
            a_min=intensity_min,
            a_max=intensity_max,
            b_min=0.0,
            b_max=1.0,
            clip=True,
        ),
        T.CropForegroundd(keys=["image"], source_key="image"),
        T.Resized(keys=["image"], spatial_size=roi_size),
        T.ToTensord(keys=["image"]),
    ]
    return T.Compose(transforms)


def get_monai_train_transforms(
    target_spacing: Tuple[float, float, float] = (1.5, 1.5, 1.5),
    roi_size: Tuple[int, int, int] = (128, 128, 128),
) -> T.Compose:
    """Training transforms with augmentation for image + mask pairs."""
    return T.Compose([
        T.LoadImaged(keys=["image", "label"], image_only=False),
        T.EnsureChannelFirstd(keys=["image", "label"]),
        T.Orientationd(keys=["image", "label"], axcodes="RAS"),
        T.Spacingd(keys=["image", "label"], pixdim=target_spacing, mode=["bilinear", "nearest"]),
        T.ScaleIntensityRanged(
            keys=["image"],
            a_min=-1000.0, a_max=400.0,
            b_min=0.0, b_max=1.0,
            clip=True,
        ),
        T.CropForegroundd(keys=["image", "label"], source_key="image"),
        T.RandCropByPosNegLabeld(
            keys=["image", "label"],
            label_key="label",
            spatial_size=roi_size,
            pos=1, neg=1,
            num_samples=2,
        ),
        # Augmentation
        T.RandFlipd(keys=["image", "label"], prob=0.5, spatial_axis=0),
        T.RandFlipd(keys=["image", "label"], prob=0.5, spatial_axis=1),
        T.RandFlipd(keys=["image", "label"], prob=0.5, spatial_axis=2),
        T.RandRotate90d(keys=["image", "label"], prob=0.5, max_k=3),
        T.RandScaleIntensityd(keys=["image"], factors=0.1, prob=0.5),
        T.RandShiftIntensityd(keys=["image"], offsets=0.1, prob=0.5),
        T.ToTensord(keys=["image", "label"]),
    ])
