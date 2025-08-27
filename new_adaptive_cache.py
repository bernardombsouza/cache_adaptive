from pydantic import BaseModel
from typing import Optional, Dict, Any, Deque
from datetime import timedelta, datetime
import threading
import time

class CachePolicy(BaseModel):
    creation_time: Optional[datetime] = None
    last_access_time: Optional[datetime] = None
    ttl:timedelta = None
    tti:timedelta = None

    def with_ttl(self, ttl: timedelta) -> 'CachePolicy':
        self.creation_time = datetime.now()
        self.ttl = ttl
        return self
    
    def with_tti(self, tti: timedelta) -> 'CachePolicy':
        self.last_access_time = datetime.now()
        self.tti = tti
        return self
    
    def expired(ttl, tti, creation_time, last_access_time) -> bool:
        now = datetime.now()
        if ttl and creation_time:
            if now - creation_time > ttl:
                return True
        if tti and last_access_time:
            if now - last_access_time > tti:
                return True
        return False

class AdaptiveCache:
    def __init__(self, max_memory_mb: int, compression_threshold_kb: int):
        self.cache_data: Dict[str, Any] = {}
        self.current_memory_usage = 0 
        self.list_queue_lru: Deque[str] = []

        self.max_memory_mb = max_memory_mb
        self.compression_threshold_kb = compression_threshold_kb
        self._lock() = threading.RLock()

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            if key in self.cache_data:
                self.list_queue_lru.remove(key)
                self.list_queue_lru.append(key)
            pass

print(CachePolicy().with_ttl(timedelta(seconds=10)).with_tti(timedelta(seconds=5)))
