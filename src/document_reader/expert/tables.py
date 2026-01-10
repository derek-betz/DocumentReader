"""
Table detection and extraction using line morphology.
"""

from __future__ import annotations

from bisect import bisect_right
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import cv2
import numpy as np

from .contracts import BoundingBox, TableCell, TableRegion


def detect_tables(
    image_path: Union[str, Path],
    page_number: int,
    config: Dict,
) -> List[TableRegion]:
    image_path = Path(image_path)
    image = cv2.imread(str(image_path))
    if image is None:
        return []
    return _detect_tables_from_image(image, page_number, config)


def extract_tables(
    image_path: Union[str, Path],
    page_number: int,
    config: Dict,
    ocr_data: Optional[Any] = None,
) -> List[TableRegion]:
    image_path = Path(image_path)
    image = cv2.imread(str(image_path))
    if image is None:
        return []

    tables = _detect_tables_from_image(image, page_number, config)
    if not tables or not bool(config.get("extract_content", True)):
        return tables

    ocr_words = _normalize_ocr_data(ocr_data)
    min_words = int(config.get("min_words_in_table", 5))
    if ocr_words and min_words > 0:
        tables = [
            table
            for table in tables
            if _count_words_in_bbox(table.bbox, ocr_words) >= min_words
        ]
    for table in tables:
        _populate_table_content(image, table, ocr_words, config)

    min_filled_cells = int(config.get("min_filled_cells", 1))
    if min_filled_cells > 0:
        tables = [
            table for table in tables if _count_filled_cells(table) >= min_filled_cells
        ]

    return tables


def _detect_tables_from_image(
    image: np.ndarray,
    page_number: int,
    config: Dict,
) -> List[TableRegion]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    binary = _binarize(gray, config)

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


def _binarize(gray: np.ndarray, config: Dict) -> np.ndarray:
    method = str(config.get("binarize_method", "otsu")).lower()
    if method == "adaptive":
        block_size = int(config.get("adaptive_block_size", 21))
        if block_size % 2 == 0:
            block_size += 1
        c_value = int(config.get("adaptive_c", 5))
        return cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY_INV,
            block_size,
            c_value,
        )

    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return binary


def _populate_table_content(
    image: np.ndarray,
    table: TableRegion,
    ocr_words: List[Dict[str, Any]],
    config: Dict,
) -> None:
    x1, y1, x2, y2 = (
        table.bbox.x1,
        table.bbox.y1,
        table.bbox.x2,
        table.bbox.y2,
    )
    roi = image[y1:y2, x1:x2]
    if roi.size == 0:
        return

    row_lines, col_lines = _extract_grid_lines(roi, config)
    if not row_lines or not col_lines:
        return

    row_lines = _ensure_boundaries(row_lines, roi.shape[0], int(config.get("line_merge_tolerance", 6)))
    col_lines = _ensure_boundaries(col_lines, roi.shape[1], int(config.get("line_merge_tolerance", 6)))

    row_lines = _filter_small_gaps(row_lines, int(config.get("min_cell_size", 12)))
    col_lines = _filter_small_gaps(col_lines, int(config.get("min_cell_size", 12)))

    if len(row_lines) < 2 or len(col_lines) < 2:
        return

    row_lines_page = [y1 + value for value in row_lines]
    col_lines_page = [x1 + value for value in col_lines]

    cells, rows = _assign_words_to_cells(
        row_lines_page,
        col_lines_page,
        ocr_words,
        config,
    )

    table.row_count = max(0, len(row_lines) - 1)
    table.column_count = max(0, len(col_lines) - 1)
    table.grid = {"rows": row_lines_page, "columns": col_lines_page}
    table.cells = cells
    table.rows = rows


def _extract_grid_lines(roi: np.ndarray, config: Dict) -> Tuple[List[int], List[int]]:
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    binary = _binarize(gray, config)
    height, width = gray.shape[:2]

    line_scale = int(config.get("line_scale", 40))
    min_length_ratio = float(config.get("min_line_length_ratio", 0.4))

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

    min_h_len = max(10, int(width * min_length_ratio))
    min_v_len = max(10, int(height * min_length_ratio))
    merge_tolerance = int(config.get("line_merge_tolerance", 6))

    row_lines = _extract_line_positions(horizontal, min_h_len, axis="y", tolerance=merge_tolerance)
    col_lines = _extract_line_positions(vertical, min_v_len, axis="x", tolerance=merge_tolerance)

    return row_lines, col_lines


def _extract_line_positions(
    mask: np.ndarray,
    min_length: int,
    *,
    axis: str,
    tolerance: int,
) -> List[int]:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    positions: List[int] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if axis == "y":
            if w < min_length:
                continue
            positions.append(int(y + h / 2))
        else:
            if h < min_length:
                continue
            positions.append(int(x + w / 2))

    return _merge_positions(positions, tolerance)


def _merge_positions(values: Iterable[int], tolerance: int) -> List[int]:
    sorted_values = sorted(int(v) for v in values)
    if not sorted_values:
        return []

    merged: List[int] = []
    cluster: List[int] = [sorted_values[0]]

    for value in sorted_values[1:]:
        if value - cluster[-1] <= tolerance:
            cluster.append(value)
        else:
            merged.append(int(round(sum(cluster) / len(cluster))))
            cluster = [value]

    if cluster:
        merged.append(int(round(sum(cluster) / len(cluster))))

    return merged


def _ensure_boundaries(values: List[int], max_value: int, tolerance: int) -> List[int]:
    if not values:
        return [0, max_value]

    values = sorted(values)
    if abs(values[0]) > tolerance:
        values.insert(0, 0)
    if abs(values[-1] - max_value) > tolerance:
        values.append(max_value)

    return values


def _filter_small_gaps(values: List[int], min_gap: int) -> List[int]:
    if len(values) < 2:
        return values

    filtered = [values[0]]
    for value in values[1:]:
        if value - filtered[-1] < min_gap:
            filtered[-1] = int(round((filtered[-1] + value) / 2))
        else:
            filtered.append(value)
    return filtered


def _assign_words_to_cells(
    row_lines: List[int],
    col_lines: List[int],
    ocr_words: List[Dict[str, Any]],
    config: Dict,
) -> Tuple[List[TableCell], List[List[str]]]:
    row_count = max(0, len(row_lines) - 1)
    col_count = max(0, len(col_lines) - 1)
    rows: List[List[str]] = [["" for _ in range(col_count)] for _ in range(row_count)]
    cell_words: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}

    for word in ocr_words:
        bbox = word.get("bbox")
        if not bbox:
            continue
        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        row_idx = _find_interval(row_lines, cy)
        col_idx = _find_interval(col_lines, cx)
        if row_idx is None or col_idx is None:
            continue
        cell_words.setdefault((row_idx, col_idx), []).append(word)

    cells: List[TableCell] = []
    padding = int(config.get("cell_padding", 2))

    for row_idx in range(row_count):
        for col_idx in range(col_count):
            x1 = col_lines[col_idx] + padding
            y1 = row_lines[row_idx] + padding
            x2 = col_lines[col_idx + 1] - padding
            y2 = row_lines[row_idx + 1] - padding
            words = cell_words.get((row_idx, col_idx), [])
            words.sort(key=lambda w: (w["bbox"][1], w["bbox"][0]))

            text = " ".join(w["text"] for w in words).strip()
            rows[row_idx][col_idx] = text

            confidences = [w.get("confidence") for w in words if w.get("confidence") is not None]
            confidence = None
            if confidences:
                confidence = float(sum(confidences) / len(confidences))

            cells.append(
                TableCell(
                    row=row_idx,
                    col=col_idx,
                    text=text,
                    bbox=BoundingBox(x1=int(x1), y1=int(y1), x2=int(x2), y2=int(y2)),
                    confidence=confidence,
                )
            )

    return cells, rows


def _find_interval(values: List[int], target: float) -> Optional[int]:
    idx = bisect_right(values, target) - 1
    if idx < 0 or idx >= len(values) - 1:
        return None
    return idx


def _normalize_ocr_data(ocr_data: Optional[Any]) -> List[Dict[str, Any]]:
    if ocr_data is None:
        return []

    if isinstance(ocr_data, list):
        normalized: List[Dict[str, Any]] = []
        for item in ocr_data:
            text = str(item.get("text", "")).strip()
            if not text:
                continue
            bbox = item.get("bbox")
            if not bbox:
                continue
            if len(bbox) == 4 and isinstance(bbox[0], (list, tuple)):
                xs = [point[0] for point in bbox]
                ys = [point[1] for point in bbox]
                bbox = [min(xs), min(ys), max(xs), max(ys)]
            if len(bbox) != 4:
                continue
            normalized.append(
                {
                    "text": text,
                    "bbox": [int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])],
                    "confidence": item.get("confidence"),
                }
            )
        return normalized

    if isinstance(ocr_data, dict) and "text" in ocr_data:
        normalized = []
        texts = ocr_data.get("text", [])
        lefts = ocr_data.get("left", [])
        tops = ocr_data.get("top", [])
        widths = ocr_data.get("width", [])
        heights = ocr_data.get("height", [])
        confs = ocr_data.get("conf", [])

        for idx, raw_text in enumerate(texts):
            text = str(raw_text).strip()
            if not text:
                continue
            x = int(lefts[idx]) if idx < len(lefts) else 0
            y = int(tops[idx]) if idx < len(tops) else 0
            w = int(widths[idx]) if idx < len(widths) else 0
            h = int(heights[idx]) if idx < len(heights) else 0
            bbox = [x, y, x + w, y + h]
            conf = None
            if idx < len(confs):
                raw_conf = confs[idx]
                try:
                    conf = float(raw_conf)
                except (TypeError, ValueError):
                    conf = None
                if conf is not None and conf < 0:
                    conf = None
            normalized.append({"text": text, "bbox": bbox, "confidence": conf})
        return normalized

    return []


def _count_words_in_bbox(bbox: BoundingBox, words: List[Dict[str, Any]]) -> int:
    count = 0
    for word in words:
        coords = word.get("bbox")
        if not coords:
            continue
        x1, y1, x2, y2 = coords
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        if bbox.x1 <= cx <= bbox.x2 and bbox.y1 <= cy <= bbox.y2:
            count += 1
    return count


def _count_filled_cells(table: TableRegion) -> int:
    return sum(1 for cell in table.cells if cell.text.strip())
