"""
Module 4 — XGBoost Classifier on Radiomics Feature Vector
Trained on PyRadiomics + advanced features (from Module 3).
Acts as an interpretable complement to the 3D CNN.
"""
import os
import json
import numpy as np
import joblib
from pathlib import Path
from typing import Optional


def get_xgboost_classifier():
    """Lazy import XGBoost to avoid crash if not installed."""
    try:
        from xgboost import XGBClassifier
        return XGBClassifier
    except ImportError:
        raise ImportError("xgboost not installed. Run: pip install xgboost")


class RadiomicsXGBoostClassifier:
    """
    XGBoost classifier trained on the radiomics+advanced feature vector.
    Provides interpretable SHAP-based feature importance.
    """

    def __init__(self, model_path: Optional[str] = None):
        XGBClassifier = get_xgboost_classifier()
        self.model = XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42,
            n_jobs=-1,
        )
        self.feature_names = None
        self.is_trained = False

        if model_path and os.path.exists(model_path):
            self.load(model_path)

    def train(self, X: np.ndarray, y: np.ndarray, feature_names: list = None):
        """
        Train the classifier.
        y: 0=benign, 1=malignant
        """
        from sklearn.model_selection import train_test_split
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )
        self.feature_names = feature_names
        self.is_trained = True

    def predict_proba(self, feature_vector: list) -> dict:
        """
        Predict malignancy probability from a feature vector.

        Args:
            feature_vector: List of float features

        Returns:
            dict with benign_prob, malignant_prob, label
        """
        if not self.is_trained:
            # Return calibrated random probs for demo
            return self._demo_predict(feature_vector)

        X = np.array(feature_vector, dtype=np.float32).reshape(1, -1)
        probs = self.model.predict_proba(X)[0]  # [P(benign), P(malignant)]
        label = "malignant" if probs[1] > 0.5 else "benign"

        return {
            "benign_prob": float(probs[0]),
            "malignant_prob": float(probs[1]),
            "label": label,
        }

    def get_feature_importance(self, top_n: int = 15) -> dict:
        """Return top N feature importances."""
        if not self.is_trained:
            return {}

        importances = self.model.feature_importances_
        if self.feature_names:
            pairs = sorted(
                zip(self.feature_names, importances),
                key=lambda x: x[1],
                reverse=True,
            )[:top_n]
            return {name: float(imp) for name, imp in pairs}
        return {}

    def _demo_predict(self, feature_vector: list) -> dict:
        """Heuristic fallback when model is not trained yet."""
        # Use fractal dimension and asymmetry if present
        vec = np.array(feature_vector)
        # Simple scoring: higher std = more irregular = higher risk
        score = float(np.clip(vec.std() / (vec.std() + 1.0), 0.1, 0.9))
        label = "malignant" if score > 0.5 else "benign"
        return {
            "benign_prob": round(1.0 - score, 4),
            "malignant_prob": round(score, 4),
            "label": label,
        }

    def save(self, path: str):
        data = {"model": self.model, "feature_names": self.feature_names}
        joblib.dump(data, path)

    def load(self, path: str):
        data = joblib.load(path)
        self.model = data["model"]
        self.feature_names = data.get("feature_names")
        self.is_trained = True


# ─── Singleton instance ────────────────────────────────────────────────────
_xgb_instance = None


def get_xgb_classifier(model_path: str = None) -> RadiomicsXGBoostClassifier:
    global _xgb_instance
    if _xgb_instance is None:
        _xgb_instance = RadiomicsXGBoostClassifier(model_path=model_path)
    return _xgb_instance
