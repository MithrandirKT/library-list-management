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
    """
    Field policy rules - SADECE GPT-OSS-20B (groq) kullanılıyor.
    Diğer tüm kaynaklar (Wikipedia, Google Books, Open Library, Wikidata, Hugging Face, Together AI) devre dışı.
    """
    return {
        "İlk Yayınlanma Tarihi": FieldRule(
            name="İlk Yayınlanma Tarihi",
            # ⚠️ SADECE GPT-OSS-20B kullanılıyor - diğer kaynaklar devre dışı
            sources=["groq"],
            gate=None,  # Quality gate'ler devre dışı (sadece AI kullanılıyor)
            default_conf=0.8,  # AI'ya daha yüksek güven
        ),
        "Orijinal Adı": FieldRule(
            name="Orijinal Adı",
            # ⚠️ SADECE GPT-OSS-20B kullanılıyor
            sources=["groq"],
            gate=None,
            default_conf=0.8,
        ),
        "Tür": FieldRule(
            name="Tür",
            # ⚠️ SADECE GPT-OSS-20B kullanılıyor
            sources=["groq"],
            gate=None,
            default_conf=0.8,
        ),
        "Ülke/Edebi Gelenek": FieldRule(
            name="Ülke/Edebi Gelenek",
            # ⚠️ SADECE GPT-OSS-20B kullanılıyor
            sources=["groq"],
            gate=None,
            default_conf=0.8,
        ),
        "Anlatı Yılı": FieldRule(
            name="Anlatı Yılı",
            # ⚠️ SADECE GPT-OSS-20B kullanılıyor
            sources=["groq"],
            gate=None,
            default_conf=0.8,
        ),
        "Konusu": FieldRule(
            name="Konusu",
            # ⚠️ SADECE GPT-OSS-20B kullanılıyor
            sources=["groq"],
            gate=None,
            default_conf=0.8,
        ),
    }


