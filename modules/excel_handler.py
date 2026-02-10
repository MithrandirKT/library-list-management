"""
Excel İşlemleri Modülü
Excel dosyası okuma, yazma ve format güncelleme işlemleri
"""

import pandas as pd
import os
from typing import List, Dict, Optional
from openpyxl import load_workbook
from openpyxl.styles import numbers

from field_registry import standard_columns

class ExcelHandler:
    """Excel dosyası işlemleri için sınıf"""
    
    # ⚠️ KRİTİK: Standart sütun sırası - ASLA DEĞİŞTİRME!
    # Bu sıra Excel dosyası formatını belirler. Değiştirirsen:
    # 1. Mevcut Excel dosyaları uyumsuz olur
    # 2. _format_guncelle() fonksiyonunu güncelle
    # 3. gui_widgets.py içindeki Treeview sütunlarını güncelle
    # 4. form_handler.py içindeki form alanlarını güncelle
    # 5. HAND_OFF_DOKUMANTASYON.md dosyasını güncelle
    # Not: Meta kolonlar da bu standarda dahildir.
    STANDART_SUTUN_SIRASI = standard_columns()
    
    def __init__(self, excel_dosyasi: str = "Kutuphanem.xlsx"):
        """
        Args:
            excel_dosyasi: Excel dosyası yolu
            
        ⚠️ DİKKAT: Varsayılan dosya adı "Kutuphanem.xlsx" - Değiştirirsen:
        - Mevcut Excel dosyaları bulunamaz
        - kitap_listesi_gui.py içindeki ExcelHandler oluşturma kısmını güncelle
        - HAND_OFF_DOKUMANTASYON.md dosyasını güncelle
        """
        self.excel_dosyasi = excel_dosyasi
    
    def yukle(self) -> List[Dict]:
        """
        Excel dosyasından kitap listesini yükler ve format günceller
        
        Returns:
            Kitap listesi (dict listesi)
        """
        if not os.path.exists(self.excel_dosyasi):
            return []
        
        try:
            df = pd.read_excel(self.excel_dosyasi, engine='openpyxl')
            df = self._ensure_columns(df)
            
            # Format kontrolü ve güncelleme
            format_guncellenmeli = self._format_kontrol_et(df)
            
            # Verileri yükle
            kitap_listesi = df.to_dict('records')
            
            # NaN değerleri boş string'e çevir
            for kitap in kitap_listesi:
                for key, value in kitap.items():
                    if pd.isna(value):
                        kitap[key] = ""
            
            # Format güncellenmeli ise kaydet
            if format_guncellenmeli and kitap_listesi:
                try:
                    df = self._format_guncelle(df)
                    df.to_excel(self.excel_dosyasi, index=False, engine='openpyxl')
                    # Güncellenmiş verileri tekrar yükle
                    kitap_listesi = df.to_dict('records')
                    for kitap in kitap_listesi:
                        for key, value in kitap.items():
                            if pd.isna(value):
                                kitap[key] = ""
                except Exception as e:
                    # Güncelleme başarısız olursa devam et
                    print(f"Format güncelleme hatası: {e}")
            
            return kitap_listesi
            
        except Exception as e:
            print(f"Excel yükleme hatası: {e}")
            return []
    
    def kaydet(self, kitap_listesi: List[Dict]) -> bool:
        """
        Kitap listesini Excel dosyasına kaydeder
        
        Args:
            kitap_listesi: Kaydedilecek kitap listesi
            
        Returns:
            Başarılı ise True
        """
        try:
            # DataFrame oluştur
            df = pd.DataFrame(kitap_listesi)
            
            # Eksik sütunları ekle
            for sutun in self.STANDART_SUTUN_SIRASI:
                if sutun not in df.columns:
                    df[sutun] = ""
            
            # Sütun sırasını düzenle
            df = df[self.STANDART_SUTUN_SIRASI]
            
            # Yıl sütunlarını sayısal formata çevir
            df = self._yil_sutunlarini_formatla(df)
            
            # Excel'e kaydet
            df.to_excel(self.excel_dosyasi, index=False, engine='openpyxl')
            
            # Excel dosyasını açıp hücre formatlarını ayarla
            self._excel_format_ayarla()
            
            return True
            
        except Exception as e:
            print(f"Excel kaydetme hatası: {e}")
            return False
    
    def sablon_olustur(self, dosya_yolu: str) -> bool:
        """
        Boş Excel şablonu oluşturur (sadece Kitap Adı ve Yazar sütunları)
        
        Args:
            dosya_yolu: Şablonun kaydedileceği yol
            
        Returns:
            Başarılı ise True
            
        ⚠️ DİKKAT: Şablon sadece 2 sütun içerir (Kitap Adı ve Yazar)
        - Diğer sütunlar otomatik doldurma ile gelir
        - Şablon formatını değiştirirsen kullanıcıları bilgilendir
        - HAND_OFF_DOKUMANTASYON.md dosyasını güncelle
        """
        try:
            # ?ablon i?in standart s?tunlar (veri + meta)
            df = pd.DataFrame(columns=self.STANDART_SUTUN_SIRASI)
            df.to_excel(dosya_yolu, index=False, engine='openpyxl')
            return True
        except Exception as e:
            print(f"Şablon oluşturma hatası: {e}")
            return False
    
    def disaridan_yukle(self, dosya_yolu: str) -> Optional[List[Dict]]:
        """
        Dışarıdan Excel dosyası yükler ve parse eder
        
        Args:
            dosya_yolu: Yüklenecek Excel dosyası yolu
            
        Returns:
            Kitap listesi veya None (hata durumunda)
        """
        try:
            df = pd.read_excel(dosya_yolu, engine='openpyxl')
            
            # Zorunlu sütun kontrolü
            gerekli_sutunlar = ['Kitap Adı', 'Yazar']
            eksik_sutunlar = [sutun for sutun in gerekli_sutunlar if sutun not in df.columns]
            
            if eksik_sutunlar:
                raise ValueError(f"Eksik sütunlar: {', '.join(eksik_sutunlar)}")

            # Zorunlu kolonlar dogrulandiktan sonra eksik meta kolonlarini tamamla
            df = self._ensure_columns(df)
            
            # Boş satırları filtrele
            df = df.dropna(subset=['Kitap Adı', 'Yazar'], how='all')
            df = df[df['Kitap Adı'].notna() & df['Yazar'].notna()]
            df = df[(df['Kitap Adı'].astype(str).str.strip() != '') & 
                    (df['Yazar'].astype(str).str.strip() != '')]
            
            # DataFrame'i sözlük listesine çevir
            kitaplar = df.to_dict('records')
            
            # NaN değerleri boş string'e çevir
            for kitap in kitaplar:
                for key, value in kitap.items():
                    if pd.isna(value):
                        kitap[key] = ""
            
            return kitaplar
            
        except Exception as e:
            print(f"Dışarıdan yükleme hatası: {e}")
            return None
    
    def dosya_acik_mi(self) -> bool:
        """
        Excel dosyasının açık olup olmadığını kontrol eder
        
        Returns:
            Açık ise True
        """
        if not os.path.exists(self.excel_dosyasi):
            return False
        
        try:
            with open(self.excel_dosyasi, 'r+b'):
                pass
            return False
        except PermissionError:
            return True
        except:
            return False
    
    def _format_kontrol_et(self, df: pd.DataFrame) -> bool:
        """
        Excel dosyas?n?n format?n?n g?ncel olup olmad???n? kontrol eder

        Args:
            df: DataFrame

        Returns:
            G?ncellenmeli ise True
        """
        # Eksik s?tun varsa format g?ncellenmeli
        for sutun in self.STANDART_SUTUN_SIRASI:
            if sutun not in df.columns:
                return True

        if len(df.columns) > 1:
            # ?kinci s?tun "Yazar" de?ilse eski format
            if df.columns[1] != "Yazar":
                return True
        elif "Yazar" not in df.columns:
            # Yazar s?tunu yoksa eski format
            return True

        return False

    def _format_guncelle(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrame'i yeni formata g?re g?nceller

        Args:
            df: G?ncellenecek DataFrame

        Returns:
            G?ncellenmi? DataFrame
        """
        # Kolonlar? standarda uyarla
        df = self._ensure_columns(df)

        # Y?l s?tunlar?n? say?sal formata ?evir
        df = self._yil_sutunlarini_formatla(df)

        return df

    def _ensure_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Eksik kolonlar? ekler ve kolon s?ras?n? standarda g?re d?zenler.
        """
        for sutun in self.STANDART_SUTUN_SIRASI:
            if sutun not in df.columns:
                df[sutun] = ""

        return df[self.STANDART_SUTUN_SIRASI]

    def _yil_sutunlarini_formatla(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Yıl sütunlarını sayısal formata çevirir (tek yıllar sayı, aralıklar metin kalır)
        
        Args:
            df: DataFrame
            
        Returns:
            Formatlanmış DataFrame
        """
        yil_sutunlari = ["Çıkış Yılı", "Anlatı Yılı"]
        
        for sutun in yil_sutunlari:
            if sutun in df.columns:
                # Her değeri kontrol et
                def yil_formatla(deger):
                    if pd.isna(deger) or deger == "":
                        return ""
                    
                    # String'e çevir
                    deger_str = str(deger).strip()
                    
                    # Boş ise boş döndür
                    if not deger_str:
                        return ""
                    
                    # Aralık formatı kontrolü (örn: "1865-1869")
                    if "-" in deger_str:
                        # Aralık formatı - metin olarak bırak
                        return deger_str
                    
                    # Tek yıl formatı - sayısal formata çevir
                    try:
                        yil = int(float(deger_str))
                        # Makul yıl aralığı kontrolü (1000-3000)
                        if 1000 <= yil <= 3000:
                            return yil
                        else:
                            # Makul aralık dışındaysa metin olarak bırak
                            return deger_str
                    except (ValueError, TypeError):
                        # Sayıya çevrilemezse metin olarak bırak
                        return deger_str
                
                # Sütunu formatla
                df[sutun] = df[sutun].apply(yil_formatla)
        
        return df
    
    def _excel_format_ayarla(self):
        """
        Excel dosyasını açıp yıl sütunlarının formatını sayısal olarak ayarlar
        """
        try:
            wb = load_workbook(self.excel_dosyasi)
            ws = wb.active
            
            # Sütun başlıklarını bul
            baslik_satiri = 1
            sutun_indeksleri = {}
            
            for col_idx, cell in enumerate(ws[baslik_satiri], start=1):
                if cell.value in ["Çıkış Yılı", "Anlatı Yılı"]:
                    sutun_indeksleri[cell.value] = col_idx
            
            # Yıl sütunlarını formatla
            for sutun_adi, col_idx in sutun_indeksleri.items():
                # Başlık hariç tüm satırları formatla
                for row_idx in range(baslik_satiri + 1, ws.max_row + 1):
                    cell = ws.cell(row=row_idx, column=col_idx)
                    if cell.value is not None and cell.value != "":
                        # Aralık formatı değilse (tire yoksa) sayısal format uygula
                        deger_str = str(cell.value)
                        if "-" not in deger_str:
                            try:
                                # Sayısal değere çevir
                                yil = int(float(deger_str))
                                if 1000 <= yil <= 3000:
                                    cell.value = yil
                                    cell.number_format = '0'  # Sayısal format (ondalık yok)
                            except (ValueError, TypeError):
                                # Sayıya çevrilemezse metin olarak bırak
                                pass
            
            wb.save(self.excel_dosyasi)
            wb.close()
            
        except Exception as e:
            # Format ayarlama başarısız olursa devam et (kritik değil)
            print(f"Excel format ayarlama hatası: {e}")
