# Progress Notes

## 2026-01-10
- Added table extraction that returns structured rows/cells, grid lines, and counts.
- Wired table extraction into the expert pipeline and engineering-plan output.
- Added table extraction tests and updated document processor tests.
- Added table extractor configuration defaults and filters for empty tables.
- Ran `python -m pytest` (pass); `black`, `flake8`, and `mypy` not installed in the env.
- End-to-end check on `summary_tables_sample.pdf` (pages 78-79): 1 populated table extracted and 1 empty table filtered out.
- Installed Tesseract OCR (UB-Mannheim) locally; note this is not tracked in git.

### Next focus
- Run full 128-page plan set and capture which summary tables extract cleanly.
- Tune table extraction thresholds (line scale, min cell size) based on target sheets.
- Map key summary table rows into quantities for downstream estimation.
