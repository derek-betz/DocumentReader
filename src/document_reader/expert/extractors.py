"""
Text-based extractors for document expert pipeline.
"""

import re
from typing import Dict, List

from .contracts import KeyValue, Measurement


def extract_measurements(text: str, page_number: int, patterns: List[str]) -> List[Measurement]:
    if not text:
        return []

    measurements: List[Measurement] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            measurements.append(
                Measurement(
                    page_number=page_number,
                    value=match.group(0),
                    span=list(match.span()),
                )
            )
    return measurements


def extract_key_values(text: str, page_number: int, config: Dict) -> List[KeyValue]:
    if not text:
        return []

    max_key_len = int(config.get("max_key_length", 48))
    max_value_len = int(config.get("max_value_length", 200))
    pattern = re.compile(r"^\s*([A-Za-z0-9 /_.()-]{2,}?)\s*[:=]\s*(.+)$")

    results: List[KeyValue] = []
    for line in text.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        key = match.group(1).strip()
        value = match.group(2).strip()
        if not key or not value:
            continue
        if len(key) > max_key_len or len(value) > max_value_len:
            continue
        results.append(KeyValue(page_number=page_number, key=key, value=value, line=line.strip()))

    return results
