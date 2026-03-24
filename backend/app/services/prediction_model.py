"""
Module 5 — LSTM & Transformer Time-Series Models
Multi-output models predicting:
  1. Volume change % (regression)
  2. Malignancy probability delta (regression)
  3. Invasion speed class (classification: slow/medium/fast)
"""
import torch
import torch.nn as nn
import math
from typing import Tuple


# ─── LSTM Model ───────────────────────────────────────────────────────────

class TumorLSTM(nn.Module):
    """
    Bidirectional LSTM for tumor progression prediction.
    Input:  (batch, seq_len, feature_dim)
    Output: dict of {volume_change, malignancy_delta, invasion_class}
    """

    def __init__(
        self,
        feature_dim: int = 57,    # 7 core + 50 radiomics
        hidden_dim: int = 256,
        num_layers: int = 3,
        dropout: float = 0.3,
    ):
        super().__init__()

        self.feature_norm = nn.LayerNorm(feature_dim)

        self.lstm = nn.LSTM(
            input_size=feature_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0,
        )

        lstm_out_dim = hidden_dim * 2  # bidirectional

        # Shared feature extractor
        self.shared_head = nn.Sequential(
            nn.Linear(lstm_out_dim, 256),
            nn.LayerNorm(256),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(256, 128),
            nn.GELU(),
            nn.Dropout(dropout * 0.5),
        )

        # Task-specific heads
        self.volume_head = nn.Linear(128, 1)           # regression
        self.malignancy_head = nn.Linear(128, 1)       # regression
        self.invasion_head = nn.Linear(128, 3)         # 3-class classification

    def forward(self, x: torch.Tensor) -> dict:
        """
        Args:
            x: (B, T, F) — batch of temporal sequences
        Returns:
            dict of predictions
        """
        x = self.feature_norm(x)
        lstm_out, _ = self.lstm(x)          # (B, T, 2*H)
        last_step = lstm_out[:, -1, :]      # (B, 2*H) — take last timestep

        shared = self.shared_head(last_step)

        return {
            "volume_change_pct": self.volume_head(shared).squeeze(-1),     # (B,)
            "malignancy_delta": self.malignancy_head(shared).squeeze(-1),  # (B,)
            "invasion_logits": self.invasion_head(shared),                  # (B, 3)
        }


# ─── Transformer Model ────────────────────────────────────────────────────

class PositionalEncoding(nn.Module):
    """Standard sinusoidal positional encoding."""

    def __init__(self, d_model: int, max_len: int = 50, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # (1, max_len, d_model)
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class TumorTransformer(nn.Module):
    """
    Transformer encoder for tumor time-series prediction.
    Uses multi-head self-attention across temporal steps.
    Input:  (batch, seq_len, feature_dim)
    Output: dict of predictions
    """

    def __init__(
        self,
        feature_dim: int = 57,
        d_model: int = 256,
        nhead: int = 8,
        num_layers: int = 4,
        dim_feedforward: int = 512,
        dropout: float = 0.2,
    ):
        super().__init__()

        self.input_proj = nn.Linear(feature_dim, d_model)
        self.pos_encoder = PositionalEncoding(d_model, dropout=dropout)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
            norm_first=True,    # Pre-LN for training stability
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.norm = nn.LayerNorm(d_model)

        # Prediction heads
        self.shared_head = nn.Sequential(
            nn.Linear(d_model, 128),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.volume_head = nn.Linear(128, 1)
        self.malignancy_head = nn.Linear(128, 1)
        self.invasion_head = nn.Linear(128, 3)

    def forward(self, x: torch.Tensor) -> dict:
        """
        Args:
            x: (B, T, F) — batch of temporal sequences
        """
        x = self.input_proj(x)          # (B, T, d_model)
        x = self.pos_encoder(x)
        x = self.transformer(x)         # (B, T, d_model)
        x = self.norm(x)

        # Aggregate: mean pooling over temporal dim
        x_agg = x.mean(dim=1)           # (B, d_model)
        shared = self.shared_head(x_agg)

        return {
            "volume_change_pct": self.volume_head(shared).squeeze(-1),
            "malignancy_delta": self.malignancy_head(shared).squeeze(-1),
            "invasion_logits": self.invasion_head(shared),
        }


# ─── Factory ─────────────────────────────────────────────────────────────

def build_prediction_model(
    variant: str = "lstm",
    feature_dim: int = 57,
    device: torch.device = None,
) -> nn.Module:
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if variant == "lstm":
        model = TumorLSTM(feature_dim=feature_dim)
    elif variant == "transformer":
        model = TumorTransformer(feature_dim=feature_dim)
    else:
        model = TumorLSTM(feature_dim=feature_dim)

    return model.to(device)


# ─── Multi-task Loss ────────────────────────────────────────────────────

class ProgressionLoss(nn.Module):
    """
    Combined loss for multi-output progression prediction.
    Weights: volume(0.4) + malignancy(0.3) + invasion(0.3)
    """

    def __init__(self, w_vol=0.4, w_mal=0.3, w_inv=0.3):
        super().__init__()
        self.vol_loss = nn.HuberLoss()           # robust regression
        self.mal_loss = nn.HuberLoss()
        self.inv_loss = nn.CrossEntropyLoss()
        self.w = (w_vol, w_mal, w_inv)

    def forward(self, preds: dict, targets: dict) -> Tuple[torch.Tensor, dict]:
        l_vol = self.vol_loss(preds["volume_change_pct"], targets["volume_change_pct"])
        l_mal = self.mal_loss(preds["malignancy_delta"], targets["malignancy_delta"])
        l_inv = self.inv_loss(preds["invasion_logits"], targets["invasion_class"])

        total = self.w[0] * l_vol + self.w[1] * l_mal + self.w[2] * l_inv
        return total, {"vol": l_vol.item(), "mal": l_mal.item(), "inv": l_inv.item()}
