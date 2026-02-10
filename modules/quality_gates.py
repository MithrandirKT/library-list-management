"""
Quality gates to reject wrong-context values.
"""

import re
from typing import Dict, Optional, Tuple


VOLUME_PATTERNS = [
    r"\bvolume\b",
    r"\bvol\.?\b",
    r"\btome\b",
    r"\bpart\b",
    r"\bbook\s+one\b",
    r"\bbook\s+two\b",
    r"\bbook\s+three\b",
    r"\bcilt\b",
    r"\bc\.?\s*\d+\b",
    r"\bbirinci\b",
    r"\bikinci\b",
    r"\bucuncu\b",
    r"\bdördüncü\b",
    r"\bbeşinci\b",
    r"\b1\.?\s*cilt\b",
    r"\b2\.?\s*cilt\b",
    r"\b3\.?\s*cilt\b",
    r"\b4\.?\s*cilt\b",
    r"\b5\.?\s*cilt\b",
    r"\bvolume\s+\w+\b",
    r"\bpart\s+[ivx]+",
    r"\bpart\s+\d+",
    r"\bchapter\s+\d+",
    r"\bbölüm\s+\d+",
    r"\bkitap\s+[ivx]+",
    r"\bkitap\s+\d+",
    r"\b\d+\.?\s*kitap",
    r"\b\d+\.?\s*part",
    r"\b\d+\.?\s*volume",
    r"\b\d+\.?\s*cilt",
    r"\b[ivx]+\.?\s*cilt",
    r"\b[ivx]+\.?\s*kitap",
]

TR_TRANSLATION_YEAR_PATTERNS = [
    r"t[üu]rk[çc]eye\s+.*\s+[0-9]{4}\s*y[ıi]l[ıi]nda",
    r"t[üu]rk[çc]eye\s+[çc]evrildi",
    r"t[üu]rk[çc]eye\s+[çc]evril",
    r"t[üu]rk[çc]e\s+bask[ıi]",
    r"t[üu]rk[çc]e\s+bas[ıi]m",
    r"t[üu]rk[çc]e\s+yay[ıi]n",
    r"t[üu]rkiyede\s+.*\s+[0-9]{4}\s*y[ıi]l[ıi]nda",
    r"t[üu]rkiyede\s+.*\s+yay[ıi]mland[ıi]",
    r"t[üu]rkiyede\s+.*\s+bas[ıi]ld[ıi]",
    r"t[üu]rkiyede\s+.*\s+[çc]evrildi",
    r"ilk\s+kez\s+t[üu]rk[çc]e",
    r"ilk\s+t[üu]rk[çc]e\s+bask[ıi]",
    r"[çc]evir",
    r"[çc]eviri",
    r"[çc]evirmen",
    r"türkçe\s+edisyon",
    r"türkçe\s+versiyon",
]

EN_PUB_CONTEXT = [
    r"first published",
    r"first published in",
    r"published in",
    r"written in",
    r"originally published",
    r"originally published in",
    r"initially published",
    r"initially published in",
    r"first appeared",
    r"first appeared in",
    r"first edition",
    r"first edition published",
    r"original publication",
    r"original publication date",
]


def has_volume_marker(text: str) -> bool:
    if not text:
        return False
    lower = text.lower()
    for p in VOLUME_PATTERNS:
        if re.search(p, lower):
            return True
    return False


def tr_translation_context(extract: str) -> bool:
    if not extract:
        return False
    lower = extract.lower()
    for p in TR_TRANSLATION_YEAR_PATTERNS:
        if re.search(p, lower):
            return True
    return False


def en_pub_context_present(extract: str) -> bool:
    if not extract:
        return False
    lower = extract.lower()
    return any(p in lower for p in EN_PUB_CONTEXT)


def _is_classic_book(kitap_adi: str, yazar: str) -> bool:
    """
    Heuristic to detect if a book is a classic (pre-1950 literature).
    This helps identify if a recent Google Books date is likely an edition date.
    """
    if not kitap_adi or not yazar:
        return False
    
    # Classic authors (common ones)
    classic_authors = [
        "tolstoy", "dostoyevsky", "dostoevsky", "chekhov", "gogol", "pushkin",
        "dickens", "austen", "bronte", "shakespeare", "homer", "virgil",
        "dante", "cervantes", "goethe", "schiller", "balzac", "flaubert",
        "zola", "stendhal", "verne", "wilde", "twain", "melville",
        "hawthorne", "poe", "whitman", "emerson", "thoreau", "thackeray",
        "eliot", "hardy", "conrad", "joyce", "kafka", "mann", "proust",
    ]
    
    yazar_lower = yazar.lower()
    for classic in classic_authors:
        if classic in yazar_lower:
            return True
    
    # Classic book titles (common ones)
    classic_titles = [
        "war and peace", "anna karenina", "crime and punishment", "brothers karamazov",
        "the idiot", "les miserables", "the hunchback", "don quixote",
        "the iliad", "the odyssey", "the divine comedy", "faust",
        "moby dick", "the scarlet letter", "pride and prejudice", "jane eyre",
        "wuthering heights", "great expectations", "david copperfield", "oliver twist",
        "the count of monte cristo", "the three musketeers", "madame bovary",
        "robinson crusoe",  # Daniel Defoe
    ]
    
    kitap_lower = kitap_adi.lower()
    for classic in classic_titles:
        if classic in kitap_lower:
            return True
    
    return False


def gate_publication_year(value: str, context: Dict[str, str]) -> Tuple[bool, Optional[str]]:
    source = context.get("source", "")
    extract = context.get("extract", "")
    localized_title = context.get("localized_title", "")
    
    # TR Wikipedia: Translation/edition context check
    if source == "trwiki" and tr_translation_context(extract):
        return False, "tr_translation_context"

    # EN Wikipedia: Must have publication context
    if source == "enwiki" and not en_pub_context_present(extract):
        return False, "missing_en_pub_context"

    # Google Books: Edition date risk for classic books
    if source == "gbooks":
        try:
            year = int(str(value).strip())
            # If it's a classic book and the year is after 1950, it's likely an edition date
            # Get author from context if available
            yazar = context.get("author", "")
            if _is_classic_book(localized_title, yazar) and year > 1950:
                # For very recent years (after 2000), be more strict
                if year > 2000:
                    return False, "gbooks_edition_date_recent"
                # For 1950-2000, still suspicious but allow with lower confidence
                # (This will be handled by the caller reducing confidence)
        except Exception:
            pass
    
    # Open Library: first_publish_year sometimes contains wrong data (modern edition dates instead of original)
    if source == "openlibrary":
        try:
            year = int(str(value).strip())
            # Get author from context if available
            yazar = context.get("author", "")
            # If it's a classic book and the year is after 2000, it's likely wrong data
            # Open Library sometimes has incorrect first_publish_year for classic books
            if _is_classic_book(localized_title, yazar) and year > 2000:
                return False, "openlibrary_wrong_first_publish_year"
            # Also check if year is suspiciously recent for any book (after 2010)
            # This catches cases where Open Library has wrong data
            if year > 2010:
                # For very recent years, be suspicious unless it's clearly a modern book
                # We'll allow it but with lower confidence (handled by caller)
                pass
        except Exception:
            pass

    # Basic sanity check for year
    try:
        year = int(str(value).strip())
        if year < 1500 or year > 2100:
            return False, "year_out_of_range"
    except Exception:
        # Allow ranges like 1865-1869; do not reject here
        pass

    return True, None


def _detect_cyrillic_or_arabic(text: str) -> bool:
    """Detect if text contains Cyrillic or Arabic characters (likely original language)"""
    if not text:
        return False
    # Cyrillic range: U+0400-U+04FF
    # Arabic range: U+0600-U+06FF
    for char in text:
        code = ord(char)
        if (0x0400 <= code <= 0x04FF) or (0x0600 <= code <= 0x06FF):
            return True
    return False


def _is_likely_original_language(text: str) -> bool:
    """
    Heuristic to detect if text is likely in original language (non-Latin script).
    Returns True if text contains Cyrillic, Arabic, Chinese, Japanese, etc.
    """
    if not text:
        return False
    
    # Check for non-Latin scripts
    if _detect_cyrillic_or_arabic(text):
        return True
    
    # Check for Chinese/Japanese characters (CJK Unified Ideographs)
    for char in text:
        code = ord(char)
        # CJK Unified Ideographs: U+4E00-U+9FFF
        if 0x4E00 <= code <= 0x9FFF:
            return True
    
    return False


def gate_original_title(value: str, context: Dict[str, str]) -> Tuple[bool, Optional[str]]:
    if not value:
        return False, "empty"
    
    # Volume/edition marker check
    if has_volume_marker(value):
        return False, "volume_marker"

    localized = context.get("localized_title", "").strip().lower()
    value_lower = value.strip().lower()
    
    # If original title equals localized title, consider low quality
    if localized and value_lower == localized:
        return False, "same_as_localized"
    
    # If localized title suggests original language (e.g., Russian author/book)
    # but original title is in Latin script and same as localized, reject
    # This catches cases where "War and Peace" is returned as original title
    # when it should be "Война и мир" or at least "Voyna i mir"
    source = context.get("source", "")
    if source in ("gbooks", "openlibrary"):
        # These sources often return translated/edition titles
        # If the book seems to be from a non-Latin script language but
        # original title is in Latin and matches localized, it's suspicious
        yazar = context.get("author", "").lower()
        # Russian authors
        russian_indicators = ["tolstoy", "dostoyevsky", "dostoevsky", "chekhov", "gogol", "pushkin", "turgenev"]
        if any(indicator in yazar for indicator in russian_indicators):
            # If original title is in Latin and same/similar to localized, reject
            if not _is_likely_original_language(value) and value_lower == localized:
                return False, "latin_same_as_localized_russian"
    
    return True, None
