"""
Module 1 — 3D U-Net Model (MONAI)
Uses MONAI's built-in UNet with configurable depth for tumor segmentation.
"""
import torch
import torch.nn as nn
from monai.networks.nets import UNet, SegResNet, SwinUNETR
from monai.networks.layers import Norm
from typing import Literal


ModelVariant = Literal["unet3d", "segresnet", "swinunetr"]


def build_segmentation_model(
    variant: ModelVariant = "unet3d",
    in_channels: int = 1,
    out_channels: int = 2,    # background + tumor
    device: torch.device = None,
) -> nn.Module:
    """
    Build the segmentation model.

    Args:
        variant: Model architecture — 'unet3d' | 'segresnet' | 'swinunetr'
        in_channels: Input image channels (1 for grayscale CT/MRI)
        out_channels: Number of segmentation classes (2 = background + tumor)
        device: Target device

    Returns:
        nn.Module ready for training or inference
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if variant == "unet3d":
        model = UNet(
            spatial_dims=3,
            in_channels=in_channels,
            out_channels=out_channels,
            channels=(16, 32, 64, 128, 256),
            strides=(2, 2, 2, 2),
            num_res_units=2,
            norm=Norm.BATCH,
            dropout=0.1,
        )

    elif variant == "segresnet":
        model = SegResNet(
            spatial_dims=3,
            in_channels=in_channels,
            out_channels=out_channels,
            init_filters=16,
        )

    elif variant == "swinunetr":
        model = SwinUNETR(
            img_size=(128, 128, 128),
            in_channels=in_channels,
            out_channels=out_channels,
            feature_size=48,
            use_checkpoint=True,
        )

    else:
        raise ValueError(f"Unknown model variant: {variant}")

    return model.to(device)


def load_model_weights(model: nn.Module, weights_path: str) -> nn.Module:
    """Load pretrained weights into model (GPU-safe)."""
    device = next(model.parameters()).device
    state_dict = torch.load(weights_path, map_location=device)
    # Handle DataParallel / DDP prefix
    state_dict = {k.replace("module.", ""): v for k, v in state_dict.items()}
    model.load_state_dict(state_dict, strict=False)
    model.eval()
    return model
