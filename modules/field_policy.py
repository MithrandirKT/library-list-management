"""
Field-level source priority and validation rules.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from quality_gates import gate_publication_year, gate_original_title


GateFn = Callable[[str, Dict[str, str]], Tuple[bool, Optional[str]]]


@dataclass
class FieldRule:
    name: str
    sources: List[str]
    gate: Optional[GateFn] = None
    default_conf: float = 0.6


def build_rules() -> Dict[str, FieldRule]:
    return {
        "Çıkış Yılı": FieldRule(
            name="Çıkış Yılı",
            # First-publication bias: structured sources first, TR wiki late due translation-edition risk.
            sources=["openlibrary", "wikidata", "enwiki", "gbooks", "trwiki", "groq", "hf", "together"],
            gate=gate_publication_year,
            default_conf=0.7,
        ),
        "Orijinal Adı": FieldRule(
            name="Orijinal Adı",
            sources=["wikidata", "enwiki", "groq", "hf", "together"],
            gate=gate_original_title,
            default_conf=0.7,
        ),
        "Tür": FieldRule(
            name="Tür",
            sources=["openlibrary", "enwiki", "trwiki", "gbooks", "groq", "hf", "together"],
            gate=None,
            default_conf=0.6,
        ),
        "Ülke/Edebi Gelenek": FieldRule(
            name="Ülke/Edebi Gelenek",
            sources=["wikidata", "enwiki", "trwiki", "gbooks", "groq", "hf", "together"],
            gate=None,
            default_conf=0.5,
        ),
        "Anlatı Yılı": FieldRule(
            name="Anlatı Yılı",
            sources=["enwiki", "trwiki", "groq", "hf", "together"],
            gate=None,
            default_conf=0.4,
        ),
        "Konusu": FieldRule(
            name="Konusu",
            sources=["enwiki", "trwiki", "openlibrary", "groq", "hf", "together"],
            gate=None,
            default_conf=0.5,
        ),
    }


