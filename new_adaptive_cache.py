from pydantic import BaseModel
from typing import Optional, Dict, Any, Deque
from datetime import timedelta, datetime
import threading
import sys
from collections import deque

class CachePolicy(BaseModel):
    creation_time: Optional[datetime] = None
    ttl:timedelta = None
    tti:timedelta = None
    max_access: Optional[int] = None

    def with_ttl(self, ttl: timedelta) -> 'CachePolicy':
        self.ttl = ttl
        return self
    
    def with_tti(self, tti: timedelta) -> 'CachePolicy':
        self.tti = tti
        return self
    
    def with_max_access(self, max_access: int) -> 'CachePolicy':
        self.max_access = max_access
        return self
    
    def is_expired(ttl, tti, creation_time, last_access_time) -> bool:
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
        self.lru_queue: Deque[str] = deque()
        self.max_memory_mb = max_memory_mb
        self.compression_threshold_kb = compression_threshold_kb

        self.hot_keys: Deque[str] = deque()
        self.hot_key_threshold: int = 100

    def get(self, key: str) -> Optional[str]:
        if key not in self.cache_data:
            return None
        
        try:
            if self.cache_data[key]['policy']:
                policy: CachePolicy = self.cache_data[key]['policy']
                if policy.ttl:
                    if self.cache_data[key]['creation_time'] + self.cache_data[key]['policy'].ttl < datetime.now():
                        del self.cache_data[key]
                        self.lru_queue.remove(key)
                        return None
            
            if key in self.hot_keys:
                self.hot_keys.remove(key)
                self.hot_keys.append(key)
            elif self.cache_data[key]['access_count'] > self.hot_key_threshold:
                self.hot_keys.append(key)

            self.lru_queue.remove(key)
            self.lru_queue.append(key)
            self.cache_data[key]['last_access_time'] = datetime.now()
            self.cache_data[key]['access_count'] += 1
            data_info = self.cache_data[key]
            value = data_info['data']
            return value
        
        except ValueError:
            return None
        

    def put(self, key: str, value: str, policy: Optional[CachePolicy] = None):

        if self.current_memory_usage + sys.getsizeof(value) > self.max_memory_mb:
            while self.current_memory_usage + sys.getsizeof(value) > self.max_memory_mb:
                lru_key = self.lru_queue.popleft()
                if lru_key not in self.hot_keys:
                    self.current_memory_usage -= sys.getsizeof(self.cache_data[lru_key]['data'])
                    del self.cache_data[lru_key]
                else:
                    if self.hot_keys == self.lru_queue:
                        lru_hot_key = self.hot_keys.popleft()
                        self.hot_keys.remove(lru_hot_key)
                        self.current_memory_usage -= sys.getsizeof(self.cache_data[lru_hot_key][value])
                        del self.cache_data[lru_key]
                    else:
                        self.lru_queue.append(lru_key)

        self.cache_data[key] = {
            'data': value,
            'policy': policy,
            'size': sys.getsizeof(value),
            'last_access_time': datetime.now(),
            'creation_time': datetime.now(),
            'access_count': 1
        }
        
        self.current_memory_usage += sys.getsizeof(value)
        if key in self.lru_queue:
            self.lru_queue.remove(key)
            self.lru_queue.append(key)
        else:
            self.lru_queue.append(key)

    def refresh_policy(self, key: str, new_policy: CachePolicy):
        if key in self.cache_data:
            self.cache_data[key]['policy'] = new_policy

    def configure_adaptive_behavior(self, hot_key_threshold: int, enable_predictive_loading: bool, compression_ratio_target: float):    
        pass

