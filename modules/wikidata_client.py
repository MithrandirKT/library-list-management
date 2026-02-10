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


def qid_from_sparql_search(book_title: str, author_name: str = "") -> Optional[str]:
    """
    SPARQL sorgusu ile Wikidata'da kitap QID'si bulur.
    Fallback yöntemi: Wikipedia'dan QID bulunamazsa kullanılır.
    """
    try:
        # SPARQL sorgusu: Kitap adı ve yazar adına göre arama
        # P31 = instance of, Q571 = book (literary work)
        # P50 = author
        # rdfs:label = label (kitap adı)
        
        # Kitap adını temizle (özel karakterleri escape et)
        book_title_clean = book_title.replace('"', '\\"').replace("'", "\\'")
        
        if author_name:
            # Yazar adı varsa, yazar filtresi ekle
            author_name_clean = author_name.replace('"', '\\"').replace("'", "\\'")
            query = f"""
            SELECT ?book WHERE {{
              ?book wdt:P31 wd:Q571.
              ?book rdfs:label ?label.
              ?book wdt:P50 ?author.
              ?author rdfs:label ?authorLabel.
              FILTER(LANG(?label) = "en" || LANG(?label) = "tr" || LANG(?label) = "ru").
              FILTER(LANG(?authorLabel) = "en" || LANG(?authorLabel) = "tr" || LANG(?authorLabel) = "ru").
              FILTER(CONTAINS(LCASE(?label), LCASE("{book_title_clean}"))).
              FILTER(CONTAINS(LCASE(?authorLabel), LCASE("{author_name_clean}"))).
            }}
            LIMIT 1
            """
        else:
            # Sadece kitap adı ile arama
            query = f"""
            SELECT ?book WHERE {{
              ?book wdt:P31 wd:Q571.
              ?book rdfs:label ?label.
              FILTER(LANG(?label) = "en" || LANG(?label) = "tr" || LANG(?label) = "ru").
              FILTER(CONTAINS(LCASE(?label), LCASE("{book_title_clean}"))).
            }}
            LIMIT 1
            """
        
        # SPARQL endpoint
        sparql_url = "https://query.wikidata.org/sparql"
        
        # Query parametrelerini hazırla
        params = {
            "query": query,
            "format": "json"
        }
        
        headers = {
            "User-Agent": "KitapListesiGUI/1.0 (https://github.com/your-repo)"
        }
        
        print(f"[DEBUG] Wikidata SPARQL sorgusu gönderiliyor: {query[:200]}...")
        resp = requests.get(sparql_url, params=params, headers=headers, timeout=15)
        print(f"[DEBUG] Wikidata SPARQL yanıt: status={resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", {}).get("bindings", [])
            print(f"[DEBUG] Wikidata SPARQL sonuç sayısı: {len(results)}")
            if results:
                book_uri = results[0].get("book", {}).get("value", "")
                if book_uri:
                    # URI'den QID'yi çıkar: http://www.wikidata.org/entity/Q165318 -> Q165318
                    qid = book_uri.split("/")[-1]
                    print(f"[DEBUG] Wikidata SPARQL QID bulundu: {qid}")
                    return qid
                else:
                    print(f"[DEBUG] Wikidata SPARQL sonuç var ama book URI yok")
            else:
                print(f"[DEBUG] Wikidata SPARQL sonuç yok")
        else:
            print(f"[DEBUG] Wikidata SPARQL hata yanıtı: {resp.status_code}, {resp.text[:200]}")
    except Exception as e:
        print(f"[DEBUG] Wikidata SPARQL sorgusu exception: {type(e).__name__}: {e}")
        import traceback
        print(f"[DEBUG] Wikidata SPARQL traceback: {traceback.format_exc()}")
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
        print("[DEBUG] Wikidata extract_fields: entity_json boş")
        return result

    entities = entity_json.get("entities", {})
    qid = next(iter(entities.keys()), None)
    if not qid:
        print("[DEBUG] Wikidata extract_fields: QID bulunamadı")
        return result

    print(f"[DEBUG] Wikidata extract_fields: QID={qid}, claims sayısı kontrol ediliyor...")
    entity = entities.get(qid, {})
    claims = entity.get("claims", {})
    print(f"[DEBUG] Wikidata extract_fields: Mevcut property'ler: {list(claims.keys())[:10]}...")  # İlk 10 property

    # P577 publication date: choose earliest sane year.
    years: list[int] = []
    if "P577" in claims:
        print(f"[DEBUG] Wikidata extract_fields: P577 (publication date) bulundu, {len(claims['P577'])} claim var")
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
            print(f"[DEBUG] Wikidata extract_fields: Publication year bulundu: {result[FIELD_PUBLICATION_YEAR]} (en erken: {min(years)})")
        else:
            print(f"[DEBUG] Wikidata extract_fields: P577 var ama geçerli yıl extract edilemedi")
    else:
        print(f"[DEBUG] Wikidata extract_fields: P577 (publication date) bulunamadı")

    # Original title fallbacks: 
    # 1. P1476 (original title) - monolingual text, dil bazlı (Russian öncelikli)
    # 2. P1705, P1680, P1813 (alternatif property'ler)
    # 3. Entity labels (son çare, Russian öncelikli)
    
    # P1476 = "original title" property (monolingual text formatında, dil bazlı)
    # Russian dilini önceliklendir (Rus yazarlar için önemli)
    if "P1476" in claims:
        print(f"[DEBUG] Wikidata extract_fields: P1476 (original title) bulundu, {len(claims['P1476'])} claim var")
        # Önce Russian'ı ara
        for claim in claims.get("P1476", []):
            value = _claim_datavalue(claim)
            if isinstance(value, dict):
                lang = value.get("language", "")
                text = value.get("text", "")
                if lang == "ru" and text:
                    result[FIELD_ORIGINAL_TITLE] = text
                    print(f"[DEBUG] Wikidata extract_fields: Original title bulundu (P1476, Russian): {text[:50]}...")
                    break
        
        # Russian bulunamadıysa, herhangi bir dildeki title'ı al
        if not result.get(FIELD_ORIGINAL_TITLE):
            for claim in claims.get("P1476", []):
                text = _claim_string(claim)
                if text:
                    result[FIELD_ORIGINAL_TITLE] = text
                    print(f"[DEBUG] Wikidata extract_fields: Original title bulundu (P1476, diğer dil): {text[:50]}...")
                    break
    
    # P1476 yoksa veya boşsa, diğer property'leri dene
    if not result.get(FIELD_ORIGINAL_TITLE):
        for prop in ("P1705", "P1680", "P1813"):
            if prop in claims:
                print(f"[DEBUG] Wikidata extract_fields: {prop} kontrol ediliyor...")
                for claim in claims.get(prop, []):
                    text = _claim_string(claim)
                    if text:
                        result[FIELD_ORIGINAL_TITLE] = text
                        print(f"[DEBUG] Wikidata extract_fields: Original title bulundu ({prop}): {text[:50]}...")
                        break
                if result.get(FIELD_ORIGINAL_TITLE):
                    break
    
    # Hala bulunamadıysa entity labels'ı kullan (Russian öncelikli)
    if not result.get(FIELD_ORIGINAL_TITLE):
        label = _pick_label(entity, preferred=("ru", "en", "tr"))
        if label:
            result[FIELD_ORIGINAL_TITLE] = label
            print(f"[DEBUG] Wikidata extract_fields: Original title bulundu (entity label): {label[:50]}...")
        else:
            print(f"[DEBUG] Wikidata extract_fields: Original title bulunamadı (hiçbir property'de yok)")

    # Country/tradition fallbacks: P495 (country of origin) then P17 (country).
    for prop in ("P495", "P17"):
        if prop in claims:
            print(f"[DEBUG] Wikidata extract_fields: {prop} (country) kontrol ediliyor...")
            ids = [_claim_entity_id(c) for c in claims.get(prop, [])]
            entity_id = next((x for x in ids if x), None)
            if not entity_id:
                print(f"[DEBUG] Wikidata extract_fields: {prop} var ama entity_id extract edilemedi")
                continue
            print(f"[DEBUG] Wikidata extract_fields: {prop} entity_id bulundu: {entity_id}")
            label = _resolve_entity_label(entity_id)
            if label:
                result[FIELD_COUNTRY_TRADITION] = label
                print(f"[DEBUG] Wikidata extract_fields: Country bulundu ({prop}): {label}")
                break
            else:
                print(f"[DEBUG] Wikidata extract_fields: {prop} entity_id var ama label bulunamadı: {entity_id}")
    if not result.get(FIELD_COUNTRY_TRADITION):
        print(f"[DEBUG] Wikidata extract_fields: Country bulunamadı (P495 ve P17 yok veya label bulunamadı)")

    return result
