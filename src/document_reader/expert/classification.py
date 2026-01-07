"""
Heuristic document type classification.
"""

import re
from typing import Dict

from .contracts import DocumentTypeResult


_TYPE_PATTERNS = {
    "engineering_plan": [
        r"\bPLAN\s+AND\s+PROFILE\b",
        r"\bCROSS[-\s]?SECTION\b",
        r"\bSHEET\b",
        r"\bSTA(?:TION)?\.?\b",
        r"\bSCALE\b",
    ],
    "construction_detail": [
        r"\bDETAIL\b",
        r"\bELEVATION\b",
        r"\bSECTION\b",
        r"\bNOTES\b",
    ],
    "invoice": [
        r"\bINVOICE\b",
        r"\bBILL\s+TO\b",
        r"\bSUBTOTAL\b",
        r"\bTOTAL\b",
        r"\bDUE\s+DATE\b",
    ],
    "receipt": [
        r"\bRECEIPT\b",
        r"\bTOTAL\b",
        r"\bCARD\b",
        r"\bCASH\b",
    ],
    "form": [
        r"\bFORM\b",
        r"\bSIGNATURE\b",
        r"\bDATE\b",
        r"\bCHECKBOX\b",
    ],
    "letter": [
        r"\bDEAR\b",
        r"\bSINCERELY\b",
        r"\bREGARDS\b",
        r"\bSUBJECT\b",
    ],
    "report": [
        r"\bEXECUTIVE\s+SUMMARY\b",
        r"\bFINDINGS\b",
        r"\bRESULTS\b",
        r"\bCONCLUSION\b",
    ],
}


def classify_document(text: str) -> DocumentTypeResult:
    if not text:
        return DocumentTypeResult()

    text_upper = text.upper()
    scores: Dict[str, float] = {}

    for doc_type, patterns in _TYPE_PATTERNS.items():
        matches = 0
        for pattern in patterns:
            if re.search(pattern, text_upper):
                matches += 1
        if matches:
            scores[doc_type] = matches / float(len(patterns))

    if not scores:
        return DocumentTypeResult()

    best_type = max(scores, key=scores.get)
    return DocumentTypeResult(
        type=best_type,
        confidence=float(scores[best_type]),
        candidates=scores,
    )
