"""
Robust Wikidata client for QID resolution and field extraction.
"""

from typing import Any, Dict, Optional
from urllib.parse import quote

import requests

from field_registry import BASE_COLUMNS


FIELD_ORIGINAL_TITLE = BASE_COLUMNS[2]
FIELD_COUNTRY_TRADITION = BASE_COLUMNS[4]
FIELD_PUBLICATION_YEAR = BASE_COLUMNS[5]


def _claim_datavalue(claim: Dict[str, Any]) -> Any:
    return claim.get("mainsnak", {}).get("datavalue", {}).get("value")


def _claim_string(claim: Dict[str, Any]) -> Optional[str]:
    value = _claim_datavalue(claim)
    if isinstance(value, dict):
        text = value.get("text")
        if text:
            return str(text).strip()
    if isinstance(value, (str, int, float)):
        return str(value).strip()
    return None


def _year_from_time(time_value: str) -> Optional[str]:
    if not time_value:
        return None
    raw = str(time_value).strip()
    if raw.startswith("+"):
        raw = raw[1:]
    year_part = raw.split("-", 1)[0]
    try:
        year = int(year_part)
    except Exception:
        return None
    if 1000 <= year <= 3000:
        return str(year)
    return None


def _claim_entity_id(claim: Dict[str, Any]) -> Optional[str]:
    value = _claim_datavalue(claim)
    if isinstance(value, dict):
        entity_id = value.get("id")
        if entity_id:
            return str(entity_id)
        numeric = value.get("numeric-id")
        if numeric is not None:
            return f"Q{numeric}"
    return None


def _pick_label(entity: Dict[str, Any], preferred: tuple[str, ...] = ("tr", "en", "ru")) -> str:
    labels = entity.get("labels", {})
    for lang in preferred:
        val = labels.get(lang, {}).get("value")
        if val:
            return str(val).strip()
    for entry in labels.values():
        val = entry.get("value")
        if val:
            return str(val).strip()
    return ""


def qid_from_wikipedia(title: str, lang: str = "en") -> Optional[str]:
    page_title = str(title or "").strip()
    if not page_title:
        return None

    try:
        summary_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{quote(page_title, safe='')}"
        resp = requests.get(summary_url, timeout=10)
        if resp.status_code == 200:
            qid = resp.json().get("wikibase_item")
            if qid:
                return str(qid)
    except Exception:
        pass

    # Fallback: MediaWiki pageprops
    try:
        api_url = f"https://{lang}.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "prop": "pageprops",
            "ppprop": "wikibase_item",
            "titles": page_title,
        }
        resp = requests.get(api_url, params=params, timeout=10)
        if resp.status_code != 200:
            return None
        pages = resp.json().get("query", {}).get("pages", {})
        for page in pages.values():
            qid = page.get("pageprops", {}).get("wikibase_item")
            if qid:
                return str(qid)
    except Exception:
        pass

    return None


def fetch_entity(qid: str) -> Optional[Dict[str, Any]]:
    try:
        url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception:
        return None


def _resolve_entity_label(entity_id: str) -> str:
    data = fetch_entity(entity_id)
    if not data:
        return ""
    entities = data.get("entities", {})
    entity = entities.get(entity_id, {})
    return _pick_label(entity)


def extract_fields(entity_json: Dict[str, Any]) -> Dict[str, str]:
    """
    Extracts normalized fields from Wikidata entity payload.
    """
    result: Dict[str, str] = {}
    if not entity_json:
        return result

    entities = entity_json.get("entities", {})
    qid = next(iter(entities.keys()), None)
    if not qid:
        return result

    entity = entities.get(qid, {})
    claims = entity.get("claims", {})

    # P577 publication date: choose earliest sane year.
    years: list[int] = []
    for claim in claims.get("P577", []):
        value = _claim_datavalue(claim)
        if not isinstance(value, dict):
            continue
        year_str = _year_from_time(value.get("time", ""))
        if not year_str:
            continue
        try:
            years.append(int(year_str))
        except Exception:
            pass
    if years:
        result[FIELD_PUBLICATION_YEAR] = str(min(years))

    # Original title fallbacks: P1476, P1705, P1680, P1813 then entity labels.
    for prop in ("P1476", "P1705", "P1680", "P1813"):
        for claim in claims.get(prop, []):
            text = _claim_string(claim)
            if text:
                result[FIELD_ORIGINAL_TITLE] = text
                break
        if result.get(FIELD_ORIGINAL_TITLE):
            break
    if not result.get(FIELD_ORIGINAL_TITLE):
        label = _pick_label(entity, preferred=("ru", "en", "tr"))
        if label:
            result[FIELD_ORIGINAL_TITLE] = label

    # Country/tradition fallbacks: P495 (country of origin) then P17 (country).
    for prop in ("P495", "P17"):
        ids = [_claim_entity_id(c) for c in claims.get(prop, [])]
        entity_id = next((x for x in ids if x), None)
        if not entity_id:
            continue
        label = _resolve_entity_label(entity_id)
        if label:
            result[FIELD_COUNTRY_TRADITION] = label
            break

    return result
