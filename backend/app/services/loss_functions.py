"""
Module 1 — Loss Functions
Dice Loss, BCE+Dice Hybrid, and Focal Loss for 3D segmentation.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from monai.losses import DiceLoss, DiceCELoss, FocalLoss


def get_loss_function(loss_type: str = "dice_ce") -> nn.Module:
    """
    Return a MONAI loss function for segmentation.

    Args:
        loss_type: 'dice' | 'dice_ce' | 'focal' | 'dice_focal'

    Returns:
        nn.Module loss function
    """
    if loss_type == "dice":
        return DiceLoss(
            to_onehot_y=True,
            softmax=True,
            smooth_nr=1e-5,
            smooth_dr=1e-5,
        )

    elif loss_type == "dice_ce":
        return DiceCELoss(
            to_onehot_y=True,
            softmax=True,
            lambda_dice=0.5,
            lambda_ce=0.5,
        )

    elif loss_type == "focal":
        return FocalLoss(to_onehot_y=True, gamma=2.0, use_softmax=True)

    elif loss_type == "dice_focal":
        return _DiceFocalLoss()

    else:
        raise ValueError(f"Unknown loss type: {loss_type}")


class _DiceFocalLoss(nn.Module):
    """Combined Dice + Focal loss (equal weighting)."""

    def __init__(self, dice_weight: float = 0.5, focal_weight: float = 0.5):
        super().__init__()
        self.dice = DiceLoss(to_onehot_y=True, softmax=True, smooth_nr=1e-5, smooth_dr=1e-5)
        self.focal = FocalLoss(to_onehot_y=True, gamma=2.0, use_softmax=True)
        self.dice_w = dice_weight
        self.focal_w = focal_weight

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        return self.dice_w * self.dice(pred, target) + self.focal_w * self.focal(pred, target)
