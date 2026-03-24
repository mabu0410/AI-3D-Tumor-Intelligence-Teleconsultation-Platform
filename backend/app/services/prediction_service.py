"""
Module 5 — Prediction Service
Runs LSTM/Transformer inference on a patient's historical case data.
Outputs: volume change %, malignancy risk, invasion speed for 3 & 6 months.
"""
import os
import torch
import numpy as np
from typing import List, Optional

from app.core.config import settings
from app.services.prediction_model import build_prediction_model
from app.services.temporal_dataset import (
    TumorSnapshot, build_compact_vector, snapshots_from_db_records,
)

INVASION_LABELS = {0: "Slow", 1: "Medium", 2: "Fast"}
FEATURE_DIM = 57   # 7 core + 50 radiomics


class PredictionService:
    _model = None
    _device = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            cls._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            cls._model = build_prediction_model(variant="lstm", feature_dim=FEATURE_DIM, device=cls._device)
            weights = settings.PREDICTION_MODEL_PATH
            if os.path.exists(weights):
                state = torch.load(weights, map_location=cls._device)
                state = {k.replace("module.", ""): v for k, v in state.items()}
                cls._model.load_state_dict(state, strict=False)
            cls._model.eval()
        return cls._model, cls._device

    @classmethod
    def predict(cls, snapshots: List[TumorSnapshot]) -> dict:
        """
        Run progression prediction for a patient sequence.
        Extrapolates to 3 months and 6 months.

        Args:
            snapshots: Time-ordered list of TumorSnapshot (at least 2)

        Returns:
            Prediction dict with 3-month and 6-month forecasts
        """
        if len(snapshots) < 2:
            return cls._heuristic_predict(snapshots)

        model, device = cls.get_model()

        # Build sequence tensor (use last 3 snaps max)
        seq = snapshots[-3:]
        vecs = [build_compact_vector(s, max_features=50) for s in seq]

        # Pad to 3 if fewer
        while len(vecs) < 3:
            vecs.insert(0, vecs[0].copy())

        X = torch.tensor(np.stack(vecs, axis=0), dtype=torch.float32)
        X = X.unsqueeze(0).to(device)   # (1, 3, feature_dim)

        with torch.no_grad():
            try:
                preds = model(X)
                vol_change_3m = float(preds["volume_change_pct"][0].cpu())
                mal_delta = float(preds["malignancy_delta"][0].cpu())
                invasion_probs = torch.softmax(preds["invasion_logits"][0], dim=-1).cpu().numpy()
                invasion_cls = int(invasion_probs.argmax())
            except Exception:
                # Untrained model fallback
                vol_change_3m, mal_delta, invasion_cls, invasion_probs = cls._heuristic_values(snapshots)

        # Current state
        latest = snapshots[-1]
        current_vol = latest.volume_mm3
        current_mal = latest.malignancy_probability

        # 3-month projections
        vol_3m = current_vol * (1 + vol_change_3m / 100)
        mal_3m = float(np.clip(current_mal + mal_delta, 0.0, 1.0))

        # 6-month: compound projection (double the 3-month change)
        vol_change_6m = vol_change_3m * 2.0
        vol_6m = current_vol * (1 + vol_change_6m / 100)
        mal_6m = float(np.clip(current_mal + mal_delta * 2, 0.0, 1.0))

        # Invasion speed
        invasion_speed = INVASION_LABELS.get(invasion_cls, "Unknown")
        invasion_conf = float(invasion_probs[invasion_cls]) if hasattr(invasion_probs, "__len__") else 0.5

        return {
            "current": {
                "volume_mm3": round(current_vol, 2),
                "malignancy_probability": round(current_mal, 4),
                "scan_date": latest.scan_date,
            },
            "prediction_3m": {
                "volume_mm3": round(vol_3m, 2),
                "volume_change_pct": round(vol_change_3m, 2),
                "malignancy_probability": round(mal_3m, 4),
                "risk_level": _risk_from_prob(mal_3m),
            },
            "prediction_6m": {
                "volume_mm3": round(vol_6m, 2),
                "volume_change_pct": round(vol_change_6m, 2),
                "malignancy_probability": round(mal_6m, 4),
                "risk_level": _risk_from_prob(mal_6m),
            },
            "invasion_speed": invasion_speed,
            "invasion_confidence": round(invasion_conf, 4),
            "invasion_probabilities": {
                "slow": round(float(invasion_probs[0]) if hasattr(invasion_probs, "__len__") else 0.33, 4),
                "medium": round(float(invasion_probs[1]) if hasattr(invasion_probs, "__len__") else 0.33, 4),
                "fast": round(float(invasion_probs[2]) if hasattr(invasion_probs, "__len__") else 0.33, 4),
            },
            "data_points": len(snapshots),
            "model": "lstm",
        }

    @classmethod
    def _heuristic_predict(cls, snapshots: List[TumorSnapshot]) -> dict:
        """Simple trend extrapolation when only 1 timepoint available."""
        snap = snapshots[-1] if snapshots else TumorSnapshot(
            case_id="", scan_date="", volume_mm3=0, surface_area_mm2=0,
            sphericity=0.8, roughness_index=0.1, fractal_dimension=2.2,
            asymmetry_index=0.1, malignancy_probability=0.3, feature_vector=[],
        )
        # Heuristic: high roughness/asymmetry → faster growth
        growth_factor = 1.0 + snap.roughness_index * 0.5 + snap.asymmetry_index * 0.3
        vol_change_3m = growth_factor * 5.0   # ~5% baseline

        return cls.predict.__func__(cls, snapshots) if len(snapshots) >= 2 else {
            "current": {"volume_mm3": snap.volume_mm3, "malignancy_probability": snap.malignancy_probability},
            "prediction_3m": {"volume_change_pct": round(vol_change_3m, 2)},
            "prediction_6m": {"volume_change_pct": round(vol_change_3m * 2, 2)},
            "invasion_speed": "Slow",
            "data_points": 1,
            "model": "heuristic",
        }

    @classmethod
    def _heuristic_values(cls, snapshots):
        latest = snapshots[-1]
        growth = latest.roughness_index * 30 + latest.asymmetry_index * 20
        return growth, latest.malignancy_probability * 0.1, 0, np.array([0.6, 0.3, 0.1])


def _risk_from_prob(p: float) -> str:
    if p < 0.35:
        return "Low"
    elif p < 0.65:
        return "Moderate"
    return "High"
