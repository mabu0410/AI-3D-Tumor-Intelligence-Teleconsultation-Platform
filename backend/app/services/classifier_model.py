"""
Module 4 — 3D CNN Classifier
ResNet3D-based deep learning classifier for tumor malignancy.
Input: 3D volume patch (1, 128, 128, 128)
Output: [P(benign), P(malignant)]
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from monai.networks.nets import DenseNet121, ResNet, EfficientNetBN
from monai.networks.nets import resnet18, resnet50
from typing import Literal


ClassifierVariant = Literal["resnet3d_18", "resnet3d_50", "densenet3d", "custom_cnn"]


class TumorClassifier3D(nn.Module):
    """
    3D ResNet-based binary classifier.
    Accepts volumetric patches and outputs malignancy probability.
    """

    def __init__(self, num_classes: int = 2, dropout: float = 0.5):
        super().__init__()

        # MONAI ResNet18 backbone (3D, pretrained on medical images)
        self.backbone = resnet18(
            pretrained=False,
            spatial_dims=3,
            n_input_channels=1,
            num_classes=512,       # feature dim before head
        )

        # Remove final FC → replace with custom head
        self.backbone.fc = nn.Identity()

        # Classification head
        self.head = nn.Sequential(
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(dropout * 0.5),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, 1, D, H, W) normalized volume tensor
        Returns:
            (B, 2) logits — apply softmax for probabilities
        """
        features = self.backbone(x)     # (B, 512)
        logits = self.head(features)    # (B, 2)
        return logits

    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """Return softmax probabilities."""
        logits = self.forward(x)
        return F.softmax(logits, dim=1)


class DenseTumorClassifier3D(nn.Module):
    """
    DenseNet-121 3D variant for richer feature reuse (MONAI).
    Slightly more compute-heavy but better feature utilization.
    """

    def __init__(self, num_classes: int = 2):
        super().__init__()
        self.model = DenseNet121(
            spatial_dims=3,
            in_channels=1,
            out_channels=num_classes,
        )

    def forward(self, x):
        return self.model(x)

    def predict_proba(self, x):
        return F.softmax(self.forward(x), dim=1)


def build_classifier(
    variant: ClassifierVariant = "resnet3d_18",
    num_classes: int = 2,
    device: torch.device = None,
) -> nn.Module:
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if variant == "resnet3d_18":
        model = TumorClassifier3D(num_classes=num_classes)
    elif variant == "densenet3d":
        model = DenseTumorClassifier3D(num_classes=num_classes)
    else:
        model = TumorClassifier3D(num_classes=num_classes)

    return model.to(device)
