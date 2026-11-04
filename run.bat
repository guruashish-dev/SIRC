@echo off
echo ============================================================
echo  Starting AI-Powered Real-Time Security Incident Response
echo  System (SIRC) - Enterprise SOC Edition
echo ============================================================

if not defined SIRC_PORT set "SIRC_PORT=8002"

docker info >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not running or not installed. Please start Docker and try again.
    pause
    exit /b 1
)

echo [1/3] Building and launching Docker containers (Redis + FastAPI Backend)...
docker-compose up --build -d

echo [2/3] Waiting for services to become ready...
timeout /t 3 /nobreak >nul

echo [3/3] Opening SIRC Web Dashboard...
start http://localhost:%SIRC_PORT%

echo ============================================================
echo  SIRC is successfully running!
echo  Web Dashboard : http://localhost:%SIRC_PORT%
echo  API Docs      : http://localhost:%SIRC_PORT%/docs
echo ============================================================
pause
