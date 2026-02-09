@echo off
chcp 65001 >nul
echo ========================================
echo GitHub Repository Guncelleme
echo ========================================
echo.
echo Repository: https://github.com/MithrandirKT/library-list-management
echo.
echo Yeni degisiklikleri GitHub'a yuklemek icin...
echo.
pause

REM Yeni dosyaları ekle
git add .

REM Commit yap
set /p COMMIT_MSG="Commit mesaji: "
if "%COMMIT_MSG%"=="" (
    set COMMIT_MSG=Guncelleme
)
git commit -m "%COMMIT_MSG%"

REM GitHub'a push
git push origin main

echo.
echo ========================================
echo Tamamlandi!
echo ========================================
echo.
echo Repository: https://github.com/MithrandirKT/library-list-management
echo.
pause
