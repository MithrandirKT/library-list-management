# 📚 Kitap Listesi Yönetim Programı

## 🎯 Program Ne İşe Yarar?

Bu program, kitap koleksiyonunuzu dijital ortamda yönetmenizi sağlayan Windows masaüstü uygulamasıdır. Kitap bilgilerinizi otomatik olarak çoklu kaynaklardan (Wikipedia, Google Books, Open Library ve AI servisleri) çekerek Excel dosyasına kaydeder.

### ✨ Ana Özellikler

- **📝 Manuel Kitap Ekleme**: Kitap adı ve yazar bilgisi girerek kitap ekleyebilirsiniz
- **🤖 Otomatik Bilgi Doldurma**: Kitap bilgileri otomatik olarak internetten çekilir
- **📊 Excel Entegrasyonu**: Tüm kitaplarınızı Excel dosyasına kaydedebilirsiniz
- **📥 Excel'den Toplu Yükleme**: Excel dosyasından toplu kitap ekleyebilirsiniz
- **🔍 Çoklu Kaynak Desteği**: Wikipedia, Google Books, Open Library ve AI servisleri kullanılır
- **💾 Otomatik Kayıt**: Excel dosyası otomatik olarak yüklenir ve kaydedilir

## 🚀 Nasıl Çalışır?

### 1️⃣ Programı Başlatma

Programı başlatmak için iki yöntem var:

**Yöntem 1 (Önerilen):**
- `PROGRAMI_AC.vbs` dosyasına çift tıklayın
- Konsol penceresi görünmez, sadece program penceresi açılır

**Yöntem 2:**
- `PROGRAMI_AC.bat` dosyasına çift tıklayın
- Konsol penceresi görünür (hata ayıklama için faydalı)

### 2️⃣ Kitap Ekleme

#### Manuel Ekleme:
1. Program açıldığında form görünür
2. **Kitap Adı** ve **Yazar** bilgilerini girin (zorunlu alanlar)
3. "Listeye Ekle" butonuna tıklayın
4. Kitap listeye eklenir

#### Otomatik Bilgi Doldurma ile Ekleme:
1. **Kitap Adı** ve **Yazar** bilgilerini girin
2. "Bilgileri Otomatik Doldur" butonuna tıklayın
3. Program otomatik olarak şu bilgileri çeker:
   - Orijinal Adı
   - Tür (Roman, Öykü, Felsefe, vb.)
   - Ülke/Edebi Gelenek
   - Çıkış Yılı
   - Anlatı Yılı (kitabın anlattığı olayların geçtiği dönem)
   - Konusu
4. Form otomatik doldurulur
5. "Listeye Ekle" butonuna tıklayın

### 3️⃣ Excel İşlemleri

#### Excel Dosyası Oluşturma:
- "Excel Dosyası Oluştur" butonuna tıklayın
- Tüm kitaplar `Kutuphanem.xlsx` dosyasına kaydedilir
- Dosya program klasöründe oluşturulur

#### Excel Şablonu Oluşturma:
- "Excel Şablonu Oluştur" butonuna tıklayın
- Boş bir Excel şablonu oluşturulur (sadece Kitap Adı ve Yazar sütunları)
- Şablonu doldurup "Excel'den Yükle" ile programa yükleyebilirsiniz

#### Excel'den Yükleme:
1. "Excel'den Yükle" butonuna tıklayın
2. Excel dosyanızı seçin
3. Kitaplar programa yüklenir
4. İki seçenek sunulur:
   - **Her kitap için toplu çağrı yap**: Tüm kitaplar için otomatik bilgi doldurma
   - **Manuel çift tıklayarak forma yükle**: Listeden kitaba çift tıklayıp "Bilgileri Otomatik Doldur" butonuna tıklayın

### 4️⃣ Liste Yönetimi

#### Kitap Seçme:
- Listede her satırın başında ☐ işareti vardır
- ☐ işaretine tıklayarak kitabı seçebilirsiniz (☑ olur)
- Başlık sütunundaki ☐ işaretine tıklayarak tüm kitapları seçebilirsiniz

#### Kitap Silme:
- Seçili kitapları silmek için "🗑️ Seçili Kitapları Sil" butonuna tıklayın
- Tek bir kitabı silmek için kitabı seçip sil butonuna tıklayın

#### Listeden Forma Yükleme:
- Listeden bir kitaba çift tıklayın
- Kitap bilgileri forma yüklenir
- Düzenleyip tekrar ekleyebilirsiniz

## 🔧 Gelişmiş Özellikler

### AI API Entegrasyonu

Program, kitap bilgilerini çekmek için çoklu AI servisleri kullanır:

1. **Groq AI** (Birincil AI Kaynak)
   - Ücretsiz API key gerektirir
   - Çok doğru ve kapsamlı bilgiler sağlar
   - Orijinal adı Latin harflerine çevirir
   - Rate limit: 100,000 token/gün

2. **Hugging Face AI** (Yedek AI Kaynak)
   - Groq başarısız olduğunda veya rate limit'e takıldığında devreye girer
   - API key isteğe bağlıdır (API key ile daha yüksek limitler)

3. **Together AI** (Alternatif Yedek AI Kaynak)
   - Hugging Face başarısız olduğunda devreye girer
   - Ücretsiz tier mevcuttur

### API Key Kurulumu

#### Groq AI API Key (Önerilen):
1. https://console.groq.com adresine gidin
2. Ücretsiz hesap oluşturun
3. API Keys bölümünden yeni bir key oluşturun
4. Programda "Groq API Key" butonuna tıklayın
5. Key'i yapıştırın
6. Key otomatik olarak `groq_api_key.txt` dosyasına kaydedilir

#### Hugging Face API Key (İsteğe Bağlı):
1. https://huggingface.co/settings/tokens adresine gidin
2. Ücretsiz hesap oluşturun
3. Yeni token oluşturun (read izni yeterli)
4. Token'ı `huggingface_api_key.txt` dosyasına kaydedin (program klasöründe)

## 📋 Çekilen Bilgiler

Program şu bilgileri otomatik olarak çeker:

- **Orijinal Adı**: Kitabın ilk çıktığı dildeki adı (Latin harflerine çevrilir)
- **Tür**: Roman, Novella, Öykü, Felsefe, Tarih, Bilim, Şiir, Tiyatro
- **Ülke/Edebi Gelenek**: Kitabın ilk çıktığı ülke (yazarın ülkesi)
- **Çıkış Yılı**: Kitabın yazıldığı/yayınlandığı ilk yıl
- **Anlatı Yılı**: Kitabın anlattığı olayların geçtiği yıl veya yıl aralığı
- **Konusu**: Kitabın konusunu 1-2 cümle ile açıklayan özet

## 🎨 Program Özellikleri

- **Kitap Temalı Tasarım**: Kütüphane temalı renkler ve Georgia fontu
- **Readonly Alanlar**: Sadece Kitap Adı ve Yazar manuel yazılabilir, diğer alanlar otomatik doldurulur
- **Checkbox Sistemi**: Her satırda ☐/☑ işareti ile seçim yapabilirsiniz
- **Toplu İşlemler**: Seçili kitapları toplu olarak silebilirsiniz
- **Otomatik Format Güncelleme**: Eski Excel formatları otomatik olarak yeni formata çevrilir
- **Progress Bar**: Bilgi çekme sırasında ilerleme gösterilir

## 📦 Kurulum

### Gereksinimler:
- Python 3.7 veya üzeri
- Windows işletim sistemi

### Bağımlılıklar:
```bash
pip install pandas openpyxl requests
```

### İsteğe Bağlı Bağımlılıklar (İkon ve Shortcut için):
```bash
pip install Pillow pywin32
```

## 📁 Dosya Yapısı

```
KÜTÜPHANE/
├── kitap_listesi_gui.py          # Ana program dosyası
├── kitap_bilgisi_cekici.py       # API entegrasyon modülü
├── excel_handler.py              # Excel işlemleri modülü
├── api_key_manager.py            # API key yönetimi modülü
├── form_handler.py               # Form işlemleri modülü
├── list_manager.py               # Liste yönetimi modülü
├── gui_widgets.py                # GUI widget'ları modülü
├── Kutuphanem.xlsx               # Oluşturulan Excel dosyası
├── groq_api_key.txt              # Groq API key dosyası
├── huggingface_api_key.txt       # Hugging Face API key dosyası (isteğe bağlı)
├── PROGRAMI_AC.vbs              # Programı başlatma scripti (önerilen)
└── README.md                     # Bu dosya
```

## 🆘 Sorun Giderme

### Program Açılmıyorsa:
- Python'un yüklü olduğundan emin olun
- Bağımlılıkların yüklü olduğundan emin olun: `pip install pandas openpyxl requests`

### Bilgiler Çekilmiyorsa:
- İnternet bağlantınızı kontrol edin
- API key'inizin doğru olduğundan emin olun
- Console çıktısını kontrol edin (hata mesajları görünebilir)

### Excel Dosyası Açıkken Kaydetme Başarısız Oluyorsa:
- Excel dosyasını kapatın ve tekrar deneyin
- Dosya izinlerini kontrol edin

## 📝 Notlar

- Program açıldığında mevcut `Kutuphanem.xlsx` dosyası otomatik olarak yüklenir
- API key'ler dosyaya kaydedilir, bir daha girmenize gerek kalmaz
- Rate limit durumunda otomatik olarak yedek API'lere geçilir
- Büyük listelerde (500+ kitap) işlemler biraz zaman alabilir

## 📄 Lisans

Bu program özgür yazılımdır ve eğitim amaçlı kullanılabilir.

## 🤝 Katkıda Bulunma

Programı geliştirmek için önerilerinizi ve hata bildirimlerinizi paylaşabilirsiniz.

---

**Versiyon**: 2024  
**Geliştirici**: Kitap Listesi Yönetim Programı  
**Son Güncelleme**: Çoklu AI API desteği, Token tasarrufu, Rate limit yönetimi
