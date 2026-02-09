@echo off
echo ========================================
echo GitHub'a Yükleme Scripti
echo ========================================
echo.
echo 1. GitHub'da repository oluşturduğunuzdan emin olun
echo 2. Repository URL'ini aşağıya girin
echo.
set /p REPO_URL="GitHub Repository URL'ini girin (örn: https://github.com/kullaniciadi/kitap-listesi-yonetim.git): "
echo.
echo Repository'ye bağlanılıyor...
git remote add origin %REPO_URL%
echo.
echo Ana branch'i 'main' olarak ayarlanıyor...
git branch -M main
echo.
echo Dosyalar GitHub'a yükleniyor...
git push -u origin main
echo.
echo ========================================
echo Tamamlandı!
echo ========================================
echo.
echo Repository'nizi şu adresten görebilirsiniz:
echo %REPO_URL%
echo.
pause
