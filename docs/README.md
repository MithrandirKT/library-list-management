# 📚 Kitap Listesi Yönetim Programı

## 🎯 Program Ne İşe Yarar?

Bu program, kitap koleksiyonunuzu dijital ortamda yönetmenizi sağlayan Windows masaüstü uygulamasıdır. Kitap bilgilerinizi otomatik olarak çoklu kaynaklardan (Wikipedia, Google Books, Open Library, Wikidata ve AI servisleri) çekerek Excel dosyasına kaydeder.

### ✨ Ana Özellikler

- **📝 Manuel Kitap Ekleme**: Kitap adı ve yazar bilgisi girerek kitap ekleyebilirsiniz
- **🤖 Otomatik Bilgi Doldurma**: Policy-driven sistem ile kitap bilgileri otomatik olarak internetten çekilir
- **📊 Excel Entegrasyonu**: Tüm kitaplarınızı Excel dosyasına kaydedebilirsiniz (masaüstünde `Kutuphanem.xlsx`)
- **📥 Excel'den Toplu Yükleme**: Excel dosyasından toplu kitap ekleyebilirsiniz
- **🔍 Çoklu Kaynak Desteği**: Wikipedia, Google Books, Open Library, Wikidata ve AI servisleri kullanılır
- **🌐 Web Search Entegrasyonu**: DuckDuckGo, Türkçe/İngilizce Wikipedia ile obscure kitaplar bulunur
- **✅ Quality Gates**: Veri kalitesi kontrolü ve "yanlış bağlam" önleme
- **💾 Otomatik Kayıt**: Excel dosyası otomatik olarak yüklenir ve kaydedilir
- **🔄 Checkpoint Mekanizması**: Toplu işlemlerde her 50 kayıtta otomatik kayıt

## 🚀 Nasıl Çalışır?

### 1️⃣ Programı Başlatma

Programı başlatmak için iki yöntem var:

**Yöntem 1 (Önerilen):**
- `scripts/PROGRAMI_AC.vbs` dosyasına çift tıklayın
- Konsol penceresi görünmez, sadece program penceresi açılır

**Yöntem 2:**
- `scripts/PROGRAMI_AC.bat` dosyasına çift tıklayın
- Konsol penceresi görünür (hata ayıklama için faydalı)

### 2️⃣ Kitap Ekleme

#### Manuel Ekleme:
1. Program açıldığında form görünür
2. **Kitap Adı** ve **Yazar** bilgilerini girin (zorunlu alanlar)
3. "Listeye Ekle" butonuna tıklayın
4. Kitap listeye eklenir

#### Otomatik Bilgi Doldurma ile Ekleme (Policy-Driven):
1. **Kitap Adı** ve **Yazar** bilgilerini girin
2. "Bilgileri Otomatik Doldur" butonuna tıklayın
3. Program policy-driven sistem ile otomatik olarak şu bilgileri çeker:
   - **Orijinal Adı**: Quality gates ile volume marker ve translation context kontrolü
   - **Tür**: Roman, Novella, Öykü, Felsefe, Tarih, Bilim, Şiir, Tiyatro
   - **Ülke/Edebi Gelenek**: Wikidata ve Wikipedia'dan yapılandırılmış veri
   - **İlk Yayınlanma Tarihi**: Quality gates ile edition date kontrolü (classic book'lar için)
   - **Anlatı Yılı**: Kitabın anlattığı olayların geçtiği yıl veya yıl aralığı
   - **Konusu**: Kitabın konusunu 1-2 cümle ile açıklayan özet
4. **Web Search**: Eğer bilgiler bulunamazsa, DuckDuckGo ve Wikipedia ile web araması yapılır
5. Form otomatik doldurulur
6. "Listeye Ekle" butonuna tıklayın

### 3️⃣ Excel İşlemleri

#### Excel Dosyası Oluşturma:
- "Excel Dosyası Oluştur" butonuna tıklayın
- Tüm kitaplar `Kutuphanem.xlsx` dosyasına kaydedilir
- Dosya **masaüstünde** oluşturulur (`C:\Users\<kullanıcı>\Desktop\Kutuphanem.xlsx`)

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
- Tek bir kitabı silmek için kitabı seçip (☐ işaretine tıklayarak) "🗑️ Seçili Kitapları Sil" butonuna tıklayın

#### Listeden Forma Yükleme:
- Listeden bir kitaba çift tıklayın
- Kitap bilgileri forma yüklenir
- Düzenleyip tekrar ekleyebilirsiniz

## 🔧 Gelişmiş Özellikler

### Policy-Driven Veri Çekme Sistemi

Program, **policy-driven** bir sistem kullanarak kitap bilgilerini çeker:

1. **Field Policy**: Her alan için kaynak öncelik sırası belirlenir (örn: "İlk Yayınlanma Tarihi" için: openlibrary -> wikidata -> enwiki -> gbooks -> trwiki -> AI)
2. **Quality Gates**: Her alan için veri kalitesi kontrolü yapılır (volume marker, translation context, edition date kontrolü)
3. **Kaynak Toplama**: Tüm kaynaklardan (Wikipedia EN/TR, Google Books, Open Library, Wikidata) veri toplanır
4. **Kaynak Seçimi**: Policy'ye göre en yüksek öncelikli kaynaktan geçen değer seçilir
5. **AI Fallback**: Eksik alanlar için AI kullanılır (router ile quota yönetimi)

### AI API Entegrasyonu

Program, kitap bilgilerini çekmek için çoklu AI servisleri kullanır:

1. **Groq AI** (Birincil AI Kaynak - GPT-OSS-20B)
   - Model: `openai/gpt-oss-20b` (GPT-OSS-20B)
   - Ücretsiz API key gerektirir
   - **Tool-Friendly Yaklaşım**: İlk kısa prompt (~50-100 token), bilmiyorsa web search
   - **Web Search Entegrasyonu**: DuckDuckGo, Türkçe Wikipedia, İngilizce Wikipedia, Google Books
   - **Token Tasarrufu**: %50-70 token tasarrufu (toplam ~150-300 token, önceden ~500-1000 token)
   - Çok doğru ve kapsamlı bilgiler sağlar
   - Orijinal adı Latin harflerine çevirir
   - Rate limit: 100,000 token/gün
   - Rate limit sonrası otomatik olarak Hugging Face AI'ye geçilir

2. **Hugging Face AI** (Yedek AI Kaynak)
   - Groq başarısız olduğunda veya rate limit'e takıldığında devreye girer
   - API key isteğe bağlıdır (API key ile daha yüksek limitler)
   - Model: `mistralai/Mistral-7B-Instruct-v0.2`

3. **Together AI** (Alternatif Yedek AI Kaynak)
   - Hugging Face başarısız olduğunda devreye girer
   - Ücretsiz tier mevcuttur

### Web Search Entegrasyonu

Program, bilgiler bulunamadığında otomatik olarak web araması yapar:

1. **DuckDuckGo Search** (Birincil web search)
2. **Türkçe Wikipedia** (Öncelikli, infobox desteği ile)
3. **İngilizce Wikipedia** (Fallback)
4. **Google Books API** (Son çare)

### Wikidata Entegrasyonu

Program, yapılandırılmış veri için Wikidata'yı kullanır:

- QID çözümleme: REST summary + MediaWiki pageprops fallback
- İlk yayınlanma tarihi: P577 için en erken yıl seçimi
- Orijinal ad: P1476/P1705/P1680/P1813/label fallback
- Ülke/gelenek: P495/P17 ve label çözümleme

### Quality Gates

Program, veri kalitesini kontrol eder:

- **Volume Marker Detection**: "Cilt 1", "Volume I", "Tome 1" gibi ifadeleri tespit eder
- **Translation Context Detection**: "Türkçeye çevrildi", "translated" gibi ifadeleri tespit eder
- **Edition Date Control**: Classic book'lar için edition yılı kontrolü
- **Classic Book Detection**: Klasik kitaplar için özel kontroller
- **Cyrillic/Arabic/CJK Detection**: Orijinal dil tespiti

### Router/Backoff Mekanizması

Program, API quota yönetimi için router kullanır:

- Rate limit (429, 503) ve API key hataları (401, 403) yönetimi
- Cooldown ve retry mekanizması
- Otomatik fallback (Groq → Hugging Face → Together AI)

### API Key Kurulumu

#### Groq AI API Key (Önerilen):
1. https://console.groq.com adresine gidin
2. Ücretsiz hesap oluşturun
3. API Keys bölümünden yeni bir key oluşturun
4. Programda "Groq API Key" butonuna tıklayın
5. Key'i yapıştırın
6. Key otomatik olarak `data/groq_api_key.txt` dosyasına kaydedilir

#### Hugging Face API Key (İsteğe Bağlı):
1. https://huggingface.co/settings/tokens adresine gidin
2. Ücretsiz hesap oluşturun
3. Yeni token oluşturun (read izni yeterli)
4. Token'ı `data/huggingface_api_key.txt` dosyasına kaydedin

#### Together AI API Key (İsteğe Bağlı):
1. https://api.together.xyz adresine gidin
2. Ücretsiz hesap oluşturun
3. API key alın
4. Environment variable olarak ayarlayın: `TOGETHER_API_KEY=your_key_here`

## 📋 Çekilen Bilgiler

Program şu bilgileri otomatik olarak çeker:

- **Orijinal Adı**: Kitabın ilk çıktığı dildeki adı (Latin harflerine çevrilir)
- **Tür**: Roman, Novella, Öykü, Felsefe, Tarih, Bilim, Şiir, Tiyatro
- **Ülke/Edebi Gelenek**: Kitabın ilk çıktığı ülke (yazarın ülkesi)
- **İlk Yayınlanma Tarihi**: Kitabın yazıldığı/yayınlandığı ilk yıl
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
pip install pandas openpyxl requests duckduckgo-search beautifulsoup4
```

veya

```bash
pip install -r requirements.txt
```

### İsteğe Bağlı Bağımlılıklar (İkon ve Shortcut için):
```bash
pip install Pillow pywin32
```

## 📁 Dosya Yapısı

```
KÜTÜPHANE/
├── kitap_listesi_gui.py          # Ana program dosyası (root'ta - kolay erişim için)
├── requirements.txt              # Python bağımlılıkları (root'ta - pip standart)
├── .gitignore                    # Git ignore dosyası (root'ta - git standart)
│
├── modules/                      # Tüm Python modülleri
│   ├── __init__.py              # Package init dosyası
│   ├── kitap_bilgisi_cekici.py  # API entegrasyon modülü (policy-driven)
│   ├── excel_handler.py         # Excel işlemleri modülü
│   ├── api_key_manager.py       # API key yönetimi modülü
│   ├── form_handler.py          # Form işlemleri modülü
│   ├── list_manager.py          # Liste yönetimi modülü
│   ├── gui_widgets.py           # GUI widget'ları modülü
│   ├── field_policy.py          # Alan bazlı kaynak öncelik ve validation
│   ├── quality_gates.py         # Veri kalitesi kontrolü ve "yanlış bağlam" önleme
│   ├── wikidata_client.py       # Wikidata QID çözümleme ve alan çıkarma
│   ├── router.py                # API quota yönetimi ve backoff mekanizması
│   ├── provenance.py            # Provenance (kaynak, güven) bilgisi yazma
│   ├── field_registry.py        # Excel şema kolon isimlerini merkezi yönetim
│   ├── test_quality_gates.py    # Quality gates için unit testler
│   └── test_regression.py       # Regression testler (end-to-end senaryolar)
│
├── scripts/                      # Yardımcı scriptler
│   ├── PROGRAMI_AC.vbs         # Programı başlatma scripti (önerilen)
│   ├── PROGRAMI_AC.bat          # Programı başlatma scripti (alternatif)
│   ├── GITHUB_AUTO_PUSH.bat     # GitHub otomatik push scripti
│   ├── ikon_olustur.py          # Kitap temalı ikon oluşturucu
│   ├── ikon_ve_shortcut_olustur.bat # İkon ve shortcut oluşturma scripti
│   ├── ikon_cache_temizle.bat   # Windows ikon cache temizleme
│   └── exe_olustur.bat          # EXE dosyası oluşturma scripti
│
├── data/                         # Veri dosyaları
│   ├── Kutuphanem.xlsx          # Oluşturulan Excel dosyası (masaüstünde de oluşturulur)
│   ├── groq_api_key.txt         # Groq API key dosyası
│   └── huggingface_api_key.txt  # Hugging Face API key dosyası (isteğe bağlı)
│
├── icons/                        # İkon dosyaları
│   ├── kitap_ikon.ico           # Oluşturulan ikon dosyası (ICO formatı)
│   └── kitap_ikon.png           # Oluşturulan ikon dosyası (PNG formatı)
│
└── docs/                         # Dokümantasyon
    ├── README.md                 # Bu dosya (kullanım kılavuzu)
    └── HAND_OFF_DOKUMANTASYON.md # Teknik dokümantasyon
```

## 🆘 Sorun Giderme

### Program Açılmıyorsa:
- Python'un yüklü olduğundan emin olun
- Bağımlılıkların yüklü olduğundan emin olun: `pip install -r requirements.txt`
- `modules/` klasörünün mevcut olduğundan emin olun

### Bilgiler Çekilmiyorsa:
- İnternet bağlantınızı kontrol edin
- API key'inizin doğru olduğundan emin olun (`data/groq_api_key.txt`)
- Console çıktısını kontrol edin (hata mesajları görünebilir)
- Rate limit durumunda otomatik olarak yedek API'lere geçilir

### Excel Dosyası Açıkken Kaydetme Başarısız Oluyorsa:
- Excel dosyasını kapatın ve tekrar deneyin
- Dosya izinlerini kontrol edin
- Excel dosyası masaüstünde oluşturulur (`C:\Users\<kullanıcı>\Desktop\Kutuphanem.xlsx`)

## 📝 Notlar

- Program açıldığında mevcut `Kutuphanem.xlsx` dosyası otomatik olarak yüklenir (masaüstünden)
- API key'ler `data/` klasörüne kaydedilir, bir daha girmenize gerek kalmaz
- Rate limit durumunda otomatik olarak yedek API'lere geçilir (Groq → Hugging Face → Together AI)
- Büyük listelerde (500+ kitap) işlemler biraz zaman alabilir
- Toplu işlemlerde her 50 kayıtta otomatik checkpoint (Excel kaydedilir)
- **Token Tasarrufu**: Tool-friendly yaklaşım ile %50-70 token tasarrufu sağlanır
- **Web Search**: Bilgiler bulunamadığında otomatik olarak web araması yapılır
- **Quality Gates**: Veri kalitesi otomatik olarak kontrol edilir (volume marker, translation context, edition date)
- **Policy-Driven**: Her alan için kaynak öncelik sırası belirlenir

## 📄 Lisans

Bu program özgür yazılımdır ve eğitim amaçlı kullanılabilir.

## 🤝 Katkıda Bulunma

Programı geliştirmek için önerilerinizi ve hata bildirimlerinizi paylaşabilirsiniz.

---

**Versiyon**: 2026-02-10  
**Geliştirici**: Kitap Listesi Yönetim Programı  
**Son Güncelleme**: 
- Web search entegrasyonu (DuckDuckGo, Wikipedia, Google Books)
- GPT-OSS-20B model (tool-friendly yaklaşım)
- Token tasarrufu (%50-70)
- Policy-driven veri çekme sistemi
- Quality gates ve veri kalitesi kontrolü
- Wikidata entegrasyonu
- Router/backoff mekanizması
- Checkpoint mekanizması (her 50 kayıtta otomatik kayıt)
- Klasör organizasyonu (modules/, scripts/, data/, icons/, docs/)
