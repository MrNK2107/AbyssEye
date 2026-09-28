#!/usr/bin/env bash
# ABYSSEYE Ground Station Bash Launcher
set -euo pipefail

echo "================================================================="
echo "  ABYSSEYE - Autonomous Sonar Ground Station Launcher           "
echo "  Launching Backend (Port 8000) and Frontend (Port 3000)...     "
echo "================================================================="

python3 run.py
