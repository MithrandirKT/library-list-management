"""
Kitap Listesi Excel Oluşturucu - GUI Versiyonu
Windows'ta çalışan grafik arayüzlü uygulama
"""

import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import threading
import sys
import os

# modules klasörünü path'e ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

from kitap_bilgisi_cekici import KitapBilgisiCekici
from excel_handler import ExcelHandler
from api_key_manager import APIKeyManager
from form_handler import FormHandler
from list_manager import ListManager
from gui_widgets import GUIWidgets


class KitapListesiGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📚 Kitap Listesi Excel Oluşturucu")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        # Kitap temalı arka plan rengi
        self.root.configure(bg='#F5E6D3')
        
        # Modüller
        # Dosya path'lerini data/ klasörüne göre ayarla
        base_dir = os.path.dirname(__file__)
        self.excel_handler = ExcelHandler(os.path.join(base_dir, "data", "Kutuphanem.xlsx"))
        self.api_key_manager = APIKeyManager(os.path.join(base_dir, "data", "groq_api_key.txt"))
        self.list_manager = ListManager()
        self.bilgi_cekici = KitapBilgisiCekici()
        
        # Excel'den yükle
        kitap_listesi = self.excel_handler.yukle()
        self.list_manager.kitap_listesi = kitap_listesi
        
        # API key yükle
        api_key = self.api_key_manager.yukle()
        if api_key:
            self.bilgi_cekici.groq_api_key = api_key
        
        # GUI widget'ları
        self.gui_widgets = GUIWidgets(self.root)
        
        # Form handler
        self.form_handler = None  # GUI oluşturulduktan sonra set edilecek
        
        # GUI oluştur
        self.gui_olustur()
        
        # Form handler'ı başlat
        self.form_handler = FormHandler(self.gui_widgets.get_widgets())
        
        # Listeyi güncelle
        self.listeyi_guncelle()
    
    def gui_olustur(self):
        """GUI arayüzünü oluştur"""
        callbacks = {
            'bilgileri_otomatik_doldur': self.bilgileri_otomatik_doldur,
            'listeye_ekle': self.listeye_ekle,
            'formu_temizle': self.formu_temizle,
            'kitap_sil': self.kitap_sil,
            'toplu_sil': self.toplu_sil,
            'tumunu_kaldir': self.tumunu_kaldir,
            'excel_olustur': self.excel_olustur,
            'excel_sablonu_olustur': self.excel_sablonu_olustur,
            'excel_yukle': self.excel_yukle,
            'groq_api_key_ayarla': self.groq_api_key_ayarla,
            'kitap_sec': self.kitap_sec
        }
        
        self.gui_widgets.olustur(callbacks)
        
        # API key buton durumunu güncelle
        durum = self.api_key_manager.durum()
        self.gui_widgets.api_key_buton_guncelle(durum)
    
    def formu_temizle(self):
        """Form alanlarını temizle"""
        if self.form_handler:
            self.form_handler.temizle()
    
    def bilgileri_otomatik_doldur(self):
        """Kitap bilgilerini otomatik olarak doldur"""
        if not self.form_handler:
            return
        
        degerler = self.form_handler.deger_al()
        kitap_adi = degerler.get('kitap_adi', '').strip()
        yazar = degerler.get('yazar', '').strip()
        
        # Zorunlu alan kontrolü
        if not kitap_adi:
            messagebox.showwarning("Uyarı", "Kitap Adı zorunludur! Lütfen önce kitap adını girin.")
            return
        
        if not yazar:
            messagebox.showwarning("Uyarı", "Yazar zorunludur! Lütfen önce yazar adını girin.")
            return
        
        # Progress bar'ı göster
        self.gui_widgets.progress_goster("Wikipedia'dan bilgiler çekiliyor...")
        self.root.update()
        
        # ⚠️ KRİTİK: Thread kullanımı (GUI donmaması için)
        # - API çağrıları uzun sürebilir, GUI donmaması için thread kullan
        # - Thread'den GUI'ye direkt erişim YAPMA! root.after() kullan
        # - Exception handling yap, hataları GUI'ye bildir
        # - Daemon thread kullan (program kapanınca thread de kapansın)
        thread = threading.Thread(target=self._bilgileri_cek_ve_doldur, args=(kitap_adi, yazar))
        thread.daemon = True
        thread.start()
    
    def _bilgileri_cek_ve_doldur(self, kitap_adi: str, yazar: str):
        """
        Arka planda bilgileri çek ve formu doldur (Policy modu)
        
        ⚠️ KRİTİK: Thread-safe GUI güncellemeleri
        - Bu fonksiyon thread'de çalışır
        - GUI güncellemeleri için root.after() kullan (thread-safe)
        - Direkt widget erişimi YAPMA!
        - Exception handling yap, hataları GUI'ye bildir
        
        ⚠️ YENİ: Policy modu kullanılıyor (field_policy + quality_gates + wikidata + router)
        """
        try:
            # Mevcut form değerlerini al (Excel kolon isimlerine dönüştür)
            form_degerler = self.form_handler.deger_al() if self.form_handler else {}
            
            # Form değerlerini Excel kolon isimlerine dönüştür
            mevcut_bilgiler = {
                "Kitap Adı": kitap_adi,
                "Yazar": yazar,
                "Orijinal Adı": form_degerler.get("orijinal_adi", ""),
                "Tür": form_degerler.get("tur", ""),
                "Ülke/Edebi Gelenek": form_degerler.get("ulke", ""),
                "Çıkış Yılı": form_degerler.get("cikis_yili", ""),
                "Anlatı Yılı": form_degerler.get("anlati_yili", ""),
                "Konusu": form_degerler.get("konusu", ""),
            }
            
            # API key kontrolü (policy fonksiyonu API key olmadan da çalışır, ama AI fallback için gerekli)
            groq_key = self.api_key_manager.get()
            if not groq_key:
                groq_key = self.api_key_manager.yukle()
            
            if groq_key:
                self.bilgi_cekici.groq_api_key = groq_key
                print(f"Groq API key kullanılıyor: {groq_key[:10]}...")
            
            # Policy modu ile bilgi çek
            self.root.after(0, lambda: self.gui_widgets.progress_mesaj_guncelle("Kaynaklardan bilgiler çekiliyor (Policy modu)..."))
            
            print(f"Policy modu ile bilgi çekiliyor: {kitap_adi} - {yazar}")
            bilgiler = self.bilgi_cekici.kitap_bilgisi_cek_policy(kitap_adi, yazar, mevcut_bilgiler)
            
            # Sadece form alanlarını çıkar (meta kolonları hariç)
            form_bilgileri = {
                "Orijinal Adı": bilgiler.get("Orijinal Adı", ""),
                "Tür": bilgiler.get("Tür", ""),
                "Ülke/Edebi Gelenek": bilgiler.get("Ülke/Edebi Gelenek", ""),
                "Çıkış Yılı": bilgiler.get("Çıkış Yılı", ""),
                "Anlatı Yılı": bilgiler.get("Anlatı Yılı", ""),
                "Konusu": bilgiler.get("Konusu", ""),
            }
            
            print(f"Policy modu sonuçları:")
            from provenance import field_key
            for alan, deger in form_bilgileri.items():
                if deger:
                    key = field_key(alan)
                    kaynak = bilgiler.get(f"src_{key}", "unknown") if key else "unknown"
                    print(f"  ✓ {alan}: {deger[:50]}... (kaynak: {kaynak})")
            
            # Formu doldur
            self.root.after(0, self._formu_doldur, form_bilgileri)
            
        except Exception as e:
            print(f"Policy modu hatası: {e}")
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: messagebox.showerror("Hata", f"Bilgiler çekilirken hata oluştu:\n\n{str(e)}"))
        finally:
            self.root.after(0, self.gui_widgets.progress_gizle)
    
    def _formu_doldur(self, bilgiler: dict):
        """Formu çekilen bilgilerle doldur"""
        if not self.form_handler:
            return
        
        self.form_handler.doldur(bilgiler, sadece_bos=True)
        
        # Bulunan bilgileri göster
        bulunan_alanlar = [k for k, v in bilgiler.items() if v and v.strip()]
        kitap_adi = self.form_handler.deger_al().get('kitap_adi', '')
        
        if bulunan_alanlar:
            # Bulunan alan sayısını göster, detayları gösterme
            mesaj = f"✅ Bilgiler başarıyla çekildi!\n\n"
            mesaj += f"📚 '{kitap_adi}' için {len(bulunan_alanlar)} alan dolduruldu:\n"
            
            # Sadece alan isimlerini göster (ilk 5 alan)
            gosterilen_alanlar = bulunan_alanlar[:5]
            for alan in gosterilen_alanlar:
                mesaj += f"  • {alan}\n"
            
            if len(bulunan_alanlar) > 5:
                mesaj += f"  ... ve {len(bulunan_alanlar) - 5} alan daha\n"
            
            if self.api_key_manager.get():
                mesaj += f"\n✨ Groq AI kullanıldı"
            
            messagebox.showinfo("✅ Başarılı", mesaj)
        else:
            mesaj = f"⚠️ '{kitap_adi}' için bilgi bulunamadı.\n\n"
            if not self.api_key_manager.get():
                mesaj += "💡 İpucu: Groq API Key ekleyerek daha fazla bilgi bulabilirsiniz.\n"
                mesaj += "(Groq API Key butonuna tıklayın)\n\n"
            mesaj += "Lütfen bilgileri manuel olarak girin."
            messagebox.showwarning("⚠️ Uyarı", mesaj)
    
    def listeye_ekle(self, mesaj_goster=True):
        """Formdan kitap bilgilerini alıp listeye ekle"""
        if not self.form_handler:
            return False
        
        # Form doğrulaması
        basarili, hata = self.form_handler.dogrula()
        if not basarili:
            messagebox.showwarning("Uyarı", hata)
            return False
        
        # Kitap dict'i oluştur
        kitap = self.form_handler.kitap_dict_olustur()
        
        # Listeye ekle
        basarili, hata = self.list_manager.ekle(kitap, tekrar_kontrol=True)
        
        if not basarili:
            if hata and "zaten listede var" in hata:
                # Hata mesajını kısalt (sadece kitap adını göster)
                kitap_adi = kitap.get('Kitap Adı', '')
                if len(kitap_adi) > 50:
                    kitap_adi = kitap_adi[:47] + "..."
                kisa_hata = f"'{kitap_adi}' adlı kitap zaten listede var."
                cevap = messagebox.askyesno("⚠️ Kitap Zaten Var", 
                                           f"{kisa_hata}\n\nYine de eklemek istiyor musunuz?")
                if cevap:
                    basarili, _ = self.list_manager.ekle(kitap, tekrar_kontrol=False)
                else:
                    return False
            else:
                messagebox.showwarning("Uyarı", hata or "Kitap eklenemedi!")
                return False
        
        # Listeyi güncelle
        self.listeyi_guncelle()
        self.formu_temizle()
        
        # Başarı mesajı - kısa ve öz
        if mesaj_goster:
            kitap_adi = kitap.get('Kitap Adı', '')
            if len(kitap_adi) > 50:
                kitap_adi = kitap_adi[:47] + "..."
            
            messagebox.showinfo("✅ Başarılı", 
                              f"📚 '{kitap_adi}' listeye eklendi!\n\n"
                              f"📊 Toplam kitap sayısı: {self.list_manager.sayi()}\n\n"
                              f"💡 Excel dosyasına kaydetmek için 'Excel Dosyası Oluştur' butonuna tıklayın.")
        return True
    
    def listeyi_guncelle(self):
        """Treeview'i güncelle"""
        kitap_listesi = self.list_manager.tumunu_getir()
        self.gui_widgets.listeyi_guncelle(kitap_listesi)
    
    def kitap_sec(self):
        """Listeden seçilen kitabı forma yükle"""
        if not self.gui_widgets.tree or not self.form_handler:
            return
        
        selected = self.gui_widgets.tree.selection()
        if not selected:
            return
        
        # Seçili satırın indeksini bul
        item = selected[0]
        index = self.gui_widgets.tree.index(item)
        
        # Kitabı listeden al
        kitap = self.list_manager.getir(index)
        if kitap:
            # Forma yükle
            self.form_handler.kitap_yukle(kitap)
    
    def kitap_sil(self):
        """Seçili kitabı listeden sil (checkbox seçimlerini de kontrol eder)"""
        if not self.gui_widgets.tree:
            return
        
        # Önce checkbox seçimlerini kontrol et
        secili_indeksler = self.gui_widgets.secili_kitaplari_getir()
        
        if secili_indeksler:
            # Checkbox ile seçili kitaplar var, toplu silme yap
            self.toplu_sil()
            return
        
        # Checkbox seçimi yoksa, Treeview'in kendi selection'ını kontrol et
        selected = self.gui_widgets.tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", 
                                  "Lütfen silmek için bir kitap seçin!\n\n"
                                  "💡 'Seç' sütunundaki ☐ işaretine tıklayarak kitap seçebilirsiniz.")
            return
        
        # Seçili satırın indeksini bul
        item = selected[0]
        index = self.gui_widgets.tree.index(item)
        
        # Kitabı listeden sil
        basarili, silinen_kitap = self.list_manager.sil(index)
        if basarili:
            self.listeyi_guncelle()
            silinen_kitap_adi = silinen_kitap.get('Kitap Adı', '')
            if len(silinen_kitap_adi) > 50:
                silinen_kitap_adi = silinen_kitap_adi[:47] + "..."
            messagebox.showinfo("✅ Başarılı", f"📚 '{silinen_kitap_adi}' listeden silindi!")
    
    def toplu_sil(self):
        """Seçili kitapları toplu olarak sil"""
        if not self.gui_widgets.tree:
            return
        
        # Seçili kitapların indekslerini al
        secili_indeksler = self.gui_widgets.secili_kitaplari_getir()
        
        if not secili_indeksler:
            messagebox.showwarning("Uyarı", "Lütfen silmek için en az bir kitap seçin!\n\n💡 'Seç' sütunundaki ☐ işaretine tıklayarak kitap seçebilirsiniz.")
            return
        
        # Onay mesajı
        secim_sayisi = len(secili_indeksler)
        cevap = messagebox.askyesno(
            "⚠️ Toplu Silme Onayı",
            f"Seçili {secim_sayisi} kitabı silmek istediğinize emin misiniz?\n\n"
            f"Bu işlem geri alınamaz!"
        )
        
        if not cevap:
            return
        
        # Kitapları tersten sil (indeks kaymasını önlemek için)
        silinen_kitaplar = []
        kitap_listesi = self.list_manager.tumunu_getir()
        
        # Tersten sırala (büyükten küçüğe)
        secili_indeksler.sort(reverse=True)
        
        for index in secili_indeksler:
            if 0 <= index < len(kitap_listesi):
                basarili, silinen_kitap = self.list_manager.sil(index)
                if basarili:
                    silinen_kitaplar.append(silinen_kitap.get('Kitap Adı', ''))
        
        # Listeyi güncelle
        self.listeyi_guncelle()
        
        # Başarı mesajı
        if silinen_kitaplar:
            mesaj = f"✅ {len(silinen_kitaplar)} kitap başarıyla silindi!\n\n"
            if len(silinen_kitaplar) <= 3:
                mesaj += "Silinen kitaplar:\n"
                for kitap_adi in silinen_kitaplar:
                    if len(kitap_adi) > 40:
                        kitap_adi = kitap_adi[:37] + "..."
                    mesaj += f"  • {kitap_adi}\n"
            else:
                mesaj += f"İlk 3 örnek:\n"
                for kitap_adi in silinen_kitaplar[:3]:
                    if len(kitap_adi) > 40:
                        kitap_adi = kitap_adi[:37] + "..."
                    mesaj += f"  • {kitap_adi}\n"
                mesaj += f"  ... ve {len(silinen_kitaplar) - 3} kitap daha"
            
            messagebox.showinfo("✅ Başarılı", mesaj)
    
    def tumunu_sec(self):
        """Tüm kitapları seç"""
        self.gui_widgets.tumunu_sec()
    
    def tumunu_kaldir(self):
        """Tüm seçimleri kaldır"""
        self.gui_widgets.tumunu_kaldir()
    
    def excel_olustur(self):
        """Kitap listesini Excel dosyasına kaydet"""
        # Formda doldurulmuş ama listeye eklenmemiş kitap var mı kontrol et
        if self.form_handler:
            degerler = self.form_handler.deger_al()
            formdaki_kitap_adi = degerler.get('kitap_adi', '').strip()
            if formdaki_kitap_adi:
                # Kitap adını kısalt
                kisa_kitap_adi = formdaki_kitap_adi
                if len(kisa_kitap_adi) > 50:
                    kisa_kitap_adi = kisa_kitap_adi[:47] + "..."
                
                cevap = messagebox.askyesno(
                    "📝 Formda Kitap Var",
                    f"Formda '{kisa_kitap_adi}' adlı bir kitap var ama listeye eklenmemiş.\n\n"
                    f"Önce listeye eklemek ister misiniz?"
                )
                if cevap:
                    if not self.listeye_ekle(mesaj_goster=False):
                        return
                    messagebox.showinfo("✅ Bilgi", f"📚 '{kisa_kitap_adi}' listeye eklendi ve Excel dosyasına kaydedilecek.")
        
        if self.list_manager.sayi() == 0:
            messagebox.showwarning("Uyarı", "Listede kitap yok! Lütfen önce kitap ekleyin.")
            return
        
        # Excel dosyası açık mı kontrol et
        if self.excel_handler.dosya_acik_mi():
            cevap = messagebox.askyesno(
                "Excel Dosyası Açık", 
                f"'{self.excel_handler.excel_dosyasi}' dosyası başka bir programda açık görünüyor.\n\n"
                f"Lütfen Excel dosyasını kapatıp tekrar deneyin.\n\n"
                f"Devam etmek istiyor musunuz?"
            )
            if not cevap:
                return
        
        try:
            kitap_listesi = self.list_manager.tumunu_getir()
            basarili = self.excel_handler.kaydet(kitap_listesi)
            
            if basarili:
                import os
                dosya_yolu = os.path.abspath(self.excel_handler.excel_dosyasi)
                toplam_kitap = len(kitap_listesi)
                
                # Sadece özet bilgi göster, kitap listesi gösterme
                mesaj = f"✅ Excel dosyası başarıyla oluşturuldu!\n\n"
                mesaj += f"📊 Toplam {toplam_kitap} kitap kaydedildi\n"
                mesaj += f"📁 Dosya konumu:\n{dosya_yolu}\n\n"
                
                # İlk 3 kitabı örnek olarak göster (sadece isim)
                if toplam_kitap > 0:
                    ilk_kitaplar = [kitap.get("Kitap Adı", "") for kitap in kitap_listesi[:3]]
                    mesaj += f"📚 Örnek kitaplar:\n"
                    for kitap_adi in ilk_kitaplar:
                        if len(kitap_adi) > 40:
                            kitap_adi = kitap_adi[:37] + "..."
                        mesaj += f"  • {kitap_adi}\n"
                    
                    if toplam_kitap > 3:
                        mesaj += f"  ... ve {toplam_kitap - 3} kitap daha"
                
                messagebox.showinfo("✅ Başarılı", mesaj)
            else:
                messagebox.showerror("Hata", "Excel dosyası kaydedilemedi!")
        except PermissionError:
            messagebox.showerror("Hata", 
                                f"Excel dosyası kaydedilemedi!\n\n"
                                f"'{self.excel_handler.excel_dosyasi}' dosyası başka bir programda açık olabilir.\n\n"
                                f"Lütfen:\n"
                                f"1. Excel dosyasını kapatın\n"
                                f"2. Dosyanın başka bir programda açık olmadığından emin olun\n"
                                f"3. Tekrar deneyin")
        except Exception as e:
            # Hata mesajını kısalt - traceback gösterme
            hata_mesaji = str(e)
            if len(hata_mesaji) > 200:
                hata_mesaji = hata_mesaji[:197] + "..."
            messagebox.showerror("❌ Hata", 
                                f"Excel dosyası oluşturulurken hata oluştu:\n\n"
                                f"{hata_mesaji}\n\n"
                                f"💡 Lütfen dosyanın açık olmadığından ve yazma izniniz olduğundan emin olun.")
    
    def excel_sablonu_olustur(self):
        """Boş Excel şablonu oluştur"""
        dosya_yolu = filedialog.asksaveasfilename(
            title="Excel Şablonu Kaydet",
            defaultextension=".xlsx",
            filetypes=[("Excel dosyaları", "*.xlsx"), ("Tüm dosyalar", "*.*")],
            initialfile="kitap_listesi_sablonu.xlsx"
        )
        
        if not dosya_yolu:
            return
        
        basarili = self.excel_handler.sablon_olustur(dosya_yolu)
        if basarili:
            # Dosya yolunu kısalt (çok uzunsa)
            if len(dosya_yolu) > 80:
                dosya_yolu_kisa = "..." + dosya_yolu[-77:]
            else:
                dosya_yolu_kisa = dosya_yolu
            
            messagebox.showinfo("✅ Başarılı", 
                              f"📄 Excel şablonu oluşturuldu!\n\n"
                              f"📁 {dosya_yolu_kisa}\n\n"
                              f"💡 Bu şablonu doldurup 'Excel'den Yükle' butonu ile programa yükleyebilirsiniz.")
        else:
            messagebox.showerror("Hata", "Excel şablonu oluşturulurken hata oluştu!")
    
    def excel_yukle(self):
        """Excel dosyasından kitap listesini yükle"""
        dosya_yolu = filedialog.askopenfilename(
            title="Excel Dosyası Seç",
            filetypes=[("Excel dosyaları", "*.xlsx"), ("Tüm dosyalar", "*.*")]
        )
        
        if not dosya_yolu:
            return
        
        try:
            kitaplar = self.excel_handler.disaridan_yukle(dosya_yolu)
            
            if kitaplar is None:
                messagebox.showerror("Hata", 
                                    f"Excel dosyası yüklenemedi!\n\n"
                                    f"Lütfen Excel şablonu kullanın veya dosyanın doğru formatta olduğundan emin olun.\n"
                                    f"Excel şablonu oluşturmak için 'Excel Şablonu Oluştur' butonunu kullanabilirsiniz.")
                return
            
            if not kitaplar:
                messagebox.showwarning("Uyarı", "Excel dosyasında kitap bulunamadı!")
                return
            
            # Toplu ekle
            sonuc = self.list_manager.toplu_ekle(kitaplar, tekrar_kontrol=True)
            
            # Listeyi güncelle
            self.listeyi_guncelle()
            
            # Sonuç mesajı - kısa ve öz
            eklenen_sayi = len(sonuc['eklenen'])
            atlanan_sayi = len(sonuc['atlanan'])
            toplam = self.list_manager.sayi()
            
            mesaj = f"✅ Excel dosyası yüklendi!\n\n"
            mesaj += f"➕ Eklenen: {eklenen_sayi} kitap\n"
            
            if atlanan_sayi > 0:
                mesaj += f"⏭️ Atlanan (zaten listede var): {atlanan_sayi} kitap\n"
                # Sadece ilk 2 atlanan kitabı göster (varsa)
                if atlanan_sayi <= 2:
                    mesaj += f"\nAtlanan kitaplar:\n"
                    for kitap in sonuc['atlanan']:
                        if len(kitap) > 40:
                            kitap = kitap[:37] + "..."
                        mesaj += f"  • {kitap}\n"
                elif atlanan_sayi > 2:
                    mesaj += f"\n(İlk 2 örnek: "
                    for i, kitap in enumerate(sonuc['atlanan'][:2]):
                        if len(kitap) > 30:
                            kitap = kitap[:27] + "..."
                        if i > 0:
                            mesaj += ", "
                        mesaj += f"{kitap}"
                    mesaj += f" ...)"
            
            mesaj += f"\n\n📚 Toplam kitap sayısı: {toplam}"
            messagebox.showinfo("✅ Başarılı", mesaj)
            
            # Otomatik bilgi doldurma seçeneği sun
            if eklenen_sayi > 0:
                secim = self._otomatik_doldurma_dialog_goster(eklenen_sayi)
                if secim == "toplu":
                    self._excel_kitaplari_otomatik_doldur(sonuc['eklenen'])
                elif secim == "iptal":
                    pass  # Hiçbir şey yapma
                # secim == "manuel" ise zaten kullanıcı çift tıklayarak yapabilir
            
        except Exception as e:
            # Hata mesajını kısalt
            hata_mesaji = str(e)
            if len(hata_mesaji) > 150:
                hata_mesaji = hata_mesaji[:147] + "..."
            messagebox.showerror("❌ Hata", 
                                f"Excel dosyası yüklenirken hata oluştu:\n\n"
                                f"{hata_mesaji}\n\n"
                                f"💡 Lütfen Excel dosyasının doğru formatta olduğundan emin olun.\n"
                                f"Excel şablonu oluşturmak için 'Excel Şablonu Oluştur' butonunu kullanabilirsiniz.")
    
    def _otomatik_doldurma_dialog_goster(self, kitap_sayisi: int) -> str:
        """
        Otomatik bilgi doldurma seçenekleri dialog'unu gösterir
        
        Args:
            kitap_sayisi: Yüklenen kitap sayısı
            
        Returns:
            "toplu", "manuel" veya "iptal"
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("🤖 Seçim Yapın")
        dialog.geometry("600x450")
        dialog.resizable(False, False)
        dialog.configure(bg='#F5E6D3')
        
        # Dialog'u modal yap
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Sonuç değişkeni
        sonuc = {"secim": "iptal"}
        secim_var = tk.StringVar(value="")
        
        # Başlık
        baslik_frame = tk.Frame(dialog, bg='#8B4513', relief=tk.RAISED, bd=3)
        baslik_frame.pack(fill=tk.X, padx=0, pady=0)
        
        baslik = tk.Label(baslik_frame, text="🤖 Otomatik Bilgi Doldurma Seçimi", 
                         font=("Georgia", 16, "bold"), 
                         bg='#8B4513', fg='#FFF8DC', pady=15)
        baslik.pack()
        
        # Ana içerik frame
        icerik_frame = tk.Frame(dialog, bg='#F5E6D3', padx=30, pady=20)
        icerik_frame.pack(fill=tk.BOTH, expand=True)
        
        # Mesaj
        mesaj_text = f"Excel'den {kitap_sayisi} kitap yüklendi.\n\nLütfen bir seçenek seçin:"
        mesaj_label = tk.Label(icerik_frame, text=mesaj_text,
                               font=("Georgia", 12, "bold"),
                               bg='#F5E6D3', fg='#654321',
                               justify=tk.CENTER)
        mesaj_label.pack(pady=(0, 20))
        
        # Seçenekler frame - Radio button'lar için
        secenekler_frame = tk.LabelFrame(icerik_frame, 
                                         text="  ⚙️ Seçenekler  ",
                                         font=("Georgia", 11, "bold"),
                                         bg='#FFF8DC', fg='#8B4513',
                                         relief=tk.RAISED, bd=2,
                                         padx=20, pady=15)
        secenekler_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Seçenek 1: Toplu çağrı
        secenek1_frame = tk.Frame(secenekler_frame, bg='#FFF8DC', relief=tk.RAISED, bd=2)
        secenek1_frame.pack(fill=tk.X, pady=10, padx=10)
        
        radio1 = tk.Radiobutton(secenek1_frame,
                               text="🔄 Her kitap için toplu çağrı yap",
                               variable=secim_var,
                               value="toplu",
                               font=("Georgia", 11, "bold"),
                               bg='#FFF8DC', fg='#654321',
                               activebackground='#FFF8DC',
                               activeforeground='#228B22',
                               selectcolor='#F5E6D3',
                               cursor='hand2',
                               anchor='w',
                               command=lambda: self._dialog_kapat(dialog, sonuc, "toplu"))
        radio1.pack(fill=tk.X, padx=15, pady=10)
        
        aciklama1 = tk.Label(secenek1_frame,
                            text="   → Tüm kitaplar için otomatik bilgi doldurma yapılır\n   → Bu işlem biraz zaman alabilir (her kitap için API çağrısı)",
                            font=("Georgia", 9),
                            bg='#FFF8DC', fg='#654321',
                            justify=tk.LEFT,
                            anchor='w')
        aciklama1.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # Seçenek 2: Manuel
        secenek2_frame = tk.Frame(secenekler_frame, bg='#FFF8DC', relief=tk.RAISED, bd=2)
        secenek2_frame.pack(fill=tk.X, pady=10, padx=10)
        
        radio2 = tk.Radiobutton(secenek2_frame,
                               text="👆 Manuel çift tıklayarak forma yükle",
                               variable=secim_var,
                               value="manuel",
                               font=("Georgia", 11, "bold"),
                               bg='#FFF8DC', fg='#654321',
                               activebackground='#FFF8DC',
                               activeforeground='#4169E1',
                               selectcolor='#F5E6D3',
                               cursor='hand2',
                               anchor='w',
                               command=lambda: self._dialog_kapat(dialog, sonuc, "manuel"))
        radio2.pack(fill=tk.X, padx=15, pady=10)
        
        aciklama2 = tk.Label(secenek2_frame,
                            text="   → Listeden bir kitaba çift tıklayarak forma yükleyin\n   → Sonra 'Bilgileri Otomatik Doldur' butonuna tıklayın",
                            font=("Georgia", 9),
                            bg='#FFF8DC', fg='#654321',
                            justify=tk.LEFT,
                            anchor='w')
        aciklama2.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # Butonlar frame
        butonlar_frame = tk.Frame(dialog, bg='#F5E6D3', padx=20, pady=15)
        butonlar_frame.pack(fill=tk.X)
        
        # Bilgi mesajı
        bilgi_label = tk.Label(butonlar_frame,
                               text="💡 Bir seçenek seçtiğinizde işlem otomatik başlar",
                               font=("Georgia", 9, "italic"),
                               bg='#F5E6D3', fg='#654321')
        bilgi_label.pack(pady=(0, 10))
        
        # İptal butonu (sadece iptal için)
        iptal_btn = tk.Button(butonlar_frame, text="❌ İptal",
                             bg='#CD5C5C', fg='#FFFFFF', activebackground='#DC143C',
                             activeforeground='#FFFFFF',
                             font=('Georgia', 11, 'bold'),
                             relief=tk.RAISED, bd=3, padx=25, pady=10,
                             cursor='hand2',
                             command=lambda: self._dialog_kapat(dialog, sonuc, "iptal"))
        iptal_btn.pack()
        
        # Dialog'u merkeze al
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Dialog kapanana kadar bekle
        dialog.wait_window()
        
        return sonuc["secim"]
    
    def _dialog_devam_et(self, dialog, sonuc, secim_var):
        """Seçimi kontrol et ve dialog'u kapat"""
        secim = secim_var.get()
        if not secim:
            messagebox.showwarning("Uyarı", "Lütfen bir seçenek seçin!")
            return
        self._dialog_kapat(dialog, sonuc, secim)
    
    def _dialog_kapat(self, dialog, sonuc, secim):
        """Dialog'u kapat ve seçimi kaydet"""
        sonuc["secim"] = secim
        dialog.destroy()
    
    def _excel_kitaplari_otomatik_doldur(self, kitaplar: list):
        """Excel'den yüklenen kitaplar için otomatik bilgi doldurma yapar"""
        if not kitaplar:
            return
        
        # API key kontrolü
        groq_key = self.api_key_manager.get()
        if not groq_key:
            groq_key = self.api_key_manager.yukle()
        
        if not groq_key:
            messagebox.showwarning(
                "Groq API Key Gerekli",
                "Otomatik bilgi doldurma için Groq API Key gereklidir!\n\n"
                "Lütfen 'Groq API Key' butonuna tıklayıp API key'inizi girin.\n"
                "Alternatif: Listeden bir kitaba çift tıklayarak forma yükleyip 'Bilgileri Otomatik Doldur' butonuna tıklayabilirsiniz."
            )
            return
        
        # API key'i bilgi_cekici'ye aktar
        self.bilgi_cekici.groq_api_key = groq_key
        
        # Progress bar göster
        self.gui_widgets.progress_goster(f"0/{len(kitaplar)} kitap işleniyor...")
        self.root.update()
        
        # Arka planda çalıştır
        thread = threading.Thread(target=self._excel_kitaplari_arka_planda_doldur, args=(kitaplar,))
        thread.daemon = True
        thread.start()
    
    def _excel_kitaplari_arka_planda_doldur(self, kitaplar: list):
        """Arka planda Excel'den yüklenen kitaplar için otomatik bilgi doldurma yapar"""
        import time
        
        try:
            toplam = len(kitaplar)
            basarili = 0
            basarisiz = 0
            
            for i, kitap in enumerate(kitaplar):
                kitap_adi = kitap.get('Kitap Adı', '').strip()
                yazar = kitap.get('Yazar', '').strip()
                
                if not kitap_adi or not yazar:
                    basarisiz += 1
                    continue
                
                # Retry logic: next_retry_at kontrolü
                next_retry_at = kitap.get('next_retry_at', '')
                if next_retry_at:
                    try:
                        from datetime import datetime
                        retry_time = datetime.fromisoformat(next_retry_at.replace('Z', '+00:00'))
                        now = datetime.utcnow()
                        if now < retry_time:
                            # Henüz retry zamanı gelmedi, atla
                            print(f"Retry bekleniyor ({kitap_adi}): {next_retry_at}")
                            continue
                    except Exception:
                        # Parse hatası, devam et
                        pass
                
                # Progress güncelle
                self.root.after(0, lambda idx=i+1, total=toplam, adi=kitap_adi: 
                    self.gui_widgets.progress_mesaj_guncelle(f"{idx}/{total} kitap işleniyor... ({adi[:30]}...)")
                )
                
                # ⚠️ ANİMASYON: Formu temizle ve kitap adı/yazarı yükle
                self.root.after(0, lambda adi=kitap_adi, yaz=yazar: self._animasyon_form_yukle(adi, yaz))
                time.sleep(0.1)  # GUI güncellemesi için kısa bekleme
                
                # Policy modu ile bilgi çek (mevcut kitap bilgilerini kullan)
                mevcut_kitap = {
                    "Kitap Adı": kitap_adi,
                    "Yazar": yazar,
                    "Orijinal Adı": kitap.get("Orijinal Adı", ""),
                    "Tür": kitap.get("Tür", ""),
                    "Ülke/Edebi Gelenek": kitap.get("Ülke/Edebi Gelenek", ""),
                    "Çıkış Yılı": kitap.get("Çıkış Yılı", ""),
                    "Anlatı Yılı": kitap.get("Anlatı Yılı", ""),
                    "Konusu": kitap.get("Konusu", ""),
                }
                
                try:
                    # Policy modu ile bilgi çek (status ve provenance dahil)
                    guncellenen_kitap = self.bilgi_cekici.kitap_bilgisi_cek_policy(kitap_adi, yazar, mevcut_kitap)
                    
                    # Sadece form alanlarını çıkar (meta kolonları zaten güncellenmiş)
                    bilgiler = {
                        "Orijinal Adı": guncellenen_kitap.get("Orijinal Adı", ""),
                        "Tür": guncellenen_kitap.get("Tür", ""),
                        "Ülke/Edebi Gelenek": guncellenen_kitap.get("Ülke/Edebi Gelenek", ""),
                        "Çıkış Yılı": guncellenen_kitap.get("Çıkış Yılı", ""),
                        "Anlatı Yılı": guncellenen_kitap.get("Anlatı Yılı", ""),
                        "Konusu": guncellenen_kitap.get("Konusu", ""),
                    }
                    
                    print(f"Policy modu sonuçları ({kitap_adi}): status={guncellenen_kitap.get('status', 'UNKNOWN')}")
                except Exception as e:
                    print(f"Policy modu hatası ({kitap_adi}): {e}")
                    import traceback
                    traceback.print_exc()
                    # Hata durumunda mevcut kitabı koru ve status yaz
                    from field_registry import ensure_row_schema
                    from provenance import set_row_status
                    guncellenen_kitap = ensure_row_schema(kitap.copy())
                    # Hata durumunda FAIL status yaz
                    set_row_status(
                        guncellenen_kitap,
                        status="FAIL",
                        missing_fields=["Orijinal Adı", "Tür", "Ülke/Edebi Gelenek", "Çıkış Yılı", "Anlatı Yılı", "Konusu"],
                        best_source="error",
                        retry_count=1,
                        next_retry_hours=6
                    )
                    bilgiler = {
                        "Orijinal Adı": kitap.get("Orijinal Adı", ""),
                        "Tür": kitap.get("Tür", ""),
                        "Ülke/Edebi Gelenek": kitap.get("Ülke/Edebi Gelenek", ""),
                        "Çıkış Yılı": kitap.get("Çıkış Yılı", ""),
                        "Anlatı Yılı": kitap.get("Anlatı Yılı", ""),
                        "Konusu": kitap.get("Konusu", ""),
                    }
                
                # ⚠️ ANİMASYON: Formu doldur (hızlı animasyon)
                self.root.after(0, lambda bilg=bilgiler: self._animasyon_form_doldur(bilg))
                time.sleep(0.3)  # Animasyon için kısa bekleme (kullanıcı görebilsin)
                
                # Listede bul ve güncelle (status ve provenance dahil)
                # ensure_row_schema ile tüm kolonların olduğundan emin ol
                from field_registry import ensure_row_schema
                guncellenen_kitap = ensure_row_schema(guncellenen_kitap)
                
                kitap_listesi = self.list_manager.tumunu_getir()
                for idx, listedeki_kitap in enumerate(kitap_listesi):
                    if (listedeki_kitap.get('Kitap Adı', '').strip() == kitap_adi and 
                        listedeki_kitap.get('Yazar', '').strip() == yazar):
                        # Kitabı güncelle (status ve provenance dahil)
                        # Mevcut kitabın diğer kolonlarını koru (Not, vb.)
                        mevcut_kitap = ensure_row_schema(listedeki_kitap.copy())
                        mevcut_kitap.update(guncellenen_kitap)
                        self.list_manager.kitap_listesi[idx] = mevcut_kitap
                        basarili += 1
                        break
                else:
                    basarisiz += 1
                
                # Checkpoint: Her 50 kitapta bir Excel'e kaydet
                if (i + 1) % 50 == 0:
                    try:
                        self.excel_handler.kaydet(self.list_manager.tumunu_getir())
                        print(f"Checkpoint: {i + 1}/{toplam} kitap Excel'e kaydedildi")
                    except Exception as e:
                        print(f"Checkpoint kaydetme hatası: {e}")
                
                # ⚠️ ANİMASYON: Formu temizle (sonraki kitap için hazırla)
                self.root.after(0, self._animasyon_form_temizle)
                time.sleep(0.1)  # Kısa bekleme
            
            # Son form temizleme
            self.root.after(0, self._animasyon_form_temizle)
            
            # Final checkpoint: Tüm kitapları Excel'e kaydet (status ve provenance dahil)
            try:
                self.excel_handler.kaydet(self.list_manager.tumunu_getir())
                print(f"Final checkpoint: Tüm kitaplar Excel'e kaydedildi")
            except Exception as e:
                print(f"Final checkpoint kaydetme hatası: {e}")
            
            # Listeyi güncelle
            self.root.after(0, self.listeyi_guncelle)
            
            # Sonuç mesajı
            self.root.after(0, lambda: messagebox.showinfo(
                "✅ Tamamlandı",
                f"📚 Otomatik bilgi doldurma tamamlandı!\n\n"
                f"✅ Başarılı: {basarili} kitap\n"
                f"❌ Başarısız: {basarisiz} kitap\n\n"
                f"💡 Listeden bir kitaba çift tıklayarak detayları görebilirsiniz."
            ))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "❌ Hata",
                f"Otomatik bilgi doldurma sırasında hata oluştu:\n\n{str(e)}"
            ))
        finally:
            self.root.after(0, self.gui_widgets.progress_gizle)
    
    def _animasyon_form_yukle(self, kitap_adi: str, yazar: str):
        """Animasyon için formu kitap adı ve yazar ile yükler"""
        if not self.form_handler:
            return
        
        # Formu temizle
        self.form_handler.temizle()
        
        # Kitap adı ve yazarı yükle
        if 'kitap_adi' in self.form_handler.widgets:
            self.form_handler.widgets['kitap_adi'].delete(0, tk.END)
            self.form_handler.widgets['kitap_adi'].insert(0, kitap_adi)
        
        if 'yazar' in self.form_handler.widgets:
            self.form_handler.widgets['yazar'].delete(0, tk.END)
            self.form_handler.widgets['yazar'].insert(0, yazar)
        
        # GUI'yi güncelle
        self.root.update_idletasks()
    
    def _animasyon_form_doldur(self, bilgiler: dict):
        """Animasyon için formu bilgilerle doldurur"""
        if not self.form_handler:
            return
        
        # Formu doldur (sadece boş alanları doldur)
        self.form_handler.doldur(bilgiler, sadece_bos=True)
        
        # GUI'yi güncelle
        self.root.update_idletasks()
    
    def _animasyon_form_temizle(self):
        """Animasyon için formu temizler"""
        if not self.form_handler:
            return
        
        # Formu temizle
        self.form_handler.temizle()
        
        # GUI'yi güncelle
        self.root.update_idletasks()
    
    def groq_api_key_ayarla(self):
        """Groq API key ayarlarını göster"""
        mesaj = "Groq API Key Ayarları\n\n"
        mevcut_key = self.api_key_manager.get()
        
        if mevcut_key:
            mesaj += f"Mevcut API Key: {mevcut_key[:10]}...\n\n"
            mesaj += "Groq API Key ücretsizdir ve kitap bilgilerini daha doğru çıkarmak için kullanılır.\n\n"
            mesaj += "Yeni bir API key girmek ister misiniz?"
            cevap = messagebox.askyesno("Groq API Key", mesaj)
            if not cevap:
                return
        else:
            mesaj += "Groq API Key ücretsizdir ve kitap bilgilerini daha doğru çıkarmak için kullanılır.\n\n"
            mesaj += "API key almak için:\n"
            mesaj += "1. https://console.groq.com adresine gidin\n"
            mesaj += "2. Ücretsiz hesap oluşturun\n"
            mesaj += "3. API Keys bölümünden yeni bir key oluşturun\n"
            mesaj += "4. Key'i buraya yapıştırın\n\n"
            mesaj += "API key olmadan da çalışır, ancak bazı bilgiler eksik kalabilir."
            messagebox.showinfo("Groq API Key", mesaj)
        
        # API key girişi
        api_key = simpledialog.askstring(
            "Groq API Key",
            "Groq API Key'inizi girin (boş bırakırsanız mevcut key silinir):",
            show='*'
        )
        
        if api_key is None:  # İptal edildi
            return
        
        if api_key.strip():
            if self.api_key_manager.kaydet(api_key.strip()):
                self.bilgi_cekici.groq_api_key = api_key.strip()
                messagebox.showinfo("Başarılı", "Groq API Key kaydedildi!")
                # Buton metnini güncelle
                durum = self.api_key_manager.durum()
                self.gui_widgets.api_key_buton_guncelle(durum)
            else:
                messagebox.showerror("Hata", "API key kaydedilemedi!")
        else:
            # API key'i sil
            if self.api_key_manager.sil():
                self.bilgi_cekici.groq_api_key = ''
                messagebox.showinfo("Bilgi", "Groq API Key silindi.")
                # Buton metnini güncelle
                durum = self.api_key_manager.durum()
                self.gui_widgets.api_key_buton_guncelle(durum)
            else:
                messagebox.showerror("Hata", "API key silinemedi!")


def main():
    root = tk.Tk()
    app = KitapListesiGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
