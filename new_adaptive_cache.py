from pydantic import BaseModel
from typing import Optional, Dict, Any, Deque
from datetime import timedelta, datetime
import sys
from collections import deque, defaultdict
import threading
import time
import json
import zlib

class CachePolicy(BaseModel):
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

class AdaptiveCache:
    def __init__(self, max_memory_mb: int, compression_threshold_kb: int):
        self.cache_data: Dict[str, Any] = {}
        self.lru_queue: Deque[str] = deque()

        self.max_memory_mb = max_memory_mb * 1024 * 1024 
        self.compression_threshold_kb = compression_threshold_kb * 1024  
        self.compression_ratio_target = 0.7
        self.current_memory_usage = 0 

        self.access_counts: Dict[str, int] = defaultdict(int)
        self.access_timestamps: Dict[str, Deque[datetime]] = defaultdict(deque)

        self.hot_keys: Deque[str] = deque()
        self.hot_key_threshold: int = 100
        self.enable_predictive_loading: bool = False

        self.monitor_thread: Optional[threading.Timer] = None
        self.lock = threading.RLock()

        self._start_access_monitor()

    def _compress_data(self, data: str) -> bytes:
        if type(data) is bytes:
            data = data.decode('utf-8')
        return zlib.compress(data.encode('utf-8'))
        
    def _decompress_data(self, data: bytes) -> str:
        return zlib.decompress(data).decode('utf-8')

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
                        self.cache_data.pop(key, None)
                        self.current_memory_usage -= sys.getsizeof(data_info['data'])
                
                    if policy.tti and (last_access_time + policy.tti < now):
                        print(f"Chave '{key}' expirou por TTI.")
                        keys_to_remove.append(key)
                        self.lru_queue.remove(key)
                        self.cache_data.pop(key, None)
                        self.current_memory_usage -= sys.getsizeof(data_info['data'])
                    
                    if policy.max_access and (current_access_count >= policy.max_access):
                        print(f"Chave '{key}' expirou por MAX_ACCESS.")
                        keys_to_remove.append(key)
                        self.lru_queue.remove(key)
                        self.cache_data.pop(key, None)
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

        self.predictive_load()
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
                if not self.cache_data[key]['compressed']:
                    return self.cache_data[key]['data']
                return self._decompress_data(self.cache_data[key]['data'])
        
    def put(self, key: str, value: str, policy: Optional[CachePolicy] = None):
        with self.lock:
            original_size = sys.getsizeof(value)
            stored_value = value
            is_compressed = False

            if original_size > self.compression_threshold_kb:
                compressed_data = self._compress_data(value)
                compressed_size = sys.getsizeof(compressed_data)
                
                if compressed_size / original_size <= self.compression_ratio_target:
                    stored_value = compressed_data
                    is_compressed = True
                    print(f"Comprimindo chave '{key}'. Tamanho original: {original_size} bytes. Novo tamanho: {compressed_size} bytes.")
                else:
                    print(f"Compressão ineficaz para '{key}'. Usando dados originais.")

            if self.current_memory_usage + sys.getsizeof(stored_value) > self.max_memory_mb:
                while self.current_memory_usage + sys.getsizeof(stored_value) > self.max_memory_mb:
                    if not self.lru_queue:
                        break  # Evita loop infinito se cache vazio
                    lru_key = self.lru_queue.popleft()
                    if lru_key not in self.hot_keys:
                        self.current_memory_usage -= sys.getsizeof(self.cache_data[lru_key]['data'])
                        del self.cache_data[lru_key]
                    else:
                        self.lru_queue.append(lru_key)
                        if len(self.hot_keys) == len(self.lru_queue):
                            lru_hot_key = self.lru_queue.popleft()
                            self.hot_keys.remove(lru_hot_key)
                            self.current_memory_usage -= sys.getsizeof(self.cache_data[lru_hot_key]['data'])
                            del self.cache_data[lru_key]

            self.cache_data[key] = {
                'data': stored_value,
                'policy': policy,
                'size': sys.getsizeof(value),
                'creation_time': datetime.now(),
                'compressed': is_compressed
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
            self.access_timestamps[key].append(time.time())

    def configure_adaptive_behavior(self, hot_key_threshold: int, enable_predictive_loading: bool, compression_ratio_target: float): 
        self.hot_key_threshold = hot_key_threshold
        self.compression_ratio_target = compression_ratio_target
        self.enable_predictive_loading = enable_predictive_loading

    def predictive_load(self):
        if not self.enable_predictive_loading:
            print("Predictive loading is disabled.")
            return
        
        with self.lock:
            with open('teste_monitor.json', 'r') as arquivo:
                dados_python = json.load(arquivo)
                for key, value in dados_python.items():
                    if key in self.hot_keys:
                        for predict_key in value:
                            if predict_key['key'] not in self.cache_data:
                                self.put(predict_key['key'], predict_key['value'])
                        print(f"Preloaded key: {key}")

    def batch_operation(self) -> 'BatchOperation':
        return BatchOperation(self)

class BatchOperation:
    """Gerenciador de contexto para operações em lote no cache."""
    
    def __init__(self, cache):
        self.cache = cache
        self.operations = []

    def put(self, key: str, value: str, policy: Optional[Any] = None):
        """Adiciona uma operação de 'put' à fila de processamento."""
        self.operations.append(('put', key, value, policy))
    
    def __enter__(self):
        """Método chamado ao iniciar o bloco 'with'."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Método chamado ao sair do bloco 'with'.
        Executa todas as operações em lote.
        """
        # Garante que as operações sejam atômicas com um lock de threading
        with self.cache.lock:
            for op in self.operations:
                op_type = op[0]
                if op_type == 'put':
                    _, key, value, policy = op
                    # Chama um método privado para processar o put
                    self.cache.put(key, value, policy)
        
        # Limpa a lista de operações para que possa ser reutilizada
        self.operations.clear()