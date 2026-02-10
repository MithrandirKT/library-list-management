"""
Helpers for provenance and row-level metadata.
"""

from typing import Dict, Iterable, List, Optional
from datetime import datetime, timedelta

from field_registry import PROVENANCE_FIELDS


def field_key(display_name: str) -> Optional[str]:
    return PROVENANCE_FIELDS.get(display_name)


def set_field(row: Dict[str, str], field_display: str, value: str, source: str, conf: float) -> None:
    row[field_display] = value
    key = field_key(field_display)
    if key:
        row[f"src_{key}"] = source
        row[f"conf_{key}"] = f"{conf:.2f}"


def set_row_status(
    row: Dict[str, str],
    status: str,
    missing_fields: Iterable[str],
    best_source: str = "",
    match_score: str = "",
    wikidata_qid: str = "",
    retry_count: Optional[int] = None,
    next_retry_hours: Optional[int] = None,
) -> None:
    row["status"] = status
    row["missing_fields"] = ";".join([f for f in missing_fields if f])
    row["best_source"] = best_source
    row["match_score"] = match_score
    row["wikidata_qid"] = wikidata_qid
    row["last_attempt_at"] = datetime.utcnow().isoformat()
    if retry_count is not None:
        row["retry_count"] = str(retry_count)
    if next_retry_hours is not None:
        row["next_retry_at"] = (datetime.utcnow() + timedelta(hours=next_retry_hours)).isoformat()
