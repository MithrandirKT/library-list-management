"""
Kitap Bilgisi Cekici Modulu
Wikipedia, Google Books, Open Library ve Groq AI API'lerini kullanarak kitap bilgilerini ceker
"""

import requests
import re
from typing import Dict, Optional, List
import time
import json
import os
from bs4 import BeautifulSoup
from urllib.parse import quote, unquote

from field_policy import build_rules
from provenance import set_field, set_row_status
from router import QuotaRouter
from wikidata_client import qid_from_wikipedia, qid_from_sparql_search, fetch_entity, extract_fields
from field_registry import ensure_row_schema

# DuckDuckGo search için
try:
    # Yeni paket adı: ddgs (duckduckgo_search yerine)
    try:
        from ddgs import DDGS
        DDG_AVAILABLE = True
    except ImportError:
        # Eski paket adı (backward compatibility)
        from duckduckgo_search import DDGS
        DDG_AVAILABLE = True
except ImportError:
    DDG_AVAILABLE = False
    print("[WARNING] ddgs veya duckduckgo-search paketi yüklü değil. Web search kullanılamayacak.")


class KitapBilgisiCekici:
    def __init__(self):
        self.wikipedia_base_url = "https://tr.wikipedia.org/api/rest_v1/page/summary/"
        self.google_books_url = "https://www.googleapis.com/books/v1/volumes"
        self.open_library_url = "https://openlibrary.org/search.json"
        self.groq_api_url = "https://api.groq.com/openai/v1/chat/completions"
        # Groq API key - kullanicidan alinacak veya environment variable'dan
        self.groq_api_key = os.getenv('GROQ_API_KEY', '')
        # Hugging Face Inference API (ucretsiz, API key gerektirmez ama rate limit var)
        # ⚠️ NOT: router.huggingface.co 404 veriyor, eski api-inference.huggingface.co'yu tekrar deniyoruz
        self.huggingface_api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        # Together AI API (ucretsiz tier var, alternatif yedek API)
        self.together_api_url = "https://api.together.xyz/v1/chat/completions"
        self.together_api_key = os.getenv('TOGETHER_API_KEY', '')
        # Hugging Face API key - once dosyadan, sonra environment variable'dan dene
        self.huggingface_api_key = self._huggingface_key_yukle()
        # Router state for AI providers
        self.router = QuotaRouter()
        self._last_status_code: Optional[int] = None
    
    def _huggingface_key_yukle(self) -> str:
        """Hugging Face API key'i yukler (once dosyadan, sonra environment variable'dan)"""
        # Once dosyadan dene
        try:
            # data/ klasöründen yükle
            base_dir = os.path.dirname(os.path.dirname(__file__))
            key_path = os.path.join(base_dir, "data", "huggingface_api_key.txt")
            if os.path.exists(key_path):
                with open(key_path, 'r', encoding='utf-8') as f:
                    key = f.read().strip()
                    if key:
                        return key
        except Exception:
            pass
        
        # Dosyadan yuklenemediyse environment variable'dan dene
        env_key = os.getenv('HUGGINGFACE_API_KEY', '')
        if env_key:
            return env_key
        
        return ''
        
    def kitap_bilgisi_cek(self, kitap_adi: str, yazar: str) -> Dict[str, str]:
        """
        Coklu kaynaktan kitap bilgilerini ceker
        
        Args:
            kitap_adi: Kitap adi (Turkce)
            yazar: Yazar adi
            
        Returns:
            Dict: Kitap bilgileri (Orijinal Adi, Tur, Ulke/Edebi Gelenek, Ilk Yayinlanma Tarihi, Konusu)
        """
        sonuc = {
            "Orijinal Adı": "",
            "Tür": "",
            "Ülke/Edebi Gelenek": "",
            "İlk Yayınlanma Tarihi": "",
            "Anlatı Yılı": "",
            "Konusu": ""
        }
        
        # Once Wikipedia'dan dene
        wikipedia_bilgi = self._wikipedia_cek(kitap_adi, yazar)
        if wikipedia_bilgi:
            sonuc.update(wikipedia_bilgi)
        
        # Eksik bilgileri Google Books'tan tamamla
        eksik_alanlar = [k for k, v in sonuc.items() if not v or v == ""]
        if eksik_alanlar:
            google_bilgi = self._google_books_cek(kitap_adi, yazar)
            if google_bilgi:
                for alan in eksik_alanlar:
                    if alan in google_bilgi and google_bilgi[alan]:
                        sonuc[alan] = google_bilgi[alan]
        
        # Hala eksik bilgiler varsa Open Library'den dene
        eksik_alanlar = [k for k, v in sonuc.items() if not v or v == ""]
        if eksik_alanlar:
            openlib_bilgi = self._open_library_cek(kitap_adi, yazar)
            if openlib_bilgi:
                for alan in eksik_alanlar:
                    if alan in openlib_bilgi and openlib_bilgi[alan]:
                        sonuc[alan] = openlib_bilgi[alan]
        
        # AI fallback for missing fields (router ile quota yönetimi)
        eksik_alanlar = [k for k, v in sonuc.items() if not v or v == ""]
        if eksik_alanlar:
            def _call_groq():
                result = self._groq_ai_cek(kitap_adi, yazar, eksik_alanlar, sonuc)
                return result, self._last_status_code

            def _call_hf():
                result = self._huggingface_ai_cek(kitap_adi, yazar, eksik_alanlar, sonuc)
                return result, self._last_status_code

            def _call_together():
                result = self._together_ai_cek(kitap_adi, yazar, eksik_alanlar, sonuc)
                return result, self._last_status_code

            for name, fn in [("groq", _call_groq), ("hf", _call_hf), ("together", _call_together)]:
                ai_data = self.router.call(name, fn)
                if not ai_data:
                    continue
                for alan in eksik_alanlar:
                    if alan in ai_data and ai_data[alan]:
                        sonuc[alan] = ai_data[alan]
                eksik_alanlar = [k for k, v in sonuc.items() if not v or v == ""]
                if not eksik_alanlar:
                    break
        
        return sonuc
    
    def _wikipedia_cek(self, kitap_adi: str, yazar: str) -> Optional[Dict[str, str]]:
        """Wikipedia'dan kitap bilgilerini ceker - Once Ingilizce'de ara (orijinal bilgiler icin)"""
        try:
            from urllib.parse import quote
            
            # Once Ingilizce Wikipedia'da ara (orijinal dildeki bilgiler icin)
            # Yazar adi ile birlikte ara
            arama_terimleri = [
                f"{kitap_adi} ({yazar})",  # Kitap adı (Yazar)
                kitap_adi,  # Sadece kitap adı
                f"{yazar} {kitap_adi}"  # Yazar Kitap adı
            ]
            
            for arama_terimi in arama_terimleri:
                arama_url_en = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(arama_terimi)}"
                response = requests.get(arama_url_en, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    # Yazar adinin da eslestigini kontrol et
                    extract = data.get('extract', '').lower()
                    if yazar.lower() in extract or arama_terimi == kitap_adi:
                        return self._wikipedia_parse(data, kitap_adi, yazar, lang='en')
            
            # Ingilizce'de bulunamazsa Turkce'de dene
            arama_url_tr = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{quote(kitap_adi)}"
            response = requests.get(arama_url_tr, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'extract' in data and yazar.lower() in data.get('extract', '').lower():
                    return self._wikipedia_parse(data, kitap_adi, yazar, lang='tr')
            
        except Exception:
            pass
        
        return None
    
    def _wikipedia_parse(self, data: dict, kitap_adi: str, yazar: str, lang: str = 'en') -> Dict[str, str]:
        """Wikipedia verisini parse eder - Iyilestirilmis versiyon"""
        sonuc = {}
        extract = data.get('extract', '')
        title = data.get('title', '')
        
        # Orijinal adi: Ingilizce sayfadaysa title'i kullan (orijinal dildeki adi)
        # Turkce sayfadaysa "Orijinal adi:" veya parantez icindeki adi bul
        if lang == 'en':
            # Ingilizce sayfada title genellikle orijinal adidir
            if title and title.lower() != kitap_adi.lower():
                sonuc["Orijinal Adı"] = title
            else:
                # Extract'te "original title" veya parantez içinde ara
                orijinal_match = re.search(r'(?:original title|original name|originally published as)[:\s]+([^(\n]+)', extract, re.IGNORECASE)
                if not orijinal_match:
                    # Parantez içinde İngilizce olmayan bir ad ara
                    parantez_match = re.search(r'\(([^)]+)\)', extract)
                    if parantez_match:
                        parantez_icerik = parantez_match.group(1)
                        # Turkce karakterler icermiyorsa orijinal adi olabilir
                        if not any(c in parantez_icerik for c in 'çğıöşüÇĞIİÖŞÜ'):
                            sonuc["Orijinal Adı"] = parantez_icerik.strip()
        else:
            # Turkce sayfada "Orijinal adi:" veya parantez icindeki adi bul
            orijinal_match = re.search(r'(?:Orijinal adı|Original title|Original name)[:\s]+([^(\n]+)', extract, re.IGNORECASE)
            if not orijinal_match:
                orijinal_match = re.search(r'\(([^)]+)\)', extract)
            if orijinal_match:
                sonuc["Orijinal Adı"] = orijinal_match.group(1).strip()
        
        # Konusu (extract'in ilk 1-2 cümlesi)
        if extract:
            cumleler = re.split(r'[.!?]+', extract)
            konu = '. '.join([c.strip() for c in cumleler[:2] if c.strip()])
            if konu and len(konu) > 20:  # En az 20 karakter olsun
                sonuc["Konusu"] = konu + '.' if not konu.endswith('.') else konu
        
        # Ilk yayinlanma tarihi: "published", "written", "first published" gibi kelimelerden sonraki yili bul
        # Basim yili degil, yazildigi/yayinlandigi ilk yil
        if extract:
            # "first published in", "written in", "published in" gibi ifadeleri ara
            # ⚠️ Son pattern (genel yıl pattern'i) kaldırıldı çünkü yanlış yılları yakalayabilir
            yil_patterns = [
                r'(?:first published|originally published)\s+(?:in\s+)?(\d{4})',  # Öncelik: "first published" veya "originally published"
                r'(?:written|published)\s+(?:in\s+)?(\d{4})',  # İkinci öncelik: "written" veya "published"
                r'(\d{4})\s+(?:yılında|yılı|year)\s+(?:yayınlandı|published|written)',  # Türkçe/İngilizce format: "1869 yılında yayınlandı"
            ]
            
            for pattern in yil_patterns:
                yil_match = re.search(pattern, extract, re.IGNORECASE)
                if yil_match:
                    try:
                        yil = int(yil_match.group(1))
                        if 1500 <= yil <= 2030:
                            sonuc["İlk Yayınlanma Tarihi"] = str(yil)
                            print(f"[DEBUG] Wikipedia parse: Ilk Yayinlanma Tarihi='{yil}' (pattern: {pattern})")
                            break
                    except:
                        continue
        
        # Tür bilgisi: Daha kapsamlı arama
        if extract:
            # Tür eşleştirme sözlüğü (İngilizce ve Türkçe)
            tur_eslesmeleri = {
                'novel': 'Roman',
                'roman': 'Roman',
                'novella': 'Novella',
                'novelle': 'Novella',
                'short story': 'Öykü',
                'story': 'Öykü',
                'öykü': 'Öykü',
                'hikaye': 'Öykü',
                'philosophy': 'Felsefe',
                'felsefe': 'Felsefe',
                'philosophical': 'Felsefe',
                'history': 'Tarih',
                'tarih': 'Tarih',
                'historical': 'Tarih',
                'science': 'Bilim',
                'bilim': 'Bilim',
                'scientific': 'Bilim',
                'poetry': 'Şiir',
                'poem': 'Şiir',
                'şiir': 'Şiir',
                'theatre': 'Tiyatro',
                'theater': 'Tiyatro',
                'play': 'Tiyatro',
                'tiyatro': 'Tiyatro',
                'drama': 'Tiyatro'
            }
            
            extract_lower = extract.lower()
            for anahtar, tur in tur_eslesmeleri.items():
                if anahtar in extract_lower:
                    sonuc["Tür"] = tur
                    break
        
        # Ülke/Edebi Gelenek: Yazarın ülkesini bul, kitap adından değil
        # Extract'te yazarın milliyeti veya ülkesi geçiyorsa onu kullan
        if extract:
            # Yazarın ülkesi için pattern'ler
            ulke_patterns = {
                r'(?:born|doğdu|from|gelen)\s+(?:in\s+)?(?:the\s+)?(?:country\s+of\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                r'(?:author|yazar|writer|yazarı)\s+(?:from|gelen|of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            }
            
            # Önce yazarın ülkesini bul
            ulke_bulundu = False
            for pattern in ulke_patterns:
                match = re.search(pattern, extract, re.IGNORECASE)
                if match:
                    potansiyel_ulke = match.group(1)
                    # Bilinen ülke listesi
                    ulkeler_map = {
                        'turkish': 'Türkiye', 'turkey': 'Türkiye', 'türkiye': 'Türkiye',
                        'british': 'İngiltere', 'england': 'İngiltere', 'english': 'İngiltere', 'ingiltere': 'İngiltere',
                        'american': 'Amerika', 'usa': 'Amerika', 'united states': 'Amerika', 'amerika': 'Amerika',
                        'french': 'Fransa', 'france': 'Fransa', 'fransa': 'Fransa',
                        'german': 'Almanya', 'germany': 'Almanya', 'almanya': 'Almanya',
                        'russian': 'Rusya', 'russia': 'Rusya', 'rusya': 'Rusya',
                        'spanish': 'İspanya', 'spain': 'İspanya', 'ispanya': 'İspanya',
                        'italian': 'İtalya', 'italy': 'İtalya', 'italya': 'İtalya',
                        'greek': 'Yunanistan', 'greece': 'Yunanistan', 'yunanistan': 'Yunanistan',
                        'japanese': 'Japonya', 'japan': 'Japonya', 'japonya': 'Japonya',
                        'chinese': 'Çin', 'china': 'Çin', 'çin': 'Çin',
                        'indian': 'Hindistan', 'india': 'Hindistan', 'hindistan': 'Hindistan'
                    }
                    potansiyel_lower = potansiyel_ulke.lower()
                    if potansiyel_lower in ulkeler_map:
                        sonuc["Ülke/Edebi Gelenek"] = ulkeler_map[potansiyel_lower]
                        ulke_bulundu = True
                        break
            
            # Yazarın ülkesi bulunamazsa, extract'te geçen ülke isimlerini ara
            if not ulke_bulundu:
                ulkeler = ["Türkiye", "İngiltere", "Amerika", "Fransa", "Almanya", "Rusya", 
                          "İspanya", "İtalya", "Yunanistan", "Japonya", "Çin", "Hindistan",
                          "Turkey", "England", "USA", "France", "Germany", "Russia",
                          "Spain", "Italy", "Greece", "Japan", "China", "India"]
                for ulke in ulkeler:
                    if ulke.lower() in extract.lower():
                        # Türkçe ülke adlarını kullan
                        if ulke in ["Turkey", "England", "USA", "France", "Germany", "Russia",
                                   "Spain", "Italy", "Greece", "Japan", "China", "India"]:
                            ceviri = {
                                "Turkey": "Türkiye", "England": "İngiltere", "USA": "Amerika",
                                "France": "Fransa", "Germany": "Almanya", "Russia": "Rusya",
                                "Spain": "İspanya", "Italy": "İtalya", "Greece": "Yunanistan",
                                "Japan": "Japonya", "China": "Çin", "India": "Hindistan"
                            }
                            sonuc["Ülke/Edebi Gelenek"] = ceviri[ulke]
                        else:
                            sonuc["Ülke/Edebi Gelenek"] = ulke
                        break
        
        return sonuc
    
    def _google_books_cek(self, kitap_adi: str, yazar: str) -> Optional[Dict[str, str]]:
        """Google Books API'den kitap bilgilerini çeker - Önce İngilizce'de ara"""
        try:
            # Önce İngilizce'de ara (orijinal dildeki bilgiler için)
            query = f"{kitap_adi} {yazar}"
            params = {
                'q': query,
                'maxResults': 5  # Daha fazla sonuç al
            }
            
            response = requests.get(self.google_books_url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'items' in data and len(data['items']) > 0:
                    # Yazar adına göre en uygun sonucu bul
                    for item in data['items']:
                        volume_info = item.get('volumeInfo', {})
                        authors = volume_info.get('authors', [])
                        # Yazar adı eşleşiyorsa bu sonucu kullan
                        if any(yazar.lower() in author.lower() or author.lower() in yazar.lower() 
                               for author in authors):
                            return self._google_books_parse(item, kitap_adi, yazar)
                    # Eşleşme yoksa ilk sonucu kullan
                    return self._google_books_parse(data['items'][0], kitap_adi, yazar)
            
        except Exception:
            pass
        
        return None
    
    def _google_books_parse(self, item: dict, kitap_adi: str, yazar: str) -> Dict[str, str]:
        """Google Books verisini parse eder - İyileştirilmiş versiyon"""
        sonuc = {}
        volume_info = item.get('volumeInfo', {})
        
        # Orijinal adı: title'ı kullan (genellikle orijinal dildeki adıdır)
        if 'title' in volume_info:
            title = volume_info['title']
            # Eğer title Türkçe karakterler içermiyorsa ve kitap adından farklıysa, orijinal adıdır
            if title.lower() != kitap_adi.lower():
                sonuc["Orijinal Adı"] = title
        
        # ⚠️ UYARI: Google Books API'den publishedDate bu edition'ın yayın tarihi olabilir,
        # ilk yayınlanma tarihi değil! Google'ın bilgi panelinde gösterdiği tarih genellikle
        # Wikipedia/Wikidata'dan gelir. Bu yüzden Google Books'tan tarih çekmeyi kaldırdık.
        # Eğer gerçekten ilk yayınlanma tarihi gerekiyorsa, Wikipedia/Wikidata/Open Library kullanılmalı.
        # if 'publishedDate' in volume_info:
        #     tarih = volume_info['publishedDate']
        #     # Yıl formatı: YYYY, YYYY-MM, veya YYYY-MM-DD olabilir
        #     yil_match = re.search(r'\b(1[5-9]\d{2}|20[0-2]\d)\b', tarih)
        #     if yil_match:
        #         yil = int(yil_match.group(1))
        #         if 1500 <= yil <= 2030:
        #             sonuc["İlk Yayınlanma Tarihi"] = str(yil)
        
        # Tür (categories) - Daha kapsamlı eşleştirme
        if 'categories' in volume_info and volume_info['categories']:
            kategoriler = volume_info['categories']
            tur_eslesmeleri = {
                'fiction': 'Roman', 'novel': 'Roman', 'roman': 'Roman',
                'novella': 'Novella', 'novelle': 'Novella',
                'short story': 'Öykü', 'story': 'Öykü',
                'philosophy': 'Felsefe', 'philosophical': 'Felsefe',
                'history': 'Tarih', 'historical': 'Tarih',
                'science': 'Bilim', 'scientific': 'Bilim',
                'poetry': 'Şiir', 'poem': 'Şiir',
                'drama': 'Tiyatro', 'theatre': 'Tiyatro', 'theater': 'Tiyatro', 'play': 'Tiyatro'
            }
            
            for kategori in kategoriler:
                kategori_lower = kategori.lower()
                for anahtar, tur in tur_eslesmeleri.items():
                    if anahtar in kategori_lower:
                        sonuc["Tür"] = tur
                        break
                if "Tür" in sonuc:
                    break
        
        # Konusu (description - ilk 1-2 cümle)
        if 'description' in volume_info:
            description = volume_info['description']
            if description:
                cumleler = re.split(r'[.!?]+', description)
                konu = '. '.join([c.strip() for c in cumleler[:2] if c.strip()])
                if konu and len(konu) > 20:
                    sonuc["Konusu"] = konu + '.' if not konu.endswith('.') else konu
        
        # ⚠️ UYARI: Google Books API'den language alanı kitabın çevrildiği dili gösterir,
        # yazarın ülkesini değil! Bu yüzden Google Books'tan ülke bilgisini çekmeyi kaldırdık.
        # Ülke bilgisi Wikipedia/Wikidata'dan gelmelidir.
        # Örnek: "War and Peace" İngilizce çevirisi için language='en' olur, ama yazar Rus'tur.
        # if 'language' in volume_info:
        #     dil = volume_info['language']
        #     dil_ulke_map = {
        #         'tr': 'Türkiye',
        #         'zh': 'Çin',
        #         'pt': 'Portekiz',
        #         'nl': 'Hollanda',
        #         'pl': 'Polonya',
        #         'cs': 'Çek Cumhuriyeti',
        #         'sv': 'İsveç',
        #         'no': 'Norveç',
        #         'da': 'Danimarka',
        #         'fi': 'Finlandiya',
        #         'hu': 'Macaristan',
        #         'ro': 'Romanya',
        #         'bg': 'Bulgaristan',
        #         'el': 'Yunanistan',
        #         'ar': 'Arap Ülkeleri',
        #         'he': 'İsrail',
        #         'ko': 'Güney Kore',
        #         'hi': 'Hindistan'
        #     }
        #     if dil in dil_ulke_map:
        #         sonuc["Ülke/Edebi Gelenek"] = dil_ulke_map[dil]
        
        return sonuc
    
    def _open_library_cek(self, kitap_adi: str, yazar: str) -> Optional[Dict[str, str]]:
        """Open Library API'den kitap bilgilerini çeker"""
        try:
            query = f"{kitap_adi} {yazar}"
            params = {
                'q': query,
                'limit': 1
            }
            
            response = requests.get(self.open_library_url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'docs' in data and len(data['docs']) > 0:
                    return self._open_library_parse(data['docs'][0], kitap_adi, yazar)
            
        except Exception:
            pass
        
        return None
    
    def _open_library_parse(self, doc: dict, kitap_adi: str, yazar: str) -> Dict[str, str]:
        """Open Library verisini parse eder - İyileştirilmiş versiyon"""
        sonuc = {}
        
        # Orijinal adı: title'ı kullan
        if 'title' in doc:
            title = doc['title']
            if title.lower() != kitap_adi.lower():
                sonuc["Orijinal Adı"] = title
        
        # İlk yayınlanma tarihi: first_publish_year kullan (ilk yayınlandığı yıl - doğru!)
        # ⚠️ ÖNEMLİ:
        # - Open Library'de bazen sadece publish_year listesi olur ve ilk yıl modern bir baskı olabilir (ör: 2017).
        # - Bu durumda publish_year'dan minimum yılı almak klasik eserler için yanlış sonuç verir.
        # - Bu yüzden SADECE first_publish_year alanını kullanıyoruz; yoksa Open Library'den yıl almıyoruz.
        print(f"[DEBUG] Open Library doc keys: {list(doc.keys())}")
        print(f"[DEBUG] Open Library first_publish_year: {doc.get('first_publish_year', 'NOT FOUND')}")
        print(f"[DEBUG] Open Library publish_year: {doc.get('publish_year', 'NOT FOUND')}")
        if 'first_publish_year' in doc and doc['first_publish_year']:
            yil = doc['first_publish_year']
            if isinstance(yil, int) and 1500 <= yil <= 2030:
                sonuc["İlk Yayınlanma Tarihi"] = str(yil)
                print(f"[DEBUG] Open Library: Using first_publish_year={yil}")
        
        # Tür (subject) - Daha kapsamlı eşleştirme
        if 'subject' in doc and doc['subject']:
            konular = doc['subject']
            tur_eslesmeleri = {
                'fiction': 'Roman', 'novel': 'Roman', 'roman': 'Roman',
                'novella': 'Novella', 'novelle': 'Novella',
                'short story': 'Öykü', 'story': 'Öykü',
                'philosophy': 'Felsefe', 'philosophical': 'Felsefe',
                'history': 'Tarih', 'historical': 'Tarih',
                'science': 'Bilim', 'scientific': 'Bilim',
                'poetry': 'Şiir', 'poem': 'Şiir',
                'drama': 'Tiyatro', 'theatre': 'Tiyatro', 'theater': 'Tiyatro', 'play': 'Tiyatro'
            }
            
            for konu in konular[:10]:  # İlk 10 konuyu kontrol et
                if isinstance(konu, str):
                    konu_lower = konu.lower()
                    for anahtar, tur in tur_eslesmeleri.items():
                        if anahtar in konu_lower:
                            sonuc["Tür"] = tur
                            break
                    if "Tür" in sonuc:
                        break
        
        # Konusu (first_sentence veya subtitle)
        if 'first_sentence' in doc and doc['first_sentence']:
            if isinstance(doc['first_sentence'], list) and len(doc['first_sentence']) > 0:
                ilk_cumle = doc['first_sentence'][0]
                if isinstance(ilk_cumle, str):
                    cumleler = re.split(r'[.!?]+', ilk_cumle)
                    konu = '. '.join([c.strip() for c in cumleler[:2] if c.strip()])
                    if konu and len(konu) > 20:
                        sonuc["Konusu"] = konu + '.' if not konu.endswith('.') else konu
        
        # Ülke bilgisi: Open Library'de yazar bilgisi varsa ondan çıkarabiliriz
        # Ama şimdilik bu bilgiyi Groq API'den alacağız
        
        return sonuc
    
    def _search_kitapyurdu(self, kitap_adi: str, yazar: str) -> Optional[str]:
        """Kitapyurdu.com'da kitap ara ve bilgileri çıkar"""
        try:
            # Kitapyurdu arama URL'i
            search_query = f"{kitap_adi} {yazar}".replace(' ', '+')
            search_url = f"https://www.kitapyurdu.com/index.php?route=product/search&search={quote(search_query)}"
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # İlk sonucu bul
                product = soup.find('div', class_='product-cr') or soup.find('div', class_='product-list')
                if product:
                    title_elem = product.find('div', class_='name') or product.find('a', class_='pr-img-link')
                    author_elem = product.find('div', class_='author') or product.find('span', class_='author')
                    publisher_elem = product.find('div', class_='publisher') or product.find('span', class_='publisher')
                    year_elem = product.find('div', class_='year') or product.find('span', class_='year')
                    description_elem = product.find('div', class_='description') or product.find('p', class_='description')
                    
                    info_parts = []
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        if title:
                            info_parts.append(f"Title: {title}")
                    if author_elem:
                        author = author_elem.get_text(strip=True)
                        if author:
                            info_parts.append(f"Author: {author}")
                    if publisher_elem:
                        publisher = publisher_elem.get_text(strip=True)
                        if publisher:
                            info_parts.append(f"Publisher: {publisher}")
                    if year_elem:
                        year = year_elem.get_text(strip=True)
                        if year:
                            info_parts.append(f"Year: {year}")
                    if description_elem:
                        description = description_elem.get_text(strip=True)
                        if description:
                            info_parts.append(f"Description: {description[:400]}")
                    
                    if info_parts:
                        result_text = " | ".join(info_parts)[:2000]
                        print(f"[DEBUG] Kitapyurdu.com'dan bilgi bulundu")
                        return result_text
        except Exception as e:
            pass
        return None
    
    def _search_amazon_tr(self, kitap_adi: str, yazar: str) -> Optional[str]:
        """Amazon.com.tr'de kitap ara ve bilgileri çıkar"""
        try:
            # Amazon TR arama URL'i
            search_query = f"{kitap_adi} {yazar}".replace(' ', '+')
            search_url = f"https://www.amazon.com.tr/s?k={quote(search_query)}&i=stripbooks"
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # İlk sonucu bul
                product = soup.find('div', {'data-component-type': 's-search-result'})
                if product:
                    title_elem = product.find('h2', class_='a-size-mini') or product.find('span', class_='a-text-normal')
                    author_elem = product.find('a', class_='a-size-base') or product.find('span', class_='a-size-base')
                    price_elem = product.find('span', class_='a-price-whole')
                    
                    info_parts = []
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        if title:
                            info_parts.append(f"Title: {title}")
                    if author_elem:
                        author = author_elem.get_text(strip=True)
                        if author:
                            info_parts.append(f"Author: {author}")
                    if price_elem:
                        price = price_elem.get_text(strip=True)
                        if price:
                            info_parts.append(f"Price: {price} TL")
                    
                    if info_parts:
                        result_text = " | ".join(info_parts)[:2000]
                        print(f"[DEBUG] Amazon.com.tr'den bilgi bulundu")
                        return result_text
        except Exception as e:
            pass
        return None
    
    def _search_nadirkitap(self, kitap_adi: str, yazar: str) -> Optional[str]:
        """NadirKitap.com'da kitap ara ve bilgileri çıkar"""
        try:
            # NadirKitap arama URL'i
            search_query = f"{kitap_adi} {yazar}".replace(' ', '+')
            search_url = f"https://www.nadirkitap.com/arama?q={quote(search_query)}"
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # İlk sonucu bul
                product = soup.find('div', class_='product-item') or soup.find('div', class_='book-item')
                if product:
                    title_elem = product.find('h3') or product.find('a', class_='product-title')
                    author_elem = product.find('div', class_='author') or product.find('span', class_='author')
                    publisher_elem = product.find('div', class_='publisher') or product.find('span', class_='publisher')
                    year_elem = product.find('div', class_='year') or product.find('span', class_='year')
                    price_elem = product.find('span', class_='price') or product.find('div', class_='price')
                    
                    info_parts = []
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        if title:
                            info_parts.append(f"Title: {title}")
                    if author_elem:
                        author = author_elem.get_text(strip=True)
                        if author:
                            info_parts.append(f"Author: {author}")
                    if publisher_elem:
                        publisher = publisher_elem.get_text(strip=True)
                        if publisher:
                            info_parts.append(f"Publisher: {publisher}")
                    if year_elem:
                        year = year_elem.get_text(strip=True)
                        if year:
                            info_parts.append(f"Year: {year}")
                    if price_elem:
                        price = price_elem.get_text(strip=True)
                        if price:
                            info_parts.append(f"Price: {price}")
                    
                    if info_parts:
                        result_text = " | ".join(info_parts)[:2000]
                        print(f"[DEBUG] NadirKitap.com'dan bilgi bulundu")
                        return result_text
        except Exception as e:
            pass
        return None
    
    def _web_search(self, query: str, num_results: int = 5, kitap_adi: str = "", yazar: str = "") -> str:
        """Web search yapar (DuckDuckGo kullanarak) ve sonuçları döndürür (token tasarrufu için kısaltılmış)"""
        # Önce DuckDuckGo'yu dene (daha fazla sonuç ile)
        if DDG_AVAILABLE:
            try:
                with DDGS() as ddgs:
                    # Birden fazla arama varyasyonu dene
                    search_queries = []
                    if kitap_adi and yazar:
                        search_queries.append(f"{kitap_adi} {yazar}")
                        search_queries.append(f'"{kitap_adi}" {yazar}')
                        search_queries.append(f"{kitap_adi} book {yazar}")
                    search_queries.append(query)
                    
                    for search_query in search_queries:
                        try:
                            results = list(ddgs.text(search_query, max_results=min(num_results * 2, 10)))
                            if results:
                                print(f"[DEBUG] DuckDuckGo {len(results)} sonuç bulundu: {search_query[:50]}...")
                                # Token tasarrufu için kısalt (max 2000 karakter)
                                search_text = "\n".join([
                                    f"{r.get('title', 'N/A')}: {r.get('body', 'N/A')[:200]}"
                                    for r in results
                                ])
                                result_text = search_text[:2000]
                                print(f"[DEBUG] Web search sonuç metni uzunluğu: {len(result_text)} karakter")
                                return result_text
                        except Exception as e:
                            continue
            except Exception as e:
                print(f"[DEBUG] DuckDuckGo hatası: {e}")
        
        # DuckDuckGo başarısız olursa, alternatif: Türkçe kaynaklardan arama
        # SADECE TÜRKÇE KAYNAKLAR: Wikipedia TR, Google Books TR, Kitapyurdu, Amazon TR, NadirKitap
        
        # 1. TÜRKÇE WIKIPEDIA (öncelikli)
        wiki_queries = []
        if kitap_adi and yazar:
            # Yazar adı ile birlikte dene (farklı formatlar)
            wiki_queries.append(f"{kitap_adi} {yazar}")
            wiki_queries.append(f"{kitap_adi} ({yazar})")
            wiki_queries.append(kitap_adi)
            # Sadece yazar adı ile de dene (bazı kitaplar için)
            if len(kitap_adi.split()) <= 3:  # Kısa başlıklar için
                wiki_queries.append(f"{yazar} {kitap_adi}")
        else:
            wiki_queries.append(query.replace(' ', '_'))
        
        # Türkçe Wikipedia'da ara
        for wiki_query in wiki_queries:
            try:
                # URL encoding ile düzgün encode et
                wiki_query_clean = wiki_query.replace(' ', '_')
                wiki_query_encoded = quote(wiki_query_clean, safe='_')
                print(f"[DEBUG] Türkçe Wikipedia deneniyor: {wiki_query_clean[:50]}...")
                
                # Önce summary API'yi dene
                wiki_url_tr = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{wiki_query_encoded}"
                response_tr = requests.get(wiki_url_tr, timeout=10)
                if response_tr.status_code == 200:
                    wiki_data_tr = response_tr.json()
                    title_tr = wiki_data_tr.get('title', '')
                    extract_tr = wiki_data_tr.get('extract', '')
                    if extract_tr:
                        # Infobox bilgilerini de al (daha fazla bilgi için)
                        try:
                            # Infobox için ayrı bir request
                            wiki_page_url = f"https://tr.wikipedia.org/api/rest_v1/page/html/{wiki_query_encoded}"
                            page_response = requests.get(wiki_page_url, timeout=10)
                            if page_response.status_code == 200:
                                # HTML'den infobox bilgilerini çıkar
                                soup = BeautifulSoup(page_response.text, 'html.parser')
                                infobox = soup.find('table', class_='infobox')
                                infobox_text = ""
                                if infobox:
                                    infobox_text = infobox.get_text(separator=' | ', strip=True)[:500]
                                
                                result_text = f"{title_tr}: {extract_tr[:1200]}"
                                if infobox_text:
                                    result_text += f"\n\nInfobox: {infobox_text}"
                                print(f"[DEBUG] Türkçe Wikipedia'dan bilgi bulundu: {title_tr}")
                                return result_text
                        except:
                            pass
                        
                        # Infobox olmadan da döndür
                        result_text = f"{title_tr}: {extract_tr[:1500]}"
                        print(f"[DEBUG] Türkçe Wikipedia'dan bilgi bulundu: {title_tr}")
                        return result_text
            except Exception as e:
                continue
        
        # 2. GOOGLE BOOKS (Türkçe kitaplar için)
        gbooks_queries = []
        if kitap_adi and yazar:
            gbooks_queries.append(f"{kitap_adi} {yazar}")
            gbooks_queries.append(f'"{kitap_adi}" {yazar}')
            gbooks_queries.append(f"intitle:{kitap_adi} inauthor:{yazar}")
            gbooks_queries.append(kitap_adi)  # Sadece kitap adı
        else:
            gbooks_queries.append(query)
        
        for gbooks_query in gbooks_queries:
            try:
                print(f"[DEBUG] Google Books deneniyor: {gbooks_query[:50]}...")
                gbooks_url = "https://www.googleapis.com/books/v1/volumes"
                params = {'q': gbooks_query, 'maxResults': 10, 'langRestrict': 'tr'}  # Türkçe kitaplar
                response = requests.get(gbooks_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])
                    if items:
                        results_text = []
                        for item in items[:10]:  # İlk 10 sonuç
                            volume_info = item.get('volumeInfo', {})
                            title = volume_info.get('title', '')
                            authors = ', '.join(volume_info.get('authors', []))
                            description = volume_info.get('description', '') or volume_info.get('subtitle', '')
                            published_date = volume_info.get('publishedDate', '')
                            publisher = volume_info.get('publisher', '')
                            language = volume_info.get('language', '')
                            
                            # Daha detaylı bilgi
                            info_parts = []
                            if title:
                                info_parts.append(f"Title: {title}")
                            if authors:
                                info_parts.append(f"Author: {authors}")
                            if published_date:
                                info_parts.append(f"Published: {published_date}")
                            if publisher:
                                info_parts.append(f"Publisher: {publisher}")
                            if language:
                                info_parts.append(f"Language: {language}")
                            if description:
                                info_parts.append(f"Description: {description[:400]}")
                            
                            if info_parts:
                                results_text.append(" | ".join(info_parts))
                        
                        if results_text:
                            result_text = "\n".join(results_text)[:2000]
                            print(f"[DEBUG] Google Books'tan {len(items)} sonuç bulundu, {len(result_text)} karakter")
                            return result_text
            except Exception as e:
                continue
        
        # 3. KITAPYURDU.COM (Türkçe kitap sitesi)
        if kitap_adi and yazar:
            try:
                print(f"[DEBUG] Kitapyurdu.com deneniyor: {kitap_adi[:50]}...")
                kitapyurdu_result = self._search_kitapyurdu(kitap_adi, yazar)
                if kitapyurdu_result:
                    return kitapyurdu_result
            except Exception as e:
                print(f"[DEBUG] Kitapyurdu.com hatası: {e}")
        
        # 4. AMAZON.COM.TR (Türkçe Amazon)
        if kitap_adi and yazar:
            try:
                print(f"[DEBUG] Amazon.com.tr deneniyor: {kitap_adi[:50]}...")
                amazon_result = self._search_amazon_tr(kitap_adi, yazar)
                if amazon_result:
                    return amazon_result
            except Exception as e:
                print(f"[DEBUG] Amazon.com.tr hatası: {e}")
        
        # 5. NADIRKITAP.COM (İkinci el kitap sitesi)
        if kitap_adi and yazar:
            try:
                print(f"[DEBUG] NadirKitap.com deneniyor: {kitap_adi[:50]}...")
                nadirkitap_result = self._search_nadirkitap(kitap_adi, yazar)
                if nadirkitap_result:
                    return nadirkitap_result
            except Exception as e:
                print(f"[DEBUG] NadirKitap.com hatası: {e}")
        
        print(f"[DEBUG] Tüm Türkçe kaynaklar başarısız (Wikipedia TR, Google Books TR, Kitapyurdu, Amazon TR, NadirKitap): {query[:50]}...")
        return ""
    
    def _browse_page(self, url: str) -> str:
        """Bir web sayfasının içeriğini çeker (token tasarrufu için kısaltılmış)"""
        try:
            response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            return text[:5000]  # Kısalt, token için
        except Exception as e:
            print(f"[DEBUG] Page browse hatası: {e}")
            return ""
    
    def _parse_ai_response(self, content: str) -> Optional[Dict[str, str]]:
        """AI response'unu parse eder ve dict'e çevirir (esnek parsing - eksik JSON'ları da handle eder)"""
        if not content:
            return None
        
        try:
            # Önce ```json ... ``` formatını kontrol et
            json_block_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_block_match:
                json_str = json_block_match.group(1)
            else:
                # Sonra sadece {...} formatını ara (daha esnek - eksik JSON'ları da handle et)
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    # Eğer hiç JSON bulunamazsa, content'in başından itibaren { ile başlayan kısmı al
                    start_idx = content.find('{')
                    if start_idx != -1:
                        json_str = content[start_idx:]
                    else:
                        return None
            
            # JSON'u parse et
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                # JSON parse hatası - eksik JSON olabilir, düzeltmeye çalış
                print(f"[DEBUG] JSON parse hatası (ilk deneme): {e}")
                
                # Eksik JSON'u düzeltmeye çalış (son kapanış parantezlerini ekle)
                if not json_str.strip().endswith('}'):
                    # Eksik kapanış parantezleri ekle
                    open_count = json_str.count('{')
                    close_count = json_str.count('}')
                    missing_closes = open_count - close_count
                    if missing_closes > 0:
                        json_str += '}' * missing_closes
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError:
                            pass
                
                # Eğer hala parse edilemezse, manuel olarak key-value çiftlerini çıkar
                print(f"[DEBUG] JSON parse başarısız, manuel parsing deneniyor...")
                result = {}
                
                # Key-value çiftlerini regex ile bul
                # "Orijinal Adı": "..." formatını ara
                field_patterns = {
                    "Orijinal Adı": r'"Orijinal Adı"\s*:\s*"([^"]*)"',
                    "Tür": r'"Tür"\s*:\s*"([^"]*)"',
                    "Ülke/Edebi Gelenek": r'"Ülke/Edebi Gelenek"\s*:\s*"([^"]*)"',
                    "İlk Yayınlanma Tarihi": r'"İlk Yayınlanma Tarihi"\s*:\s*"([^"]*)"',
                    "Anlatı Yılı": r'"Anlatı Yılı"\s*:\s*"([^"]*)"',
                    "Konusu": r'"Konusu"\s*:\s*"([^"]*)"',
                }
                
                for field, pattern in field_patterns.items():
                    match = re.search(pattern, json_str, re.IGNORECASE)
                    if match:
                        result[field] = match.group(1).strip()
                
                if result:
                    print(f"[DEBUG] Manuel parsing başarılı: {list(result.keys())}")
                    return result
                else:
                    print(f"[DEBUG] Manuel parsing de başarısız")
                    return None
                    
        except Exception as e:
            print(f"[DEBUG] _parse_ai_response genel hata: {e}")
            return None
    
    def _groq_ai_cek(self, kitap_adi: str, yazar: str, eksik_alanlar: list, mevcut_bilgiler: dict) -> Optional[Dict[str, str]]:
        """Groq AI API kullanarak eksik kitap bilgilerini çeker (Tool-Friendly: İlk kısa prompt, bilmiyorsa web search)"""
        try:
            # API key'i temizle (başında/sonunda boşluk olabilir)
            api_key = (self.groq_api_key or '').strip()
            if not api_key:
                return None
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            eksik_alan_str = ", ".join(eksik_alanlar)
            
            # ADIM 1: İlk kısa prompt (token tasarrufu) - AI'ye kitap sor, eğer obscure ise "WEB_SEARCH" dönsün
            first_prompt = f"""Kitap: {kitap_adi}, Yazar: {yazar}
Eksik alanlar: {eksik_alan_str}

Bu kitap hakkında bilgileri biliyorsan doğrudan JSON formatında ver. Bilmiyorsan veya emin değilsen, sadece "WEB_SEARCH" yaz.

JSON formatı:
{{
    "Orijinal Adı": "...",
    "Tür": "...",
    "Ülke/Edebi Gelenek": "...",
    "İlk Yayınlanma Tarihi": "...",
    "Anlatı Yılı": "...",
    "Konusu": "..."
}}"""
            
            data_first = {
                'model': 'openai/gpt-oss-20b',
                'messages': [
                    {
                        'role': 'system',
                        'content': 'Sen bir kitap bilgisi uzmanısın. Bilgileri biliyorsan JSON döndür, bilmiyorsan "WEB_SEARCH" yaz.'
                    },
                    {
                        'role': 'user',
                        'content': first_prompt
                    }
                ],
                'temperature': 0.3,
                'max_tokens': 500  # Kısa prompt, token tasarrufu
            }
            
            response_first = requests.post(self.groq_api_url, headers=headers, json=data_first, timeout=30)
            self._last_status_code = response_first.status_code
            
            if response_first.status_code != 200:
                return None
            
            result_first = response_first.json()
            if 'choices' not in result_first or len(result_first['choices']) == 0:
                return None
            
            content_first = result_first.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # Token kullanımını logla
            usage = result_first.get('usage', {})
            print(f"[DEBUG] GPT-OSS-20B ilk sorgu token: {usage.get('total_tokens', 0)} (prompt: {usage.get('prompt_tokens', 0)}, completion: {usage.get('completion_tokens', 0)})")
            
            # Eğer "WEB_SEARCH" derse veya boş dönerse, web search yap
            needs_web_search = 'WEB_SEARCH' in content_first.upper() or not content_first.strip()
            
            if needs_web_search:
                print(f"[DEBUG] GPT-OSS-20B bilmiyor, web search yapılıyor: {kitap_adi} - {yazar}")
                
                # ADIM 2: Web search yap (sadece kitap adı ve yazar - gereksiz kelimeler kaldırıldı)
                search_query = f"{kitap_adi} {yazar}"
                search_results = self._web_search(search_query, num_results=5, kitap_adi=kitap_adi, yazar=yazar)
                
                if not search_results:
                    print(f"[DEBUG] Web search sonuç bulamadı")
                    return None
                
                # ADIM 3: Web search sonuçlarını AI'ye ver, parse ettir (token tasarrufu için kısalt)
                parse_prompt = f"""Bu web arama sonuçlarından kitap bilgilerini parse et:

{search_results[:2000]}  # Token tasarrufu için kısalt

Kitap: {kitap_adi}, Yazar: {yazar}
Eksik alanlar: {eksik_alan_str}

JSON formatında döndür:
{{
    "Orijinal Adı": "...",
    "Tür": "...",
    "Ülke/Edebi Gelenek": "...",
    "İlk Yayınlanma Tarihi": "...",
    "Anlatı Yılı": "...",
    "Konusu": "..."
}}"""
                
                data_parse = {
                    'model': 'openai/gpt-oss-20b',
                    'messages': [
                        {
                            'role': 'system',
                            'content': 'Sen bir kitap bilgisi uzmanısın. Web arama sonuçlarından bilgileri parse et ve SADECE JSON formatında döndür. Reasoning yapma, direkt JSON döndür. Örnek format:\n{\n    "Orijinal Adı": "...",\n    "Tür": "...",\n    "Ülke/Edebi Gelenek": "...",\n    "İlk Yayınlanma Tarihi": "...",\n    "Anlatı Yılı": "...",\n    "Konusu": "..."\n}'
                        },
                        {
                            'role': 'user',
                            'content': parse_prompt
                        }
                    ],
                    'temperature': 0.1,  # Daha düşük temperature (daha deterministik)
                    'max_tokens': 1000  # Parse için yeterli
                }
                
                response_parse = requests.post(self.groq_api_url, headers=headers, json=data_parse, timeout=30)
                if response_parse.status_code == 200:
                    result_parse = response_parse.json()
                    if 'choices' in result_parse and len(result_parse['choices']) > 0:
                        content_parse = result_parse.get('choices', [{}])[0].get('message', {}).get('content', '')
                        
                        # Token kullanımını logla
                        usage_parse = result_parse.get('usage', {})
                        print(f"[DEBUG] GPT-OSS-20B parse sorgu token: {usage_parse.get('total_tokens', 0)} (prompt: {usage_parse.get('prompt_tokens', 0)}, completion: {usage_parse.get('completion_tokens', 0)})")
                        
                        # Content'i logla (ilk 500 karakter)
                        if content_parse:
                            print(f"[DEBUG] GPT-OSS-20B parse response (ilk 500 karakter): {content_parse[:500]}...")
                        else:
                            # Reasoning mode kontrolü - eğer reasoning varsa, onu parse etmeye çalış
                            reasoning = result_parse.get('choices', [{}])[0].get('message', {}).get('reasoning', '')
                            if reasoning:
                                print(f"[DEBUG] GPT-OSS-20B parse response boş ama reasoning var (ilk 500 karakter): {reasoning[:500]}...")
                                # Reasoning'den bilgi çıkarmaya çalış - ama bu güvenilir değil
                                # İkinci bir request yap, daha kısa ve direkt prompt ile
                                print(f"[DEBUG] GPT-OSS-20B reasoning mode aktif, ikinci request yapılıyor...")
                                
                                # Daha kısa ve direkt prompt
                                short_prompt = f"""Web arama sonuçları:
{search_results[:1500]}

Kitap: {kitap_adi}, Yazar: {yazar}

SADECE JSON döndür (başka açıklama yok):
{{
    "Orijinal Adı": "...",
    "Tür": "...",
    "Ülke/Edebi Gelenek": "...",
    "İlk Yayınlanma Tarihi": "...",
    "Anlatı Yılı": "...",
    "Konusu": "..."
}}"""
                                
                                data_retry = {
                                    'model': 'openai/gpt-oss-20b',
                                    'messages': [
                                        {
                                            'role': 'system',
                                            'content': 'SADECE JSON döndür. Başka hiçbir şey yazma.'
                                        },
                                        {
                                            'role': 'user',
                                            'content': short_prompt
                                        }
                                    ],
                                    'temperature': 0.1,
                                    'max_tokens': 800
                                }
                                
                                response_retry = requests.post(self.groq_api_url, headers=headers, json=data_retry, timeout=30)
                                if response_retry.status_code == 200:
                                    result_retry = response_retry.json()
                                    if 'choices' in result_retry and len(result_retry['choices']) > 0:
                                        content_retry = result_retry.get('choices', [{}])[0].get('message', {}).get('content', '')
                                        reasoning_retry = result_retry.get('choices', [{}])[0].get('message', {}).get('reasoning', '')
                                        
                                        if content_retry:
                                            print(f"[DEBUG] GPT-OSS-20B retry response (ilk 500 karakter): {content_retry[:500]}...")
                                            content_parse = content_retry  # Retry response'unu kullan
                                        elif reasoning_retry:
                                            # Reasoning'den bilgi çıkarmaya çalış (son çare)
                                            print(f"[DEBUG] GPT-OSS-20B retry response boş ama reasoning var, reasoning'den parse ediliyor...")
                                            # Reasoning'de JSON olup olmadığını kontrol et (daha esnek)
                                            # Önce ```json ... ``` formatını kontrol et
                                            json_block_match = re.search(r'```json\s*(\{.*?\})\s*```', reasoning_retry, re.DOTALL)
                                            if json_block_match:
                                                json_from_reasoning = json_block_match.group(1)
                                                print(f"[DEBUG] Reasoning'den JSON block çıkarıldı (ilk 300 karakter): {json_from_reasoning[:300]}...")
                                                content_parse = json_from_reasoning
                                            elif '{' in reasoning_retry and '}' in reasoning_retry:
                                                # Reasoning'den JSON çıkarmaya çalış (daha esnek - tüm JSON'u bul)
                                                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', reasoning_retry, re.DOTALL)
                                                if json_match:
                                                    json_from_reasoning = json_match.group(0)
                                                    print(f"[DEBUG] Reasoning'den JSON çıkarıldı (ilk 300 karakter): {json_from_reasoning[:300]}...")
                                                    content_parse = json_from_reasoning
                                                else:
                                                    # Son çare: ilk { ve son } arasındaki her şeyi al
                                                    json_start = reasoning_retry.find('{')
                                                    json_end = reasoning_retry.rfind('}') + 1
                                                    if json_start != -1 and json_end > json_start:
                                                        json_from_reasoning = reasoning_retry[json_start:json_end]
                                                        print(f"[DEBUG] Reasoning'den JSON çıkarıldı (son çare, ilk 300 karakter): {json_from_reasoning[:300]}...")
                                                        content_parse = json_from_reasoning
                                                    else:
                                                        print(f"[DEBUG] Reasoning'den JSON çıkarılamadı")
                                                        return None
                                            else:
                                                print(f"[DEBUG] Reasoning'de JSON yok")
                                                return None
                                        else:
                                            print(f"[DEBUG] GPT-OSS-20B retry response de boş!")
                                            return None
                                    else:
                                        return None
                                else:
                                    print(f"[DEBUG] GPT-OSS-20B retry request başarısız: {response_retry.status_code}")
                                    return None
                            else:
                                print(f"[DEBUG] GPT-OSS-20B parse response boş ve reasoning yok!")
                                # Full response'u logla
                                print(f"[DEBUG] GPT-OSS-20B parse full response: {json.dumps(result_parse, indent=2)[:1000]}...")
                                return None
                        
                        # Parse et
                        bilgiler = self._parse_ai_response(content_parse)
                        if bilgiler:
                            print(f"[DEBUG] GPT-OSS-20B parse edilen bilgiler: {list(bilgiler.keys())}")
                            # Sadece eksik alanları döndür
                            sonuc = {}
                            for alan in eksik_alanlar:
                                if alan in bilgiler and bilgiler[alan]:
                                    sonuc[alan] = str(bilgiler[alan]).strip()
                            
                            if sonuc:
                                print(f"[DEBUG] GPT-OSS-20B Web Search ile bilgiler bulundu: {list(sonuc.keys())}")
                            else:
                                print(f"[DEBUG] GPT-OSS-20B Parse edilen bilgiler eksik alanlarla eşleşmedi")
                            return sonuc
                        else:
                            print(f"[DEBUG] GPT-OSS-20B Parse başarısız - JSON parse edilemedi")
                            print(f"[DEBUG] GPT-OSS-20B Parse edilemeyen content: {content_parse[:500]}...")
                            return None
                    else:
                        print(f"[DEBUG] GPT-OSS-20B parse response'da choices yok")
                        return None
                else:
                    print(f"[DEBUG] GPT-OSS-20B parse request başarısız: {response_parse.status_code}")
                    return None
            else:
                # ADIM 4: İlk prompt'tan gelen bilgileri parse et
                bilgiler = self._parse_ai_response(content_first)
                if bilgiler:
                    # Sadece eksik alanları döndür
                    sonuc = {}
                    for alan in eksik_alanlar:
                        if alan in bilgiler and bilgiler[alan]:
                            sonuc[alan] = str(bilgiler[alan]).strip()
                    
                    if sonuc:
                        print(f"[DEBUG] GPT-OSS-20B Training data'dan bilgiler bulundu: {list(sonuc.keys())}")
                    return sonuc
            
            return None
            
        except requests.exceptions.Timeout:
            return None
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] GPT-OSS-20B request hatası: {e}")
            return None
        except Exception as e:
            print(f"[DEBUG] GPT-OSS-20B genel hata: {e}")
            return None
    
    def _huggingface_ai_cek(self, kitap_adi: str, yazar: str, eksik_alanlar: list, mevcut_bilgiler: dict) -> Optional[Dict[str, str]]:
        """Hugging Face Inference API kullanarak eksik kitap bilgilerini çeker (ücretsiz, yedek API)"""
        try:
            
            # Eksik bilgiler için prompt oluştur
            eksik_alan_str = ", ".join(eksik_alanlar)
            mevcut_bilgi_str = "\n".join([f"- {k}: {v}" for k, v in mevcut_bilgiler.items() if v])
            
            prompt = f"""Sen bir kitap bilgisi uzmanısın. Aşağıdaki kitap hakkında eksik bilgileri doldur.

Kitap Adı (Türkçe): {kitap_adi}
Yazar: {yazar}

Mevcut Bilgiler:
{mevcut_bilgi_str if mevcut_bilgi_str else "Henüz bilgi yok"}

Eksik Bilgiler: {eksik_alan_str}

Lütfen şu bilgileri bul ve JSON formatında döndür:
- Orijinal Adı: Kitabın ilk çıktığı dildeki orijinal adı (Türkçe çeviri değil!)
- Tür: Roman, Novella, Öykü, Felsefe, Tarih, Bilim, Şiir, Tiyatro (sadece birini seç)
- Ülke/Edebi Gelenek: Kitabın ilk çıktığı ülke (yazarın ülkesi, Türkçe çeviri değil!)
- İlk Yayınlanma Tarihi: Kitabın yazıldığı/yayınlandığı ilk yıl (basım yılı değil, ilk yayın yılı)
- Anlatı Yılı: Kitabın anlattığı olayların geçtiği yıl veya yıl aralığı (örn: "1865", "1865-1869", "19. yüzyıl"). Eğer kitap belirli bir dönemi anlatmıyorsa boş bırak.
- Konusu: Kitabın konusunu 1-2 cümle ile açıkla

ÖNEMLİ:
- Orijinal Adı: 
  * Türkçe çeviri değil, kitabın ilk çıktığı dildeki adı olmalı
  * Eğer orijinal dil Kiril, Arap, Çin, Japon, Kore veya başka bir alfabe kullanıyorsa, MUTLAKA Latin harflerine transliterasyon yap (örn: Kiril "Война и мир" → Latin "Voina i mir")
  * Her zaman Latin alfabesi kullan, orijinal alfabeyi kullanma
- Ülke: Türkçe çeviri değil, kitabın ilk çıktığı ülke olmalı (yazarın ülkesi)
- İlk Yayınlanma Tarihi: İlk yayınlandığı yıl, basım yılı değil
- Anlatı Yılı: Kitabın anlattığı olayların geçtiği tarihsel dönem. Eğer belirli bir dönem yoksa boş bırak.

Sadece JSON formatında döndür, başka açıklama yapma. Örnek format:
{{
    "Orijinal Adı": "...",
    "Tür": "...",
    "Ülke/Edebi Gelenek": "...",
    "İlk Yayınlanma Tarihi": "...",
    "Anlatı Yılı": "...",
    "Konusu": "..."
}}"""

            headers = {
                'Content-Type': 'application/json'
            }
            
            # API key varsa ekle (rate limit'i artırır)
            if self.huggingface_api_key:
                headers['Authorization'] = f'Bearer {self.huggingface_api_key}'
            
            # Hugging Face Router API formatı (güncellenmiş)
            # Router API formatı biraz farklı olabilir, önce eski formatı dene
            data = {
                'inputs': prompt,
                'parameters': {
                    'max_new_tokens': 500,
                    'temperature': 0.3,
                    'return_full_text': False
                }
            }
            
            response = requests.post(self.huggingface_api_url, headers=headers, json=data, timeout=30)
            self._last_status_code = response.status_code
            
            if response.status_code == 200:
                result = response.json()
                
                # Hugging Face yanıt formatı: [{"generated_text": "..."}]
                if isinstance(result, list) and len(result) > 0:
                    content = result[0].get('generated_text', '')
                elif isinstance(result, dict):
                    content = result.get('generated_text', '')
                else:
                    return None
                
                if not content:
                    return None
                
                # JSON'u parse et
                try:
                    # Önce ```json ... ``` formatını kontrol et
                    json_block_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                    if json_block_match:
                        json_str = json_block_match.group(1)
                    else:
                        # Sonra sadece {...} formatını ara
                        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(0)
                        else:
                            return None
                    
                    bilgiler = json.loads(json_str)
                    
                    # Sadece eksik alanları döndür
                    sonuc = {}
                    for alan in eksik_alanlar:
                        if alan in bilgiler and bilgiler[alan]:
                            sonuc[alan] = str(bilgiler[alan]).strip()
                    
                    return sonuc
                    
                except json.JSONDecodeError:
                    return None
            elif response.status_code == 503:
                # Model yükleniyor, router tarafından yönetilecek
                return None
            else:
                # Hata durumu
                return None
            
        except requests.exceptions.Timeout:
            return None
        except requests.exceptions.RequestException:
            return None
        except Exception:
            return None

    def _together_ai_cek(self, kitap_adi: str, yazar: str, eksik_alanlar: list, mevcut_bilgiler: dict) -> Optional[Dict[str, str]]:
        """Together AI API kullanarak eksik kitap bilgilerini çeker (alternatif yedek API)"""
        try:
            if not self.together_api_key:
                return None

            eksik_alan_str = ", ".join(eksik_alanlar)
            mevcut_bilgi_str = "\n".join([f"- {k}: {v}" for k, v in mevcut_bilgiler.items() if v])

            prompt = f"""Sen bir kitap bilgisi uzmanısın. Aşağıdaki kitap hakkında eksik bilgileri doldur.

Kitap Adı (Türkçe): {kitap_adi}
Yazar: {yazar}

Mevcut Bilgiler:
{mevcut_bilgi_str if mevcut_bilgi_str else "Henüz bilgi yok"}

Eksik Bilgiler: {eksik_alan_str}

Lütfen şu bilgileri bul ve JSON formatında döndür:
- Orijinal Adı
- Tür
- Ülke/Edebi Gelenek
- İlk Yayınlanma Tarihi
- Anlatı Yılı
- Konusu
Sadece JSON döndür."""

            headers = {
                'Authorization': f'Bearer {self.together_api_key}',
                'Content-Type': 'application/json'
            }
            data = {
                'model': 'meta-llama/Llama-3.1-70B-Instruct-Turbo',
                'messages': [
                    {'role': 'system', 'content': 'Sadece JSON formatında yanıt ver.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.3,
                'max_tokens': 500
            }
            response = requests.post(self.together_api_url, headers=headers, json=data, timeout=30)
            self._last_status_code = response.status_code

            if response.status_code != 200:
                return None

            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            if not content:
                return None

            # JSON parse
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            if not json_match:
                return None

            bilgiler = json.loads(json_match.group(0))
            sonuc = {}
            for alan in eksik_alanlar:
                if alan in bilgiler and bilgiler[alan]:
                    sonuc[alan] = str(bilgiler[alan]).strip()
            return sonuc
        except Exception:
            return None

    def _wikipedia_fetch_lang(self, kitap_adi: str, yazar: str, lang: str) -> Dict[str, str]:
        """Belirli dilde Wikipedia özetinden bilgi çeker ve parse eder."""
        try:
            from urllib.parse import quote

            arama_terimleri = [
                f"{kitap_adi} ({yazar})",
                kitap_adi,
                f"{yazar} {kitap_adi}",
            ]
            for arama_terimi in arama_terimleri:
                url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{quote(arama_terimi)}"
                print(f"[DEBUG] Wikipedia {lang} arama: {arama_terimi} -> {url}")
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    extract = data.get('extract', '')
                    if not extract:
                        print(f"[DEBUG] Wikipedia {lang} sayfa bulundu ama extract boş: {arama_terimi}")
                        continue
                    if yazar.lower() in extract.lower() or arama_terimi == kitap_adi:
                        fields = self._wikipedia_parse(data, kitap_adi, yazar, lang=lang)
                        fields["_extract"] = extract
                        fields["_title"] = data.get("title", "")
                        wikibase_item = data.get("wikibase_item", "")
                        fields["_wikibase_item"] = wikibase_item
                        print(f"[DEBUG] Wikipedia {lang} başarılı: title='{fields['_title']}', wikibase_item='{wikibase_item}'")
                        return fields
                    else:
                        print(f"[DEBUG] Wikipedia {lang} sayfa bulundu ama yazar eşleşmedi: {arama_terimi}")
                else:
                    print(f"[DEBUG] Wikipedia {lang} sayfa bulunamadı (status={response.status_code}): {arama_terimi}")
        except Exception as e:
            print(f"[DEBUG] Wikipedia {lang} hata: {e}")
            pass
        print(f"[DEBUG] Wikipedia {lang} hiçbir sayfa bulunamadı")
        return {}

    def _collect_sources(self, kitap_adi: str, yazar: str) -> Dict[str, Dict[str, str]]:
        sources: Dict[str, Dict[str, str]] = {}

        enwiki = self._wikipedia_fetch_lang(kitap_adi, yazar, "en")
        if enwiki:
            sources["enwiki"] = enwiki
            print(f"[DEBUG] enwiki: Ilk Yayinlanma Tarihi='{enwiki.get('İlk Yayınlanma Tarihi', '')}', Ulke='{enwiki.get('Ülke/Edebi Gelenek', '')}'")

        trwiki = self._wikipedia_fetch_lang(kitap_adi, yazar, "tr")
        if trwiki:
            sources["trwiki"] = trwiki
            print(f"[DEBUG] trwiki: Ilk Yayinlanma Tarihi='{trwiki.get('İlk Yayınlanma Tarihi', '')}', Ulke='{trwiki.get('Ülke/Edebi Gelenek', '')}'")

        gbooks = self._google_books_cek(kitap_adi, yazar) or {}
        if gbooks:
            sources["gbooks"] = gbooks
            print(f"[DEBUG] gbooks: Ilk Yayinlanma Tarihi='{gbooks.get('İlk Yayınlanma Tarihi', '')}', Ulke='{gbooks.get('Ülke/Edebi Gelenek', '')}'")

        openlib = self._open_library_cek(kitap_adi, yazar) or {}
        if openlib:
            sources["openlibrary"] = openlib
            print(f"[DEBUG] openlibrary: Ilk Yayinlanma Tarihi='{openlib.get('İlk Yayınlanma Tarihi', '')}', Ulke='{openlib.get('Ülke/Edebi Gelenek', '')}'")

        # Wikidata
        qid = (
            sources.get("enwiki", {}).get("_wikibase_item")
            or sources.get("trwiki", {}).get("_wikibase_item")
        )
        if qid:
            print(f"[DEBUG] Wikidata QID bulundu (Wikipedia'dan): {qid}")
        else:
            print(f"[DEBUG] Wikidata QID Wikipedia'dan bulunamadı - enwiki wikibase_item: {sources.get('enwiki', {}).get('_wikibase_item')}, trwiki wikibase_item: {sources.get('trwiki', {}).get('_wikibase_item')}")
            
        # Fallback: Wikipedia title'ından QID bul
        if not qid and "enwiki" in sources and sources["enwiki"].get("_title"):
            print(f"[DEBUG] Wikidata QID bulma denemesi: enwiki title='{sources['enwiki']['_title']}'")
            qid = qid_from_wikipedia(sources["enwiki"]["_title"], "en")
            if qid:
                print(f"[DEBUG] Wikidata QID bulundu (enwiki title'dan): {qid}")
        if not qid and "trwiki" in sources and sources["trwiki"].get("_title"):
            print(f"[DEBUG] Wikidata QID bulma denemesi: trwiki title='{sources['trwiki']['_title']}'")
            qid = qid_from_wikipedia(sources["trwiki"]["_title"], "tr")
            if qid:
                print(f"[DEBUG] Wikidata QID bulundu (trwiki title'dan): {qid}")
        
        # Son çare: SPARQL sorgusu ile doğrudan Wikidata'da arama
        if not qid:
            print(f"[DEBUG] Wikidata QID bulma denemesi: SPARQL sorgusu (kitap_adi='{kitap_adi}', yazar='{yazar}')")
            qid = qid_from_sparql_search(kitap_adi, yazar)
            if qid:
                print(f"[DEBUG] Wikidata QID bulundu (SPARQL sorgusu): {qid}")
            else:
                print(f"[DEBUG] Wikidata QID bulunamadı (SPARQL sorgusu da başarısız)")
        
        if qid:
            print(f"[DEBUG] Wikidata entity fetch ediliyor: {qid}")
            entity = fetch_entity(qid)
            if not entity:
                print(f"[DEBUG] Wikidata entity fetch başarısız: {qid}")
            else:
                print(f"[DEBUG] Wikidata entity fetch başarılı: {qid}")
                wd_fields = extract_fields(entity)
                if wd_fields:
                    wd_fields["_qid"] = qid
                    sources["wikidata"] = wd_fields
                    print(f"[DEBUG] wikidata: Ilk Yayinlanma Tarihi='{wd_fields.get('İlk Yayınlanma Tarihi', '')}', Ulke='{wd_fields.get('Ülke/Edebi Gelenek', '')}', Orijinal Adi='{wd_fields.get('Orijinal Adı', '')}'")
                else:
                    print(f"[DEBUG] Wikidata extract_fields boş döndü: {qid} (entity var ama field'lar extract edilemedi)")
        else:
            print(f"[DEBUG] Wikidata QID bulunamadı - Wikidata kullanılamıyor")

        return sources

    def kitap_bilgisi_cek_policy(self, kitap_adi: str, yazar: str, mevcut: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Field-policy tabanlı bilgi çekme.
        ⚠️ SADECE GPT-OSS-20B (groq) kullanılıyor - diğer tüm kaynaklar devre dışı.
        """
        row = ensure_row_schema(mevcut or {})
        rules = build_rules()
        
        # ⚠️ _collect_sources() çağrısı kaldırıldı - diğer kaynaklar kullanılmıyor
        # sources = self._collect_sources(kitap_adi, yazar)  # DEVRE DIŞI
        
        # Alan bazlı doldurma (non-AI) - DEVRE DIŞI (sadece AI kullanılıyor)
        # for field, rule in rules.items():
        #     if row.get(field):
        #         continue
        #     for source in rule.sources:
        #         if source not in sources:
        #             continue
        #         candidate = sources[source].get(field)
        #         if not candidate:
        #             continue
        #         ... (kaldırıldı)

        # SADECE AI kullan - tüm eksik alanlar için
        missing = [f for f in rules.keys() if not row.get(f)]
        
        if missing:
            print(f"[DEBUG] GPT-OSS-20B ile eksik alanlar dolduruluyor: {missing}")
            # Sadece Groq AI kullan (diğer AI'lar devre dışı)
            def _call_groq():
                result = self._groq_ai_cek(kitap_adi, yazar, missing, row)
                return result, self._last_status_code
            
            ai_data = self.router.call("groq", _call_groq)
            if ai_data:
                for field, value in ai_data.items():
                    if field in rules and not row.get(field) and value:
                        set_field(row, field, str(value).strip(), "groq", 0.8)
                missing = [f for f in rules.keys() if not row.get(f)]
        
        # Status güncelleme
        status = "OK" if not missing else ("PARTIAL" if any(row.get(f) for f in rules.keys()) else "FAIL")
        retry_count = 0 if status == "OK" else 1
        next_retry_hours = 6 if status != "OK" else None
        set_row_status(row, status, missing, best_source="groq", wikidata_qid="", retry_count=retry_count, next_retry_hours=next_retry_hours)
        return row

