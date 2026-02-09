@echo off
chcp 65001 >nul
echo ========================================
echo Commit Mesajlarini Duzeltme ve GitHub'a Push
echo ========================================
echo.
echo Repository: https://github.com/MithrandirKT/library-list-management
echo.
echo Ilk commit mesajini duzeltmek icin interactive rebase kullanilacak.
echo.
echo ADIMLAR:
echo 1. Notepad acilacak
echo 2. Ilk satirdaki "pick" kelimesini "reword" olarak degistirin
echo 3. Dosyayi kaydedin ve kapatin
echo 4. Yeni bir Notepad penceresi acilacak
echo 5. Commit mesajini duzeltin: "Ilk commit: Kitap Listesi Yonetim Programi"
echo 6. Dosyayi kaydedin ve kapatin
echo.
pause

REM İlk commit'i düzeltmek için rebase
git rebase -i --root

echo.
echo ========================================
echo Commit mesajlari duzeltildi!
echo ========================================
echo.
echo GitHub'a force push yapiliyor...
echo.
git push -f origin main

echo.
echo ========================================
echo Tamamlandi!
echo ========================================
echo.
echo Repository'nizi kontrol edin:
echo https://github.com/MithrandirKT/library-list-management
echo.
pause
