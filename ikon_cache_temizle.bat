@echo off
chcp 65001 >nul
title Windows Ikon Cache Temizleme
echo.
echo ========================================
echo   Windows Ikon Cache Temizleme
echo ========================================
echo.
echo Bu script Windows'un ikon cache'ini temizler.
echo Boylece yeni ikonlar hemen gorunur.
echo.
echo Dikkat: Yonetici yetkisi gerekebilir!
echo.
pause

REM Windows ikon cache dosyalarini sil
echo Ikon cache temizleniyor...
del /a /q "%LOCALAPPDATA%\IconCache.db" 2>nul
del /a /q "%LOCALAPPDATA%\Microsoft\Windows\Explorer\iconcache*.db" 2>nul

REM Explorer'i yeniden baslat
echo.
echo Explorer yeniden baslatiliyor...
taskkill /f /im explorer.exe >nul 2>&1
start explorer.exe

echo.
echo ✅ Ikon cache temizlendi!
echo.
echo Shortcut'lari kontrol edin. Ikonlar guncellenmis olmali.
echo.
pause
