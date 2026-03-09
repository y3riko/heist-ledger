#!/bin/bash
# Build 10 CHAMBERS — THE HEIST LEDGER v1 for Windows (.exe) using Wine on Linux
set -e
echo "Building for Windows via Wine..."

wine python -m pip install PyQt6 reportlab pyinstaller --quiet

wine pyinstaller \
  --onefile \
  --windowed \
  --name "HeistLedger" \
  --add-data "assets;assets" \
  --collect-all PyQt6 \
  --hidden-import reportlab \
  --hidden-import reportlab.platypus \
  --hidden-import reportlab.lib.pagesizes \
  main.py

echo ""
echo "Done! Windows exe at: dist/HeistLedger.exe"
