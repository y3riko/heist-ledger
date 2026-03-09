#!/bin/bash
# Build 10 CHAMBERS — THE HEIST LEDGER v1 for Linux
set -e
echo "Building for Linux..."

pip install -r requirements.txt --quiet

pyinstaller \
  --onefile \
  --windowed \
  --name "HeistLedger" \
  --add-data "assets:assets" \
  --hidden-import "reportlab" \
  --hidden-import "reportlab.platypus" \
  --hidden-import "reportlab.lib.pagesizes" \
  main.py

echo ""
echo "Done! Binary at: dist/HeistLedger"
