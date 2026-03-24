"""
Module 1 — Training Script
Trains the 3D segmentation model using MONAI on BraTS/TCIA dataset.

Usage:
    python -m app.services.segmentation_train \
        --data_dir /path/to/dataset \
        --model unet3d \
        --loss dice_ce \
        --epochs 100 \
        --batch_size 2
"""
import os
import argparse
import torch
from torch.utils.data import DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from monai.data import Dataset, CacheDataset, decollate_batch
from monai.metrics import DiceMetric
from monai.transforms import AsDiscrete, Compose
import json
from pathlib import Path
from loguru import logger

from app.services.segmentation_model import build_segmentation_model
from app.services.loss_functions import get_loss_function
from app.services.dicom_preprocessor import get_monai_train_transforms, get_monai_transforms


def prepare_data_dicts(data_dir: str, split: float = 0.8) -> tuple:
    """
    Scan dataset directory for paired image/label NIfTI files.
    Expects structure: data_dir/images/*.nii.gz, data_dir/labels/*.nii.gz
    """
    images_dir = Path(data_dir) / "images"
    labels_dir = Path(data_dir) / "labels"

    images = sorted(images_dir.glob("*.nii*"))
    labels = sorted(labels_dir.glob("*.nii*"))

    assert len(images) == len(labels), f"Mismatch: {len(images)} images vs {len(labels)} labels"

    data_dicts = [{"image": str(img), "label": str(lbl)} for img, lbl in zip(images, labels)]

    split_idx = int(len(data_dicts) * split)
    return data_dicts[:split_idx], data_dicts[split_idx:]


def train(
    data_dir: str,
    model_variant: str = "unet3d",
    loss_type: str = "dice_ce",
    epochs: int = 100,
    batch_size: int = 2,
    lr: float = 1e-4,
    roi_size: tuple = (128, 128, 128),
    output_dir: str = "./models/weights",
):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Training on device: {device}")

    # Data
    train_dicts, val_dicts = prepare_data_dicts(data_dir)
    train_transforms = get_monai_train_transforms(roi_size=roi_size)
    val_transforms = get_monai_transforms(roi_size=roi_size)

    train_ds = CacheDataset(data=train_dicts, transform=train_transforms, cache_rate=0.5, num_workers=4)
    val_ds = CacheDataset(data=val_dicts, transform=val_transforms, cache_rate=1.0, num_workers=4)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=4, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=1, shuffle=False, num_workers=2)

    # Model, loss, optimizer
    model = build_segmentation_model(variant=model_variant, device=device)
    criterion = get_loss_function(loss_type)
    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=1e-5)
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)

    # Metrics
    dice_metric = DiceMetric(include_background=False, reduction="mean")
    post_pred = Compose([AsDiscrete(argmax=True, to_onehot=2)])
    post_label = Compose([AsDiscrete(to_onehot=2)])

    best_dice = 0.0
    history = {"train_loss": [], "val_dice": []}
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, epochs + 1):
        model.train()
        epoch_loss = 0.0

        for batch_idx, batch in enumerate(train_loader):
            images = batch["image"].to(device)
            labels = batch["label"].to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

        avg_loss = epoch_loss / len(train_loader)
        history["train_loss"].append(avg_loss)
        scheduler.step()

        # Validation every 5 epochs
        if epoch % 5 == 0:
            model.eval()
            dice_metric.reset()
            with torch.no_grad():
                for val_batch in val_loader:
                    val_images = val_batch["image"].to(device)
                    val_labels = val_batch["label"].to(device)
                    val_outputs = model(val_images)

                    val_outputs_list = decollate_batch(val_outputs)
                    val_labels_list = decollate_batch(val_labels)
                    val_preds = [post_pred(x) for x in val_outputs_list]
                    val_targets = [post_label(x) for x in val_labels_list]
                    dice_metric(y_pred=val_preds, y=val_targets)

            mean_dice = dice_metric.aggregate().item()
            history["val_dice"].append({"epoch": epoch, "dice": mean_dice})
            logger.info(f"[Epoch {epoch}/{epochs}] Loss: {avg_loss:.4f} | Val Dice: {mean_dice:.4f}")

            if mean_dice > best_dice:
                best_dice = mean_dice
                weights_path = str(output_path / "unet3d_best.pth")
                torch.save(model.state_dict(), weights_path)
                logger.info(f"  ✅ Best model saved: Dice={best_dice:.4f}")
        else:
            logger.info(f"[Epoch {epoch}/{epochs}] Loss: {avg_loss:.4f}")

    # Save training history
    with open(str(output_path / "training_history.json"), "w") as f:
        json.dump(history, f, indent=2)

    logger.info(f"Training complete. Best Dice: {best_dice:.4f}")
    return best_dice


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train 3D Tumor Segmentation Model")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to dataset directory")
    parser.add_argument("--model", type=str, default="unet3d", choices=["unet3d", "segresnet", "swinunetr"])
    parser.add_argument("--loss", type=str, default="dice_ce", choices=["dice", "dice_ce", "focal", "dice_focal"])
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch_size", type=int, default=2)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--output_dir", type=str, default="./models/weights")
    args = parser.parse_args()

    train(
        data_dir=args.data_dir,
        model_variant=args.model,
        loss_type=args.loss,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        output_dir=args.output_dir,
    )
