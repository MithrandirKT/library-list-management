"""
GUI Widget'lari Modulu
GUI widget'larinin olusturulmasi ve yonetimi
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, Optional


class GUIWidgets:
    """GUI widget'lari icin sinif"""
    
    def __init__(self, root: tk.Tk):
        """
        Args:
            root: Tkinter root penceresi
        """
        self.root = root
        self.widgets: Dict[str, tk.Widget] = {}
        self.progress_frame: Optional[ttk.Frame] = None
        self.progress_bar: Optional[ttk.Progressbar] = None
        self.progress_label: Optional[ttk.Label] = None
        self.tree: Optional[ttk.Treeview] = None
        self.checkbox_vars: dict = {}  # Her satır için checkbox değişkenleri
    
    def olustur(self, callbacks: Dict[str, Callable]):
        """
        Tum GUI widget'larini olusturur
        
        Args:
            callbacks: Callback fonksiyonları dict'i
                Örnek: {
                    'listeye_ekle': fonksiyon,
                    'formu_temizle': fonksiyon,
                    ...
                }
        """
        # Kitap temalı renkler
        self.root.configure(bg='#F5E6D3')  # Açık bej/kahverengi arka plan
        
        # Ana frame
        main_frame = tk.Frame(self.root, bg='#F5E6D3', padx=15, pady=15)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Başlık - Kitap temalı
        baslik_frame = tk.Frame(main_frame, bg='#8B4513', relief=tk.RAISED, bd=2)
        baslik_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        
        baslik = tk.Label(baslik_frame, text="📚 Kitap Bilgileri Girişi 📚", 
                         font=("Georgia", 20, "bold"), 
                         bg='#8B4513', fg='#FFF8DC', pady=10)
        baslik.pack()
        
        # Üst kısım: Form ve Konusu yan yana
        ust_frame = tk.Frame(main_frame, bg='#F5E6D3')
        ust_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Sol taraf: Form alanları
        form_frame = self._form_frame_olustur(ust_frame, callbacks)
        form_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Sağ taraf: Konusu (dikey)
        konusu_frame = self._konusu_frame_olustur(ust_frame)
        konusu_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Liste görüntüleme
        liste_frame = self._liste_frame_olustur(main_frame, callbacks)
        liste_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 0))
        
        # Grid ağırlıkları
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=2)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        ust_frame.columnconfigure(0, weight=2)
        ust_frame.columnconfigure(1, weight=1)
        ust_frame.rowconfigure(0, weight=1)
        liste_frame.columnconfigure(0, weight=1)
        liste_frame.rowconfigure(0, weight=1)
    
    def _form_frame_olustur(self, parent, callbacks: Dict[str, Callable]) -> tk.LabelFrame:
        """Form frame'ini oluşturur"""
        form_frame = tk.LabelFrame(parent, text="📖 Yeni Kitap Ekle", 
                                   font=("Georgia", 12, "bold"),
                                   bg='#FFF8DC', fg='#8B4513', 
                                   relief=tk.RAISED, bd=3, padx=15, pady=15)
        
        # Stil ayarları
        label_font = ("Georgia", 10)
        entry_font = ("Georgia", 9)
        readonly_bg = '#F5F5DC'  # Açık bej
        readonly_fg = '#654321'  # Koyu kahverengi
        normal_bg = '#FFFFFF'    # Beyaz
        
        # Kitap Adı (zorunlu) - YAZILABILIR
        kitap_label = tk.Label(form_frame, text="Kitap Adı (Türkçe) *:", 
                               font=label_font, bg='#FFF8DC', fg='#8B4513', anchor='w')
        kitap_label.grid(row=0, column=0, sticky=tk.W, pady=8)
        self.widgets['kitap_adi'] = tk.Entry(form_frame, width=40, font=entry_font,
                                             bg=normal_bg, fg='#000000',
                                             relief=tk.SOLID, bd=2, insertbackground='#000000')
        self.widgets['kitap_adi'].grid(row=0, column=1, pady=8, padx=5, sticky=(tk.W, tk.E))
        
        # Yazar (zorunlu) - YAZILABILIR
        yazar_label = tk.Label(form_frame, text="Yazar *:", 
                              font=label_font, bg='#FFF8DC', fg='#8B4513', anchor='w')
        yazar_label.grid(row=1, column=0, sticky=tk.W, pady=8)
        self.widgets['yazar'] = tk.Entry(form_frame, width=40, font=entry_font,
                                         bg=normal_bg, fg='#000000',
                                         relief=tk.SOLID, bd=2, insertbackground='#000000')
        self.widgets['yazar'].grid(row=1, column=1, pady=8, padx=5, sticky=(tk.W, tk.E))
        
        # Orijinal Adı - READONLY
        orijinal_label = tk.Label(form_frame, text="Orijinal Adı:", 
                                  font=label_font, bg='#FFF8DC', fg='#8B4513', anchor='w')
        orijinal_label.grid(row=2, column=0, sticky=tk.W, pady=8)
        self.widgets['orijinal_adi'] = tk.Entry(form_frame, width=40, font=entry_font,
                                               bg=readonly_bg, fg=readonly_fg,
                                               relief=tk.SOLID, bd=2, state='readonly')
        self.widgets['orijinal_adi'].grid(row=2, column=1, pady=8, padx=5, sticky=(tk.W, tk.E))
        
        # Tür - READONLY
        tur_label = tk.Label(form_frame, text="Tür:", 
                            font=label_font, bg='#FFF8DC', fg='#8B4513', anchor='w')
        tur_label.grid(row=3, column=0, sticky=tk.W, pady=8)
        self.widgets['tur'] = ttk.Combobox(form_frame, width=37, font=entry_font,
                                           values=["Roman", "Novella", "Öykü", "Felsefe", "Tarih", "Bilim", "Şiir", "Tiyatro"],
                                           state='readonly')
        self.widgets['tur'].grid(row=3, column=1, pady=8, padx=5, sticky=(tk.W, tk.E))
        
        # Ülke/Edebi Gelenek - READONLY
        ulke_label = tk.Label(form_frame, text="Ülke/Edebi Gelenek:", 
                              font=label_font, bg='#FFF8DC', fg='#8B4513', anchor='w')
        ulke_label.grid(row=4, column=0, sticky=tk.W, pady=8)
        self.widgets['ulke'] = tk.Entry(form_frame, width=40, font=entry_font,
                                         bg=readonly_bg, fg=readonly_fg,
                                         relief=tk.SOLID, bd=2, state='readonly')
        self.widgets['ulke'].grid(row=4, column=1, pady=8, padx=5, sticky=(tk.W, tk.E))
        
        # Çıkış Yılı - READONLY
        cikis_label = tk.Label(form_frame, text="Çıkış Yılı:", 
                               font=label_font, bg='#FFF8DC', fg='#8B4513', anchor='w')
        cikis_label.grid(row=5, column=0, sticky=tk.W, pady=8)
        self.widgets['cikis_yili'] = tk.Entry(form_frame, width=40, font=entry_font,
                                             bg=readonly_bg, fg=readonly_fg,
                                             relief=tk.SOLID, bd=2, state='readonly')
        self.widgets['cikis_yili'].grid(row=5, column=1, pady=8, padx=5, sticky=(tk.W, tk.E))
        
        # Anlatı Yılı - READONLY
        anlati_label = tk.Label(form_frame, text="Anlatı Yılı:", 
                               font=label_font, bg='#FFF8DC', fg='#8B4513', anchor='w')
        anlati_label.grid(row=6, column=0, sticky=tk.W, pady=8)
        self.widgets['anlati_yili'] = tk.Entry(form_frame, width=40, font=entry_font,
                                               bg=readonly_bg, fg=readonly_fg,
                                               relief=tk.SOLID, bd=2, state='readonly')
        self.widgets['anlati_yili'].grid(row=6, column=1, pady=8, padx=5, sticky=(tk.W, tk.E))
        
        # Not - READONLY
        not_label = tk.Label(form_frame, text="Not (Alternatif çeviri adları):", 
                            font=label_font, bg='#FFF8DC', fg='#8B4513', anchor='w')
        not_label.grid(row=7, column=0, sticky=tk.W, pady=8)
        self.widgets['not_alan'] = tk.Entry(form_frame, width=40, font=entry_font,
                                            bg=readonly_bg, fg=readonly_fg,
                                            relief=tk.SOLID, bd=2, state='readonly')
        self.widgets['not_alan'].grid(row=7, column=1, pady=8, padx=5, sticky=(tk.W, tk.E))
        
        # Butonlar - Kitap temalı
        button_frame = tk.Frame(form_frame, bg='#FFF8DC')
        button_frame.grid(row=8, column=0, columnspan=2, pady=15)
        
        button_style = {'font': ('Georgia', 10, 'bold'), 'relief': tk.RAISED, 'bd': 2,
                       'padx': 12, 'pady': 8, 'cursor': 'hand2'}
        
        if 'bilgileri_otomatik_doldur' in callbacks:
            auto_btn = tk.Button(button_frame, text="✨ Bilgileri Otomatik Doldur", 
                                bg='#8B4513', fg='#FFF8DC', activebackground='#A0522D',
                                activeforeground='#FFFFFF', command=callbacks['bilgileri_otomatik_doldur'],
                                **button_style)
            auto_btn.pack(side=tk.LEFT, padx=5)
        
        if 'listeye_ekle' in callbacks:
            ekle_btn = tk.Button(button_frame, text="➕ Listeye Ekle", 
                                bg='#228B22', fg='#FFFFFF', activebackground='#32CD32',
                                activeforeground='#FFFFFF', command=callbacks['listeye_ekle'],
                                **button_style)
            ekle_btn.pack(side=tk.LEFT, padx=5)
        
        if 'formu_temizle' in callbacks:
            temizle_btn = tk.Button(button_frame, text="🗑️ Formu Temizle", 
                                   bg='#CD5C5C', fg='#FFFFFF', activebackground='#DC143C',
                                   activeforeground='#FFFFFF', command=callbacks['formu_temizle'],
                                   **button_style)
            temizle_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress bar ve durum etiketi (başlangıçta gizli)
        self.progress_frame = tk.Frame(form_frame, bg='#FFF8DC')
        self.progress_frame.grid(row=9, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        self.progress_frame.grid_remove()  # Başlangıçta gizle
        
        self.progress_label = tk.Label(self.progress_frame, text="Bilgiler çekiliyor...",
                                      font=('Georgia', 9), bg='#FFF8DC', fg='#8B4513')
        self.progress_label.pack(side=tk.LEFT, padx=5)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate', length=300)
        self.progress_bar.pack(side=tk.LEFT, padx=5)
        
        form_frame.columnconfigure(1, weight=1)
        
        return form_frame
    
    def _konusu_frame_olustur(self, parent) -> tk.LabelFrame:
        """Konusu frame'ini oluşturur (sağ taraf, dikey)"""
        konusu_frame = tk.LabelFrame(parent, text="📝 Konusu", 
                                     font=("Georgia", 12, "bold"),
                                     bg='#FFF8DC', fg='#8B4513', 
                                     relief=tk.RAISED, bd=3, padx=15, pady=15)
        
        # Konusu Text widget - READONLY, dikey
        self.widgets['konusu'] = tk.Text(konusu_frame, width=35, height=20, 
                                         font=("Georgia", 10),
                                         bg='#F5F5DC', fg='#654321',
                                         relief=tk.SOLID, bd=2, wrap=tk.WORD,
                                         state='disabled',  # Readonly için disabled kullanıyoruz
                                         padx=10, pady=10)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(konusu_frame, orient=tk.VERTICAL, 
                                command=self.widgets['konusu'].yview,
                                bg='#D2B48C', troughcolor='#F5E6D3',
                                activebackground='#8B4513')
        self.widgets['konusu'].configure(yscrollcommand=scrollbar.set)
        
        self.widgets['konusu'].grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        konusu_frame.columnconfigure(0, weight=1)
        konusu_frame.rowconfigure(0, weight=1)
        
        return konusu_frame
    
    def _liste_frame_olustur(self, parent, callbacks: Dict[str, Callable]) -> tk.LabelFrame:
        """Liste frame'ini oluşturur"""
        liste_frame = tk.LabelFrame(parent, text="📚 Kitap Listesi (0 kitap)", 
                                    font=("Georgia", 12, "bold"),
                                    bg='#FFF8DC', fg='#8B4513', 
                                    relief=tk.RAISED, bd=3, padx=15, pady=15)
        
        # Treeview (tablo) - Kitap temalı stil
        columns = ("Seç", "Kitap Adı", "Yazar", "Tür", "Çıkış Yılı")
        self.tree = ttk.Treeview(liste_frame, columns=columns, show="headings", height=12)
        
        # Stil ayarları
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background="#F5F5DC", foreground="#654321",
                       fieldbackground="#F5F5DC", font=("Georgia", 9))
        style.configure("Treeview.Heading", background="#8B4513", foreground="#FFF8DC",
                      font=("Georgia", 10, "bold"))
        style.map("Treeview", background=[("selected", "#A0522D")])
        
        # Sütun başlıkları ve genişlikleri
        self.tree.heading("Seç", text="☑", command=self._baslik_checkbox_toggle)
        self.tree.column("Seç", width=50, anchor='center')
        
        for col in columns[1:]:  # "Seç" hariç diğer sütunlar
            self.tree.heading(col, text=col)
            self.tree.column(col, width=180)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(liste_frame, orient=tk.VERTICAL, 
                                command=self.tree.yview,
                                bg='#D2B48C', troughcolor='#F5E6D3',
                                activebackground='#8B4513')
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Çift tıklama event'i - kitabı forma yüklemek için (sadece "Seç" sütunu dışında)
        if 'kitap_sec' in callbacks:
            def on_double_click(event):
                region = self.tree.identify_region(event.x, event.y)
                if region == "cell":
                    column = self.tree.identify_column(event.x)  # Sadece x koordinatı
                    # "Seç" sütunu değilse
                    if column != "#1":
                        callbacks['kitap_sec']()
            self.tree.bind('<Double-1>', on_double_click)
        
        # Checkbox tıklama event'i - "Seç" sütununa tıklama
        # ⚠️ DİKKAT: Event handling mantığı
        # - Button-1 event'i ile checkbox toggle yapılır
        # - "Seç" sütununa (#1) tıklanınca checkbox toggle edilir
        # - return "break" ile Treeview'in kendi selection'ı engellenir
        # - Checkbox toggle edildiğinde Treeview selection'ı da güncellenir
        self.tree.bind('<Button-1>', self._on_tree_click)
        
        # Liste butonları - Kitap temalı
        liste_button_frame = tk.Frame(liste_frame, bg='#FFF8DC')
        liste_button_frame.grid(row=1, column=0, columnspan=2, pady=15)
        
        button_style = {'font': ('Georgia', 9, 'bold'), 'relief': tk.RAISED, 'bd': 2,
                       'padx': 10, 'pady': 6, 'cursor': 'hand2'}
        
        # Tümünü Kaldır butonu
        if 'tumunu_kaldir' in callbacks:
            tumunu_kaldir_btn = tk.Button(liste_button_frame, text="☐ Tümünü Kaldır", 
                                         bg='#4169E1', fg='#FFFFFF', activebackground='#6495ED',
                                         activeforeground='#FFFFFF', command=callbacks['tumunu_kaldir'],
                                         **button_style)
            tumunu_kaldir_btn.pack(side=tk.LEFT, padx=5)
        
        if 'kitap_sil' in callbacks:
            sil_btn = tk.Button(liste_button_frame, text="🗑️ Seçili Kitabı Sil", 
                               bg='#CD5C5C', fg='#FFFFFF', activebackground='#DC143C',
                               activeforeground='#FFFFFF', command=callbacks['kitap_sil'],
                               **button_style)
            sil_btn.pack(side=tk.LEFT, padx=5)
        
        if 'toplu_sil' in callbacks:
            toplu_sil_btn = tk.Button(liste_button_frame, text="🗑️ Seçili Kitapları Sil", 
                                     bg='#DC143C', fg='#FFFFFF', activebackground='#B22222',
                                     activeforeground='#FFFFFF', command=callbacks['toplu_sil'],
                                     **button_style)
            toplu_sil_btn.pack(side=tk.LEFT, padx=5)
        
        if 'excel_olustur' in callbacks:
            excel_btn = tk.Button(liste_button_frame, text="📊 Excel Dosyası Oluştur", 
                                 bg='#228B22', fg='#FFFFFF', activebackground='#32CD32',
                                 activeforeground='#FFFFFF', command=callbacks['excel_olustur'],
                                 **button_style)
            excel_btn.pack(side=tk.LEFT, padx=5)
        
        # Excel işlemleri için ayrı bir frame
        excel_button_frame = tk.Frame(liste_button_frame, bg='#FFF8DC')
        excel_button_frame.pack(side=tk.LEFT, padx=5)
        
        if 'excel_sablonu_olustur' in callbacks:
            sablon_btn = tk.Button(excel_button_frame, text="📄 Excel Şablonu Oluştur", 
                                   bg='#4169E1', fg='#FFFFFF', activebackground='#6495ED',
                                   activeforeground='#FFFFFF', command=callbacks['excel_sablonu_olustur'],
                                   **button_style)
            sablon_btn.pack(side=tk.LEFT, padx=2)
        
        if 'excel_yukle' in callbacks:
            yukle_btn = tk.Button(excel_button_frame, text="📥 Excel'den Yükle", 
                                 bg='#4169E1', fg='#FFFFFF', activebackground='#6495ED',
                                 activeforeground='#FFFFFF', command=callbacks['excel_yukle'],
                                 **button_style)
            yukle_btn.pack(side=tk.LEFT, padx=2)
        
        # Groq API Key ayarları butonu
        if 'groq_api_key_ayarla' in callbacks:
            self.api_key_button = tk.Button(liste_button_frame, text="🔑 Groq API Key (✗)", 
                                           bg='#8B4513', fg='#FFF8DC', activebackground='#A0522D',
                                           activeforeground='#FFFFFF', command=callbacks['groq_api_key_ayarla'],
                                           **button_style)
            self.api_key_button.pack(side=tk.RIGHT, padx=5)
        
        return liste_frame
    
    def listeyi_guncelle(self, kitap_listesi: list):
        """Treeview'i günceller"""
        if not self.tree:
            return
        
        # Mevcut öğeleri temizle
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # ⚠️ KRİTİK: Checkbox değişkenlerini temizle
        # Her satır için BooleanVar tutulur (checkbox_vars dict'i)
        # Listeyi güncellerken mutlaka temizle, aksi halde eski checkbox'lar kalır
        self.checkbox_vars = {}
        
        # Kitapları ekle
        for idx, kitap in enumerate(kitap_listesi):
            # Her satır için checkbox değişkeni oluştur
            var = tk.BooleanVar(value=False)
            self.checkbox_vars[idx] = var
            
            # Checkbox durumunu göster (☑ veya ☐)
            checkbox_text = "☐"
            
            self.tree.insert("", tk.END, values=(
                checkbox_text,
                kitap.get("Kitap Adı", ""),
                kitap.get("Yazar", ""),
                kitap.get("Tür", ""),
                kitap.get("Çıkış Yılı", "")
            ), tags=(f"item_{idx}",))
        
        # Başlığı güncelle
        liste_frame = self.tree.master
        liste_frame.config(text=f"📚 Kitap Listesi ({len(kitap_listesi)} kitap)")
        
        # Başlık sütunundaki ☑ işaretini güncelle
        if self.checkbox_vars:
            tumu_secili = all(var.get() for var in self.checkbox_vars.values())
            baslik_text = "☑" if tumu_secili else "☐"
            self.tree.heading("Seç", text=baslik_text, command=self._baslik_checkbox_toggle)
        else:
            self.tree.heading("Seç", text="☐", command=self._baslik_checkbox_toggle)
    
    def _on_tree_click(self, event):
        """Treeview tıklama event'i - checkbox kontrolü yapar"""
        if not self.tree:
            return
        
        # Tıklanan bölgeyi kontrol et
        try:
            region = self.tree.identify_region(event.x, event.y)
            if region != "cell":
                return
        except:
            return
        
        # Tıklanan sütunu bul
        # ⚠️ KRİTİK: identify_column() sadece x koordinatı alır (y koordinatı yok!)
        # Python 3.10+ için: identify_column(event.x) - sadece x
        # Eski versiyonlar için: identify_column(event.x, event.y) - hata verir
        try:
            column = self.tree.identify_column(event.x)  # Sadece x koordinatı
        except:
            return
        
        # İlk sütun (Seç - #1) ise checkbox toggle et
        if column == "#1":
            try:
                item = self.tree.identify_row(event.y)
            except:
                return
            
            if item:
                # Satır indeksini bul
                children = list(self.tree.get_children())
                if item in children:
                    idx = children.index(item)
                    # Checkbox durumunu toggle et
                    if idx in self.checkbox_vars:
                            var = self.checkbox_vars[idx]
                            var.set(not var.get())
                            # Treeview'de güncelle
                            checkbox_text = "☑" if var.get() else "☐"
                            try:
                                values = list(self.tree.item(item, "values"))
                                if values:
                                    values[0] = checkbox_text
                                    self.tree.item(item, values=values)
                                # Satırı seçili göster veya kaldır
                                if var.get():
                                    self.tree.selection_add(item)
                                else:
                                    self.tree.selection_remove(item)
                            except:
                                pass
                            # Event'i durdur (normal selection'ı engelle)
                            return "break"
        
        # "Seç" sütunu değilse normal davranışa izin ver
        return
    
    def _baslik_checkbox_toggle(self):
        """Başlık sütunundaki ☑ işaretine tıklanınca tümünü seç/kaldır"""
        if not self.tree or not self.checkbox_vars:
            return
        
        # Tüm checkbox'ların durumunu kontrol et
        tumu_secili = all(var.get() for var in self.checkbox_vars.values())
        
        # Eğer hepsi seçiliyse kaldır, değilse seç
        if tumu_secili:
            self.tumunu_kaldir()
            # Başlığı güncelle
            self.tree.heading("Seç", text="☐")
        else:
            self.tumunu_sec()
            # Başlığı güncelle
            self.tree.heading("Seç", text="☑")
    
    def secili_kitaplari_getir(self) -> list:
        """Seçili kitapların indekslerini döndürür"""
        secili_indeksler = []
        for idx, var in self.checkbox_vars.items():
            if var.get():
                secili_indeksler.append(idx)
        return secili_indeksler
    
    def tumunu_sec(self):
        """Tüm kitapları seç"""
        if not self.tree:
            return
        
        children = list(self.tree.get_children())
        for idx, var in self.checkbox_vars.items():
            var.set(True)
            # Treeview'de güncelle
            if idx < len(children):
                item = children[idx]
                try:
                    values = list(self.tree.item(item, "values"))
                    if values:
                        values[0] = "☑"
                        self.tree.item(item, values=values)
                        # Satırı seçili göster
                        self.tree.selection_add(item)
                except:
                    pass
    
    def tumunu_kaldir(self):
        """Tüm seçimleri kaldır"""
        if not self.tree:
            return
        
        children = list(self.tree.get_children())
        for idx, var in self.checkbox_vars.items():
            var.set(False)
            # Treeview'de güncelle
            if idx < len(children):
                item = children[idx]
                try:
                    values = list(self.tree.item(item, "values"))
                    if values:
                        values[0] = "☐"
                        self.tree.item(item, values=values)
                        # Satır seçimini kaldır
                        self.tree.selection_remove(item)
                except:
                    pass
    
    def progress_goster(self, mesaj: str = "Bilgiler çekiliyor..."):
        """Progress bar'ı gösterir"""
        if self.progress_frame and self.progress_bar and self.progress_label:
            self.progress_frame.grid()
            self.progress_bar.start()
            self.progress_label.config(text=mesaj)
    
    def progress_gizle(self):
        """Progress bar'ı gizler"""
        if self.progress_bar:
            self.progress_bar.stop()
        if self.progress_frame:
            self.progress_frame.grid_remove()
    
    def progress_mesaj_guncelle(self, mesaj: str):
        """Progress bar mesajını günceller"""
        if self.progress_label:
            self.progress_label.config(text=mesaj)
    
    def api_key_buton_guncelle(self, durum: str):
        """API key butonunu günceller"""
        if hasattr(self, 'api_key_button'):
            durum_icon = "✓" if durum == "✓" else "✗"
            self.api_key_button.config(text=f"🔑 Groq API Key ({durum_icon})")
    
    def get_widgets(self) -> Dict[str, tk.Widget]:
        """Widget'ları döndürür"""
        return self.widgets
