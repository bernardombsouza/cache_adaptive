from collections import defaultdict, deque
import threading
import zlib
import sys
from pydantic import BaseModel
from typing import Optional, Any, Dict, Deque
from datetime import timedelta
import time
from contextlib import contextmanager

def compress(data: str) -> bytes:
    return zlib.compress(data.encode('utf-8'))

def decompress(data: bytes) -> str:
    return zlib.decompress(data).decode('utf-8')

class CachePolicy(BaseModel):
    ttl: Optional[timedelta] = None
    tti: Optional[timedelta] = None
    max_access: Optional[int] = None

class AdaptiveCache:
    def __init__(self, max_memory_mb: int, compression_threshold_kb: int):
        self.cache_data: Dict[str, Any] = {}
        self.current_memory_usage = 0 
        self.memory_limit = max_memory_mb * 1024 * 1024 
        self.compression_threshold = compression_threshold_kb * 1024 
        
        self.access_timestamps: Dict[str, Deque[float]] = defaultdict(deque)
        self.access_counts: Dict[str, int] = defaultdict(int)
        self.hot_keys: set = set()
        
        self.hot_key_threshold: int = 100
        self.compression_ratio_target: float = 0.7 
        self.monitor_thread: Optional[threading.Timer] = None
        self.lock = threading.Lock()

    def _start_access_monitor(self):
        self.monitor_thread = threading.Timer(1.0, self._monitor_access_counts)
        self.monitor_thread.daemon = True
        self.monitor_thread.start() 

    def _monitor_access_counts(self):
        with self.lock:
            current_time = time.time()
            window_start_time = current_time - 60
            
            keys_to_remove = []
            for key, timestamps in self.access_timestamps.items():
                while timestamps and timestamps[0] < window_start_time:
                    timestamps.popleft()
                
                access_count = len(timestamps)
                self.access_counts[key] = access_count
                
                if access_count >= self.hot_key_threshold:
                    self.hot_keys.add(key)
                
                if not timestamps:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.access_timestamps[key]
        
        self._start_access_monitor()

    def configure_adaptive_behavior(self, hot_key_threshold: int, compression_ratio_target: float):
        self.hot_key_threshold = hot_key_threshold
        self.compression_ratio_target = compression_ratio_target
        
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            print("Iniciando monitoramento de acessos em background...")
            self._start_access_monitor()

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            self.access_timestamps[key].append(time.time())
            
            if key in self.cache_data:
                self.lru_queue.remove(key)
                self.lru_queue.append(key)
                return decompress(self.cache_data[key])
            
            return None 

    def put(self, key: str, value: Any, policy: Optional[CachePolicy] = None):
        with self.lock:
            value_str = str(value)
            original_size = sys.getsizeof(value_str)
            
            if original_size > self.compression_threshold:
                data_to_store = compress(value_str)
            else:
                data_to_store = value_str.encode('utf-8')
            
            size_to_store = sys.getsizeof(data_to_store)

            while self.current_memory_usage + size_to_store > self.memory_limit:
                evicted_key = self.lru_queue.popleft()
                
                if evicted_key not in self.hot_keys:
                    self.current_memory_usage -= sys.getsizeof(self.cache_data[evicted_key])
                    del self.cache_data[evicted_key]
                else:
                    self.lru_queue.append(evicted_key)
                    if self.current_memory_usage + size_to_store > self.memory_limit:
                        raise MemoryError("Cache memory limit exceeded, even after hot key protection.")

            self.cache_data[key] = data_to_store
            self.current_memory_usage += size_to_store
            self.lru_queue.append(key)

    def refresh_policy(self, key: str, new_policy: CachePolicy):
        with self.lock:
            if key in self.cache_data:
                if new_policy.ttl:
                    self.hot_keys.add(key)
                
    def predictive_load(self, key: str, value: Any, policy: Optional[CachePolicy] = None):
        print(f"Pré-carregando {key} no cache...")
        self.put(key, value, policy if policy else CachePolicy(ttl=timedelta(minutes=30)))
        self.hot_keys.add(key)
        
    @contextmanager
    def batch_operation(self):
        print("Iniciando operação em lote...")
        yield self
        print("Operação em lote concluída.")

    def get_most_accessed_products(self, top_n: int = 5) -> list:
        with self.lock:
            sorted_counts = sorted(self.access_counts.items(), key=lambda item: item[1], reverse=True)
            return sorted_counts[:top_n]
