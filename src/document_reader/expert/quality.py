"""
Quality metrics for document images.
"""

from pathlib import Path
from typing import Dict, Union

import cv2
import numpy as np

from .contracts import QualityMetrics


def compute_quality(image_path: Union[str, Path], config: Dict) -> QualityMetrics:
    image_path = Path(image_path)
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape[:2]

    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    contrast_score = float(np.std(gray))
    mean_brightness = float(np.mean(gray))

    skew_angle = _estimate_skew_angle(gray, config)

    flags = []
    if blur_score < float(config.get("blur_threshold", 100.0)):
        flags.append("low_sharpness")
    if contrast_score < float(config.get("contrast_threshold", 25.0)):
        flags.append("low_contrast")
    if abs(skew_angle) > float(config.get("skew_threshold", 1.5)):
        flags.append("skewed")
    if mean_brightness < float(config.get("brightness_min", 50.0)):
        flags.append("dark")
    if mean_brightness > float(config.get("brightness_max", 200.0)):
        flags.append("bright")

    return QualityMetrics(
        width=width,
        height=height,
        blur_score=blur_score,
        contrast_score=contrast_score,
        skew_angle=skew_angle,
        mean_brightness=mean_brightness,
        flags=flags,
    )


def _estimate_skew_angle(gray, config: Dict) -> float:
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    threshold = int(config.get("hough_threshold", 200))
    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold)
    if lines is None:
        return 0.0

    angles = []
    for rho, theta in lines[:, 0]:
        angles.append(np.degrees(theta) - 90)

    if not angles:
        return 0.0

    return float(np.median(angles))
