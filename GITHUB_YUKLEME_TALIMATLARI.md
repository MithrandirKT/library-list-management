# 🚀 GitHub'a Yükleme Talimatları

## Adım 1: GitHub'da Repository Oluşturun

1. **GitHub'a gidin**: https://github.com
2. **Giriş yapın** (hesabınız yoksa ücretsiz oluşturun)
3. **Yeni repository oluşturun**:
   - Sağ üstteki **"+"** butonuna tıklayın
   - **"New repository"** seçin
4. **Repository bilgilerini doldurun**:
   - **Repository name**: `kitap-listesi-yonetim` (veya istediğiniz isim)
   - **Description**: "Kitap koleksiyonu yönetim programı - Windows GUI uygulaması"
   - **Public** veya **Private** seçin (önerilen: Public)
   - ⚠️ **"Initialize this repository with a README"** seçeneğini **İŞARETLEMEYİN** (zaten README.md dosyamız var)
5. **"Create repository"** butonuna tıklayın

## Adım 2: Repository URL'ini Kopyalayın

Repository oluşturulduktan sonra GitHub size bir URL gösterecek:
```
https://github.com/KULLANICI_ADINIZ/kitap-listesi-yonetim.git
```
Bu URL'yi kopyalayın.

## Adım 3: Projeyi GitHub'a Yükleyin

### Yöntem 1: Otomatik Script (Önerilen)

1. `GITHUB_YUKLEME.bat` dosyasına çift tıklayın
2. Repository URL'ini yapıştırın
3. Enter'a basın
4. İşlem tamamlanacak!

### Yöntem 2: Manuel Komutlar

PowerShell veya Command Prompt'ta şu komutları çalıştırın:

```bash
# 1. GitHub repository URL'ini ekleyin (KULLANICI_ADINIZ ve REPO_ADI kısımlarını değiştirin)
git remote add origin https://github.com/KULLANICI_ADINIZ/REPO_ADI.git

# 2. Ana branch'i 'main' olarak ayarlayın
git branch -M main

# 3. Dosyaları GitHub'a yükleyin
git push -u origin main
```

**Örnek:**
```bash
git remote add origin https://github.com/ahmet/kitap-listesi-yonetim.git
git branch -M main
git push -u origin main
```

## Adım 4: Doğrulama

1. GitHub'da repository sayfanıza gidin
2. Tüm dosyaların yüklendiğini kontrol edin
3. README.md dosyasının düzgün göründüğünü kontrol edin

## ✅ Tamamlandı!

Artık projeniz GitHub'da! Diğer geliştiricilerle paylaşabilir, issue açabilir, pull request alabilirsiniz.

## 🔄 Sonraki Güncellemeler İçin

Projede değişiklik yaptıktan sonra GitHub'a yüklemek için:

```bash
git add .
git commit -m "Değişiklik açıklaması"
git push
```

## 📝 Önemli Notlar

- ⚠️ **API Key dosyaları `.gitignore`'da**: `groq_api_key.txt` ve `huggingface_api_key.txt` dosyaları GitHub'a yüklenmez (güvenlik için)
- ⚠️ **Excel dosyaları yüklenmez**: `Kutuphanem.xlsx` gibi kullanıcı verileri GitHub'a yüklenmez
- ✅ **Tüm kaynak kodlar yüklendi**: Python dosyaları, README, dokümantasyon vb.

## 🆘 Sorun Giderme

### "remote origin already exists" hatası:
```bash
git remote remove origin
git remote add origin https://github.com/KULLANICI_ADINIZ/REPO_ADI.git
```

### "Authentication failed" hatası:
- GitHub'da Personal Access Token oluşturun
- Token ile şifre yerine token kullanın
- Veya GitHub Desktop uygulamasını kullanın

### "Permission denied" hatası:
- Repository URL'inin doğru olduğundan emin olun
- GitHub hesabınızın repository'ye erişim izni olduğundan emin olun
