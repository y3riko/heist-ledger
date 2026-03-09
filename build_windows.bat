@echo off
echo Building 10 CHAMBERS - THE HEIST LEDGER v1 for Windows...
pip install -r requirements.txt

pyinstaller ^
  --onefile ^
  --windowed ^
  --name "HeistLedger" ^
  --add-data "assets;assets" ^
  --hidden-import reportlab ^
  --hidden-import reportlab.platypus ^
  --hidden-import reportlab.lib.pagesizes ^
  --icon assets\logo_badge.png ^
  main.py

echo.
echo Done! Executable at: dist\HeistLedger.exe
pause
