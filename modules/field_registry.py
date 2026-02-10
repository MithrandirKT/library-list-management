"""
Field registry for Excel schema and metadata columns.
Centralizes column names to keep Excel format stable.
"""

from typing import Dict, List

# Base data columns (order must remain stable)
# Sadece temel veri kolonları - meta ve provenance kolonları kaldırıldı
BASE_COLUMNS: List[str] = [
    "Kitap Adı",
    "Yazar",
    "Orijinal Adı",
    "Tür",
    "Ülke/Edebi Gelenek",
    "İlk Yayınlanma Tarihi",
    "Anlatı Yılı",
    "Konusu",
]

# Fields that will have src_/conf_ provenance columns
PROVENANCE_FIELDS: Dict[str, str] = {
    "Orijinal Adı": "orijinal_adi",
    "Tür": "tur",
    "Ülke/Edebi Gelenek": "ulke",
    "İlk Yayınlanma Tarihi": "cikis_yili",
    "Anlatı Yılı": "anlati_yili",
    "Konusu": "konusu",
}

# Row-level metadata columns (status/backoff/debug)
ROW_META_COLUMNS: List[str] = [
    "status",
    "missing_fields",
    "last_attempt_at",
    "retry_count",
    "next_retry_at",
    "best_source",
    "match_score",
    "wikidata_qid",
]


def build_provenance_columns() -> List[str]:
    cols: List[str] = []
    for _, key in PROVENANCE_FIELDS.items():
        cols.append(f"src_{key}")
        cols.append(f"conf_{key}")
    return cols


def standard_columns() -> List[str]:
    """
    Returns the Excel schema in stable order.
    Sadece temel veri kolonları - meta ve provenance kolonları kaldırıldı.
    """
    return BASE_COLUMNS


def ensure_row_schema(row: Dict[str, str]) -> Dict[str, str]:
    """
    Ensures all standard columns exist in the row.
    Missing columns are filled with empty strings.
    """
    cols = standard_columns()
    out = dict(row)
    for col in cols:
        if col not in out:
            out[col] = ""
    return out
