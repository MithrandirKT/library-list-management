@echo off
echo Kitap Listesi GUI - EXE Dosyasi Olusturuluyor...
echo.

REM PyInstaller yuklu mu kontrol et
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller yukleniyor...
    pip install pyinstaller
)

echo.
echo EXE dosyasi olusturuluyor...
cd /d "%~dp0\.."
pyinstaller --onefile --windowed --name "KitapListesi" --icon=icons\kitap_ikon.ico --add-data "modules;modules" --add-data "data;data" --add-data "icons;icons" kitap_listesi_gui.py

echo.
echo Tamamlandi! EXE dosyasi 'dist' klasorunde bulunuyor.
pause
