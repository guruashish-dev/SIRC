import os
import redis
import json
import logging

logger = logging.getLogger("sirc.redis")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

class RedisManager:
    def __init__(self):
        try:
            self.client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
            self.client.ping()
            self.connected = True
            logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        except Exception as e:
            self.connected = False
            logger.warning(f"Failed to connect to Redis at {REDIS_HOST}:{REDIS_PORT}: {e}. Falling back to in-memory store.")
            self._memory_incidents = []
            self._memory_stats = {
                "total_tokens": 0,
                "total_requests": 0,
                "mitigated_count": 0
            }

    def save_incident(self, incident: dict):
        if self.connected:
            try:
                self.client.lpush("sirc:incidents", json.dumps(incident))
                self.client.ltrim("sirc:incidents", 0, 199) # keep last 200
                self.client.hincrby("sirc:stats", "total_incidents", 1)
                if incident.get("status") in ["MITIGATED", "BLOCKED"]:
                    self.client.hincrby("sirc:stats", "mitigated_count", 1)
            except Exception as e:
                logger.error(f"Redis save error: {e}")
        else:
            self._memory_incidents.insert(0, incident)
            if len(self._memory_incidents) > 200:
                self._memory_incidents.pop()

    def get_incidents(self, limit: int = 50) -> list:
        if self.connected:
            try:
                raw = self.client.lrange("sirc:incidents", 0, limit - 1)
                return [json.loads(item) for item in raw]
            except Exception as e:
                logger.error(f"Redis get error: {e}")
                return []
        else:
            return self._memory_incidents[:limit]

    def clear_incidents(self):
        if self.connected:
            try:
                self.client.delete("sirc:incidents")
                self.client.delete("sirc:stats")
            except Exception as e:
                logger.error(f"Redis clear error: {e}")
        else:
            self._memory_incidents = []

    def update_stats(self, tokens: int, latency_ms: float):
        if self.connected:
            try:
                self.client.incrby("sirc:tokens_total", tokens)
                self.client.incr("sirc:requests_total")
            except Exception as e:
                logger.error(f"Redis stats error: {e}")
        else:
            self._memory_stats["total_tokens"] += tokens
            self._memory_stats["total_requests"] += 1

    def get_metrics(self) -> dict:
        if self.connected:
            try:
                total_incidents = int(self.client.hget("sirc:stats", "total_incidents") or 0)
                mitigated_count = int(self.client.hget("sirc:stats", "mitigated_count") or 0)
                total_tokens = int(self.client.get("sirc:tokens_total") or 0)
                total_requests = int(self.client.get("sirc:requests_total") or 0)
                active_threats = max(0, total_incidents - mitigated_count)
                return {
                    "total_incidents": total_incidents,
                    "mitigated_count": mitigated_count,
                    "active_threats": active_threats,
                    "total_tokens": total_tokens,
                    "total_requests": total_requests
                }
            except Exception as e:
                logger.error(f"Redis metrics error: {e}")
                return {"total_incidents": 0, "mitigated_count": 0, "active_threats": 0, "total_tokens": 0, "total_requests": 0}
        else:
            total_incidents = len(self._memory_incidents)
            mitigated_count = sum(1 for i in self._memory_incidents if i.get("status") in ["MITIGATED", "BLOCKED"])
            return {
                "total_incidents": total_incidents,
                "mitigated_count": mitigated_count,
                "active_threats": total_incidents - mitigated_count,
                "total_tokens": self._memory_stats["total_tokens"],
                "total_requests": self._memory_stats["total_requests"]
            }

redis_manager = RedisManager()
