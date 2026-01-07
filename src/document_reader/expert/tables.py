"""
Table detection using line morphology.
"""

from pathlib import Path
from typing import Dict, List, Union

import cv2

from .contracts import BoundingBox, TableRegion


def detect_tables(
    image_path: Union[str, Path],
    page_number: int,
    config: Dict,
) -> List[TableRegion]:
    image_path = Path(image_path)
    image = cv2.imread(str(image_path))
    if image is None:
        return []

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    height, width = gray.shape[:2]
    line_scale = int(config.get("line_scale", 40))
    min_table_area_ratio = float(config.get("min_table_area_ratio", 0.01))

    h_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT, (max(10, width // line_scale), 1)
    )
    v_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT, (1, max(10, height // line_scale))
    )

    horizontal = cv2.erode(binary, h_kernel, iterations=1)
    horizontal = cv2.dilate(horizontal, h_kernel, iterations=1)

    vertical = cv2.erode(binary, v_kernel, iterations=1)
    vertical = cv2.dilate(vertical, v_kernel, iterations=1)

    table_mask = cv2.add(horizontal, vertical)
    contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_area = (width * height) * min_table_area_ratio
    tables: List[TableRegion] = []

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        if area < min_area or w < 40 or h < 40:
            continue

        tables.append(
            TableRegion(
                page_number=page_number,
                bbox=BoundingBox(x1=int(x), y1=int(y), x2=int(x + w), y2=int(y + h)),
                confidence=None,
                method="opencv_lines",
            )
        )

    return tables
