"""
Kitap Bilgisi Çekici Modülü
Wikipedia, Google Books, Open Library ve Groq AI API'lerini kullanarak kitap bilgilerini çeker
"""

import requests
import re
from typing import Dict, Optional
import time
import json
import os

from field_policy import build_rules
from provenance import set_field, set_row_status
from router import QuotaRouter
from wikidata_client import qid_from_wikipedia, fetch_entity, extract_fields
from field_registry import ensure_row_schema


class KitapBilgisiCekici:
    def __init__(self):
        self.wikipedia_base_url = "https://tr.wikipedia.org/api/rest_v1/page/summary/"
        self.google_books_url = "https://www.googleapis.com/books/v1/volumes"
        self.open_library_url = "https://openlibrary.org/search.json"
        self.groq_api_url = "https://api.groq.com/openai/v1/chat/completions"
        # Groq API key - kullanıcıdan alınacak veya environment variable'dan
        self.groq_api_key = os.getenv('GROQ_API_KEY', '')
        # Hugging Face Inference API (ücretsiz, API key gerektirmez ama rate limit var)
        # ⚠️ NOT: router.huggingface.co 404 veriyor, eski api-inference.huggingface.co'yu tekrar deniyoruz
        self.huggingface_api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        # Together AI API (ücretsiz tier var, alternatif yedek API)
        self.together_api_url = "https://api.together.xyz/v1/chat/completions"
        self.together_api_key = os.getenv('TOGETHER_API_KEY', '')
        # Hugging Face API key - önce dosyadan, sonra environment variable'dan dene
        self.huggingface_api_key = self._huggingface_key_yukle()
        # Router state for AI providers
        self.router = QuotaRouter()
        self._last_status_code: Optional[int] = None
    
    def _huggingface_key_yukle(self) -> str:
        """Hugging Face API key'i yükler (önce dosyadan, sonra environment variable'dan)"""
        # Önce dosyadan dene
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
        
        # Dosyadan yüklenemediyse environment variable'dan dene
        env_key = os.getenv('HUGGINGFACE_API_KEY', '')
        if env_key:
            return env_key
        
        return ''
        
    def kitap_bilgisi_cek(self, kitap_adi: str, yazar: str) -> Dict[str, str]:
        """
        Çoklu kaynaktan kitap bilgilerini çeker
        
        Args:
            kitap_adi: Kitap adı (Türkçe)
            yazar: Yazar adı
            
        Returns:
            Dict: Kitap bilgileri (Orijinal Adı, Tür, Ülke/Edebi Gelenek, Çıkış Yılı, Konusu)
        """
        sonuc = {
            "Orijinal Adı": "",
            "Tür": "",
            "Ülke/Edebi Gelenek": "",
            "Çıkış Yılı": "",
            "Anlatı Yılı": "",
            "Konusu": ""
        }
        
        # Önce Wikipedia'dan dene
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
        """Wikipedia'dan kitap bilgilerini çeker - Önce İngilizce'de ara (orijinal bilgiler için)"""
        try:
            from urllib.parse import quote
            
            # Önce İngilizce Wikipedia'da ara (orijinal dildeki bilgiler için)
            # Yazar adı ile birlikte ara
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
                    # Yazar adının da eşleştiğini kontrol et
                    extract = data.get('extract', '').lower()
                    if yazar.lower() in extract or arama_terimi == kitap_adi:
                        return self._wikipedia_parse(data, kitap_adi, yazar, lang='en')
            
            # İngilizce'de bulunamazsa Türkçe'de dene
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
        """Wikipedia verisini parse eder - İyileştirilmiş versiyon"""
        sonuc = {}
        extract = data.get('extract', '')
        title = data.get('title', '')
        
        # Orijinal adı: İngilizce sayfadaysa title'ı kullan (orijinal dildeki adı)
        # Türkçe sayfadaysa "Orijinal adı:" veya parantez içindeki adı bul
        if lang == 'en':
            # İngilizce sayfada title genellikle orijinal adıdır
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
                        # Türkçe karakterler içermiyorsa orijinal adı olabilir
                        if not any(c in parantez_icerik for c in 'çğıöşüÇĞIİÖŞÜ'):
                            sonuc["Orijinal Adı"] = parantez_icerik.strip()
        else:
            # Türkçe sayfada "Orijinal adı:" veya parantez içindeki adı bul
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
        
        # Çıkış yılı: "published", "written", "first published" gibi kelimelerden sonraki yılı bul
        # Basım yılı değil, yazıldığı/yayınlandığı ilk yıl
        if extract:
            # "first published in", "written in", "published in" gibi ifadeleri ara
            yil_patterns = [
                r'(?:first published|originally published|written|published)\s+(?:in\s+)?(\d{4})',
                r'(\d{4})\s+(?:yılında|yılı|year|yayınlandı|published|written)',
                r'\b(1[5-9]\d{2}|20[0-2]\d)\b'
            ]
            
            for pattern in yil_patterns:
                yil_match = re.search(pattern, extract, re.IGNORECASE)
                if yil_match:
                    try:
                        yil = int(yil_match.group(1))
                        if 1500 <= yil <= 2030:
                            sonuc["Çıkış Yılı"] = str(yil)
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
        
        # Çıkış yılı: publishedDate'ten ilk yılı al
        if 'publishedDate' in volume_info:
            tarih = volume_info['publishedDate']
            # Yıl formatı: YYYY, YYYY-MM, veya YYYY-MM-DD olabilir
            yil_match = re.search(r'\b(1[5-9]\d{2}|20[0-2]\d)\b', tarih)
            if yil_match:
                yil = int(yil_match.group(1))
                if 1500 <= yil <= 2030:
                    sonuc["Çıkış Yılı"] = str(yil)
        
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
        
        # Ülke/Edebi Gelenek: Yazarın ülkesini bul (language'dan değil, yazar bilgisinden)
        # Language kitabın çevrildiği dili gösterir, yazarın ülkesini değil
        # Ancak eğer language bilgisi varsa ve yazar bilgisi yoksa, language'ı kullan
        authors = volume_info.get('authors', [])
        if authors:
            # Yazar bilgisinden ülke çıkaramıyoruz, bu yüzden language'ı kullan
            # Ama bu yanıltıcı olabilir çünkü çeviri kitaplar için yanlış olabilir
            pass  # Bu bilgiyi Groq API'den alacağız
        
        # Language bilgisini sadece son çare olarak kullan
        if 'language' in volume_info and "Ülke/Edebi Gelenek" not in sonuc:
            dil = volume_info['language']
            dil_ulke_map = {
                'tr': 'Türkiye',
                'en': 'İngiltere',  # İngilizce genellikle İngiltere veya Amerika, ama varsayılan İngiltere
                'fr': 'Fransa',
                'de': 'Almanya',
                'es': 'İspanya',
                'it': 'İtalya',
                'ru': 'Rusya',
                'ja': 'Japonya',
                'zh': 'Çin',
                'pt': 'Portekiz',
                'nl': 'Hollanda',
                'pl': 'Polonya',
                'cs': 'Çek Cumhuriyeti',
                'sv': 'İsveç',
                'no': 'Norveç',
                'da': 'Danimarka',
                'fi': 'Finlandiya',
                'hu': 'Macaristan',
                'ro': 'Romanya',
                'bg': 'Bulgaristan',
                'el': 'Yunanistan',
                'ar': 'Arap Ülkeleri',
                'he': 'İsrail',
                'ko': 'Güney Kore',
                'hi': 'Hindistan'
            }
            if dil in dil_ulke_map:
                sonuc["Ülke/Edebi Gelenek"] = dil_ulke_map[dil]
        
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
        
        # Çıkış yılı: first_publish_year kullan (ilk yayınlandığı yıl - doğru!)
        if 'first_publish_year' in doc and doc['first_publish_year']:
            yil = doc['first_publish_year']
            if isinstance(yil, int) and 1500 <= yil <= 2030:
                sonuc["Çıkış Yılı"] = str(yil)
        elif 'publish_year' in doc and doc['publish_year']:
            yillar = doc['publish_year']
            if isinstance(yillar, list) and len(yillar) > 0:
                # En eski yılı al
                yillar_int = [y for y in yillar if isinstance(y, int) and 1500 <= y <= 2030]
                if yillar_int:
                    sonuc["Çıkış Yılı"] = str(min(yillar_int))
        
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
    
    def _groq_ai_cek(self, kitap_adi: str, yazar: str, eksik_alanlar: list, mevcut_bilgiler: dict) -> Optional[Dict[str, str]]:
        """Groq AI API kullanarak eksik kitap bilgilerini çeker"""
        try:
            # API key'i temizle (başında/sonunda boşluk olabilir)
            api_key = (self.groq_api_key or '').strip()
            if not api_key:
                return None
            
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
- Çıkış Yılı: Kitabın yazıldığı/yayınlandığı ilk yıl (basım yılı değil, ilk yayın yılı)
- Anlatı Yılı: Kitabın anlattığı olayların geçtiği yıl veya yıl aralığı (örn: "1865", "1865-1869", "19. yüzyıl"). Eğer kitap belirli bir dönemi anlatmıyorsa boş bırak.
- Konusu: Kitabın konusunu 1-2 cümle ile açıkla

ÖNEMLİ:
- Orijinal Adı: 
  * Türkçe çeviri değil, kitabın ilk çıktığı dildeki adı olmalı
  * Eğer orijinal dil Kiril, Arap, Çin, Japon, Kore veya başka bir alfabe kullanıyorsa, MUTLAKA Latin harflerine transliterasyon yap (örn: Kiril "Война и мир" → Latin "Voina i mir")
  * Her zaman Latin alfabesi kullan, orijinal alfabeyi kullanma
- Ülke: Türkçe çeviri değil, kitabın ilk çıktığı ülke olmalı (yazarın ülkesi)
- Çıkış Yılı: İlk yayınlandığı yıl, basım yılı değil
- Anlatı Yılı: Kitabın anlattığı olayların geçtiği tarihsel dönem. Eğer belirli bir dönem yoksa boş bırak.

Sadece JSON formatında döndür, başka açıklama yapma. Örnek format:
{{
    "Orijinal Adı": "...",
    "Tür": "...",
    "Ülke/Edebi Gelenek": "...",
    "Çıkış Yılı": "...",
    "Anlatı Yılı": "...",
    "Konusu": "..."
}}"""

            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'llama-3.3-70b-versatile',  # Güncellenmiş model (eski: llama-3.1-70b-versatile kullanımdan kaldırıldı)
                'messages': [
                    {
                        'role': 'system',
                        'content': 'Sen bir kitap bilgisi uzmanısın. Sadece JSON formatında yanıt ver.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.3,
                'max_tokens': 500
            }
            
            response = requests.post(self.groq_api_url, headers=headers, json=data, timeout=30)
            self._last_status_code = response.status_code
            
            if response.status_code == 200:
                result = response.json()
                
                # Yanıtı kontrol et
                if 'choices' not in result or len(result['choices']) == 0:
                    return None
                
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
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
            elif response.status_code == 429:
                # Rate limit hatası - router tarafından yönetilecek
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
- Çıkış Yılı: Kitabın yazıldığı/yayınlandığı ilk yıl (basım yılı değil, ilk yayın yılı)
- Anlatı Yılı: Kitabın anlattığı olayların geçtiği yıl veya yıl aralığı (örn: "1865", "1865-1869", "19. yüzyıl"). Eğer kitap belirli bir dönemi anlatmıyorsa boş bırak.
- Konusu: Kitabın konusunu 1-2 cümle ile açıkla

ÖNEMLİ:
- Orijinal Adı: 
  * Türkçe çeviri değil, kitabın ilk çıktığı dildeki adı olmalı
  * Eğer orijinal dil Kiril, Arap, Çin, Japon, Kore veya başka bir alfabe kullanıyorsa, MUTLAKA Latin harflerine transliterasyon yap (örn: Kiril "Война и мир" → Latin "Voina i mir")
  * Her zaman Latin alfabesi kullan, orijinal alfabeyi kullanma
- Ülke: Türkçe çeviri değil, kitabın ilk çıktığı ülke olmalı (yazarın ülkesi)
- Çıkış Yılı: İlk yayınlandığı yıl, basım yılı değil
- Anlatı Yılı: Kitabın anlattığı olayların geçtiği tarihsel dönem. Eğer belirli bir dönem yoksa boş bırak.

Sadece JSON formatında döndür, başka açıklama yapma. Örnek format:
{{
    "Orijinal Adı": "...",
    "Tür": "...",
    "Ülke/Edebi Gelenek": "...",
    "Çıkış Yılı": "...",
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
- Çıkış Yılı
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
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    extract = data.get('extract', '')
                    if not extract:
                        continue
                    if yazar.lower() in extract.lower() or arama_terimi == kitap_adi:
                        fields = self._wikipedia_parse(data, kitap_adi, yazar, lang=lang)
                        fields["_extract"] = extract
                        fields["_title"] = data.get("title", "")
                        fields["_wikibase_item"] = data.get("wikibase_item", "")
                        return fields
        except Exception:
            pass
        return {}

    def _collect_sources(self, kitap_adi: str, yazar: str) -> Dict[str, Dict[str, str]]:
        sources: Dict[str, Dict[str, str]] = {}

        enwiki = self._wikipedia_fetch_lang(kitap_adi, yazar, "en")
        if enwiki:
            sources["enwiki"] = enwiki

        trwiki = self._wikipedia_fetch_lang(kitap_adi, yazar, "tr")
        if trwiki:
            sources["trwiki"] = trwiki

        gbooks = self._google_books_cek(kitap_adi, yazar) or {}
        if gbooks:
            sources["gbooks"] = gbooks

        openlib = self._open_library_cek(kitap_adi, yazar) or {}
        if openlib:
            sources["openlibrary"] = openlib

        # Wikidata
        qid = (
            sources.get("enwiki", {}).get("_wikibase_item")
            or sources.get("trwiki", {}).get("_wikibase_item")
        )
        if not qid and "enwiki" in sources and sources["enwiki"].get("_title"):
            qid = qid_from_wikipedia(sources["enwiki"]["_title"], "en")
        if not qid and "trwiki" in sources and sources["trwiki"].get("_title"):
            qid = qid_from_wikipedia(sources["trwiki"]["_title"], "tr")
        if qid:
            entity = fetch_entity(qid)
            wd_fields = extract_fields(entity)
            if wd_fields:
                wd_fields["_qid"] = qid
                sources["wikidata"] = wd_fields

        return sources

    def kitap_bilgisi_cek_policy(self, kitap_adi: str, yazar: str, mevcut: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Field-policy tabanlı bilgi çekme.
        Sadece boş alanları doldurur ve provenance yazar.
        """
        row = ensure_row_schema(mevcut or {})
        rules = build_rules()
        sources = self._collect_sources(kitap_adi, yazar)

        # Alan bazlı doldurma (non-AI)
        for field, rule in rules.items():
            if row.get(field):
                continue

            for source in rule.sources:
                if source not in sources:
                    continue

                candidate = sources[source].get(field)
                if not candidate:
                    continue

                context = {
                    "source": source,
                    "extract": sources[source].get("_extract", ""),
                    "localized_title": kitap_adi,
                    "author": yazar,
                }
                if rule.gate:
                    ok, reason = rule.gate(candidate, context)
                    if not ok:
                        print(f"Gate RED field='{field}' source='{source}' reason='{reason}' value='{candidate}'")
                        continue

                set_field(row, field, str(candidate).strip(), source, rule.default_conf)
                break

        # AI fallback for missing fields
        missing = [f for f in rules.keys() if not row.get(f)]
        if missing:
            def _call_groq():
                result = self._groq_ai_cek(kitap_adi, yazar, missing, row)
                return result, self._last_status_code

            def _call_hf():
                result = self._huggingface_ai_cek(kitap_adi, yazar, missing, row)
                return result, self._last_status_code

            def _call_together():
                result = self._together_ai_cek(kitap_adi, yazar, missing, row)
                return result, self._last_status_code

            for name, fn in [("groq", _call_groq), ("hf", _call_hf), ("together", _call_together)]:
                ai_data = self.router.call(name, fn)
                if not ai_data:
                    continue
                for field, value in ai_data.items():
                    if field in rules and not row.get(field) and value:
                        set_field(row, field, str(value).strip(), name, 0.4)
                missing = [f for f in rules.keys() if not row.get(f)]
                if not missing:
                    break

        # Status and qid
        qid = ""
        if "wikidata" in sources:
            qid = sources["wikidata"].get("_qid", "")
        status = "OK" if not missing else ("PARTIAL" if any(row.get(f) for f in rules.keys()) else "FAIL")
        retry_count = 0 if status == "OK" else 1
        next_retry_hours = 6 if status != "OK" else None
        set_row_status(row, status, missing, best_source="policy", wikidata_qid=qid, retry_count=retry_count, next_retry_hours=next_retry_hours)
        return row

