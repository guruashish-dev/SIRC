#!/usr/bin/env bash
set -e

SIRC_PORT="${SIRC_PORT:-8002}"
export SIRC_PORT

echo "============================================================"
echo " Starting AI-Powered Real-Time Security Incident Response"
echo " System (SIRC) - Enterprise SOC Edition"
echo "============================================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running or not installed. Please start Docker and try again."
    exit 1
fi

echo "[1/4] Building and launching Docker containers (Redis + FastAPI Backend)..."
docker-compose up --build -d

echo "[2/4] Waiting for services to become ready..."
sleep 3

echo "[3/4] Checking SIRC Health Endpoint..."
until curl -s "http://localhost:${SIRC_PORT}/api/health" > /dev/null; do
    echo "Waiting for SIRC backend service..."
    sleep 2
done

echo "============================================================"
echo " SIRC is successfully running!"
echo "------------------------------------------------------------"
echo " Web Dashboard : http://localhost:${SIRC_PORT}"
echo " API Docs      : http://localhost:${SIRC_PORT}/docs"
echo " Redis Cache   : localhost:6379"
echo " Ollama Status : Integrated (uses local Ollama at localhost:11434)"
echo "============================================================"
echo "To view live container logs, run: docker-compose logs -f"
echo "To stop the system, run: docker-compose down"
echo "============================================================"

# Try opening browser if available
if command -v xdg-open > /dev/null; then
    xdg-open "http://localhost:${SIRC_PORT}"
elif command -v start > /dev/null; then
    start "" "http://localhost:${SIRC_PORT}"
fi
