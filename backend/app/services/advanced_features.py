"""
Module 3 — Advanced Shape & Texture Feature Extractor
Computes features NOT in PyRadiomics:
  - Fractal Dimension (box-counting method)
  - Surface Gradient Distribution
  - Intensity Gradient Statistics
  - Asymmetry Index (3D moment-based)
  - Local Binary Pattern histogram (2D slices → aggregated 3D)
"""
import numpy as np
from scipy import ndimage
from typing import Tuple


# ─── Fractal Dimension ───────────────────────────────────────────────────

def compute_fractal_dimension(mask: np.ndarray) -> float:
    """
    Minkowski–Bouligand (box-counting) fractal dimension of a 3D binary mask.
    FD close to 3 = space-filling (solid tumor)
    FD close to 2 = surface-like (thin shell)
    FD ≈ 2.5 = complex irregular surface (malignant indicator)

    Args:
        mask: 3D binary numpy array (D, H, W)

    Returns:
        Fractal dimension as float
    """
    if mask.sum() == 0:
        return 0.0

    # Sizes for box-counting (powers of 2)
    sizes = [2, 4, 8, 16, 32]
    counts = []

    for size in sizes:
        # Coarsen the mask by dividing into boxes of `size`
        d = max(1, mask.shape[0] // size)
        h = max(1, mask.shape[1] // size)
        w = max(1, mask.shape[2] // size)

        # Block-reduce: check if any voxel in each box is 1
        count = 0
        for i in range(d):
            for j in range(h):
                for k in range(w):
                    block = mask[
                        i * size: (i + 1) * size,
                        j * size: (j + 1) * size,
                        k * size: (k + 1) * size,
                    ]
                    if block.any():
                        count += 1
        counts.append(count)

    # Log-log regression: FD = slope of log(count) vs log(1/size)
    log_sizes = np.log(1.0 / np.array(sizes, dtype=float))
    log_counts = np.log(np.array(counts, dtype=float) + 1e-8)

    coeffs = np.polyfit(log_sizes, log_counts, 1)
    return float(abs(coeffs[0]))


# ─── Gradient Features ────────────────────────────────────────────────────

def compute_gradient_features(image: np.ndarray, mask: np.ndarray) -> dict:
    """
    Gradient-based texture features inside the tumor region.

    Args:
        image: 3D float intensity volume (D, H, W)
        mask:  3D binary mask (D, H, W)

    Returns:
        dict of gradient statistics
    """
    # Compute 3D gradient magnitude
    gz = ndimage.sobel(image, axis=0)
    gy = ndimage.sobel(image, axis=1)
    gx = ndimage.sobel(image, axis=2)
    magnitude = np.sqrt(gz**2 + gy**2 + gx**2)

    # Extract inside tumor
    tumor_grad = magnitude[mask.astype(bool)]
    if len(tumor_grad) == 0:
        return {
            "gradient_mean": 0.0,
            "gradient_std": 0.0,
            "gradient_max": 0.0,
            "gradient_entropy": 0.0,
            "gradient_kurtosis": 0.0,
        }

    from scipy.stats import kurtosis, entropy
    hist, _ = np.histogram(tumor_grad, bins=64, density=True)
    hist = hist + 1e-10  # avoid log(0)

    return {
        "gradient_mean": float(tumor_grad.mean()),
        "gradient_std": float(tumor_grad.std()),
        "gradient_max": float(tumor_grad.max()),
        "gradient_entropy": float(entropy(hist)),
        "gradient_kurtosis": float(kurtosis(tumor_grad)),
    }


# ─── Asymmetry Index ─────────────────────────────────────────────────────

def compute_asymmetry_index(mask: np.ndarray) -> float:
    """
    3D Asymmetry Index based on second-order moments.
    Compares the mask against its mirror (flip along each axis).
    Higher value = more asymmetric = malignant indicator.

    Returns: float in [0, 1]
    """
    if mask.sum() == 0:
        return 0.0

    total = float(mask.sum())
    scores = []

    for axis in range(3):
        flipped = np.flip(mask, axis=axis)
        intersection = np.logical_and(mask, flipped).sum()
        union = np.logical_or(mask, flipped).sum()
        if union > 0:
            jaccard = intersection / union
            scores.append(1.0 - jaccard)  # asymmetry = 1 - similarity

    return float(np.mean(scores)) if scores else 0.0


# ─── Intensity Features ───────────────────────────────────────────────────

def compute_intensity_features(image: np.ndarray, mask: np.ndarray) -> dict:
    """
    Statistical intensity features inside the tumor mask.

    Args:
        image: 3D float intensity array
        mask:  3D binary mask

    Returns:
        dict of intensity statistics
    """
    from scipy.stats import skew, kurtosis
    tumor_intensities = image[mask.astype(bool)]

    if len(tumor_intensities) == 0:
        return {}

    return {
        "intensity_mean": float(tumor_intensities.mean()),
        "intensity_std": float(tumor_intensities.std()),
        "intensity_min": float(tumor_intensities.min()),
        "intensity_max": float(tumor_intensities.max()),
        "intensity_skewness": float(skew(tumor_intensities)),
        "intensity_kurtosis": float(kurtosis(tumor_intensities)),
        "intensity_range": float(tumor_intensities.max() - tumor_intensities.min()),
        "intensity_p10": float(np.percentile(tumor_intensities, 10)),
        "intensity_p90": float(np.percentile(tumor_intensities, 90)),
        "intensity_iqr": float(
            np.percentile(tumor_intensities, 75) - np.percentile(tumor_intensities, 25)
        ),
    }


# ─── Combined Feature Vector ──────────────────────────────────────────────

def extract_advanced_features(
    image: np.ndarray,
    mask: np.ndarray,
) -> dict:
    """
    Extract all advanced (non-radiomics) features.
    Returns a flat dict ready for JSON serialization and ML feature vectors.
    """
    features = {}

    # Fractal dimension
    features["fractal_dimension"] = compute_fractal_dimension(mask)

    # Asymmetry
    features["asymmetry_index"] = compute_asymmetry_index(mask)

    # Gradient stats
    grad = compute_gradient_features(image.astype(np.float32), mask)
    features.update(grad)

    # Intensity stats
    intensity = compute_intensity_features(image.astype(np.float32), mask)
    features.update(intensity)

    # Round all values
    return {k: round(float(v), 8) if v is not None else None for k, v in features.items()}
