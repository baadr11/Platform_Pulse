#!/bin/bash
set -e

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║     نبض المنصات | Platform Pulse — Setup      ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# ── Python version check ──────────────────────────
PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
    echo "❌  Python 3.9+ is required but not found."
    exit 1
fi
PY_VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
echo "✓  Python $PY_VERSION"

# ── Create virtual environment ────────────────────
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv venv
fi

if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

echo "✓  Virtual environment ready"

# ── Upgrade pip ───────────────────────────────────
pip install --upgrade pip --quiet

# ── Install dependencies ──────────────────────────
echo "Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt --quiet
echo "✓  Dependencies installed"

# ── Create directory structure ────────────────────
for dir in \
    data/raw \
    data/processed \
    data/sample \
    data/logs \
    config \
    logs; do
    mkdir -p "$dir"
done
echo "✓  Directory structure created"

# ── Copy .env.example ────────────────────────────
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✓  .env created from .env.example"
        echo "⚠️  Edit .env with your API credentials before running."
    fi
fi

# ── Verify Streamlit config ───────────────────────
if [ ! -f ".streamlit/config.toml" ]; then
    mkdir -p .streamlit
    cat > .streamlit/config.toml << 'TOML'
[server]
port = 8501
headless = true
enableCORS = false
enableXsrfProtection = true

[theme]
base = "dark"
primaryColor = "#00c896"
backgroundColor = "#0a0f1e"
secondaryBackgroundColor = "#0d1526"
textColor = "#e2e8f0"
font = "sans serif"

[browser]
gatherUsageStats = false
TOML
    echo "✓  Streamlit config created"
fi

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║   ✅  Setup complete! Run: bash run.sh         ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
