from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class SecurityIncident(BaseModel):
    id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    source_ip: str
    attack_type: str  # e.g., "SQL Injection", "SSH Brute Force", "DDoS", "XSS", "Credential Stuffing"
    severity: str     # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    payload: str
    status: str = "DETECTED" # "DETECTED", "ANALYZING", "MITIGATED", "BLOCKED"
    ai_analysis: Optional[str] = None
    playbook_action: Optional[str] = None
    confidence: float = 0.0
    tokens_used: int = 0
    processing_time_ms: float = 0.0

class SimulationRequest(BaseModel):
    attack_type: Optional[str] = "random"
    count: int = 1

class SystemStats(BaseModel):
    total_incidents: int
    mitigated_count: int
    active_threats: int
    ollama_status: str
    model_name: str
    api_exchange_rate_tps: float  # Tokens per second / API exchange rate metric
    total_tokens_processed: int
    avg_latency_ms: float
