"""
Image preprocessing for OCR and layout analysis.
"""

from pathlib import Path
from typing import Dict, List, Tuple, Union

from ..utils.image_utils import (
    enhance_image_for_ocr,
    deskew_image,
    binarize_image,
    remove_noise,
)


def preprocess_image(
    image_path: Union[str, Path],
    output_dir: Union[str, Path],
    config: Dict,
) -> Tuple[Path, List[str]]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    current = Path(image_path)
    steps: List[str] = []
    base = current.stem

    if config.get("enhance", True):
        enhanced = output_dir / f"{base}_enhanced.png"
        enhance_image_for_ocr(current, enhanced)
        current = enhanced
        steps.append("enhance")

    if config.get("denoise", True):
        denoised = output_dir / f"{base}_denoised.png"
        remove_noise(current, denoised)
        current = denoised
        steps.append("denoise")

    if config.get("deskew", True):
        deskewed = output_dir / f"{base}_deskewed.png"
        deskew_image(current, deskewed)
        current = deskewed
        steps.append("deskew")

    if config.get("binarize", False):
        binarized = output_dir / f"{base}_binarized.png"
        binarize_image(current, binarized)
        current = binarized
        steps.append("binarize")

    return current, steps
