@echo off
chcp 65001 >nul
echo ========================================
echo GitHub Repository Guncelleme
echo ========================================
echo.
echo Repository: https://github.com/MithrandirKT/library-list-management
echo.
echo Local'deki duzeltilmis commit'ler GitHub'a yuklenecek.
echo.
echo DURUM:
echo - Local: Commit mesajlari duzeltildi (Turkce karakterler duzgun)
echo - Remote: Eski commit'ler var (Turkce karakterler bozuk)
echo.
echo Force push yapilacak (commit gecmisi degistirilecek).
echo.
pause

REM Yeni dosyaları ekle (varsa)
git add .

REM Commit yap (eğer değişiklik varsa)
git status | findstr /C:"Changes to be committed" >nul
if %errorlevel% == 0 (
    echo.
    echo Yeni degisiklikler commit ediliyor...
    git commit -m "Git sorunları çözüm scriptleri eklendi"
)

REM GitHub'a force push
echo.
echo GitHub'a force push yapiliyor...
git push -f origin main

echo.
echo ========================================
echo Tamamlandi!
echo ========================================
echo.
echo Repository: https://github.com/MithrandirKT/library-list-management
echo.
echo NOT: Ilk commit mesaji hala bozuk. Duzeltmek icin:
echo COMMIT_MESAJLARI_DUZELT_VE_PUSH.bat dosyasini calistirin.
echo.
pause
