"""
Tests for table extraction logic.
"""

from pathlib import Path

from PIL import Image, ImageDraw

from src.document_reader.expert.tables import extract_tables


def _make_table_image(path: Path) -> None:
    width, height = 400, 200
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    for x in (0, width // 2, width - 1):
        draw.line([(x, 0), (x, height - 1)], fill="black", width=2)
    for y in (0, height // 2, height - 1):
        draw.line([(0, y), (width - 1, y)], fill="black", width=2)

    image.save(path)


def test_extract_tables_with_ocr_words(tmp_path: Path) -> None:
    image_path = tmp_path / "table.png"
    _make_table_image(image_path)

    ocr_words = [
        {"text": "ITEM", "bbox": [20, 20, 80, 40], "confidence": 90.0},
        {"text": "QTY", "bbox": [220, 20, 260, 40], "confidence": 88.0},
        {"text": "PIPE", "bbox": [20, 130, 80, 150], "confidence": 92.0},
        {"text": "5", "bbox": [220, 130, 230, 150], "confidence": 85.0},
    ]

    tables = extract_tables(
        image_path,
        page_number=1,
        config={"min_words_in_table": 0, "min_filled_cells": 0},
        ocr_data=ocr_words,
    )
    assert len(tables) == 1
    table = tables[0]

    assert table.row_count == 2
    assert table.column_count == 2
    assert table.rows[0][0] == "ITEM"
    assert table.rows[0][1] == "QTY"
    assert table.rows[1][0] == "PIPE"
    assert table.rows[1][1] == "5"
