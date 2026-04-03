#!/bin/bash

set -e

if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate || { echo "venv not found. Run setup.sh first."; exit 1; }
else
    source venv/bin/activate || { echo "venv not found. Run setup.sh first."; exit 1; }
fi

echo "[1/4] Collecting data from all sources..."
python -m src.collectors.run_all_collectors
echo ""

echo "[2/4] Cleaning and normalizing data..."
python -m src.processing.cleaner
python -m src.processing.normalizer
python -m src.processing.validator
echo ""

echo "[3/4] Running analytical models..."
python -m run_models
echo ""

echo "[4/4] Starting dashboard..."
echo ""
echo "Dashboard running at: http://localhost:8501"
echo ""

streamlit run src/dashboard/app.py --server.port 8501
