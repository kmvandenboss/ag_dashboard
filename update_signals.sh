#!/bin/bash
# Daily Signal Update Script
# Run this each morning after market open to update signals

echo ""
echo "==============================================================================="
echo " AG FUTURES SIGNAL UPDATE"
echo "==============================================================================="
echo ""

# Generate signals
echo "[1/3] Generating signals..."
python scripts/generate_signals_high_conviction.py

echo ""
echo "[2/3] Committing to git..."
git add signals/current_signals.csv
git commit -m "Update signals for $(date +%Y-%m-%d)"

echo ""
echo "[3/3] Pushing to GitHub..."
git push origin main

echo ""
echo "==============================================================================="
echo " DONE! Cloud dashboard will update automatically."
echo "==============================================================================="
echo ""
