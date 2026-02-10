@echo off
chcp 65001 >nul
echo ========================================
echo   GitHub Otomatik Push
echo ========================================
echo.
echo Bu script tum degisiklikleri GitHub'a push edecek.
echo.
echo 10 saniye icinde islem baslayacak...
echo Iptal etmek icin pencereyi kapatin (X butonu)
echo.

timeout /t 10 /nobreak >nul

echo.
echo [1/4] Git durumu kontrol ediliyor...
git status

echo.
echo [2/4] Tum degisiklikler ekleniyor...
git add -A

echo.
echo [3/4] Commit yapiliyor...
set COMMIT_MSG=Otomatik guncelleme: %date% %time%
git commit -m "%COMMIT_MSG%"

if %errorlevel% neq 0 (
    echo.
    echo UYARI: Commit yapilamadi. Yeni degisiklik yok olabilir.
    echo Devam ediliyor...
)

echo.
echo [4/4] GitHub'a push ediliyor...
git push

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   BASARILI! Tum degisiklikler push edildi.
    echo ========================================
) else (
    echo.
    echo ========================================
    echo   HATA! Push basarisiz oldu.
    echo ========================================
)

echo.
echo Pencereyi kapatmak icin bir tusa basin...
pause >nul
