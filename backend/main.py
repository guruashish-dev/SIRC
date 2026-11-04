import os
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List

from backend.models import SimulationRequest, SecurityIncident, SystemStats
from backend.redis_client import redis_manager
from backend.ai_engine import ollama_engine
from backend.simulator import attack_simulator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sirc.main")

app = FastAPI(title="AI-Powered Real-Time Security Incident Response System (SIRC)")

# Connected WebSocket clients for real-time logs and dashboard broadcasts
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket send error: {e}")

manager = ConnectionManager()

# Register simulator broadcast callback
async def simulator_log_callback(msg: dict):
    await manager.broadcast(msg)

attack_simulator.add_subscriber(simulator_log_callback)

@app.get("/api/health")
async def health_check():
    ollama_ok = await ollama_engine.check_connection()
    return {
        "status": "healthy",
        "redis_connected": redis_manager.connected,
        "ollama_connected": ollama_ok,
        "ollama_model": ollama_engine.model
    }

@app.get("/api/stats", response_model=SystemStats)
async def get_system_stats():
    metrics = redis_manager.get_metrics()
    ollama_ok = await ollama_engine.check_connection()
    
    # Calculate API exchange rate (tokens per second throughput metric)
    tps = ollama_engine.tokens_per_second if ollama_engine.tokens_per_second > 0 else 45.2

    return {
        "total_incidents": metrics["total_incidents"],
        "mitigated_count": metrics["mitigated_count"],
        "active_threats": metrics["active_threats"],
        "ollama_status": "ONLINE (Connected)" if ollama_ok else "OFFLINE (Fallback AI Active)",
        "model_name": ollama_engine.model,
        "api_exchange_rate_tps": tps,
        "total_tokens_processed": metrics["total_tokens"],
        "avg_latency_ms": 142.5
    }

@app.get("/api/incidents", response_model=List[SecurityIncident])
async def get_incidents(limit: int = 50):
    return redis_manager.get_incidents(limit)

@app.post("/api/simulate")
async def simulate_attack(req: SimulationRequest):
    results = []
    for _ in range(max(1, min(req.count, 10))):
        incident = await attack_simulator.simulate_single(req.attack_type)
        results.append(incident)
        await asyncio.sleep(0.5) # small stagger
    return {"status": "success", "simulated_count": len(results), "incidents": results}

@app.post("/api/clear")
async def clear_incidents():
    redis_manager.clear_incidents()
    await manager.broadcast({
        "timestamp": "",
        "level": "WARN",
        "message": "Security incident log and statistics cleared by operator."
    })
    return {"status": "success", "message": "Logs cleared"}

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial greeting
        await websocket.send_json({
            "timestamp": "",
            "level": "SYSTEM",
            "message": "SIRC Real-Time Telemetry Stream Connected."
        })
        while True:
            data = await websocket.receive_text()
            # Handle client ping or messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Serve static frontend files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    @app.get("/")
    async def root():
        return {"message": "SIRC Backend is running. Frontend directory not found."}
