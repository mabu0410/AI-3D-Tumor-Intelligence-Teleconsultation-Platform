"""
Module 4 — Classification Service
Ensemble: 3D CNN (deep learning) + XGBoost (radiomics) → weighted Risk Score.

Risk Score formula:
  risk_score = 0.6 × CNN_malignant_prob + 0.4 × XGB_malignant_prob

Label thresholds:
  risk_score < 0.35  → Benign (Low Risk)
  risk_score < 0.65  → Indeterminate (Follow-up)
  risk_score ≥ 0.65  → Malignant (High Risk)
"""
import os
import torch
import numpy as np
import nibabel as nib
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.services.classifier_model import build_classifier
from app.services.xgboost_classifier import get_xgb_classifier


# ─── Risk scoring ─────────────────────────────────────────────────────────

def compute_risk_score(cnn_prob: float, xgb_prob: float, weights=(0.6, 0.4)) -> float:
    """Weighted ensemble risk score in [0, 1]."""
    return float(weights[0] * cnn_prob + weights[1] * xgb_prob)


def interpret_risk_score(risk_score: float) -> dict:
    """Translate numeric risk score to clinical label and recommendation."""
    if risk_score < 0.35:
        return {
            "label": "benign",
            "risk_level": "Low",
            "recommendation": "Routine follow-up in 12 months.",
            "color": "green",
        }
    elif risk_score < 0.65:
        return {
            "label": "indeterminate",
            "risk_level": "Moderate",
            "recommendation": "Follow-up imaging in 3–6 months. Clinical correlation required.",
            "color": "orange",
        }
    else:
        return {
            "label": "malignant",
            "risk_level": "High",
            "recommendation": "Urgent specialist consultation. Biopsy may be indicated.",
            "color": "red",
        }


# ─── CNN Inference ────────────────────────────────────────────────────────

class ClassificationService:
    _cnn_model = None
    _device = None

    @classmethod
    def get_cnn_model(cls):
        if cls._cnn_model is None:
            cls._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            cls._cnn_model = build_classifier(variant="resnet3d_18", device=cls._device)
            weights = settings.CLASSIFICATION_MODEL_PATH
            if os.path.exists(weights):
                state = torch.load(weights, map_location=cls._device)
                state = {k.replace("module.", ""): v for k, v in state.items()}
                cls._cnn_model.load_state_dict(state, strict=False)
            cls._cnn_model.eval()
        return cls._cnn_model, cls._device

    @classmethod
    def classify_from_volume(cls, mask_path: str) -> dict:
        """
        Run 3D CNN on the segmentation mask as input proxy.
        (In production, use the original image cropped to tumor ROI.)
        """
        model, device = cls.get_cnn_model()

        from monai.transforms import (
            LoadImage, EnsureChannelFirst, Resize, ScaleIntensityRange, ToTensor, Compose,
        )
        transforms = Compose([
            LoadImage(image_only=True),
            EnsureChannelFirst(),
            Resize(spatial_size=(64, 64, 64)),    # smaller for classification
            ScaleIntensityRange(a_min=0, a_max=1, b_min=0, b_max=1, clip=True),
            ToTensor(),
        ])

        try:
            volume = transforms(mask_path).unsqueeze(0).float().to(device)  # (1,1,64,64,64)
            with torch.no_grad():
                probs = model.predict_proba(volume)[0].cpu().numpy()   # [P(benign), P(malignant)]
            return {
                "benign_prob": float(probs[0]),
                "malignant_prob": float(probs[1]),
                "model": "resnet3d_18",
            }
        except Exception:
            # Untrained model — use heuristic from mask density
            mask = nib.load(mask_path).get_fdata()
            density = float(mask.mean())
            mal_prob = float(np.clip(density * 3.0, 0.05, 0.95))
            return {
                "benign_prob": round(1 - mal_prob, 4),
                "malignant_prob": round(mal_prob, 4),
                "model": "heuristic",
            }

    @classmethod
    def classify(
        cls,
        case_id: str,
        mask_path: str,
        feature_vector: Optional[list] = None,
    ) -> dict:
        """
        Full classification pipeline:
          1. CNN inference on volume/mask
          2. XGBoost on feature vector
          3. Ensemble risk score
          4. Clinical interpretation

        Returns complete classification result dict.
        """
        # CNN
        cnn_result = cls.classify_from_volume(mask_path)
        cnn_mal_prob = cnn_result["malignant_prob"]

        # XGBoost
        xgb_result = {"malignant_prob": 0.5, "benign_prob": 0.5, "label": "indeterminate"}
        if feature_vector and len(feature_vector) > 0:
            xgb_classifier = get_xgb_classifier(
                model_path=os.path.join(settings.MODEL_WEIGHTS_DIR, "xgb_classifier.joblib")
            )
            xgb_result = xgb_classifier.predict_proba(feature_vector)

        xgb_mal_prob = xgb_result["malignant_prob"]

        # Ensemble
        risk_score = compute_risk_score(cnn_mal_prob, xgb_mal_prob)
        interpretation = interpret_risk_score(risk_score)

        return {
            "case_id": case_id,
            "cnn": cnn_result,
            "xgboost": xgb_result,
            "risk_score": round(risk_score, 4),
            "malignancy_probability": round(risk_score, 4),
            "label": interpretation["label"],
            "risk_level": interpretation["risk_level"],
            "recommendation": interpretation["recommendation"],
            "color": interpretation["color"],
        }
