"""
Module 5 — Temporal Dataset
Loads multi-timepoint tumor data for LSTM/Transformer training.

Expected DB structure: patient has multiple Cases at different scan dates.
Each case has a FeatureResult with feature_vector + geometric data.

Dataset item: sequence of feature vectors [T0, T1, T2, ...] → target
Target:
  - volume_delta:   % volume change at next timepoint
  - malignancy:     probability at next timepoint
  - invasion_speed: 0=slow, 1=medium, 2=fast (classification head)
"""
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class TumorSnapshot:
    """Features at a single timepoint."""
    case_id: str
    scan_date: str           # ISO format
    volume_mm3: float
    surface_area_mm2: float
    sphericity: float
    roughness_index: float
    fractal_dimension: float
    asymmetry_index: float
    malignancy_probability: float
    feature_vector: List[float]


def snapshots_from_db_records(records: list) -> List[TumorSnapshot]:
    """
    Convert DB records (Case + joined results) to TumorSnapshot list.
    records: list of dicts with merged Case, ReconstructionResult, FeatureResult, ClassificationResult
    """
    snapshots = []
    for r in records:
        snap = TumorSnapshot(
            case_id=str(r.get("case_id", "")),
            scan_date=str(r.get("scan_date", "")),
            volume_mm3=float(r.get("volume_mm3") or 0.0),
            surface_area_mm2=float(r.get("surface_area_mm2") or 0.0),
            sphericity=float(r.get("sphericity") or 0.0),
            roughness_index=float(r.get("roughness_index") or 0.0),
            fractal_dimension=float(r.get("fractal_dimension") or 0.0),
            asymmetry_index=float(r.get("surface_irregularity") or 0.0),
            malignancy_probability=float(r.get("malignancy_probability") or 0.0),
            feature_vector=r.get("feature_vector") or [],
        )
        snapshots.append(snap)
    return snapshots


def build_compact_vector(snap: TumorSnapshot, max_features: int = 50) -> np.ndarray:
    """
    Build a compact time-step vector from a snapshot.
    Uses core geometric + radiomics features.

    Layout (fixed 9 core features + up to max_features radiomics):
      [volume, surface_area, sphericity, roughness, fractal_dim, asymmetry,
       malignancy_prob, ...radiomics (padded to max_features)]
    """
    core = np.array([
        snap.volume_mm3 / 1e4,            # normalize ~mm³
        snap.surface_area_mm2 / 1e3,
        snap.sphericity,
        snap.roughness_index,
        snap.fractal_dimension / 3.0,     # normalize to [0,1]
        snap.asymmetry_index,
        snap.malignancy_probability,
    ], dtype=np.float32)

    # Radiomics features (padded/truncated to max_features)
    radio = np.array(snap.feature_vector[:max_features], dtype=np.float32)
    if len(radio) < max_features:
        radio = np.pad(radio, (0, max_features - len(radio)))

    return np.concatenate([core, radio])   # shape: (7 + max_features,)


class TumorProgressionDataset(Dataset):
    """
    Temporal sequence dataset for tumor progression prediction.

    Each item:
      X: (seq_len, feature_dim) — sequence of time-step feature vectors
      y: dict of regression targets for next timepoint
        - volume_change_pct: float (% change in volume)
        - malignancy_delta:  float (change in malignancy prob)
        - invasion_class:    int   (0=slow, 1=medium, 2=fast)
    """

    def __init__(
        self,
        patient_sequences: List[List[TumorSnapshot]],
        seq_len: int = 3,
        max_features: int = 50,
        augment: bool = False,
    ):
        """
        Args:
            patient_sequences: List of snapshot sequences, one per patient
            seq_len: Fixed number of timepoints to use as input
            max_features: Radiomics features to include
            augment: Whether to add small noise for data augmentation
        """
        self.seq_len = seq_len
        self.max_features = max_features
        self.augment = augment
        self.samples = []

        for sequence in patient_sequences:
            # Sort by date
            sequence_sorted = sorted(sequence, key=lambda s: s.scan_date)

            # Build sliding windows
            for i in range(len(sequence_sorted) - seq_len):
                x_snaps = sequence_sorted[i: i + seq_len]
                y_snap = sequence_sorted[i + seq_len]

                x_vecs = [build_compact_vector(s, max_features) for s in x_snaps]
                X = np.stack(x_vecs, axis=0)  # (seq_len, feature_dim)

                # Compute targets
                vol_0 = x_snaps[-1].volume_mm3
                vol_1 = y_snap.volume_mm3
                vol_change_pct = ((vol_1 - vol_0) / (vol_0 + 1e-6)) * 100.0

                malignancy_delta = y_snap.malignancy_probability - x_snaps[-1].malignancy_probability

                if abs(vol_change_pct) < 5:
                    invasion_class = 0   # slow
                elif abs(vol_change_pct) < 20:
                    invasion_class = 1   # medium
                else:
                    invasion_class = 2   # fast

                self.samples.append({
                    "X": X.astype(np.float32),
                    "volume_change_pct": float(vol_change_pct),
                    "malignancy_delta": float(malignancy_delta),
                    "invasion_class": int(invasion_class),
                    "future_volume_mm3": float(vol_1),
                    "future_malignancy": float(y_snap.malignancy_probability),
                })

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        X = torch.tensor(sample["X"], dtype=torch.float32)

        if self.augment:
            X = X + torch.randn_like(X) * 0.01   # small Gaussian noise

        return {
            "X": X,
            "volume_change_pct": torch.tensor(sample["volume_change_pct"], dtype=torch.float32),
            "malignancy_delta": torch.tensor(sample["malignancy_delta"], dtype=torch.float32),
            "invasion_class": torch.tensor(sample["invasion_class"], dtype=torch.long),
            "future_volume_mm3": torch.tensor(sample["future_volume_mm3"], dtype=torch.float32),
            "future_malignancy": torch.tensor(sample["future_malignancy"], dtype=torch.float32),
        }
