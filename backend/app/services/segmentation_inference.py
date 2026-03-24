"""
Module 1 — Inference Service
Runs 3D segmentation on a DICOM case and saves binary mask.
"""
import os
import uuid
import torch
import numpy as np
import nibabel as nib
from pathlib import Path
from monai.inferers import sliding_window_inference
from monai.transforms import (
    LoadImage, EnsureChannelFirst, Orientation, Spacing,
    ScaleIntensityRange, CropForeground, Resize, ToTensor, Compose,
    SaveImage,
)
import torch.nn.functional as F

from app.core.config import settings
from app.services.segmentation_model import build_segmentation_model, load_model_weights


class SegmentationService:
    """Singleton-style inference service for 3D tumor segmentation."""

    _model = None
    _device = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            cls._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            cls._model = build_segmentation_model(variant="unet3d", device=cls._device)
            weights = settings.SEGMENTATION_MODEL_PATH
            if os.path.exists(weights):
                cls._model = load_model_weights(cls._model, weights)
            else:
                # Use untrained model (demo/testing mode)
                cls._model.eval()
        return cls._model, cls._device

    @classmethod
    def segment(cls, dicom_dir: str, case_id: str) -> dict:
        """
        Run segmentation on a DICOM series.

        Args:
            dicom_dir: Directory containing DICOM files
            case_id: Unique case identifier for output file naming

        Returns:
            dict with mask_path, dice_score (dummy if no GT), metrics
        """
        model, device = cls.get_model()

        # Build inference transform
        infer_transforms = Compose([
            LoadImage(image_only=True),
            EnsureChannelFirst(),
            Orientation(axcodes="RAS"),
            Spacing(pixdim=(1.5, 1.5, 1.5), mode="bilinear"),
            ScaleIntensityRange(a_min=-1000.0, a_max=400.0, b_min=0.0, b_max=1.0, clip=True),
            CropForeground(source_key=None),
            Resize(spatial_size=(128, 128, 128)),
            ToTensor(),
        ])

        # Load first .dcm or .nii file
        dicom_path = Path(dicom_dir)
        nii_files = list(dicom_path.glob("*.nii*"))
        dcm_files = sorted(dicom_path.glob("*.dcm"))

        if nii_files:
            input_path = str(nii_files[0])
        elif dcm_files:
            input_path = str(dcm_files[0])  # SimpleITK handles series via dir
        else:
            raise FileNotFoundError(f"No DICOM or NIfTI files found in {dicom_dir}")

        image_tensor = infer_transforms(input_path)  # (1, D, H, W)
        image_tensor = image_tensor.unsqueeze(0).to(device)  # (1, 1, D, H, W)

        with torch.no_grad():
            outputs = sliding_window_inference(
                inputs=image_tensor,
                roi_size=(128, 128, 128),
                sw_batch_size=1,
                predictor=model,
                overlap=0.5,
            )
            # outputs: (1, 2, D, H, W) — softmax probabilities
            probs = F.softmax(outputs, dim=1)
            mask = torch.argmax(probs, dim=1).squeeze(0)  # (D, H, W) binary mask

        # Save mask as NIfTI
        output_dir = Path(settings.STORAGE_LOCAL_PATH) / "masks"
        output_dir.mkdir(parents=True, exist_ok=True)
        mask_path = str(output_dir / f"{case_id}_mask.nii.gz")

        mask_np = mask.cpu().numpy().astype(np.uint8)
        nib_img = nib.Nifti1Image(mask_np, affine=np.eye(4))
        nib.save(nib_img, mask_path)

        # Compute basic stats
        tumor_voxels = int(mask_np.sum())
        total_voxels = int(mask_np.size)

        return {
            "case_id": case_id,
            "mask_path": mask_path,
            "tumor_voxels": tumor_voxels,
            "total_voxels": total_voxels,
            "tumor_fraction": round(tumor_voxels / total_voxels, 6) if total_voxels > 0 else 0.0,
            "dice_score": None,   # Requires ground truth
            "iou_score": None,
            "hausdorff_distance": None,
            "status": "completed",
        }


def compute_metrics(pred: np.ndarray, gt: np.ndarray, smooth: float = 1e-5) -> dict:
    """
    Compute Dice, IoU, and Hausdorff Distance between prediction and ground truth masks.

    Args:
        pred: Binary prediction mask (D, H, W)
        gt: Binary ground truth mask (D, H, W)
        smooth: Smoothing constant to avoid division by zero

    Returns:
        dict with dice, iou, hausdorff_distance
    """
    from scipy.ndimage import distance_transform_edt

    pred_flat = pred.flatten().astype(bool)
    gt_flat = gt.flatten().astype(bool)

    intersection = (pred_flat & gt_flat).sum()
    dice = (2.0 * intersection + smooth) / (pred_flat.sum() + gt_flat.sum() + smooth)
    iou = (intersection + smooth) / (pred_flat.sum() + gt_flat.sum() - intersection + smooth)

    # Hausdorff Distance (95th percentile)
    if pred_flat.any() and gt_flat.any():
        dist_pred = distance_transform_edt(~pred)
        dist_gt = distance_transform_edt(~gt)
        hd95 = max(
            np.percentile(dist_pred[gt.astype(bool)], 95),
            np.percentile(dist_gt[pred.astype(bool)], 95),
        )
    else:
        hd95 = float("inf")

    return {
        "dice_score": float(dice),
        "iou_score": float(iou),
        "hausdorff_distance": float(hd95),
    }
