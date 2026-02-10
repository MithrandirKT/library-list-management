"""
Liste Yonetimi Modulu
Kitap listesi CRUD islemleri
"""

from typing import List, Dict, Optional
from tkinter import messagebox

from field_registry import ensure_row_schema


class ListManager:
    """Kitap listesi yonetimi icin sinif"""
    
    def __init__(self, kitap_listesi: List[Dict] = None):
        """
        Args:
            kitap_listesi: Baslangic kitap listesi
        """
        self.kitap_listesi = kitap_listesi or []
    
    def ekle(self, kitap: Dict, tekrar_kontrol: bool = True) -> tuple[bool, Optional[str]]:
        """
        Kitap ekler
        
        Args:
            kitap: Eklenecek kitap dict'i
            tekrar_kontrol: Ayni kitap kontrolu yapilsin mi
            
        Returns:
            (Basarili mi, Hata mesaji)
        """
        kitap_adi = kitap.get("Kitap Adı", "").strip()
        
        if not kitap_adi:
            return False, "Kitap Adi bos olamaz!"
        
        # Tekrar kontrolü
        if tekrar_kontrol:
            mevcut_isimler = [k.get("Kitap Adı", "").lower() for k in self.kitap_listesi]
            if kitap_adi.lower() in mevcut_isimler:
                return False, f"'{kitap_adi}' adli kitap zaten listede var!"
        
        self.kitap_listesi.append(ensure_row_schema(kitap))
        return True, None
    
    def sil(self, index: int) -> tuple[bool, Optional[Dict]]:
        """
        Kitap siler
        
        Args:
            index: Silinecek kitabin indeksi
            
        Returns:
            (Basarili mi, Silinen kitap)
        """
        if 0 <= index < len(self.kitap_listesi):
            silinen = self.kitap_listesi.pop(index)
            return True, silinen
        return False, None
    
    def getir(self, index: int) -> Optional[Dict]:
        """
        Kitap getirir
        
        Args:
            index: Kitabin indeksi
            
        Returns:
            Kitap dict'i veya None
        """
        if 0 <= index < len(self.kitap_listesi):
            return self.kitap_listesi[index]
        return None
    
    def tumunu_getir(self) -> List[Dict]:
        """
        Tum kitap listesini getirir
        
        Returns:
            Kitap listesi
        """
        return self.kitap_listesi.copy()
    
    def sayi(self) -> int:
        """
        Kitap sayisini dondurur
        
        Returns:
            Kitap sayisi
        """
        return len(self.kitap_listesi)
    
    def temizle(self):
        """Listeyi temizler"""
        self.kitap_listesi = []
    
    def toplu_ekle(self, kitaplar: List[Dict], tekrar_kontrol: bool = True) -> Dict[str, List]:
        """
        Toplu kitap ekler
        
        Args:
            kitaplar: Eklenecek kitap listesi
            tekrar_kontrol: Tekrar kontrolu yapilsin mi
            
        Returns:
            {
                'eklenen': [eklenen kitaplar],
                'atlanan': [atlanan kitaplar]
            }
        """
        mevcut_isimler = [k.get("Kitap Adı", "").lower() for k in self.kitap_listesi]
        eklenecekler = []
        atlananlar = []
        
        for kitap in kitaplar:
            kitap_adi = kitap.get("Kitap Adı", "").strip()
            yazar = kitap.get("Yazar", "").strip()
            
            # Zorunlu alan kontrolü
            if not kitap_adi or not yazar:
                continue
            
            if tekrar_kontrol and kitap_adi.lower() in mevcut_isimler:
                atlananlar.append(kitap_adi)
            else:
                eklenecekler.append(ensure_row_schema(kitap))
                mevcut_isimler.append(kitap_adi.lower())
        
        # Ekle
        self.kitap_listesi.extend(eklenecekler)
        
        return {
            'eklenen': eklenecekler,
            'atlanan': atlananlar
        }
    
    def ara(self, arama_terimi: str) -> List[Dict]:
        """
        Kitap arar
        
        Args:
            arama_terimi: Aranacak terim
            
        Returns:
            Bulunan kitaplar listesi
        """
        arama_lower = arama_terimi.lower()
        sonuclar = []
        
        for kitap in self.kitap_listesi:
            kitap_adi = kitap.get("Kitap Adı", "").lower()
            yazar = kitap.get("Yazar", "").lower()
            
            if arama_lower in kitap_adi or arama_lower in yazar:
                sonuclar.append(kitap)
        
        return sonuclar
