#!/usr/bin/env bash
# ==============================================================================
# ABYSSEYE Industrial Scale One-Command Deployment & Health Verification
# ==============================================================================
set -euo pipefail

echo "================================================================="
echo "  ABYSSEYE — Industrial Deployment Automation                   "
echo "================================================================="

# 1. Environment Check
if [ ! -f .env ]; then
    echo "[*] Creating .env from .env.example..."
    cp .env.example .env
fi

# 2. Run Test Suite Verification
echo "[*] Executing pre-deployment test suite..."
python -m pytest -v

# 3. Build and Launch Containers
echo "[*] Building and starting production Docker stack..."
docker compose -f docker-compose.prod.yml up -d --build

# 4. Wait for Healthcheck Probe
echo "[*] Polling service health probes..."
RETRIES=15
until curl -s http://localhost/healthz > /dev/null || [ $RETRIES -eq 0 ]; do
    echo "    Waiting for services to become healthy ($RETRIES remaining)..."
    sleep 3
    RETRIES=$((RETRIES-1))
done

if [ $RETRIES -eq 0 ]; then
    echo "[ERROR] Deployment healthcheck timed out. Check docker logs."
    docker compose -f docker-compose.prod.yml logs
    exit 1
fi

echo "================================================================="
echo "  [SUCCESS] ABYSSEYE Deployed & Healthy!                        "
echo "  Web UI: http://localhost                                      "
echo "  API Health: http://localhost/api/v1/sonar/health              "
echo "================================================================="
