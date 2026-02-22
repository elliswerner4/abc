#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "=== Prologis Racking BOM Tool ==="
echo ""

# Check Python deps
DEPS="fastapi uvicorn python-multipart openpyxl pdf2image Pillow httpx python-dotenv"
MISSING=""
for pkg in $DEPS; do
  python3 -c "import importlib; importlib.import_module('${pkg//-/_}')" 2>/dev/null || MISSING="$MISSING $pkg"
done

if [ -n "$MISSING" ]; then
  echo "Installing missing Python packages:$MISSING"
  python3 -m pip install --break-system-packages $MISSING
  echo ""
fi

# Check poppler
if ! command -v pdftoppm &>/dev/null; then
  echo "ERROR: poppler-utils not installed. Run: sudo apt install poppler-utils"
  exit 1
fi

# Check .env
if [ ! -f config/.env ]; then
  echo "WARNING: config/.env not found. Create it with OPENAI_API_KEY=sk-..."
fi

echo "Starting server on http://localhost:8080"
echo "Press Ctrl+C to stop."
echo ""

python3 -m uvicorn server:app --host 0.0.0.0 --port 8080 --reload
