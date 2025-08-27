from pydantic import BaseModel
from typing import Optional, Dict, Any, Deque
from datetime import timedelta, datetime
import sys
from collections import deque, defaultdict
import threading
import time

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
    
    # def is_expired(ttl, tti, creation_time, last_access_time) -> bool:
    #     now = datetime.now()
    #     if ttl and creation_time:
    #         if now - creation_time > ttl:
    #             return True
    #     if tti and last_access_time:
    #         if now - last_access_time > tti:
    #             return True
    #     return False

class AdaptiveCache:
    def __init__(self, max_memory_mb: int, compression_threshold_kb: int):
        self.cache_data: Dict[str, Any] = {}
        self.lru_queue: Deque[str] = deque()

        self.max_memory_mb = max_memory_mb
        self.compression_threshold_kb = compression_threshold_kb
        self.compression_ratio_target = 0.7
        self.current_memory_usage = 0 

        self.access_counts: Dict[str, int] = defaultdict(int)
        self.access_timestamps: Dict[str, Deque[datetime]] = defaultdict(deque)

        self.hot_keys: Deque[str] = deque()
        self.hot_key_threshold: int = 100

        self.monitor_thread: Optional[threading.Timer] = None
        self.lock = threading.RLock()

    def _start_access_monitor(self):
        self.monitor_thread = threading.Timer(1.0, self._monitor_access_counts)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def _monitor_access_counts(self):
        with self.lock:
            now = datetime.now()
            current_time = time.time()
            window_start_time = current_time - 60

            keys_to_remove = []
            for key, timestamps in self.access_timestamps.items(): 
                data_info = self.cache_data.get(key)
                last_access_time = datetime.fromtimestamp(timestamps[-1]) if timestamps else None   
                current_access_count = len(timestamps)

                if data_info and data_info.get('policy'):
                    policy: CachePolicy = data_info['policy']
                    if policy.ttl and (data_info['creation_time'] + policy.ttl < now):
                        print(f"Chave '{key}' expirou por TTL.")
                        keys_to_remove.append(key)
                        self.lru_queue.remove(key)
                        del self.cache_data[key]
                        self.current_memory_usage -= sys.getsizeof(data_info['data'])
                
                if policy.tti and (last_access_time + policy.tti < now):
                    print(f"Chave '{key}' expirou por TTI.")
                    keys_to_remove.append(key)
                    self.lru_queue.remove(key)
                    del self.cache_data[key]
                    self.current_memory_usage -= sys.getsizeof(data_info['data'])
                
                if policy.max_access and (current_access_count >= policy.max_access):
                    print(f"Chave '{key}' expirou por MAX_ACCESS.")
                    keys_to_remove.append(key)
                    self.lru_queue.remove(key)
                    del self.cache_data[key]
                    self.current_memory_usage -= sys.getsizeof(data_info['data'])

                while timestamps and timestamps[0] < window_start_time:
                    timestamps.popleft()

                access_count = len(timestamps)
                self.access_counts[key] = access_count

                if access_count >= self.hot_key_threshold:
                    if key not in self.hot_keys:
                        self.hot_keys.append(key)
                
                if not timestamps:
                    keys_to_remove.append(key)
                
            for key in keys_to_remove:
                del self.access_timestamps[key]

        #     if data_info and data_info.get('policy'):
        #     policy: CachePolicy = data_info['policy']
        #     if policy.ttl and (data_info['creation_time'] + policy.ttl < now):
        #         print(f"Chave '{key}' expirou por TTL.")
        #         keys_to_remove.append(key)
        #         del self.cache_data[key]
        #         self.current_memory_usage -= sys.getsizeof(data_info['data'])

        #     if policy.max_access and (access_count >= policy.max_access):
        #         print(f"Chave '{key}' expirou por MAX_ACCESS.")
        #         keys_to_remove.append(key)
        #         del self.cache_data[key]
        #         self.current_memory_usage -= sys.getsizeof(data_info['data'])

        #     if policy.tti and (last_access_time + policy.tti < now):
        #         print(f"Chave '{key}' expirou por TTI.")
        #         keys_to_remove.append(key)
        #         del self.cache_data[key]
        #         self.current_memory_usage -= sys.getsizeof(data_info['data'])

        self._start_access_monitor()

    def get(self, key: str) -> Optional[str]:
        if key not in self.cache_data:
            return None
        
        with self.lock:
            self.access_timestamps[key].append(time.time())

            if key in self.hot_keys:
                self.hot_keys.remove(key)
                self.hot_keys.append(key)

            if key in self.cache_data:
                self.lru_queue.remove(key)
                self.lru_queue.append(key)
                return self.cache_data[key]['data']
            
            return None 
        
    def put(self, key: str, value: str, policy: Optional[CachePolicy] = None):
        with self.lock:
            # ADICIONAR POLITICA DE COMPRESSAO E DESCOMPRESSAO AQUI
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
                'creation_time': datetime.now(),
            }
            
            self.current_memory_usage += sys.getsizeof(value)
            if key in self.lru_queue:
                self.lru_queue.remove(key)
                self.lru_queue.append(key)
            else:
                self.lru_queue.append(key)

    def refresh_policy(self, key: str, policy: CachePolicy):
        if key in self.cache_data:
            self.cache_data[key]['policy'] = policy
            self.cache_data[key]['creation_time'] = datetime.now()
            self.cache_data[key]['last_access_time'] = datetime.now()

    def configure_adaptive_behavior(self, hot_key_threshold: int, enable_predictive_loading: bool, compression_ratio_target: float): 
        self.hot_key_threshold = hot_key_threshold
        self.compression_ratio_target = compression_ratio_target
