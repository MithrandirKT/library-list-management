# Kitap Listesi Excel Oluşturucu - Hand-off Dokümantasyonu

## 📊 Güncel Durum ve İlerleme (Son Güncelleme: 2026-02-10)

### 🎯 Başlangıç Amacı
Bu çalışma, kitap bilgisini çoklu kaynaktan doğru bağlamda çekmek, Excel'e meta/provenance yazmak ve kota/yanıt hatalarını kontrollü yönetmek için **"field policy + quality gates + wikidata + router + status/checkpoint"** altyapısını kurma amacıyla başladı.

### ✅ Tamamlanan Adımlar

#### Adım 1: Excel Meta/Migration ✅ **TAMAMLANDI**
- Excel şemasına meta kolonlar eklendi (`status`, `missing_fields`, `last_attempt_at`, `retry_count`, `next_retry_at`, `best_source`, `match_score`, `wikidata_qid`)
- Her alan için `src_<field>` ve `conf_<field>` kolonları eklendi
- Eski formatı yeni formata çeviren migration mekanizması eklendi
- **Test Sonucu**: ✅ PASS (Excel migration unit testi)

#### Adım 2: Field Policy + Gates ✅ **TAMAMLANDI** (Kısmen)
- `field_policy.py` modülü oluşturuldu
- Her alan için kaynak öncelik sırası tanımlandı
- "Çıkış Yılı" kaynak sırası iyileştirildi: `openlibrary -> wikidata -> enwiki -> gbooks -> trwiki -> AI`
- `quality_gates.py` modülü oluşturuldu
- Quality gate fonksiyonları eklendi (`gate_publication_year`, `gate_original_title`)
- Regex pattern'leri genişletildi (volume marker, translation context, edition date kontrolü)
- Classic book detection eklendi
- Cyrillic/Arabic/CJK character detection eklendi
- **Test Sonucu**: ✅ PASS (Policy + gate davranış testi, 37 quality gate unit testi)

#### Adım 3: Wikidata Integration ✅ **TAMAMLANDI**
- `wikidata_client.py` modülü oluşturuldu
- QID çözümleme: REST summary + MediaWiki pageprops fallback
- P577 için en erken yıl seçimi
- Orijinal ad için P1476/P1705/P1680/P1813/label fallback
- Ülke/gelenek için P495/P17 ve label çözümleme
- Wikipedia cevabından `_wikibase_item` alınıyor ve QID çözümleme sırasına eklendi (en->tr fallback)
- **Test Sonucu**: ✅ PASS (Wikidata çözümleme ve extract_fields testi)

#### Adım 4: Quality Gates Genişletmesi ✅ **TAMAMLANDI**
- Volume marker detection genişletildi (İngilizce, Türkçe, Romen rakamları)
- TR Wikipedia translation context detection eklendi
- EN Wikipedia publication context detection eklendi
- Google Books edition yılı kontrolü eklendi (classic book'lar için)
- Russian author Latin script kontrolü eklendi
- Gate RED nedenleri `kitap_bilgisi_cekici.py` içinde debug log'a eklendi
- **Test Sonucu**: ✅ PASS (37 unit test, tüm testler geçti)

#### Adım 5: GUI Policy Entegrasyonu ✅ **TAMAMLANDI**
- `kitap_listesi_gui.py` içinde `bilgileri_otomatik_doldur()` refactor edildi
- `kitap_bilgisi_cek_policy()` kullanımına geçildi
- `_excel_kitaplari_arka_planda_doldur()` refactor edildi
- Mevcut form/Excel verileri `mevcut_bilgiler` olarak policy fonksiyonuna aktarılıyor
- Checkpoint mekanizması eklendi (her 50 kayıtta Excel save)

### 🚧 Kısmen Tamamlanan Adımlar

#### Adım 5: Router/Backoff ✅ **TAMAMLANDI**
- `router.py` modülü oluşturuldu
- `ProviderState` ve `QuotaRouter` sınıfları eklendi
- Rate limit (429, 503) ve API key hataları (401, 403) yönetimi eklendi
- Cooldown ve retry mekanizması eklendi
- Policy akışında router kullanımı tam entegre (`kitap_bilgisi_cek_policy()`)
- Eski akışta router kullanımı eklendi (`kitap_bilgisi_cek()`)
- Loglar sadeleştirildi (debug logları kaldırıldı)
- **Test Sonucu**: ✅ PASS (Router quota yönetimi çalışıyor)

#### Adım 6: Status/Checkpoint ✅ **TAMAMLANDI**
- Status yazımı policy akışı içinde var (`provenance.py` modülü)
- Checkpoint mekanizması toplu akışta eklendi (her 50 kayıtta save)
- Status/missing_fields güncellemesi Excel'e yazılıyor (toplu akışta tam entegre)
- Hata durumunda status yazımı eklendi (FAIL status)
- Retry logic eklendi (next_retry_at kontrolü)
- **Test Sonucu**: ✅ PASS (Status/missing_fields Excel'e yazılıyor)

### ❌ Kalan İşler (Öncelik Sırasına Göre)

1. ~~**Router/Backoff Entegrasyonu** (Öncelik: Yüksek)~~ ✅ **TAMAMLANDI**
   - ~~GUI akışında router kullanımını sağla~~ ✅
   - ~~Logları sadeleştir~~ ✅
   - ~~Policy dışı çağrılarda router entegrasyonu~~ ✅

2. ~~**Status/Checkpoint Tamamlama** (Öncelik: Orta)~~ ✅ **TAMAMLANDI**
   - ~~Toplu akışta her N kayıtta Excel save~~ ✅
   - ~~Status/missing_fields güncellemesini Excel'e yaz~~ ✅
   - ~~Retry logic'i tamamla~~ ✅

3. ~~**Regression Test** (Öncelik: Orta)~~ ✅ **TAMAMLANDI**
   - ~~War and Peace senaryosu için entegre test ekle~~ ✅
   - ~~Yaygın problemler için test senaryoları~~ ✅

### 📁 Yeni Eklenen Modüller

1. **`field_policy.py`**: Alan bazlı kaynak öncelik ve validation kuralları
2. **`quality_gates.py`**: Veri kalitesi kontrolü ve "yanlış bağlam" önleme
3. **`wikidata_client.py`**: Wikidata QID çözümleme ve alan çıkarma
4. **`router.py`**: API quota yönetimi ve backoff mekanizması
5. **`provenance.py`**: Provenance (kaynak, güven) bilgisi yazma
6. **`field_registry.py`**: Excel şema kolon isimlerini merkezi yönetim
7. **`test_quality_gates.py`**: Quality gates için unit testler (37 test)

### 📝 Codex 5.3 Oturumunda Yapılanlar (2026-02-10)

1. `kitap_listesi_gui.py` stabil sürüme geri alındı (truncate problemi giderildi)
2. Excel dışarıdan yükleme validasyon sırası düzeltildi: zorunlu kolon kontrolü önce, meta kolon tamamlama sonra
3. Field policy içinde "Çıkış Yılı" kaynak sırası iyileştirildi
4. Wikidata istemcisi güçlendirildi (QID çözümleme, field extraction)
5. Wikipedia cevabından `_wikibase_item` alındı
6. Gate RED nedenleri debug log'a eklendi

### 📁 Klasör Organizasyonu Güncellemesi (2026-02-10)

**Yapılan Değişiklikler:**
1. ✅ Tüm dosyalar kategorilere göre klasörlere taşındı:
   - **`modules/`**: Tüm Python modülleri (ana modüller + yeni modüller)
   - **`scripts/`**: Yardımcı script dosyaları (.bat, .vbs, .py)
   - **`data/`**: Veri dosyaları (.xlsx, API key .txt dosyaları)
   - **`icons/`**: İkon dosyaları (.ico, .png)
   - **`docs/`**: Dokümantasyon dosyaları (.md)

2. ✅ Ana program dosyası (`kitap_listesi_gui.py`) root'ta kaldı (kolay erişim için)

3. ✅ Import path'leri güncellendi:
   - `kitap_listesi_gui.py` içinde `sys.path` ile `modules/` klasörü eklendi
   - Tüm modül import'ları çalışır durumda

4. ✅ Dosya path'leri güncellendi:
   - Excel dosyası: `data/Kutuphanem.xlsx`
   - API key dosyaları: `data/groq_api_key.txt`, `data/huggingface_api_key.txt`
   - İkon dosyaları: `icons/kitap_ikon.ico`, `icons/kitap_ikon.png`

5. ✅ Script path'leri güncellendi:
   - `PROGRAMI_AC.bat` ve `PROGRAMI_AC.vbs` root'tan çalışacak şekilde güncellendi
   - `ikon_olustur.py` ikonları `icons/` klasörüne kaydedecek şekilde güncellendi
   - `exe_olustur.bat` güncellendi (ikon path'i ve data klasörleri için)

6. ✅ `modules/__init__.py` dosyası oluşturuldu (package yapısı için)

**⚠️ ÖNEMLİ - Yeni Dosya Oluşturma Kuralları:**
- **Yeni Python modülü** oluşturulurken → `modules/` klasörüne oluşturulmalı
- **Yeni script dosyası** oluşturulurken → `scripts/` klasörüne oluşturulmalı
- **Yeni veri dosyası** oluşturulurken → `data/` klasörüne oluşturulmalı
- **Yeni ikon/resim** oluşturulurken → `icons/` klasörüne oluşturulmalı
- **Yeni dokümantasyon** oluşturulurken → `docs/` klasörüne oluşturulmalı
- **Eğer ilgili klasör yoksa**, önce klasör oluşturulmalı, sonra dosya oluşturulmalı

**📌 Root'ta Kalan Dosyalar (Neden Dışarıda?):**
Aşağıdaki dosyalar **kasıtlı olarak** root'ta (ana klasörde) bırakılmıştır:
- **`kitap_listesi_gui.py`**: Ana program dosyası - kolay erişim için root'ta (kullanıcılar doğrudan çalıştırabilir)
- **`requirements.txt`**: Python bağımlılıkları - Python projelerinde standart olarak root'ta bulunur (`pip install -r requirements.txt`)
- **`.gitignore`**: Git ignore dosyası - Git projelerinde standart olarak root'ta bulunur (Git root'tan başlar)

Bu dosyalar root'ta kalmalıdır çünkü:
1. **Kolay erişim**: Kullanıcılar ana programı doğrudan çalıştırabilir
2. **Standart yapı**: Python/Git projelerinde bu dosyalar root'ta olur
3. **Tool uyumluluğu**: `pip`, `git` gibi araçlar bu dosyaları root'ta arar

**⚠️ ÖNEMLİ - Commit Mesajları ve Türkçe Karakterler:**
- **Commit mesajlarında Türkçe karakterler kullanmayın!** (ç, ğ, ı, ö, ş, ü, İ, Ç, Ğ, Ö, Ş, Ü)
- Türkçe karakterler yerine İngilizce karakterler kullanın:
  - ç → c, Ç → C
  - ğ → g, Ğ → G
  - ı → i, İ → I
  - ö → o, Ö → O
  - ş → s, Ş → S
  - ü → u, Ü → U
- Bu sayede GitHub'da commit mesajları düzgün görünür ve encoding sorunları önlenir
- Örnek: "Klasör organizasyonu" yerine "Klasor organizasyonu" kullanın

### 📝 Son Oturumda Yapılanlar (2026-02-10 - GitHub Güncelleme ve Commit Mesaj Düzeltme)

1. **GitHub Güncelleme** (2026-02-10):
   - Klasör organizasyonu değişiklikleri GitHub'a push edildi
   - Tüm dosyalar klasörlere taşındı (modules/, scripts/, data/, icons/, docs/)
   - Commit mesajları ASCII karakterlerle düzeltildi (Türkçe karakterler İngilizce karakterlerle değiştirildi)
   - **Not**: Eski commit'lerde bazı Türkçe karakterler bozuk görünebilir, ancak yeni commit'ler ASCII kullanıyor

2. **Commit Mesaj Düzeltme Stratejisi** (2026-02-10):
   - Türkçe karakterler İngilizce karakterlerle değiştirildi:
     - ç → c, Ç → C
     - ğ → g, Ğ → G
     - ı → i, İ → I
     - ö → o, Ö → O
     - ş → s, Ş → S
     - ü → u, Ü → U
   - Bu sayede encoding sorunları önlendi
   - GitHub'da commit mesajları düzgün görünüyor

### 📝 Önceki Oturumda Yapılanlar (2026-02-10 - Regression Test)

1. **Regression Test Eklendi** (2026-02-10):
   - `test_regression.py` modülü oluşturuldu
   - War and Peace senaryosu için entegre test eklendi
   - Yaygın problemler için test senaryoları eklendi:
     - Empty input handling
     - Partial data scenario
     - Complete data scenario
     - Retry logic
     - Provenance tracking
     - Router integration
     - Field policy integration
     - Wikidata QID format validation
   - **Test Sonucu**: ✅ PASS (Tüm regression testler geçti)

### 📝 Önceki Oturumda Yapılanlar (2026-02-10 - Status/Checkpoint Tamamlama)

1. **Status/Checkpoint Tamamlama** (2026-02-10):
   - Hata durumunda status yazımı eklendi (FAIL status, missing_fields, retry_count, next_retry_at)
   - Retry logic eklendi (next_retry_at kontrolü - henüz retry zamanı gelmemişse atla)
   - Status/missing_fields güncellemesi Excel'e yazılıyor (ensure_row_schema ile garanti edildi)
   - Mevcut kitabın diğer kolonları korunuyor (Not, vb.)

### 📝 Önceki Oturumda Yapılanlar (2026-02-10 - Router Entegrasyonu)

1. **Router/Backoff Entegrasyonu Tamamlandı** (2026-02-10):
   - Eski `kitap_bilgisi_cek()` fonksiyonunda router kullanımı eklendi
   - AI çağrıları router ile quota yönetimi yapıyor
   - Loglar sadeleştirildi (debug logları kaldırıldı)
   - Router zaten policy akışında kullanılıyordu, şimdi her iki akışta da çalışıyor

### 📝 Önceki Oturumda Yapılanlar (2026-02-10)

1. **Klasör Organizasyonu** (2026-02-10):
   - Tüm dosyalar kategorilere göre klasörlere taşındı:
     - `modules/`: Tüm Python modülleri
     - `scripts/`: Yardımcı script dosyaları
     - `data/`: Veri dosyaları (Excel, API key'ler)
     - `icons/`: İkon dosyaları
     - `docs/`: Dokümantasyon dosyaları
   - Ana program dosyası (`kitap_listesi_gui.py`) root'ta kaldı
   - Import path'leri güncellendi (`sys.path` ile `modules/` eklendi)
   - Dosya path'leri güncellendi (data/, icons/ klasörlerine göre)
   - Script path'leri güncellendi (root'tan çalışacak şekilde)
   - `modules/__init__.py` oluşturuldu

2. GUI akışı policy moduna geçirildi:
   - `bilgileri_otomatik_doldur()` refactor edildi
   - `_excel_kitaplari_arka_planda_doldur()` refactor edildi
   - `kitap_bilgisi_cek_policy()` kullanımına geçildi
2. Quality gates genişletildi:
   - Volume marker pattern'leri genişletildi
   - Translation context pattern'leri genişletildi
   - Classic book detection eklendi
   - Google Books edition yılı kontrolü eklendi
   - Russian author Latin script kontrolü eklendi
3. Checkpoint mekanizması eklendi (her 50 kayıtta Excel save)
4. Quality gates unit testleri oluşturuldu ve tüm testler geçti (37 test)

### 🎯 İş Sırası ve Hareket Planı

**Öncelik 1: Router/Backoff Entegrasyonu**
1. GUI akışında router kullanımını sağla
2. Logları sadeleştir
3. Policy dışı çağrılarda router entegrasyonu

**Öncelik 2: Status/Checkpoint Tamamlama**
1. Toplu akışta status/missing_fields güncellemesini Excel'e yaz
2. Retry logic'i tamamla

**Öncelik 3: Regression Test**
1. War and Peace senaryosu için entegre test ekle
2. Yaygın problemler için test senaryoları

### 📊 İlerleme Özeti

- ✅ **Adım 1**: Excel meta/migration - %100
- ✅ **Adım 2**: Field policy + gates - %100
- ✅ **Adım 3**: Wikidata - %100
- ✅ **Adım 4**: Quality gates genişletmesi - %100
- ✅ **Adım 5**: Router/backoff - %100
- ✅ **Adım 6**: Status/checkpoint - %100
- ✅ **Adım 7**: Regression test - %100

**Genel İlerleme**: %100 tamamlandı ✅

---

## Programın Amacı

Windows'ta çalışan, grafik arayüzlü bir kitap listesi yönetim uygulamasıdır. Kullanıcıların kitap bilgilerini girip Excel dosyası olarak kaydetmesini sağlar. **Yeni özellik:** Kitap bilgileri otomatik olarak çoklu kaynaklardan (Wikipedia, Google Books, Open Library ve Groq AI) çekilerek formu doldurur.

## Ana Özellikler

### 1. Kitap Bilgisi Girişi
- Formdan kitap bilgileri girilir
- **Zorunlu alanlar**: Kitap Adı, Yazar
- **İsteğe bağlı alanlar**: Orijinal Adı, Tür, Ülke/Edebi Gelenek, Çıkış Yılı, Anlatı Yılı, Konusu, Not
- **Otomatik Bilgi Doldurma**: "Bilgileri Otomatik Doldur" butonu ile kitap bilgileri otomatik çekilir

### 2. Otomatik Bilgi Çekme Sistemi (YENİ)

#### 2.1. Çoklu Kaynak Yaklaşımı
Program şu kaynakları sırayla kullanarak kitap bilgilerini çeker:

1. **Wikipedia API** (Ana kaynak)
   - Türkçe ve İngilizce Wikipedia sayfalarından bilgi çeker
   - Önce İngilizce sayfada arama yapar (orijinal dildeki bilgiler için)
   - Yazar adı eşleşmesi kontrol edilir
   - Extract'ten bilgiler parse edilir

2. **Google Books API** (Yedek kaynak)
   - Eksik bilgileri tamamlamak için kullanılır
   - Yazar adına göre en uygun sonucu bulur
   - Volume info'dan detaylı bilgiler çıkarılır

3. **Open Library API** (Yedek kaynak)
   - `first_publish_year` kullanarak ilk yayın yılını bulur
   - Subject bilgilerinden tür çıkarılır
   - First sentence'den konu bilgisi alınır

4. **Groq AI API** (Birincil AI kaynak - Ücretsiz)
   - Eksik bilgileri AI ile tamamlar
   - Ücretsiz API key gerektirir
   - Çok daha doğru ve kapsamlı bilgiler sağlar
   - **Özellik**: Orijinal adı her zaman Latin harflerine transliterasyon yapar (Kiril, Arap, Çin, Japon vb.)
   - **Token Tasarrufu**: Prompt optimize edilmiştir (~200-300 token, önceden ~400-600 token)
   - **Rate Limit**: 100,000 token/gün (ücretsiz tier)
   - Rate limit sonrası otomatik olarak Hugging Face AI'ye geçer

5. **Hugging Face Inference API** (Yedek AI kaynak - Ücretsiz)
   - Groq AI başarısız olduğunda veya rate limit'e takıldığında devreye girer
   - Groq'dan sonra hala eksik bilgiler varsa kullanılır
   - API key isteğe bağlıdır (API key ile daha yüksek rate limit)
   - Model: `mistralai/Mistral-7B-Instruct-v0.2`
   - URL: `https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2`

6. **Together AI API** (Alternatif yedek AI kaynak - Ücretsiz)
   - Hugging Face başarısız olduğunda veya hala eksik bilgiler varsa devreye girer
   - Ücretsiz tier mevcuttur
   - API key gerektirir (https://api.together.xyz)

#### 2.2. Çekilen Bilgiler
- **Orijinal Adı**: Kitabın ilk çıktığı dildeki adı (Latin harflerine transliterasyon yapılır)
- **Tür**: Roman, Novella, Öykü, Felsefe, Tarih, Bilim, Şiir, Tiyatro
- **Ülke/Edebi Gelenek**: Kitabın ilk çıktığı ülke (yazarın ülkesi)
- **Çıkış Yılı**: Kitabın yazıldığı/yayınlandığı ilk yıl (basım yılı değil)
- **Anlatı Yılı**: Kitabın anlattığı olayların geçtiği yıl veya yıl aralığı (örn: "1865", "1865-1869", "19. yüzyıl")
- **Konusu**: Kitabın konusunu 1-2 cümle ile açıklayan özet

#### 2.3. Bilgi Çekme Mantığı (Policy-Driven - YENİ - 2026)

**Eski Yaklaşım (Kullanılmıyor):**
1. Önce Wikipedia'dan bilgi çekilir
2. Eksik bilgiler Google Books'tan tamamlanır
3. Hala eksik varsa Open Library'den tamamlanır
4. Son olarak Groq AI ile eksik bilgiler tamamlanır (API key varsa)
5. Groq'dan sonra hala eksik bilgiler varsa Hugging Face AI ile tamamlanır
6. Hugging Face başarısız olduğunda veya hala eksik varsa Together AI ile tamamlanır (API key varsa)

**Yeni Policy-Driven Yaklaşım (Önerilen - 2026):**
1. **Field Policy**: Her alan için kaynak öncelik sırası belirlenir (örn: "Çıkış Yılı" için: openlibrary -> wikidata -> enwiki -> gbooks -> trwiki -> AI)
2. **Kaynak Toplama**: Tüm kaynaklardan (Wikipedia EN/TR, Google Books, Open Library, Wikidata) veri toplanır
3. **Quality Gates**: Her alan için quality gate fonksiyonları çalıştırılır:
   - Çıkış Yılı: Translation context kontrolü, edition date kontrolü (classic book'lar için)
   - Orijinal Adı: Volume marker kontrolü, same as localized kontrolü (Russian author'lar için)
4. **Kaynak Seçimi**: Policy'ye göre en yüksek öncelikli kaynaktan geçen değer seçilir
5. **AI Fallback**: Eksik alanlar için AI kullanılır (router ile quota yönetimi):
   - Groq AI (birincil) → Hugging Face AI (yedek) → Together AI (alternatif yedek)
   - Rate limit (429, 503) ve API key hataları (401, 403) router tarafından yönetilir
6. **Provenance Yazma**: Her alan için kaynak (`src_<field>`) ve güven (`conf_<field>`) bilgisi Excel'e yazılır
7. **Status Yönetimi**: Satır seviyesinde status, missing_fields, retry info, best_source, wikidata_qid yazılır
8. **Sadece boş alanlar doldurulur** (kullanıcı doldurmuşsa değiştirilmez)

### 3. Liste Yönetimi (YENİ - 2024)
- Eklenen kitaplar tablo görünümünde listelenir
- **Checkbox Sistemi**: Her satırda ☐/☑ işareti ile seçim yapılabilir
- **Başlık Sütunu ile Tümünü Seç/Kaldır**: "Seç" sütunundaki ☑/☐ işaretine tıklayarak tüm kitaplar seçilir/kaldırılır
- **Toplu Silme**: Seçili kitapları toplu olarak silme
- **Listeden Forma Yükleme**: Listeden bir kitaba çift tıklayarak forma yüklenir
- Gerçek zamanlı liste güncelleme
- Toplam kitap sayısı gösterimi
- Seçili satırlar görsel olarak vurgulanır

### 4. Excel Entegrasyonu
- **Excel dosyası oluşturma**: Tüm kitapları Excel'e kaydetme (`Kutuphanem.xlsx`)
- **Excel şablonu oluşturma**: Boş şablon oluşturma (sadece "Kitap Adı" ve "Yazar" sütunları)
- **Excel'den yükleme**: Excel dosyasından toplu kitap ekleme
- **Excel'den Yükleme Sonrası Otomatik Bilgi Doldurma (YENİ - 2024)**: 
  - Excel'den yükleme sonrası 2 seçenek sunulur:
    1. **Her kitap için toplu çağrı yap**: Tüm kitaplar için otomatik bilgi doldurma
    2. **Manuel çift tıklayarak forma yükle**: Listeden kitaba çift tıklayıp "Bilgileri Otomatik Doldur" butonuna tıklayın
- **Otomatik format güncelleme**: Eski formatı yeni formata çevirme

### 5. API Key Yönetimi (YENİ)
- **Groq API Key**: 
  - API key dosyaya kaydedilir (`groq_api_key.txt`)
  - Program her açılışta otomatik yükler
  - GUI'de "Groq API Key" butonu ile yönetilir
  - API key durumu gösterilir (✓/✗)
  - Key olmadan da çalışır, ancak bazı bilgiler eksik kalabilir
- **Hugging Face API Key** (İsteğe Bağlı):
  - API key dosyaya kaydedilir (`huggingface_api_key.txt`)
  - Program her açılışta otomatik yükler
  - API key ile daha yüksek rate limit
  - Key olmadan da çalışır (daha düşük rate limit ile)
- **Together AI API Key** (İsteğe Bağlı):
  - Environment variable olarak ayarlanabilir (`TOGETHER_API_KEY`)
  - Hugging Face başarısız olduğunda alternatif yedek olarak kullanılır

### 6. Readonly Form Alanları (YENİ - 2024)
- **Sadece Kitap Adı ve Yazar manuel yazılabilir**
- Diğer tüm alanlar (Orijinal Adı, Tür, Ülke/Edebi Gelenek, Çıkış Yılı, Anlatı Yılı, Konusu, Not) **readonly** - sadece otomatik doldurma ile doldurulur
- Kullanıcı bu alanlara manuel yazamaz, bilgiler sadece "Bilgileri Otomatik Doldur" butonu ile gelir
- Bu sayede veri tutarlılığı sağlanır ve kullanıcı hataları önlenir

### 7. Kitap Temalı UI Tasarımı (YENİ - 2024)
- **Renkler**: Kütüphane temalı kahverengi tonları (#8B4513, #F5E6D3, #FFF8DC)
- **Fontlar**: Georgia (kitap temalı, okunabilir)
- **Layout**: Konusu alanı sağ tarafa dikey olarak taşındı (daha geniş ve okunabilir)
- **Butonlar**: Renkli, kategorize edilmiş, hover efektli
- **Başlıklar**: Kitap emojili ve stilize edilmiş
- **Treeview**: Kitap temalı renklerle güncellendi
- **Pencere boyutu**: 1200x800 (daha geniş ve kullanıcı dostu)

### 8. Kısa ve Kullanıcı Dostu Mesajlar (YENİ - 2024)
- Tüm mesaj kutularındaki uzun listeler kısaltıldı
- 500+ kitap olsa bile mesajlar kısa ve okunabilir kalıyor
- Sadece özet bilgiler gösteriliyor, detaylar gösterilmiyor
- Emoji'ler eklendi (✅, 📚, 📊, 💡, vb.)
- Uzun metinler otomatik kısaltılıyor (50-200 karakter arası)
- Kullanıcı dostu ipuçları eklendi

### 9. Kitap Temalı İkon Sistemi (YENİ - 2024)
- **İkon Oluşturucu**: `ikon_olustur.py` - Kütüphane temalı ikonlar oluşturur
- **Otomatik Script**: `ikon_ve_shortcut_olustur.bat` - Tek tıkla ikon ve shortcut oluşturur
- **İkon Tasarımı**: Yan yana 4 dikey kitap, duvara dayanmış görünüm, kütüphane temalı renkler
- **Özelleştirilebilir**: Shortcut adını kullanıcı belirleyebilir
- **İkon Cache Temizleme**: `ikon_cache_temizle.bat` - Windows ikon cache'ini temizler

## Mimari Kararlar ve Tasarım Prensipleri

### Neden Modüler Mimari?

**Problem:** Başlangıçta tüm kod tek bir dosyada (977 satır) toplanmıştı. Bu durum:
- Kod bakımını zorlaştırıyordu
- Yeni özellik eklemek karmaşık hale geliyordu
- Test etmek zordu
- Kod tekrarı artıyordu

**Çözüm:** Kod 7 ayrı modüle bölündü. Her modül:
- **Tek bir sorumluluğa** odaklanır (Single Responsibility Principle)
- **Bağımsız test edilebilir**
- **Yeniden kullanılabilir**
- **Kolay genişletilebilir**

### Modüller Arası İletişim ve Bağımlılıklar

```
kitap_listesi_gui.py (Ana Koordinatör)
    ├── ExcelHandler (Excel işlemleri)
    ├── APIKeyManager (API key yönetimi)
    ├── ListManager (Liste yönetimi)
    ├── KitapBilgisiCekici (API entegrasyonu)
    │       ├── FieldPolicy (Alan bazlı kaynak öncelik)
    │       ├── QualityGates (Veri kalitesi kontrolü)
    │       ├── WikidataClient (Wikidata entegrasyonu)
    │       ├── QuotaRouter (API quota yönetimi)
    │       ├── Provenance (Provenance yazma)
    │       └── FieldRegistry (Excel şema yönetimi)
    ├── GUIWidgets (GUI widget'ları)
    └── FormHandler (Form işlemleri)
            └── GUIWidgets.get_widgets() (widget'lara erişim)
```

**Önemli Notlar:**
- `kitap_listesi_gui.py` tüm modülleri koordine eder, ancak modüller birbirini tanımaz
- `FormHandler` sadece widget'lara erişir, GUI yapısını bilmez
- `GUIWidgets` sadece widget'ları oluşturur, iş mantığını bilmez
- Modüller arası iletişim callback'ler ve return değerleri ile yapılır

### Kod Yazım Mantığı ve Prensipleri

#### 1. Separation of Concerns (Sorumlulukların Ayrılması)
- **GUIWidgets**: Sadece görsel widget'ları oluşturur, iş mantığı yok
- **FormHandler**: Sadece form işlemlerini yapar, GUI yapısını bilmez
- **ListManager**: Sadece liste yönetimini yapar, GUI'den bağımsız
- **ExcelHandler**: Sadece Excel işlemlerini yapar, GUI'den bağımsız

#### 2. Readonly Widget Yönetimi
**Problem:** Tkinter'da readonly widget'lar için state yönetimi karmaşık.

**Çözüm:** `FormHandler` modülünde özel state yönetimi:
```python
# Readonly widget'a yazmak için:
widget.config(state='normal')
widget.insert(0, value)
widget.config(state='readonly')
```

**⚠️ DİKKAT:** Her readonly widget işleminde state'i geçici olarak 'normal' yap, işlem bitince 'readonly' yap.

#### 3. Checkbox Sistemi Mantığı
**Problem:** Treeview'de gerçek checkbox widget'ı eklemek zor.

**Çözüm:** 
- Treeview'in ilk sütununu checkbox gibi kullan (☐/☑ karakterleri)
- Her satır için `BooleanVar` tutulur (`checkbox_vars` dict'i)
- Tıklama event'i ile toggle edilir
- Treeview'in kendi selection mekanizması ile görsel vurgulama yapılır

**⚠️ DİKKAT:** 
- `identify_column()` sadece x koordinatı alır (y koordinatı yok!)
- Event handling'de `return "break"` kullanarak Treeview'in kendi selection'ını engelle
- Checkbox toggle edildiğinde Treeview selection'ını da güncelle

#### 4. Thread Kullanımı (GUI Donmaması İçin)
**Problem:** API çağrıları uzun sürebilir, GUI donar.

**Çözüm:** 
- Tüm API çağrıları thread'de yapılır
- GUI güncellemeleri `root.after()` ile yapılır (thread-safe)
- Progress bar ile kullanıcıya geri bildirim verilir

**⚠️ DİKKAT:**
- Thread'den GUI'ye direkt erişim YAPMA! `root.after()` kullan
- Thread'de exception handling yap, hataları GUI'ye bildir

#### 5. Excel Format Tutarlılığı
**Problem:** Excel dosyası formatı değişebilir, eski formatlar uyumsuz olabilir.

**Çözüm:**
- `STANDART_SUTUN_SIRASI` sabiti ile sütun sırası garanti edilir
- `_format_kontrol_et()` ile format kontrolü yapılır
- `_format_guncelle()` ile eski format yeni formata çevrilir

**⚠️ DİKKAT:**
- Excel sütun sırasını değiştirirsen `STANDART_SUTUN_SIRASI`'ı güncelle
- Şablon oluştururken sadece zorunlu sütunları kullan (sadece "Kitap Adı" ve "Yazar")

#### 6. Mesaj Kısaltma Mantığı
**Problem:** 500+ kitap olsa bile mesajlar okunabilir olmalı.

**Çözüm:**
- Uzun metinler otomatik kısaltılır (50-200 karakter)
- Sadece özet bilgiler gösterilir
- Detaylar gösterilmez, sadece sayılar ve örnekler

**⚠️ DİKKAT:**
- Yeni mesaj eklerken uzun listeler gösterme
- Sadece özet bilgiler ve sayılar göster

### Güncelleme Yaparken Dikkat Edilmesi Gerekenler

#### ⚠️ KRİTİK: Excel Sütun Sırası
**ASLA DEĞİŞTİRME:**
- `excel_handler.py` içindeki `STANDART_SUTUN_SIRASI` listesi
- Bu sıra Excel dosyası formatını belirler
- Değiştirirsen mevcut Excel dosyaları uyumsuz olur

**Güncelleme Yaparken:**
1. Yeni sütun eklemek istersen `STANDART_SUTUN_SIRASI`'a ekle
2. `_format_guncelle()` fonksiyonunu güncelle (eski formatları yeni formata çevir)
3. `gui_widgets.py` içindeki Treeview sütunlarını güncelle
4. `form_handler.py` içindeki form alanlarını güncelle

#### ⚠️ KRİTİK: Readonly Widget State Yönetimi
**ASLA UNUTMA:**
- Readonly widget'lara yazmak için state'i geçici olarak 'normal' yap
- İşlem bitince mutlaka 'readonly' yap
- Aksi halde kullanıcı manuel yazabilir (istenmeyen davranış)

**Güncelleme Yaparken:**
1. `form_handler.py` içindeki `doldur()` ve `kitap_yukle()` fonksiyonlarını kontrol et
2. Her readonly widget işleminde state yönetimini doğru yap
3. Yeni readonly widget eklersen state yönetimini ekle

#### ⚠️ KRİTİK: Checkbox Sistemi
**ASLA UNUTMA:**
- Checkbox'lar Treeview'in ilk sütununda (☐/☑ karakterleri)
- Her satır için `BooleanVar` tutulur (`gui_widgets.py` içinde `checkbox_vars` dict'i)
- Checkbox toggle edildiğinde Treeview selection'ını da güncelle

**Güncelleme Yaparken:**
1. `gui_widgets.py` içindeki `listeyi_guncelle()` fonksiyonunu güncelle (checkbox_vars dict'ini güncelle)
2. `_on_tree_click()` fonksiyonunu güncelle (checkbox toggle mantığı)
3. `_baslik_checkbox_toggle()` fonksiyonunu güncelle (tümünü seç/kaldır)

#### ⚠️ KRİTİK: Thread ve GUI Güncellemeleri
**ASLA UNUTMA:**
- Thread'den GUI'ye direkt erişim YAPMA!
- `root.after()` kullanarak GUI güncellemeleri yap
- Exception handling yap, hataları GUI'ye bildir

**Güncelleme Yaparken:**
1. Yeni thread başlatırsan `root.after()` kullan
2. Exception handling ekle
3. Progress bar güncellemelerini `root.after()` ile yap

#### ⚠️ KRİTİK: Excel Dosya Adı
**ASLA DEĞİŞTİRME:**
- Excel dosya adı: `Kutuphanem.xlsx` (sabit)
- Değiştirirsen mevcut Excel dosyaları bulunamaz

**Güncelleme Yaparken:**
1. `excel_handler.py` içindeki varsayılan dosya adını değiştirme
2. `kitap_listesi_gui.py` içindeki ExcelHandler oluşturma kısmını değiştirme

#### ⚠️ KRİTİK: Excel Şablonu Formatı
**ASLA DEĞİŞTİRME:**
- Şablon sadece "Kitap Adı" ve "Yazar" sütunlarını içerir
- Diğer sütunlar otomatik doldurma ile gelir

**Güncelleme Yaparken:**
1. `excel_handler.py` içindeki `sablon_olustur()` fonksiyonunu değiştirme
2. Şablon formatını değiştirirsen kullanıcıları bilgilendir

### Best Practices ve Anti-patterns

#### ✅ YAPILMASI GEREKENLER:

1. **Modüler Yapıyı Koru**
   - Yeni özellik eklerken ilgili modüle ekle
   - Ana dosyayı şişirme, modüllere dağıt

2. **State Yönetimini Doğru Yap**
   - Readonly widget'larda state yönetimini unutma
   - Checkbox state'lerini doğru yönet

3. **Hata Yönetimi Yap**
   - Try-except blokları kullan
   - Kullanıcıya anlaşılır hata mesajları göster
   - Console'a detaylı log yaz

4. **Thread-Safe GUI Güncellemeleri**
   - Thread'den GUI'ye `root.after()` ile eriş
   - Direkt erişim yapma

5. **Mesajları Kısa Tut**
   - Uzun listeler gösterme
   - Sadece özet bilgiler göster

#### ❌ YAPILMAMASI GEREKENLER:

1. **Modüller Arası Doğrudan Bağımlılık**
   - Modüller birbirini import etmesin
   - Sadece ana dosya modülleri import etsin

2. **GUI'de İş Mantığı**
   - GUIWidgets modülünde iş mantığı olmasın
   - İş mantığı ilgili modüllerde olsun

3. **Thread'den Direkt GUI Erişimi**
   - Thread'den widget'lara direkt erişim yapma
   - `root.after()` kullan

4. **Excel Formatını Değiştirme**
   - `STANDART_SUTUN_SIRASI`'ı değiştirme
   - Değiştirirsen migration kodu yaz

5. **Readonly Widget State'ini Unutma**
   - State yönetimini unutma
   - Kullanıcının manuel yazmasına izin verme

### Hata Ayıklama İpuçları

#### 1. Checkbox Çalışmıyorsa
- `gui_widgets.py` içindeki `_on_tree_click()` fonksiyonunu kontrol et
- `identify_column()` sadece x koordinatı alıyor mu kontrol et
- `checkbox_vars` dict'inin doğru güncellendiğini kontrol et
- Console'da hata mesajı var mı kontrol et

#### 2. Readonly Widget'a Yazılamıyorsa
- `form_handler.py` içindeki state yönetimini kontrol et
- State'i geçici olarak 'normal' yapıyor mu kontrol et
- İşlem bitince 'readonly' yapıyor mu kontrol et

#### 3. Thread'de Hata Oluyorsa
- Exception handling var mı kontrol et
- `root.after()` kullanılıyor mu kontrol et
- Console'da traceback var mı kontrol et

#### 4. Excel Dosyası Bulunamıyorsa
- Dosya adı `Kutuphanem.xlsx` mi kontrol et
- Dosya yolu doğru mu kontrol et
- Dosya izinleri var mı kontrol et

#### 5. API Çağrıları Çalışmıyorsa
- Internet bağlantısı var mı kontrol et
- API key doğru mu kontrol et
- Console'da API hata mesajları var mı kontrol et
- Rate limit aşıldı mı kontrol et

### Test Stratejisi

#### Modül Bazlı Test
Her modül bağımsız test edilebilir:

1. **ExcelHandler Test:**
   - Excel dosyası okuma/yazma
   - Format kontrolü ve güncelleme
   - Şablon oluşturma

2. **ListManager Test:**
   - Kitap ekleme/silme
   - Tekrar kontrolü
   - Toplu ekleme

3. **FormHandler Test:**
   - Form doğrulama
   - Form doldurma
   - Readonly widget state yönetimi

4. **APIKeyManager Test:**
   - API key kaydetme/yükleme
   - API key silme
   - Durum kontrolü

5. **KitapBilgisiCekici Test:**
   - API çağrıları (mock ile)
   - Veri parse etme
   - Hata yönetimi

#### Entegrasyon Testi
- Modüller arası iletişim
- GUI ve iş mantığı entegrasyonu
- Excel ve liste yönetimi entegrasyonu

### Gelecek Geliştirmeler İçin Notlar

#### Yeni Özellik Eklerken:

1. **Yeni Modül Ekle:**
   - Yeni bir sorumluluk varsa yeni modül oluştur
   - Modül adı açıklayıcı olsun (örn: `search_manager.py`)
   - Modülü `kitap_listesi_gui.py` içinde import et ve başlat

2. **Mevcut Modüle Ekle:**
   - İlgili modüle ekle
   - Modülün sorumluluğunu bozma
   - Fonksiyon adları açıklayıcı olsun

3. **GUI'ye Yeni Widget Ekle:**
   - `gui_widgets.py` içinde ekle
   - `get_widgets()` fonksiyonuna ekle
   - Callback'leri `kitap_listesi_gui.py` içinde bağla

4. **Excel Formatını Değiştir:**
   - `STANDART_SUTUN_SIRASI`'ı güncelle
   - `_format_guncelle()` fonksiyonunu güncelle
   - Migration kodu yaz (eski formatı yeni formata çevir)

5. **Yeni API Eklemek:**
   - `kitap_bilgisi_cekici.py` içinde ekle
   - `kitap_bilgisi_cek()` fonksiyonuna entegre et
   - Hata yönetimi ekle

#### Kod Güncellerken:

1. **Dokümantasyonu Güncelle:**
   - `HAND_OFF_DOKUMANTASYON.md` dosyasını güncelle
   - Yeni özellikleri ekle
   - Güncellenen fonksiyonları güncelle

2. **Satır Sayılarını Güncelle:**
   - Modül satır sayılarını güncelle
   - Toplam satır sayısını güncelle

3. **Kullanım Senaryolarını Güncelle:**
   - Yeni senaryolar ekle
   - Güncellenen senaryoları güncelle

4. **Best Practices'i Takip Et:**
   - Modüler yapıyı koru
   - State yönetimini doğru yap
   - Hata yönetimi ekle

## Teknik Detaylar

### Teknoloji Stack
- **Python 3.7+**
- **Tkinter** (GUI framework)
- **pandas** (Veri işleme)
- **openpyxl** (Excel işlemleri)
- **requests** (HTTP istekleri - API çağrıları için)
- **Pillow** (İkon oluşturma - isteğe bağlı)
- **pywin32** (Windows shortcut oluşturma - isteğe bağlı)

### Dosya Yapısı (KLASÖR ORGANİZASYONU - 2026-02-10 Güncellemesi)

```
KÜTÜPHANE/
├── kitap_listesi_gui.py          # Ana program dosyası (root'ta - kolay erişim için)
├── requirements.txt              # Python bağımlılıkları (root'ta - pip standart)
├── .gitignore                    # Git ignore dosyası (root'ta - git standart)
│
├── modules/                      # Tüm Python modülleri (YENİ KLASÖR)
│   ├── __init__.py              # Package init dosyası
│   ├── kitap_bilgisi_cekici.py  # API entegrasyon modülü (~1089 satır)
│   ├── excel_handler.py         # Excel işlemleri modülü (~227 satır)
│   ├── api_key_manager.py       # API key yönetimi modülü (~108 satır)
│   ├── form_handler.py          # Form işlemleri modülü (~229 satır)
│   ├── list_manager.py          # Liste yönetimi modülü (~157 satır)
│   ├── gui_widgets.py           # GUI widget'ları modülü (~375 satır)
│   ├── field_policy.py          # Alan bazlı kaynak öncelik ve validation (YENİ - 2026)
│   ├── quality_gates.py         # Veri kalitesi kontrolü ve "yanlış bağlam" önleme (YENİ - 2026)
│   ├── wikidata_client.py       # Wikidata QID çözümleme ve alan çıkarma (YENİ - 2026)
│   ├── router.py                # API quota yönetimi ve backoff mekanizması (YENİ - 2026)
│   ├── provenance.py            # Provenance (kaynak, güven) bilgisi yazma (YENİ - 2026)
│   ├── field_registry.py        # Excel şema kolon isimlerini merkezi yönetim (YENİ - 2026)
│   ├── test_quality_gates.py    # Quality gates için unit testler (YENİ - 2026)
│   └── test_regression.py       # Regression testler (end-to-end senaryolar) (YENİ - 2026)
│
├── scripts/                      # Yardımcı scriptler (YENİ KLASÖR)
│   ├── PROGRAMI_AC.vbs          # Programı başlatma scripti (VBScript - konsol penceresi gizli) ⭐ ÖNERİLEN
│   ├── PROGRAMI_AC.bat          # Programı başlatma scripti (alternatif)
│   ├── ikon_olustur.py          # Kitap temalı ikon oluşturucu (YENİ - 2024)
│   ├── ikon_ve_shortcut_olustur.bat # İkon ve shortcut oluşturma scripti (YENİ - 2024)
│   ├── ikon_cache_temizle.bat   # Windows ikon cache temizleme (YENİ - 2024)
│   └── exe_olustur.bat          # EXE dosyası oluşturma scripti
│
├── data/                         # Veri dosyaları (YENİ KLASÖR)
│   ├── Kutuphanem.xlsx          # Oluşturulan Excel dosyası
│   ├── groq_api_key.txt         # Groq API key dosyası
│   └── huggingface_api_key.txt  # Hugging Face API key dosyası (isteğe bağlı)
│
├── icons/                        # İkon dosyaları (YENİ KLASÖR)
│   ├── kitap_ikon.ico           # Oluşturulan ikon dosyası (ICO formatı)
│   └── kitap_ikon.png           # Oluşturulan ikon dosyası (PNG formatı)
│
└── docs/                         # Dokümantasyon (YENİ KLASÖR)
    ├── README.md                 # Kullanım kılavuzu
    └── HAND_OFF_DOKUMANTASYON.md # Bu dokümantasyon dosyası
```

**Klasör Organizasyonu Avantajları:**
- ✅ Dosyalar kategorilere göre organize edildi
- ✅ Modüller `modules/` klasöründe toplandı
- ✅ Script'ler `scripts/` klasöründe toplandı
- ✅ Veri dosyaları `data/` klasöründe toplandı
- ✅ İkon dosyaları `icons/` klasöründe toplandı
- ✅ Dokümantasyon `docs/` klasöründe toplandı
- ✅ Ana program dosyası root'ta kaldı (kolay erişim için)
- ✅ Import path'leri otomatik güncellendi (`sys.path` ile `modules/` eklendi)
- ✅ Dosya path'leri güncellendi (data/, icons/ klasörlerine göre)

**⚠️ ÖNEMLİ NOT - Yeni Dosya Oluşturma:**
Yeni dosya oluşturulurken ilgili klasör altına oluşturulmalıdır:
- **Python modülleri** → `modules/` klasörüne
- **Script dosyaları** (.bat, .vbs, .py yardımcı scriptler) → `scripts/` klasörüne
- **Veri dosyaları** (.xlsx, .txt API key'ler) → `data/` klasörüne
- **İkon/resim dosyaları** → `icons/` klasörüne
- **Dokümantasyon** (.md) → `docs/` klasörüne

**📌 Root'ta Kalması Gereken Dosyalar:**
- **`kitap_listesi_gui.py`**: Ana program dosyası (kolay erişim)
- **`requirements.txt`**: Python bağımlılıkları (pip standart)
- **`.gitignore`**: Git ignore dosyası (git standart)

Eğer ilgili klasör yoksa, önce klasör oluşturulmalıdır.

**Modüler Yapı Avantajları:**
- ✅ Her modül kendi sorumluluğuna odaklanır (Separation of Concerns)
- ✅ Kod bakımı ve genişletme kolaylaşır
- ✅ Modüller bağımsız test edilebilir
- ✅ Kod tekrarı azalır ve okunabilirlik artar
- ✅ Yeni özellikler ilgili modüle eklenir, ana dosya şişmez

### Excel Formatı

**Sütun sırası (sabit - YENİ - 2026):**

**Veri Kolonları:**
1. **Kitap Adı** (zorunlu)
2. **Yazar** (zorunlu)
3. Orijinal Adı
4. Tür
5. Ülke/Edebi Gelenek
6. Çıkış Yılı (tek yıl veya aralık formatı: "1869" veya "1865-1869")
7. Anlatı Yılı (kitabın anlattığı olayların geçtiği dönem, örn: "1865", "1865-1869", "19. yüzyıl")
8. Konusu
9. Not

**Provenance Kolonları (Her alan için kaynak ve güven bilgisi - YENİ - 2026):**
10. src_Orijinal Adı (kaynak: "enwiki", "trwiki", "gbooks", "openlibrary", "wikidata", "groq", "hf", "together")
11. conf_Orijinal Adı (güven: 0.0-1.0)
12. src_Tür
13. conf_Tür
14. src_Ülke/Edebi Gelenek
15. conf_Ülke/Edebi Gelenek
16. src_Çıkış Yılı
17. conf_Çıkış Yılı
18. src_Anlatı Yılı
19. conf_Anlatı Yılı
20. src_Konusu
21. conf_Konusu

**Satır Seviyesinde Metadata Kolonları (YENİ - 2026):**
22. status (PENDING, OK, PARTIAL, FAIL, NEEDS_REVIEW)
23. missing_fields (eksik alanlar listesi, virgülle ayrılmış)
24. last_attempt_at (son deneme zamanı, ISO format)
25. retry_count (deneme sayısı)
26. next_retry_at (sonraki deneme zamanı, ISO format)
27. best_source (en iyi kaynak: "enwiki", "trwiki", "gbooks", "openlibrary", "wikidata", "groq", "hf", "together")
28. match_score (eşleşme skoru, 0.0-1.0)
29. wikidata_qid (Wikidata QID, örn: "Q12345")

### Kod Yapısı ve Mantık

#### Modüller Arası İletişim Akışı

**1. Başlangıç Akışı:**
```
kitap_listesi_gui.py (main)
    ↓
    ├─ sys.path'e modules/ klasörü eklenir
    ├─ ExcelHandler.__init__() → "data/Kutuphanem.xlsx" dosyasını hazırla
    ├─ APIKeyManager.__init__() → "data/groq_api_key.txt" dosyasını hazırla
    ├─ ListManager.__init__() → Boş liste oluştur
    ├─ KitapBilgisiCekici.__init__() → API URL'lerini hazırla
    ├─ GUIWidgets.__init__() → Root penceresini al
    ↓
    ├─ ExcelHandler.yukle() → Mevcut Excel'i yükle
    ├─ APIKeyManager.yukle() → API key'i yükle
    ├─ KitapBilgisiCekici.groq_api_key → API key'i aktar
    ├─ GUIWidgets.olustur() → GUI'yi oluştur
    ├─ FormHandler.__init__() → Widget'ları al ve başlat
    └─ GUIWidgets.listeyi_guncelle() → Listeyi göster
```

**2. Kitap Ekleme Akışı:**
```
Kullanıcı "Listeye Ekle" butonuna tıklar
    ↓
kitap_listesi_gui.listeye_ekle()
    ↓
    ├─ FormHandler.dogrula() → Form doğrulaması
    ├─ FormHandler.kitap_dict_olustur() → Dict oluştur
    ├─ ListManager.ekle() → Listeye ekle (tekrar kontrolü)
    ├─ GUIWidgets.listeyi_guncelle() → Treeview'i güncelle
    └─ Mesaj göster
```

**3. Otomatik Bilgi Doldurma Akışı (Policy-Driven - YENİ):**
```
Kullanıcı "Bilgileri Otomatik Doldur" butonuna tıklar
    ↓
kitap_listesi_gui.bilgileri_otomatik_doldur()
    ↓
    ├─ FormHandler.dogrula() → Kitap Adı ve Yazar kontrolü
    ├─ GUIWidgets.progress_goster() → Progress bar göster
    ├─ Thread başlat → _bilgileri_cek_ve_doldur()
    ↓
    Thread içinde:
    ├─ KitapBilgisiCekici.kitap_bilgisi_cek_policy() → Policy-driven bilgi çekme
    │   ├─ FieldPolicy.build_rules() → Alan bazlı kuralları al
    │   ├─ _collect_sources() → Çoklu kaynaktan veri topla (Wikipedia, Google Books, Open Library, Wikidata)
    │   ├─ QualityGates.gate_*() → Veri kalitesi kontrolü
    │   ├─ QuotaRouter.call() → AI çağrıları (rate limit yönetimi ile)
    │   ├─ Provenance.set_field() → Provenance bilgisi yaz
    │   └─ Provenance.set_row_status() → Satır seviyesinde metadata yaz
    ├─ root.after() → GUI güncellemesi (thread-safe)
    ├─ FormHandler.doldur() → Formu doldur (meta kolonlar hariç)
    └─ GUIWidgets.progress_gizle() → Progress bar gizle
```

**4. Checkbox Toggle Akışı:**
```
Kullanıcı "Seç" sütunundaki ☐ işaretine tıklar
    ↓
gui_widgets._on_tree_click()
    ↓
    ├─ identify_column() → "#1" sütunu mu kontrol et
    ├─ identify_row() → Hangi satır tıklandı
    ├─ checkbox_vars[idx] → BooleanVar'ı bul
    ├─ var.set(not var.get()) → Toggle et
    ├─ Treeview'i güncelle → ☐ → ☑
    ├─ tree.selection_add/remove() → Selection güncelle
    └─ return "break" → Treeview'in kendi selection'ını engelle
```

**5. Excel'den Yükleme Akışı:**
```
Kullanıcı "Excel'den Yükle" butonuna tıklar
    ↓
kitap_listesi_gui.excel_yukle()
    ↓
    ├─ ExcelHandler.disaridan_yukle() → Excel'i parse et
    ├─ ListManager.toplu_ekle() → Listeye ekle
    ├─ GUIWidgets.listeyi_guncelle() → Treeview'i güncelle
    ├─ _otomatik_doldurma_dialog_goster() → Seçenek dialog'u
    ↓
    Kullanıcı seçim yapar:
    ├─ "Her kitap için toplu çağrı yap" → _excel_kitaplari_otomatik_doldur()
    └─ "Manuel çift tıklayarak forma yükle" → Dialog kapanır
```

#### Kritik Kod Mantıkları

**1. Readonly Widget State Yönetimi:**
```python
# ❌ YANLIŞ:
widget.insert(0, value)  # Readonly widget'a yazamazsın!

# ✅ DOĞRU:
widget.config(state='normal')  # Geçici olarak normal yap
widget.delete(0, tk.END)
widget.insert(0, value)
widget.config(state='readonly')  # Tekrar readonly yap
```

**2. Thread-Safe GUI Güncellemeleri:**
```python
# ❌ YANLIŞ:
messagebox.showinfo("Başarılı", "İşlem tamamlandı")  # Thread'den direkt erişim!

# ✅ DOĞRU:
self.root.after(0, lambda: messagebox.showinfo("Başarılı", "İşlem tamamlandı"))
```

**3. Checkbox Toggle Mantığı:**
```python
# Checkbox durumunu toggle et
var.set(not var.get())

# Treeview'de güncelle
checkbox_text = "☑" if var.get() else "☐"
values = list(self.tree.item(item, "values"))
values[0] = checkbox_text
self.tree.item(item, values=values)

# Treeview selection'ı güncelle
if var.get():
    self.tree.selection_add(item)
else:
    self.tree.selection_remove(item)

# Event'i durdur (Treeview'in kendi selection'ını engelle)
return "break"
```

**4. Excel Format Tutarlılığı:**
```python
# Sütun sırasını garanti et
df = df[STANDART_SUTUN_SIRASI]  # Her zaman aynı sıra

# Eksik sütunları ekle
for sutun in STANDART_SUTUN_SIRASI:
    if sutun not in df.columns:
        df[sutun] = ""
```

### Program Akışı

#### Başlangıç (MODÜLER YAPI):
1. `KitapListesiGUI` sınıfı başlatılır
2. **Modüller başlatılır:**
   - `ExcelHandler`: Excel dosyası işlemleri için
   - `APIKeyManager`: API key yönetimi için
   - `ListManager`: Kitap listesi yönetimi için
   - `KitapBilgisiCekici`: API entegrasyonu için
   - `GUIWidgets`: GUI widget'ları için
3. `ExcelHandler.yukle()` ile mevcut Excel dosyası yüklenir ve format kontrolü yapılır
4. `APIKeyManager.yukle()` ile API key yüklenir (varsa)
5. `KitapBilgisiCekici` modülüne API key aktarılır
6. `GUIWidgets.olustur()` ile GUI oluşturulur
7. `FormHandler` başlatılır ve widget'lara bağlanır
8. Mevcut kitaplar listeye yüklenir

#### Kitap Ekleme (Manuel - MODÜLER YAPI):
1. Kullanıcı **sadece Kitap Adı ve Yazar** girer (diğer alanlar readonly)
2. `FormHandler.dogrula()` ile form doğrulaması yapılır (Kitap Adı ve Yazar zorunlu)
3. `FormHandler._cikis_yili_dogrula()` ile çıkış yılı kontrolü:
   - Tek yıl: "1869" (1500-2030 aralığında)
   - Aralık: "1865-1869" (her iki yıl da kontrol edilir)
   - Metin: Sayısal kontrol başarısız olursa metin olarak kabul edilir
4. `FormHandler.kitap_dict_olustur()` ile kitap dict'i oluşturulur
5. `ListManager.ekle()` ile listeye ekleme (tekrar kontrolü otomatik)
6. `GUIWidgets.listeyi_guncelle()` ile görüntüleme güncellenir
7. Kısa ve öz başarı mesajı gösterilir (uzun listeler gösterilmez)

#### Otomatik Bilgi Doldurma (Policy-Driven - YENİ - 2026):
1. Kullanıcı **Kitap Adı ve Yazar** girer (diğer alanlar readonly)
2. Kullanıcı "Bilgileri Otomatik Doldur" butonuna tıklar
3. `FormHandler.dogrula()` ile Kitap Adı ve Yazar kontrolü yapılır
4. `GUIWidgets.progress_goster()` ile progress bar gösterilir
5. Arka planda thread başlatılır (GUI donmaması için)
6. `KitapBilgisiCekici.kitap_bilgisi_cek_policy()` ile policy-driven bilgi çekme:
   - **Field Policy**: `FieldPolicy.build_rules()` ile alan bazlı kurallar alınır
   - **Kaynak Toplama**: `_collect_sources()` ile çoklu kaynaktan veri toplanır:
     - Wikipedia API (EN/TR): İngilizce sayfada arama → Türkçe sayfada arama → `_wikibase_item` yakalama
     - Google Books API: Yazar adına göre en uygun sonucu bul
     - Open Library API: first_publish_year kullanarak bilgi çek
     - Wikidata API: QID çözümleme (Wikipedia'dan veya doğrudan) → yapılandırılmış veri çekme
   - **Quality Gates**: Her alan için quality gate fonksiyonları çalıştırılır:
     - Çıkış Yılı: Translation context, edition date kontrolü
     - Orijinal Adı: Volume marker, same as localized kontrolü
   - **Kaynak Seçimi**: Policy'ye göre en yüksek öncelikli kaynaktan geçen değer seçilir
   - **AI Fallback**: Eksik alanlar için AI kullanılır (`QuotaRouter` ile):
     - Groq AI (birincil) → Hugging Face AI (yedek) → Together AI (alternatif yedek)
     - Rate limit ve API key hataları router tarafından yönetilir
   - **Provenance Yazma**: `Provenance.set_field()` ile her alan için kaynak ve güven bilgisi yazılır
   - **Status Yönetimi**: `Provenance.set_row_status()` ile satır seviyesinde metadata yazılır
7. `FormHandler.doldur()` ile bulunan bilgiler forma otomatik doldurulur (meta kolonlar hariç)
8. **Readonly alanlar** otomatik doldurulur (state geçici olarak normal yapılır)
9. Sadece boş alanlar doldurulur (kullanıcı doldurmuşsa değiştirilmez)
10. **Kısa ve öz başarı mesajı** gösterilir (sadece alan isimleri, değerler gösterilmez)
11. `GUIWidgets.progress_gizle()` ile progress bar gizlenir

#### Excel İşlemleri (MODÜLER YAPI - Policy-Driven - YENİ - 2026):
- **Excel Dosyası Oluştur**: 
  - `ListManager.tumunu_getir()` ile liste alınır
  - `ExcelHandler.kaydet()` ile Excel'e kaydedilir (`Kutuphanem.xlsx`)
  - Meta kolonlar (provenance, status, missing_fields, vb.) otomatik yazılır
- **Excel Şablonu Oluştur**: 
  - `ExcelHandler.sablon_olustur()` ile boş şablon oluşturulur (sadece "Kitap Adı" ve "Yazar" sütunları)
- **Excel'den Yükle**: 
  - `ExcelHandler.disaridan_yukle()` ile Excel dosyası yüklenir
  - Zorunlu kolon kontrolü önce yapılır, meta kolon tamamlama sonra yapılır
  - `ListManager.toplu_ekle()` ile mevcut listeye eklenir
  - `GUIWidgets.listeyi_guncelle()` ile görüntüleme güncellenir
  - **Otomatik Bilgi Doldurma Seçeneği (YENİ - 2024, Policy-Driven - 2026)**:
    - Kullanıcıya 2 seçenek sunulur (radio button'lar ile):
      1. **Her kitap için toplu çağrı yap**: Tüm kitaplar için policy-driven otomatik bilgi doldurma
         - `kitap_bilgisi_cek_policy()` kullanılır
         - Her 50 kayıtta checkpoint: Excel otomatik kaydedilir (crash recovery için)
         - Status, missing_fields, provenance bilgileri Excel'e yazılır
      2. **Manuel çift tıklayarak forma yükle**: Listeden kitaba çift tıklayıp "Bilgileri Otomatik Doldur" butonuna tıklayın
    - Seçim yapıldığında otomatik olarak işlem başlar

### API Entegrasyon Detayları

#### Wikipedia API
- **URL**: `https://en.wikipedia.org/api/rest_v1/page/summary/` ve `https://tr.wikipedia.org/api/rest_v1/page/summary/`
- **Yöntem**: REST API
- **Arama Stratejisi**:
  1. Önce İngilizce Wikipedia'da ara (orijinal dildeki bilgiler için)
  2. Yazar adı eşleşmesi kontrol et
  3. Bulunamazsa Türkçe Wikipedia'da ara
- **Parse Edilen Bilgiler**:
  - Orijinal adı: İngilizce sayfada title kullanılır veya extract'ten çıkarılır
  - Çıkış yılı: "first published", "written", "published in" gibi ifadelerden yıl çıkarılır
  - Tür: Extract'te geçen tür bilgileri eşleştirilir
  - Ülke: Yazarın ülkesi extract'ten çıkarılır
  - Konusu: Extract'in ilk 1-2 cümlesi

#### Google Books API
- **URL**: `https://www.googleapis.com/books/v1/volumes`
- **Yöntem**: REST API
- **Parametreler**:
  - `q`: Kitap adı + Yazar
  - `maxResults`: 5 (en uygun sonucu bulmak için)
- **Parse Edilen Bilgiler**:
  - Orijinal adı: `volumeInfo.title`
  - Çıkış yılı: `volumeInfo.publishedDate` (YYYY, YYYY-MM, veya YYYY-MM-DD formatı)
  - Tür: `volumeInfo.categories` (kategori eşleştirmesi)
  - Konusu: `volumeInfo.description` (ilk 1-2 cümle)
  - Ülke: `volumeInfo.language` (dil-ülke eşleştirmesi)

#### Open Library API
- **URL**: `https://openlibrary.org/search.json`
- **Yöntem**: REST API
- **Parametreler**:
  - `q`: Kitap adı + Yazar
  - `limit`: 1
- **Parse Edilen Bilgiler**:
  - Orijinal adı: `title`
  - Çıkış yılı: `first_publish_year` (ilk yayın yılı - doğru!)
  - Tür: `subject` (konu eşleştirmesi)
  - Konusu: `first_sentence` (ilk 1-2 cümle)

#### Groq AI API
- **URL**: `https://api.groq.com/openai/v1/chat/completions`
- **Yöntem**: REST API (OpenAI uyumlu)
- **Model**: `llama-3.3-70b-versatile` (güncel model)
- **API Key**: Ücretsiz (https://console.groq.com)
- **Özellikler**:
  - Çok daha doğru ve kapsamlı bilgiler
  - Orijinal adı her zaman Latin harflerine transliterasyon yapar
  - Yazarın ülkesini doğru bulur
  - İlk yayın yılını doğru bulur
  - **Anlatı Yılı** bilgisini de bulur
- **Prompt Özellikleri**:
  - Sistem mesajı: "Sen bir kitap bilgisi uzmanısın. Sadece JSON formatında yanıt ver."
  - **⚠️ Token Tasarrufu**: Prompt optimize edilmiştir (~200-300 token, önceden ~400-600 token)
  - Kısa ve öz prompt ile 2x daha fazla kitap işlenebilir
  - Temperature: 0.3 (daha tutarlı sonuçlar için)
  - Max tokens: 500
- **Rate Limit Yönetimi**:
  - Limit: 100,000 token/gün (ücretsiz tier)
  - Rate limit (429) hatası durumunda otomatik olarak Hugging Face AI'ye geçilir
  - Her çağrı ~200-300 token kullanır (optimize edilmiş prompt ile)
- **Yanıt İşleme**:
  - JSON formatında yanıt beklenir
  - ````json ... ```` formatı veya `{...}` formatı parse edilir
  - Sadece eksik alanlar döndürülür
  - Groq başarılı döndü ama bazı alanlar boş olabilir, bu durumda Hugging Face AI devreye girer

#### Hugging Face Inference API
- **URL**: `https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2`
- **Yöntem**: REST API
- **Model**: `mistralai/Mistral-7B-Instruct-v0.2`
- **API Key**: İsteğe bağlı (API key ile daha yüksek rate limit)
- **Özellikler**:
  - Groq AI başarısız olduğunda veya rate limit'e takıldığında yedek olarak kullanılır
  - Groq'dan sonra hala eksik bilgiler varsa devreye girer
  - Ücretsiz tier mevcuttur
- **Rate Limits**:
  - API key olmadan: ~30 istek/dakika
  - API key ile: Daha yüksek limitler
- **Yanıt İşleme**:
  - JSON formatında yanıt beklenir
  - `[{"generated_text": "..."}]` formatı parse edilir
  - Sadece eksik alanlar döndürülür

#### Together AI API
- **URL**: `https://api.together.xyz/v1/chat/completions`
- **Yöntem**: REST API (OpenAI uyumlu)
- **API Key**: Ücretsiz tier mevcuttur (https://api.together.xyz)
- **Özellikler**:
  - Hugging Face başarısız olduğunda veya hala eksik bilgiler varsa alternatif yedek olarak kullanılır
  - Ücretsiz tier mevcuttur
- **Yanıt İşleme**:
  - JSON formatında yanıt beklenir
  - OpenAI uyumlu format parse edilir
  - Sadece eksik alanlar döndürülür

### Önemli Fonksiyonlar (MODÜLER YAPI)

#### `kitap_listesi_gui.py` (Ana Koordinasyon - ~905 satır):

- `__init__()`: Modülleri başlatır ve koordine eder
- `gui_olustur()`: GUI widget'larını oluşturur ve callback'leri bağlar
- `bilgileri_otomatik_doldur()`: Otomatik bilgi doldurma başlatır
- `_bilgileri_cek_ve_doldur()`: Arka planda API çağrılarını yapar (thread'de çalışır)
- `_formu_doldur()`: Çekilen bilgileri forma doldurur
- `listeye_ekle()`: Formdan kitap bilgilerini alıp listeye ekler
- `kitap_sec()`: Listeden seçilen kitabı forma yükler (çift tıklama)
- `kitap_sil()`: Seçili kitabı listeden siler (checkbox veya selection kontrolü)
- `toplu_sil()`: Seçili kitapları toplu olarak siler
- `tumunu_kaldir()`: Tüm seçimleri kaldırır
- `groq_api_key_ayarla()`: Groq API key ayarları dialog'unu gösterir
- `excel_olustur()`: Kitap listesini Excel'e kaydetme koordinasyonu
- `excel_yukle()`: Excel'den yükleme koordinasyonu (otomatik bilgi doldurma seçeneği ile)
- `_otomatik_doldurma_dialog_goster()`: Excel'den yükleme sonrası seçenek dialog'unu gösterir
- `_excel_kitaplari_otomatik_doldur()`: Excel'den yüklenen kitaplar için toplu bilgi doldurma

#### `excel_handler.py` (Excel İşlemleri Modülü - ~229 satır):

- `__init__()`: Excel dosyası yolunu ayarlar (varsayılan: `Kutuphanem.xlsx`)
- `yukle()`: Excel dosyasından kitap listesini yükler ve format günceller
- `kaydet()`: Kitap listesini Excel dosyasına kaydeder (`Kutuphanem.xlsx`)
- `sablon_olustur()`: Boş Excel şablonu oluşturur (sadece "Kitap Adı" ve "Yazar" sütunları)
- `disaridan_yukle()`: Dışarıdan Excel dosyası yükler ve parse eder
- `dosya_acik_mi()`: Excel dosyasının açık olup olmadığını kontrol eder
- `_format_kontrol_et()`: Format kontrolü yapar
- `_format_guncelle()`: Formatı günceller

#### `api_key_manager.py` (API Key Yönetimi Modülü - ~90 satır):

- `__init__()`: API key dosyası yolunu ayarlar
- `yukle()`: API key'i dosyadan yükler
- `kaydet()`: API key'i dosyaya kaydeder
- `sil()`: API key'i siler
- `durum()`: API key durumunu döndürür (✓/✗)
- `get()`: Mevcut API key'i döndürür

#### `form_handler.py` (Form İşlemleri Modülü - ~260 satır):

- `__init__()`: Form widget'larını alır
- `temizle()`: Form alanlarını temizler (readonly widget'lar için state yönetimi)
- `deger_al()`: Form değerlerini dict olarak alır (disabled Text widget için özel işlem)
- `dogrula()`: Form doğrulaması yapar (Kitap Adı ve Yazar zorunlu)
- `doldur()`: Formu bilgilerle doldurur (readonly widget'lar için state geçici normal yapılır)
- `kitap_yukle()`: Kitap bilgilerini forma yükler (listeden çift tıklama için)
- `kitap_dict_olustur()`: Formdan kitap dict'i oluşturur
- `_cikis_yili_dogrula()`: Çıkış yılı doğrulaması yapar

#### `list_manager.py` (Liste Yönetimi Modülü - ~120 satır):

- `__init__()`: Kitap listesini başlatır
- `ekle()`: Kitap ekler (tekrar kontrolü ile)
- `sil()`: Kitap siler
- `getir()`: Belirli bir kitabı getirir
- `tumunu_getir()`: Tüm kitap listesini getirir
- `sayi()`: Kitap sayısını döndürür
- `temizle()`: Listeyi temizler
- `toplu_ekle()`: Toplu kitap ekler
- `ara()`: Kitap arar

#### `gui_widgets.py` (GUI Widget'ları Modülü - ~553 satır):

- `__init__()`: Root penceresini alır
- `olustur()`: Tüm GUI widget'larını oluşturur (kitap temalı tasarım)
- `_form_frame_olustur()`: Form frame'ini oluşturur (readonly alanlar ile)
- `_konusu_frame_olustur()`: Konusu frame'ini oluşturur (sağ taraf, dikey)
- `_liste_frame_olustur()`: Liste frame'ini oluşturur (kitap temalı renkler, checkbox sistemi ile)
- `listeyi_guncelle()`: Treeview'i günceller (checkbox'lar ile)
- `_on_tree_click()`: Treeview tıklama event'i (checkbox toggle için)
- `_baslik_checkbox_toggle()`: Başlık sütunundaki ☑ işaretine tıklama (tümünü seç/kaldır)
- `secili_kitaplari_getir()`: Seçili kitapların indekslerini döndürür
- `tumunu_sec()`: Tüm kitapları seçer
- `tumunu_kaldir()`: Tüm seçimleri kaldırır
- `progress_goster()`: Progress bar'ı gösterir
- `progress_gizle()`: Progress bar'ı gizler
- `progress_mesaj_guncelle()`: Progress bar mesajını günceller
- `api_key_buton_guncelle()`: API key butonunu günceller
- `get_widgets()`: Widget'ları döndürür

#### `kitap_bilgisi_cekici.py` (~1089 satır):

- `__init__()`: API URL'lerini ve API key'leri başlatır (Groq, Hugging Face, Together AI)
- `kitap_bilgisi_cek()`: Ana fonksiyon - çoklu kaynaktan bilgi çeker (ESKİ - kullanılmıyor)
- `kitap_bilgisi_cek_policy()`: Policy-driven bilgi çekme (YENİ - önerilen)
- `_wikipedia_cek()`: Wikipedia API'den bilgi çeker
- `_wikipedia_parse()`: Wikipedia verisini parse eder
- `_google_books_cek()`: Google Books API'den bilgi çeker
- `_google_books_parse()`: Google Books verisini parse eder
- `_open_library_cek()`: Open Library API'den bilgi çeker
- `_open_library_parse()`: Open Library verisini parse eder
- `_groq_ai_cek()`: Groq AI API'den bilgi çeker (birincil AI kaynak, optimize edilmiş prompt ile)
- `_huggingface_ai_cek()`: Hugging Face Inference API'den bilgi çeker (yedek AI kaynak)
- `_together_ai_cek()`: Together AI API'den bilgi çeker (alternatif yedek AI kaynak)
- `_collect_sources()`: Çoklu kaynaktan veri toplama (policy akışı için)

#### `field_policy.py` (YENİ - 2026):

- `FieldRule`: Alan bazlı kural dataclass'ı
- `build_rules()`: Tüm alanlar için kuralları oluşturur
- Her alan için kaynak öncelik sırası ve quality gate fonksiyonu tanımlanır

#### `quality_gates.py` (YENİ - 2026):

- `has_volume_marker()`: Volume marker detection
- `tr_translation_context()`: TR Wikipedia translation context detection
- `en_pub_context_present()`: EN Wikipedia publication context detection
- `_is_classic_book()`: Classic book detection
- `_detect_cyrillic_or_arabic()`: Cyrillic/Arabic/CJK character detection
- `_is_likely_original_language()`: Orijinal dil tespiti
- `gate_publication_year()`: Çıkış yılı için quality gate
- `gate_original_title()`: Orijinal ad için quality gate

#### `wikidata_client.py` (YENİ - 2026):

- `qid_from_wikipedia()`: Wikipedia sayfasından QID çözümleme (REST summary + MediaWiki pageprops fallback)
- `extract_fields()`: Wikidata entity'den alan çıkarma (P577, P1476, P1705, P1680, P1813, P495, P17)

#### `router.py` (YENİ - 2026):

- `ProviderState`: API provider durumu (available, cooldown, dead)
- `QuotaRouter`: API quota yönetimi ve backoff mekanizması
- Rate limit (429, 503) ve API key hataları (401, 403) yönetimi

#### `provenance.py` (YENİ - 2026):

- `set_field()`: Alan için provenance (kaynak, güven) bilgisi yazma
- `set_row_status()`: Satır seviyesinde metadata yazma (status, missing_fields, retry info, best_source, wikidata_qid)

#### `field_registry.py` (YENİ - 2026):

- `BASE_COLUMNS`: Temel Excel kolonları
- `PROVENANCE_FIELDS`: Provenance kolonları alan listesi
- `ROW_META_COLUMNS`: Satır seviyesinde metadata kolonları
- `standard_columns()`: Tüm standart kolonları döndürür
- `ensure_row_schema()`: Satır şemasını garanti eder

### Özel Özellikler

1. **Modüler Mimari (YENİ)**: Kod 7 ayrı modüle bölünmüştür, bakım ve genişletme kolaylaşmıştır
2. **Readonly Form Alanları (YENİ - 2024)**: Sadece Kitap Adı ve Yazar manuel yazılabilir, diğer alanlar otomatik doldurulur
3. **Kitap Temalı UI (YENİ - 2024)**: Kütüphane temalı renkler, Georgia fontu, düzenli layout
4. **Kısa Mesajlar (YENİ - 2024)**: 500+ kitap olsa bile mesajlar kısa ve okunabilir
5. **Kitap Temalı İkonlar (YENİ - 2024)**: Yan yana dikey kitaplar, kütüphane temalı, özelleştirilebilir shortcut'lar
6. **VBScript Başlatıcı (YENİ - 2024)**: Konsol penceresi görünmez, gerçek uygulama gibi açılır
7. **Checkbox Sistemi (YENİ - 2024)**: Her satırda ☐/☑ işareti ile seçim, başlık sütunundan tümünü seç/kaldır
8. **Toplu Silme (YENİ - 2024)**: Seçili kitapları toplu olarak silme
9. **Listeden Forma Yükleme (YENİ - 2024)**: Listeden kitaba çift tıklayarak forma yükleme
10. **Excel'den Yükleme Sonrası Otomatik Bilgi Doldurma (YENİ - 2024)**: 2 seçenek ile toplu veya manuel bilgi doldurma
11. **Excel Şablonu Basitleştirme (YENİ - 2024)**: Şablon sadece "Kitap Adı" ve "Yazar" sütunlarını içerir
12. **Excel Dosya Adı (YENİ - 2024)**: `Kutuphanem.xlsx` olarak değiştirildi
13. **Otomatik format güncelleme**: `ExcelHandler` modülü eski formatı algılayıp yeni formata çevirir
14. **Akıllı birleştirme**: `ListManager.toplu_ekle()` ile Excel'den yüklerken mevcut listeye ekler, üzerine yazmaz
15. **Tekrar kontrolü**: `ListManager.ekle()` otomatik tekrar kontrolü yapar
16. **Form kontrolü**: Excel oluştururken formda doldurulmuş ama eklenmemiş kitap varsa uyarır
17. **Progress bar**: `GUIWidgets` modülü ile bilgi çekme sırasında kullanıcıya geri bildirim verilir
18. **Thread kullanımı**: API çağrıları arka planda yapılır, GUI donmaz
19. **Hata yönetimi**: Her modülde detaylı hata mesajları ve console logları
20. **API key yönetimi**: `APIKeyManager` modülü ile dosyaya kaydedilir, otomatik yüklenir
21. **Latin transliterasyon**: Groq AI her zaman Latin harflerine çevirir
22. **Yıl formatı esnekliği**: `FormHandler` modülü tek yıl ("1869") veya aralık ("1865-1869") kabul eder
23. **Separation of Concerns**: Her modül kendi sorumluluğuna odaklanır
24. **Test Edilebilirlik**: Modüller bağımsız test edilebilir
25. **Yeniden Kullanılabilirlik**: Modüller başka projelerde kullanılabilir
26. **Çoklu AI API Desteği (YENİ - 2024)**: Groq AI (birincil), Hugging Face AI (yedek), Together AI (alternatif yedek)
27. **Token Tasarrufu (YENİ - 2024)**: Groq prompt'u optimize edilmiştir (~200-300 token, önceden ~400-600 token)
28. **Rate Limit Yönetimi (YENİ - 2024)**: Groq rate limit sonrası otomatik olarak Hugging Face AI'ye geçiş
29. **Anlatı Yılı Desteği (YENİ - 2024)**: Kitabın anlattığı olayların geçtiği dönem bilgisi eklendi
30. **Akıllı Fallback Sistemi (YENİ - 2024)**: Groq → Hugging Face → Together AI sıralı fallback mekanizması
31. **Policy-Driven Veri Çekme (YENİ - 2026)**: Alan bazlı kaynak öncelik ve validation kuralları (`field_policy.py`)
32. **Quality Gates (YENİ - 2026)**: Veri kalitesi kontrolü ve "yanlış bağlam" önleme (`quality_gates.py`)
33. **Wikidata Entegrasyonu (YENİ - 2026)**: QID çözümleme ve yapılandırılmış veri çekme (`wikidata_client.py`)
34. **API Quota Yönetimi (YENİ - 2026)**: Router/backoff mekanizması ile rate limit yönetimi (`router.py`)
35. **Provenance Tracking (YENİ - 2026)**: Her alan için kaynak ve güven bilgisi (`provenance.py`)
36. **Excel Meta Kolonları (YENİ - 2026)**: Status, missing_fields, retry info, best_source, wikidata_qid
37. **Checkpoint Mekanizması (YENİ - 2026)**: Toplu işlemlerde her 50 kayıtta otomatik save
38. **Quality Gates Unit Testleri (YENİ - 2026)**: 37 test, tümü geçti (`test_quality_gates.py`)
39. **Regression Testler (YENİ - 2026)**: End-to-end senaryolar için testler (`test_regression.py`)

## Kullanım Senaryoları

### Senaryo 1: Manuel Kitap Ekleme
1. Programı aç
2. Formu doldur (Kitap Adı ve Yazar zorunlu)
3. "Listeye Ekle" butonuna tıkla
4. İstediğin kadar kitap ekle
5. "Excel Dosyası Oluştur" ile kaydet

### Senaryo 2: Otomatik Bilgi Doldurma (YENİ)
1. Programı aç
2. Kitap Adı ve Yazar gir
3. "Bilgileri Otomatik Doldur" butonuna tıkla
4. Progress bar'da bilgi çekme durumunu izle
5. Form otomatik doldurulur
6. İstersen düzenle
7. "Listeye Ekle" ile kaydet

### Senaryo 3: Groq API Key ile Gelişmiş Otomatik Doldurma
1. "Groq API Key" butonuna tıkla
2. https://console.groq.com adresinden ücretsiz API key al
3. API key'i gir (bir kez, dosyaya kaydedilir)
4. Kitap Adı ve Yazar gir
5. "Bilgileri Otomatik Doldur" butonuna tıkla
6. Groq AI çok daha doğru bilgiler sağlar
7. Form otomatik doldurulur

### Senaryo 4: Excel Şablonu ile Toplu Ekleme
1. "Excel Şablonu Oluştur" ile şablon oluştur (sadece "Kitap Adı" ve "Yazar" sütunları)
2. Excel'de şablonu doldur
3. "Excel'den Yükle" ile programa yükle
4. Otomatik bilgi doldurma seçeneği sunulur:
   - **Her kitap için toplu çağrı yap**: Tüm kitaplar için otomatik bilgi doldurma
   - **Manuel çift tıklayarak forma yükle**: Listeden kitaba çift tıklayıp "Bilgileri Otomatik Doldur" butonuna tıklayın
5. "Excel Dosyası Oluştur" ile kaydet (`Kutuphanem.xlsx`)

### Senaryo 5: Mevcut Excel'i Güncelleme
1. Program açıldığında mevcut Excel (`Kutuphanem.xlsx`) otomatik yüklenir
2. Yeni kitaplar eklenebilir (manuel veya otomatik)
3. "Excel Dosyası Oluştur" ile güncellenmiş liste kaydedilir

### Senaryo 6: Checkbox ile Toplu İşlemler (YENİ - 2024)
1. Listeden kitapları seçmek için "Seç" sütunundaki ☐ işaretine tıklayın → ☑ olur
2. Tümünü seçmek için başlık sütunundaki ☐ işaretine tıklayın
3. Tümünü kaldırmak için başlık sütunundaki ☑ işaretine veya "☐ Tümünü Kaldır" butonuna tıklayın
4. Seçili kitapları silmek için "🗑️ Seçili Kitapları Sil" butonuna tıklayın

### Senaryo 7: Listeden Forma Yükleme (YENİ - 2024)
1. Listeden bir kitaba çift tıklayın (kitap forma yüklenir)
2. "Bilgileri Otomatik Doldur" butonuna tıklayarak eksik bilgileri doldurabilirsiniz
3. İsterseniz düzenleyip "Listeye Ekle" ile kaydedebilirsiniz

## Güncelleme Yaparken Checklist

### ⚠️ Her Güncellemede Kontrol Edilmesi Gerekenler

#### 1. Excel Formatı Değiştirildiyse
- [ ] `excel_handler.py` içindeki `STANDART_SUTUN_SIRASI` güncellendi mi?
- [ ] `_format_guncelle()` fonksiyonu güncellendi mi? (eski formatı yeni formata çevir)
- [ ] `gui_widgets.py` içindeki Treeview sütunları güncellendi mi?
- [ ] `form_handler.py` içindeki form alanları güncellendi mi?
- [ ] `HAND_OFF_DOKUMANTASYON.md` dosyası güncellendi mi?

#### 2. Readonly Widget Eklendi/Değiştirildiyse
- [ ] `form_handler.py` içindeki `doldur()` fonksiyonuna eklendi mi?
- [ ] `form_handler.py` içindeki `temizle()` fonksiyonuna eklendi mi?
- [ ] State yönetimi doğru yapıldı mı? (normal → işlem → readonly)
- [ ] `gui_widgets.py` içindeki widget oluşturma kısmı güncellendi mi?

#### 3. Checkbox Sistemi Değiştirildiyse
- [ ] `gui_widgets.py` içindeki `listeyi_guncelle()` fonksiyonu güncellendi mi?
- [ ] `checkbox_vars` dict'i doğru yönetiliyor mu?
- [ ] `_on_tree_click()` fonksiyonu güncellendi mi?
- [ ] `_baslik_checkbox_toggle()` fonksiyonu güncellendi mi?
- [ ] Treeview selection güncellemesi yapılıyor mu?

#### 4. Thread Kullanıldıysa
- [ ] GUI güncellemeleri `root.after()` ile yapılıyor mu?
- [ ] Exception handling var mı?
- [ ] Hatalar GUI'ye bildiriliyor mu?
- [ ] Progress bar güncellemeleri thread-safe mi?

#### 5. Yeni Modül Eklendiyse
- [ ] Modül `kitap_listesi_gui.py` içinde import edildi mi?
- [ ] Modül `__init__()` içinde başlatıldı mı?
- [ ] Modül callback'leri `gui_olustur()` içinde bağlandı mı?
- [ ] `HAND_OFF_DOKUMANTASYON.md` dosyasına eklendi mi?

#### 6. Yeni Fonksiyon Eklendiyse
- [ ] Fonksiyon docstring'i var mı?
- [ ] Fonksiyon `HAND_OFF_DOKUMANTASYON.md` dosyasına eklendi mi?
- [ ] Fonksiyon hata yönetimi yapıyor mu?

#### 7. Dosya Adı/Formatı Değiştirildiyse
- [ ] Tüm referanslar güncellendi mi?
- [ ] `HAND_OFF_DOKUMANTASYON.md` dosyası güncellendi mi?
- [ ] `README.md` dosyası güncellendi mi?

#### 8. UI Değişikliği Yapıldıysa
- [ ] `gui_widgets.py` içinde güncellendi mi?
- [ ] Callback'ler `kitap_listesi_gui.py` içinde bağlandı mı?
- [ ] Renkler ve fontlar tutarlı mı?

### Güncelleme Sonrası Test Listesi

1. **Temel Fonksiyonlar:**
   - [ ] Program açılıyor mu?
   - [ ] Excel dosyası yükleniyor mu?
   - [ ] Kitap ekleniyor mu?
   - [ ] Kitap siliniyor mu?

2. **Checkbox Sistemi:**
   - [ ] Checkbox'lar çalışıyor mu?
   - [ ] Tümünü seç/kaldır çalışıyor mu?
   - [ ] Toplu silme çalışıyor mu?

3. **Otomatik Bilgi Doldurma:**
   - [ ] "Bilgileri Otomatik Doldur" çalışıyor mu?
   - [ ] Excel'den yükleme sonrası seçenek dialog'u çalışıyor mu?
   - [ ] Toplu bilgi doldurma çalışıyor mu?

4. **Excel İşlemleri:**
   - [ ] Excel dosyası oluşturuluyor mu?
   - [ ] Excel şablonu oluşturuluyor mu?
   - [ ] Excel'den yükleme çalışıyor mu?

5. **Hata Yönetimi:**
   - [ ] Hata mesajları gösteriliyor mu?
   - [ ] Console'da log mesajları var mı?
   - [ ] Exception handling çalışıyor mu?

## Geliştirme Notları

### Gelecek İyileştirmeler
- Web araştırması entegrasyonu (otomatik kitap bilgisi çekme) ✅ **TAMAMLANDI**
- Modüler mimari refactoring ✅ **TAMAMLANDI** (2024)
- Policy-driven veri çekme sistemi ✅ **TAMAMLANDI** (2026)
- Quality gates ve "yanlış bağlam" önleme ✅ **TAMAMLANDI** (2026)
- Wikidata entegrasyonu ✅ **TAMAMLANDI** (2026)
- Excel meta kolonları ve provenance tracking ✅ **TAMAMLANDI** (2026)
- Quality gates unit testleri ✅ **TAMAMLANDI** (2026, 37 test)
- Router/backoff entegrasyonu ⚠️ **KISMEN TAMAMLANDI** (2026, GUI entegrasyonu kısmen)
- Status/checkpoint mekanizması ⚠️ **KISMEN TAMAMLANDI** (2026, checkpoint eklendi, status yazımı kısmen)
- Veritabanı desteği
- Çoklu dil desteği
- İleri filtreleme ve arama
- Kitap kapak resmi çekme
- ISBN desteği
- Regression test (War and Peace senaryosu) ✅ **TAMAMLANDI**

### Bilinen Sınırlamalar
- Sadece .xlsx formatı desteklenir
- Excel dosyası açıkken kaydetme başarısız olabilir
- Büyük listelerde performans sorunları olabilir
- API çağrıları internet bağlantısı gerektirir
- Groq API key olmadan bazı bilgiler eksik kalabilir

### Hata Yönetimi
- Dosya izinleri kontrol edilir
- Excel dosyası açıkken uyarı verilir
- Zorunlu alanlar kontrol edilir
- Format hatalarında açıklayıcı mesajlar gösterilir
- API hatalarında detaylı console logları
- Network timeout'ları yönetilir
- API key hatalarında kullanıcıya bilgi verilir

### API Rate Limits ve Kullanım
- **Wikipedia API**: Rate limit yok (ancak aşırı kullanımda IP engellenebilir)
- **Google Books API**: Günlük 1000 istek (ücretsiz)
- **Open Library API**: Rate limit yok
- **Groq API**: 
  - Ücretsiz tier: 100,000 token/gün (her çağrı ~200-300 token, optimize edilmiş prompt ile)
  - Rate limit (429) hatası durumunda otomatik olarak Hugging Face AI'ye geçilir
  - Token tasarrufu sayesinde 2x daha fazla kitap işlenebilir
- **Hugging Face Inference API**:
  - API key olmadan: ~30 istek/dakika
  - API key ile: Daha yüksek limitler
  - Groq rate limit sonrası veya eksik bilgiler için yedek olarak kullanılır
- **Together AI API**:
  - Ücretsiz tier mevcuttur
  - Hugging Face başarısız olduğunda alternatif yedek olarak kullanılır

### Debug ve Loglama
- Console'da detaylı log mesajları
- API çağrıları loglanır
- Hata mesajları traceback ile gösterilir
- API key durumu loglanır
- Bilgi çekme adımları loglanır

## Çalıştırma

### Geliştirme Ortamı
```bash
python kitap_listesi_gui.py
```

### Kullanıcı için
```bash
PROGRAMI_AC.vbs  # Çift tıkla (önerilen - konsol penceresi görünmez) ⭐
# veya
PROGRAMI_AC.bat  # Çift tıkla (alternatif - konsol penceresi görünür)
```

### Kitap Temalı İkon ve Shortcut Oluşturma (İsteğe Bağlı)
```bash
ikon_ve_shortcut_olustur.bat  # Çift tıkla
# - Kitap temalı ikon oluşturur
# - Windows shortcut'ları oluşturur
# - Shortcut adını özelleştirebilirsiniz
# - Hem program klasörüne hem masaüstüne oluşturur
```

### Windows İkon Cache Temizleme (İkon Değişmiyorsa)
```bash
ikon_cache_temizle.bat  # Çift tıkla (yönetici olarak önerilir)
# - Windows'un ikon cache'ini temizler
# - Explorer'ı yeniden başlatır
# - Yeni ikonlar görünür hale gelir
```

### EXE Oluşturma
```bash
exe_olustur.bat  # Çift tıkla
```

## Bağımlılıklar

### Temel Bağımlılıklar (Zorunlu)
```
pandas>=2.0.0
openpyxl>=3.1.0
requests>=2.31.0
```

### İsteğe Bağlı Bağımlılıklar (İkon ve Shortcut için)
```
Pillow>=10.0.0      # İkon oluşturma için
pywin32>=306        # Windows shortcut oluşturma için
```

Kurulum:
```bash
# Temel bağımlılıklar
pip install pandas openpyxl requests

# İkon ve shortcut için (isteğe bağlı)
pip install Pillow pywin32
```

veya

```bash
pip install -r requirements.txt
```

## API Key Kurulumu

### Groq AI API Key (Önerilen - Birincil AI Kaynak)
1. https://console.groq.com adresine git
2. Ücretsiz hesap oluştur
3. API Keys bölümünden yeni bir key oluştur
4. Programda "Groq API Key" butonuna tıkla
5. Key'i yapıştır
6. Key otomatik olarak `groq_api_key.txt` dosyasına kaydedilir
7. Bir daha girmenize gerek kalmaz
8. **Rate Limit**: 100,000 token/gün (ücretsiz tier)
9. Rate limit sonrası otomatik olarak Hugging Face AI'ye geçilir

### Hugging Face API Key (İsteğe Bağlı - Yedek AI Kaynak)
1. https://huggingface.co/settings/tokens adresine git
2. Ücretsiz hesap oluştur
3. Yeni token oluştur (read izni yeterli)
4. Token'ı `huggingface_api_key.txt` dosyasına kaydedin (program klasöründe)
5. Program otomatik olarak yükler
6. **Rate Limit**: API key olmadan ~30 istek/dakika, API key ile daha yüksek limitler
7. Groq rate limit sonrası veya eksik bilgiler için yedek olarak kullanılır

### Together AI API Key (İsteğe Bağlı - Alternatif Yedek AI Kaynak)
1. https://api.together.xyz adresine git
2. Ücretsiz hesap oluştur
3. API key alın
4. Environment variable olarak ayarlayın: `TOGETHER_API_KEY=your_key_here`
5. Hugging Face başarısız olduğunda alternatif yedek olarak kullanılır

## Özet

Bu uygulama, kitap bilgilerini yönetmek ve Excel formatında saklamak için tasarlanmış bir masaüstü uygulamasıdır. Tkinter GUI, pandas veri işleme, openpyxl Excel entegrasyonu ve çoklu API entegrasyonları kullanır. 

**Modüler Mimari (YENİ - 2024, Genişletilmiş - 2026):**
Program artık 13 ayrı modüle bölünmüştür:
- `kitap_listesi_gui.py` (~1089 satır): Ana koordinasyon dosyası
- `excel_handler.py` (~229 satır): Excel işlemleri
- `api_key_manager.py` (~108 satır): API key yönetimi
- `form_handler.py` (~229 satır): Form işlemleri (readonly widget desteği, kitap yükleme)
- `list_manager.py` (~157 satır): Liste yönetimi
- `gui_widgets.py` (~375 satır): GUI widget'ları (kitap temalı tasarım, checkbox sistemi)
- `kitap_bilgisi_cekici.py` (~1089 satır): API entegrasyonu (policy-driven)
- `field_policy.py` (YENİ - 2026): Alan bazlı kaynak öncelik ve validation
- `quality_gates.py` (YENİ - 2026): Veri kalitesi kontrolü ve "yanlış bağlam" önleme
- `wikidata_client.py` (YENİ - 2026): Wikidata QID çözümleme ve alan çıkarma
- `router.py` (YENİ - 2026): API quota yönetimi ve backoff mekanizması
- `provenance.py` (YENİ - 2026): Provenance (kaynak, güven) bilgisi yazma
- `field_registry.py` (YENİ - 2026): Excel şema kolon isimlerini merkezi yönetim

**Ana Özellikler:**
- ✅ Modüler mimari ile bakım ve genişletme kolaylığı
- ✅ Readonly form alanları (sadece Kitap Adı ve Yazar yazılabilir)
- ✅ Kitap temalı UI tasarımı (kütüphane renkleri, Georgia fontu)
- ✅ Kısa ve kullanıcı dostu mesajlar (500+ kitap olsa bile)
- ✅ Kitap temalı ikon sistemi (yan yana dikey kitaplar)
- ✅ VBScript başlatıcı (konsol penceresi görünmez)
- ✅ Checkbox sistemi (tek tek seçim, tümünü seç/kaldır, toplu silme)
- ✅ Listeden forma yükleme (çift tıklama)
- ✅ Excel'den yükleme sonrası otomatik bilgi doldurma (2 seçenek)
- ✅ Excel şablonu basitleştirme (sadece 2 sütun)
- ✅ Excel dosya adı: `Kutuphanem.xlsx`
- ✅ Otomatik bilgi çekme (Wikipedia, Google Books, Open Library, Groq AI, Hugging Face AI, Together AI)
- ✅ Groq AI entegrasyonu (ücretsiz, çok doğru sonuçlar, optimize edilmiş prompt ile token tasarrufu)
- ✅ Hugging Face AI entegrasyonu (yedek AI kaynak, Groq rate limit sonrası otomatik geçiş)
- ✅ Together AI entegrasyonu (alternatif yedek AI kaynak)
- ✅ API key yönetimi (Groq ve Hugging Face için dosyaya kaydetme, otomatik yükleme)
- ✅ Rate limit yönetimi (Groq rate limit sonrası otomatik fallback)
- ✅ Anlatı Yılı desteği (kitabın anlattığı olayların geçtiği dönem)
- ✅ Progress bar ve durum göstergeleri
- ✅ Latin harflerine otomatik transliterasyon
- ✅ Esnek yıl formatı (tek yıl veya aralık)
- ✅ Separation of Concerns prensibi ile temiz kod yapısı
- ✅ Policy-driven veri çekme sistemi (YENİ - 2026): Alan bazlı kaynak öncelik ve validation
- ✅ Quality gates (YENİ - 2026): Veri kalitesi kontrolü ve "yanlış bağlam" önleme
- ✅ Wikidata entegrasyonu (YENİ - 2026): QID çözümleme ve yapılandırılmış veri çekme
- ✅ API quota yönetimi (YENİ - 2026): Router/backoff mekanizması ile rate limit yönetimi
- ✅ Provenance tracking (YENİ - 2026): Her alan için kaynak ve güven bilgisi
- ✅ Excel meta kolonları (YENİ - 2026): Status, missing_fields, retry info, best_source, wikidata_qid
- ✅ Checkpoint mekanizması (YENİ - 2026): Toplu işlemlerde her 50 kayıtta otomatik save
- ✅ Quality gates unit testleri (YENİ - 2026): 37 test, tümü geçti

**Kod İstatistikleri:**
- Önceki durum: 1 dosya, 977 satır
- Yeni durum: 13 modül + 1 ana dosya, ~4000+ satır (toplam)
- Ana dosya: Genişletilmiş özelliklerle ~1089 satır
- API modülü: Policy-driven çoklu AI API desteği ile ~1089 satır
- Her modül bağımsız ve test edilebilir
- İkon ve shortcut sistemleri eklendi
- Çoklu AI API entegrasyonu (Groq, Hugging Face, Together AI)
- Policy-driven veri çekme sistemi (field_policy, quality_gates, wikidata, router, provenance)
- Quality gates unit testleri (37 test, tümü geçti)

Kullanıcılar formdan kitap ekleyebilir, otomatik bilgi çekme ile formu doldurulabilir, Excel'den toplu yükleme yapabilir ve tüm listeyi Excel dosyası olarak kaydedebilir.
