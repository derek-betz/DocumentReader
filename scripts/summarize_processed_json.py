import json
import re
import sys
from collections import Counter
from pathlib import Path


def _uniq(seq):
    seen = set()
    out = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/summarize_processed_json.py <path-to-json>")
        return 2

    json_path = Path(sys.argv[1])
    if not json_path.exists():
        print(f"File not found: {json_path}")
        return 2

    obj = json.loads(json_path.read_text(encoding="utf-8", errors="ignore"))

    pages = obj.get("pages") or []
    ocr = obj.get("ocr_text") or ""
    indot = obj.get("indot_sheet_info") or {}
    eng = obj.get("engineering_data") or {}

    print("== Summary ==")
    print("Top-level keys:", ", ".join(sorted(obj.keys())))
    print("Pages:", len(pages))
    if indot:
        print("Sheet type (guess):", indot.get("sheet_type"), "confidence:", indot.get("confidence"))
        for k in ("sheet_number", "project_number", "sheet_title"):
            if indot.get(k):
                print(f"{k}:", indot.get(k))

    print("OCR length:", len(ocr))

    # Pull common roadway-plan tokens
    patterns = {
        "routes": r"\b(?:SR|US|I)\s*[- ]?\d{1,4}\b",
        "stationing": r"\b\d{1,3}\+\d{2}\b",
        "elevations": r"\bEL\.?\s*[-+]?\d{2,4}(?:\.\d{1,2})?\b",
        "pipe_sizes": r"\b\d{2,3}\s*(?:in\.|inch|\")\b",
    }

    print("\n== Detected tokens (from OCR) ==")
    for name, pat in patterns.items():
        hits = re.findall(pat, ocr, flags=re.IGNORECASE)
        hits = [h.strip() for h in hits if h and h.strip()]
        if not hits:
            print(f"{name}: (none)")
            continue
        c = Counter(hits)
        common = [f"{k} ({v})" for k, v in c.most_common(10)]
        print(f"{name}:", ", ".join(common))

    meas = eng.get("measurements") or []
    meas_vals = [m.get("value") for m in meas if isinstance(m, dict) and m.get("value")]
    print("\n== Measurements ==")
    print("Count:", len(meas_vals))
    if meas_vals:
        print("Sample:", ", ".join(_uniq(meas_vals)[:20]))

    # Page-level hints
    print("\n== Page-level hints ==")
    page_ocr_lengths = []
    for p in pages:
        if isinstance(p, dict):
            t = p.get("ocr_text")
            if isinstance(t, str):
                page_ocr_lengths.append(len(t))
    if page_ocr_lengths:
        print("OCR chars per page: min/avg/max =",
              min(page_ocr_lengths),
              sum(page_ocr_lengths)//len(page_ocr_lengths),
              max(page_ocr_lengths))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
