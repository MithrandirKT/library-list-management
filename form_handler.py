"""
Form İşlemleri Modülü
Form doğrulama, temizleme ve doldurma işlemleri
"""

import tkinter as tk
from tkinter import messagebox
from typing import Dict, Optional


class FormHandler:
    """Form işlemleri için sınıf"""
    
    def __init__(self, form_widgets: Dict[str, tk.Widget]):
        """
        Args:
            form_widgets: Form widget'larının dict'i
                Örnek: {
                    'kitap_adi': Entry widget,
                    'yazar': Entry widget,
                    ...
                }
        """
        self.widgets = form_widgets
    
    def temizle(self):
        """Form alanlarını temizler"""
        if 'kitap_adi' in self.widgets:
            self.widgets['kitap_adi'].delete(0, tk.END)
        if 'yazar' in self.widgets:
            self.widgets['yazar'].delete(0, tk.END)
        if 'orijinal_adi' in self.widgets:
            # Readonly widget için state'i geçici olarak normal yap
            self.widgets['orijinal_adi'].config(state='normal')
            self.widgets['orijinal_adi'].delete(0, tk.END)
            self.widgets['orijinal_adi'].config(state='readonly')
        if 'tur' in self.widgets:
            if hasattr(self.widgets['tur'], 'set'):
                self.widgets['tur'].set("")
            else:
                self.widgets['tur'].delete(0, tk.END)
        if 'ulke' in self.widgets:
            self.widgets['ulke'].config(state='normal')
            self.widgets['ulke'].delete(0, tk.END)
            self.widgets['ulke'].config(state='readonly')
        if 'cikis_yili' in self.widgets:
            self.widgets['cikis_yili'].config(state='normal')
            self.widgets['cikis_yili'].delete(0, tk.END)
            self.widgets['cikis_yili'].config(state='readonly')
        if 'anlati_yili' in self.widgets:
            self.widgets['anlati_yili'].config(state='normal')
            self.widgets['anlati_yili'].delete(0, tk.END)
            self.widgets['anlati_yili'].config(state='readonly')
        if 'konusu' in self.widgets:
            # Disabled Text widget için state'i geçici olarak normal yap
            self.widgets['konusu'].config(state='normal')
            self.widgets['konusu'].delete("1.0", tk.END)
            self.widgets['konusu'].config(state='disabled')
        if 'not_alan' in self.widgets:
            self.widgets['not_alan'].config(state='normal')
            self.widgets['not_alan'].delete(0, tk.END)
            self.widgets['not_alan'].config(state='readonly')
    
    def deger_al(self) -> Dict[str, str]:
        """
        Form değerlerini alır
        
        Returns:
            Form değerlerinin dict'i
        """
        degerler = {}
        
        if 'kitap_adi' in self.widgets:
            degerler['kitap_adi'] = self.widgets['kitap_adi'].get().strip()
        if 'yazar' in self.widgets:
            degerler['yazar'] = self.widgets['yazar'].get().strip()
        if 'orijinal_adi' in self.widgets:
            degerler['orijinal_adi'] = self.widgets['orijinal_adi'].get().strip()
        if 'tur' in self.widgets:
            if hasattr(self.widgets['tur'], 'get'):
                degerler['tur'] = self.widgets['tur'].get().strip()
        if 'ulke' in self.widgets:
            degerler['ulke'] = self.widgets['ulke'].get().strip()
        if 'cikis_yili' in self.widgets:
            degerler['cikis_yili'] = self.widgets['cikis_yili'].get().strip()
        if 'anlati_yili' in self.widgets:
            degerler['anlati_yili'] = self.widgets['anlati_yili'].get().strip()
        if 'konusu' in self.widgets:
            # Disabled Text widget için geçici olarak normal yap
            state = self.widgets['konusu']['state']
            if state == 'disabled':
                self.widgets['konusu'].config(state='normal')
                degerler['konusu'] = self.widgets['konusu'].get("1.0", tk.END).strip()
                self.widgets['konusu'].config(state='disabled')
            else:
                degerler['konusu'] = self.widgets['konusu'].get("1.0", tk.END).strip()
        if 'not_alan' in self.widgets:
            degerler['not_alan'] = self.widgets['not_alan'].get().strip()
        
        return degerler
    
    def dogrula(self):
        """
        Form doğrulaması yapar
        
        Returns:
            tuple: (Başarılı mı, Hata mesajı)
        """
        degerler = self.deger_al()
        
        # Zorunlu alan kontrolü
        if not degerler.get('kitap_adi'):
            return False, "Kitap Adı zorunludur! Lütfen kitap adını girin."
        
        if not degerler.get('yazar'):
            return False, "Yazar zorunludur! Lütfen yazar adını girin."
        
        # Çıkış yılı kontrolü
        cikis_yili = degerler.get('cikis_yili', '')
        if cikis_yili:
            hata = self._cikis_yili_dogrula(cikis_yili)
            if hata:
                return False, hata
        
        return True, None
    
    def doldur(self, bilgiler: Dict[str, str], sadece_bos: bool = True):
        """
        Formu bilgilerle doldurur
        
        Args:
            bilgiler: Doldurulacak bilgiler dict'i
            sadece_bos: Sadece boş alanları doldur (varsayılan: True)
            
        ⚠️ KRİTİK: Readonly widget state yönetimi
        - Readonly widget'lara yazmak için state'i geçici olarak 'normal' yap
        - İşlem bitince mutlaka 'readonly' yap
        - Aksi halde kullanıcı manuel yazabilir (istenmeyen davranış)
        - Yeni readonly widget eklersen bu pattern'i takip et
        """
        # Orijinal Adı - Readonly widget
        # ⚠️ DİKKAT: State yönetimi - normal → işlem → readonly
        if 'orijinal_adi' in self.widgets and bilgiler.get("Orijinal Adı"):
            if not sadece_bos or not self.widgets['orijinal_adi'].get().strip():
                self.widgets['orijinal_adi'].config(state='normal')
                self.widgets['orijinal_adi'].delete(0, tk.END)
                self.widgets['orijinal_adi'].insert(0, bilgiler.get("Orijinal Adı", ""))
                self.widgets['orijinal_adi'].config(state='readonly')
        
        # Tür - Readonly combobox
        if 'tur' in self.widgets and bilgiler.get("Tür"):
            if not sadece_bos or not self.widgets['tur'].get().strip():
                if hasattr(self.widgets['tur'], 'set'):
                    self.widgets['tur'].set(bilgiler.get("Tür", ""))
        
        # Ülke/Edebi Gelenek - Readonly widget
        if 'ulke' in self.widgets and bilgiler.get("Ülke/Edebi Gelenek"):
            if not sadece_bos or not self.widgets['ulke'].get().strip():
                self.widgets['ulke'].config(state='normal')
                self.widgets['ulke'].delete(0, tk.END)
                self.widgets['ulke'].insert(0, bilgiler.get("Ülke/Edebi Gelenek", ""))
                self.widgets['ulke'].config(state='readonly')
        
        # Çıkış Yılı - Readonly widget
        if 'cikis_yili' in self.widgets and bilgiler.get("Çıkış Yılı"):
            if not sadece_bos or not self.widgets['cikis_yili'].get().strip():
                self.widgets['cikis_yili'].config(state='normal')
                self.widgets['cikis_yili'].delete(0, tk.END)
                self.widgets['cikis_yili'].insert(0, bilgiler.get("Çıkış Yılı", ""))
                self.widgets['cikis_yili'].config(state='readonly')
        
        # Anlatı Yılı - Readonly widget
        if 'anlati_yili' in self.widgets and bilgiler.get("Anlatı Yılı"):
            if not sadece_bos or not self.widgets['anlati_yili'].get().strip():
                self.widgets['anlati_yili'].config(state='normal')
                self.widgets['anlati_yili'].delete(0, tk.END)
                self.widgets['anlati_yili'].insert(0, bilgiler.get("Anlatı Yılı", ""))
                self.widgets['anlati_yili'].config(state='readonly')
        
        # Konusu - Disabled Text widget
        if 'konusu' in self.widgets and bilgiler.get("Konusu"):
            if not sadece_bos or not self.widgets['konusu'].get("1.0", tk.END).strip():
                self.widgets['konusu'].config(state='normal')
                self.widgets['konusu'].delete("1.0", tk.END)
                self.widgets['konusu'].insert("1.0", bilgiler.get("Konusu", ""))
                self.widgets['konusu'].config(state='disabled')
        
        # Not - Readonly widget
        if 'not_alan' in self.widgets and bilgiler.get("Not"):
            if not sadece_bos or not self.widgets['not_alan'].get().strip():
                self.widgets['not_alan'].config(state='normal')
                self.widgets['not_alan'].delete(0, tk.END)
                self.widgets['not_alan'].insert(0, bilgiler.get("Not", ""))
                self.widgets['not_alan'].config(state='readonly')
    
    def _cikis_yili_dogrula(self, cikis_yili: str) -> Optional[str]:
        """
        Çıkış yılı doğrulaması yapar
        
        Args:
            cikis_yili: Doğrulanacak çıkış yılı
            
        Returns:
            Hata mesajı veya None
        """
        if not cikis_yili:
            return None
        
        # Aralık formatı kontrolü (örn: "1865-1869")
        if '-' in cikis_yili:
            parts = cikis_yili.split('-')
            if len(parts) != 2:
                return "Çıkış yılı aralığı geçersiz format! Örnek: '1865-1869'"
            
            try:
                yil1 = int(parts[0].strip())
                yil2 = int(parts[1].strip())
                if not (1500 <= yil1 <= 2030 and 1500 <= yil2 <= 2030):
                    return "Çıkış yılı mantıklı bir yıl aralığında olmalıdır (1500-2030)!"
            except ValueError:
                return "Çıkış yılı aralığı geçersiz format! Örnek: '1865-1869'"
        else:
            # Tek yıl formatı
            try:
                yil = int(cikis_yili)
                if not (1500 <= yil <= 2030):
                    return "Çıkış yılı mantıklı bir yıl aralığında olmalıdır (1500-2030)!"
            except ValueError:
                # Sayı değilse metin olarak kabul et (örn: "yaklaşık 1869")
                pass
        
        return None
    
    def kitap_yukle(self, kitap: Dict[str, str]):
        """
        Kitap bilgilerini forma yükler
        
        Args:
            kitap: Kitap bilgileri dict'i
        """
        # Kitap Adı - Yazılabilir
        if 'kitap_adi' in self.widgets:
            self.widgets['kitap_adi'].delete(0, tk.END)
            self.widgets['kitap_adi'].insert(0, kitap.get("Kitap Adı", ""))
        
        # Yazar - Yazılabilir
        if 'yazar' in self.widgets:
            self.widgets['yazar'].delete(0, tk.END)
            self.widgets['yazar'].insert(0, kitap.get("Yazar", ""))
        
        # Diğer alanlar readonly olduğu için doldur() fonksiyonunu kullan
        self.doldur(kitap, sadece_bos=False)
    
    def kitap_dict_olustur(self) -> Dict[str, str]:
        """
        Formdan kitap dict'i oluşturur
        
        Returns:
            Kitap bilgileri dict'i
        """
        degerler = self.deger_al()
        
        # Çıkış yılı doğrulaması ve formatlama
        cikis_yili = degerler.get('cikis_yili', '')
        if cikis_yili and '-' in cikis_yili:
            # Aralık formatını koru
            parts = cikis_yili.split('-')
            if len(parts) == 2:
                try:
                    yil1 = int(parts[0].strip())
                    yil2 = int(parts[1].strip())
                    if 1500 <= yil1 <= 2030 and 1500 <= yil2 <= 2030:
                        cikis_yili = cikis_yili  # "1865-1869" formatında kalır
                except ValueError:
                    pass
        elif cikis_yili:
            try:
                yil = int(cikis_yili)
                if 1500 <= yil <= 2030:
                    cikis_yili = str(yil)
            except ValueError:
                pass
        
        return {
            "Kitap Adı": degerler.get('kitap_adi', ''),
            "Yazar": degerler.get('yazar', ''),
            "Orijinal Adı": degerler.get('orijinal_adi', ''),
            "Tür": degerler.get('tur', ''),
            "Ülke/Edebi Gelenek": degerler.get('ulke', ''),
            "Çıkış Yılı": cikis_yili,
            "Anlatı Yılı": degerler.get('anlati_yili', ''),
            "Konusu": degerler.get('konusu', ''),
            "Not": degerler.get('not_alan', '')
        }
