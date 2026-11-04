# AI-Powered Real-Time Security Incident Response System (SIRC)

An enterprise-grade, real-time Security Operations Center (SOC) platform powered by **Ollama** AI models, **Redis** caching, **FastAPI**, and a modern SOC web dashboard.

---

## 🚀 Architecture & Features

1. **Autonomous AI Threat Analysis (`Ollama`)**:
   - Analyzes incoming security telemetry in real-time.
   - Automatically detects attack vectors (SQL Injection, SSH Brute Force, DDoS, XSS, Credential Stuffing).
   - Generates confidence scores, severity ratings, and automated mitigation playbooks.
   - Fallback AI mode ensures high availability even if Ollama is offline.

2. **Redis Caching & Telemetry State**:
   - High-performance caching for security incident history (FIFO queue of last 200 incidents).
   - Real-time aggregation of active threats, total tokens processed, and API throughput metrics.

3. **Attack Simulation Engine**:
   - Built-in simulator to test attack vectors on demand with a single click.
   - Triggers live logging streams sent over WebSocket to the frontend.

4. **Enterprise SOC Web Dashboard**:
   - Modern Tailwind CSS dark-mode interface.
   - **API Exchange Rate & Throughput Widget**: Displays real-time tokens-per-second (`t/s`) generation rate and API usage metrics.
   - **Live Log Stream Terminal**: Bottom console streaming every executed step (SIEM ingestion -> AI analysis -> Playbook execution) in real-time via WebSocket.

5. **Single-Script Execution (`run.sh` / `run.bat`)**:
   - Automatically builds and starts Docker containers (Redis + FastAPI backend) and opens the dashboard.

---

## 🛠️ Quick Start

### Prerequisites
- [Docker & Docker Compose](https://www.docker.com/) installed and running.
- [Ollama](https://ollama.com/) running locally (optional, defaults to `http://localhost:11434` with `llama3` or `mistral`).

### Running the Project

Simply execute the run script:

**On Linux / macOS / Bash:**
```bash
bash run.sh
```

**On Windows:**
```cmd
run.bat
```

Or manually with Docker Compose:
```bash
docker-compose up --build -d
```
Access the dashboard at **`http://localhost:8002`**. Set `SIRC_PORT` before launching to use a different host port.

---

## 📂 Project Structure

```
d:\ASE\SIRC\
├── docker-compose.yml     # Orchestrates Redis & FastAPI backend
├── Dockerfile             # Container definition for Python backend
├── requirements.txt       # Python dependencies
├── run.sh                 # Single-file bash launcher
├── run.bat                # Windows batch launcher
├── README.md              # Documentation
├── backend\
│   ├── main.py            # FastAPI application & WebSocket server
│   ├── ai_engine.py       # Ollama integration & AI analyzer
│   ├── simulator.py       # Attack simulation generator
│   ├── redis_client.py    # Redis cache & metrics manager
│   └── models.py          # Pydantic data schemas
└── frontend\
    ├── index.html         # SOC Dashboard UI (Tailwind CSS)
    └── app.js             # Dashboard frontend logic & WebSocket client
```
