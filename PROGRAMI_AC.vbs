Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

REM Mevcut dizini al
scriptPath = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptPath

REM Python programini baslat (konsol penceresi gizli)
REM 0 = gizli pencere, False = bekleme yok
On Error Resume Next
WshShell.Run "python kitap_listesi_gui.py", 0, False

REM Hata durumunda kullaniciya bilgi ver
If Err.Number <> 0 Then
    WshShell.Popup "HATA: Program baslatilamadi!" & vbCrLf & vbCrLf & "Kontrol edin:" & vbCrLf & "1. Python yuklu mu? (python --version)" & vbCrLf & "2. Gerekli paketler yuklu mu? (pip install pandas openpyxl requests)" & vbCrLf & vbCrLf & "Hata: " & Err.Description, 0, "Kitap Listesi Excel Olusturucu", 48
End If
On Error Goto 0

Set WshShell = Nothing
Set fso = Nothing
