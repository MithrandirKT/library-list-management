@echo off
chcp 65001 >nul
title Kitap Temali Ikon Olusturucu
echo.
echo ========================================
echo   Kitap Temali Ikon Olusturucu
echo ========================================
echo.

REM Pillow kontrolu
python -c "import PIL" 2>nul
if errorlevel 1 (
    echo Pillow yukleniyor...
    pip install Pillow
    echo.
)

REM Eski ikon dosyalarini sil (yeniden olusturmak icin)
if exist kitap_ikon.ico del kitap_ikon.ico
if exist kitap_ikon.png del kitap_ikon.png

REM Ikon olustur
echo Ikon olusturuluyor...
cd /d "%~dp0"
python ikon_olustur.py
cd /d "%~dp0\.."
echo.

REM pywin32 kontrolu
python -c "import win32com.client" 2>nul
if errorlevel 1 (
    echo pywin32 yukleniyor...
    pip install pywin32
    echo.
)

REM Shortcut adi sor
echo.
echo ========================================
echo   Shortcut Adi Belirleme
echo ========================================
echo.
set /p SHORTCUT_ADI="Shortcut adini girin (Enter'a basarsaniz 'Kitap Listesi' kullanilir): "
if "%SHORTCUT_ADI%"=="" set SHORTCUT_ADI=Kitap Listesi
echo.
echo Shortcut adi: %SHORTCUT_ADI%
echo.

REM Eski shortcut'lari sil (yeniden olusturmak icin)
if exist "Kitap Listesi.lnk" del "Kitap Listesi.lnk"
if exist "%SHORTCUT_ADI%.lnk" del "%SHORTCUT_ADI%.lnk"
if exist "Kitap Listesi (Batch).lnk" del "Kitap Listesi (Batch).lnk"

REM Shortcut olustur
echo Shortcut'lar olusturuluyor...
python shortcut_olustur.py "%SHORTCUT_ADI%"
echo.

REM Windows ikon cache'ini yenilemek icin ipucu
echo.
echo ========================================
echo   Ikon Guncelleme Ipuclari
echo ========================================
echo.
echo Eger ikon degismedi ise:
echo 1. Shortcut'a sag tiklayin
echo 2. "Ozellikler" secin
echo 3. "Degistir" butonuna tiklayin
echo 4. Yeni ikon dosyasini secin: icons\kitap_ikon.ico
echo.
echo VEYA
echo.
echo Windows Explorer'i yeniden baslatin (F5)
echo.

echo.
echo ========================================
echo   Tamamlandi!
echo ========================================
echo.
echo Shortcut'lar olusturuldu:
echo   - Program klasorunde (bu klasor)
echo   - Masaustunde (varsa)
echo.
echo Program klasorunde "%SHORTCUT_ADI%.lnk" dosyasini gorebilirsiniz.
echo.
pause
