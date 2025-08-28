import unittest
from datetime import datetime, timedelta
from freezegun import freeze_time
import time
import random   
import string

# Substitua 'adaptive_cache' pelo nome do seu arquivo.
from new_adaptive_cache import AdaptiveCache, CachePolicy 

# Dados de teste para reutilização
TEST_KEY = "test_key"
TEST_VALUE = "test_value"
LARGE_VALUE = "a" * 1024 # Valor grande para teste de memória (1MB)
SMALL_VALUE = "b" * 1024 # 1 KB

def generate_random_data(size_kb: int = 10) -> str:
    """Gera uma string de dados aleatórios."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=size_kb * 1024))

class TestAdaptiveCache(unittest.TestCase):
    
    def setUp(self):
        # Limpa o cache para cada novo teste
        self.cache = AdaptiveCache(max_memory_mb=0.0001, compression_threshold_kb=100)

    def tearDown(self):
        # Para a thread do monitor após o teste
        if self.cache.monitor_thread and self.cache.monitor_thread.is_alive():
            self.cache.monitor_thread.cancel()

    def test_put_adds_new_item(self):
        """Testa se o método put adiciona um novo item ao cache."""
        print('''TESTE DE INSERÇÃO DE VALOR...''')
        self.cache.put(key=TEST_KEY, value=TEST_VALUE)
        print("VALOR DENTRO DO CACHE TEM QUE SER test_value: ", self.cache.get(TEST_KEY), '\n')
        self.assertIn(TEST_KEY, self.cache.cache_data)
        self.assertEqual(self.cache.get(TEST_KEY), TEST_VALUE)
    
    def test_put_updates_existing_item(self):
        """Testa se o método put atualiza um item existente."""
        print("\nTESTE DE ATUALIZAÇÃO DE VALOR...")
        self.cache.put(TEST_KEY, "valor_antigo")
        print("VALOR ANTIGO ", self.cache.get(TEST_KEY))
        self.cache.put(TEST_KEY, "valor_novo")
        print("VALOR NOVO ", self.cache.get(TEST_KEY), '\n')
        self.assertEqual(self.cache.get(TEST_KEY), "valor_novo")
    
    def test_put_enforces_memory_limit(self):
        """Testa se o cache remove itens quando atinge o limite de memória."""
        print("TESTE DE LIMITE DE MEMÓRIA...")
        for i in range(0, 500):
            self.cache.put(f"key_{i}", TEST_VALUE)
            key = f"key_{i}"
            print("MEMORIA USADA", self.cache.current_memory_usage)
            print("MEMORIA TOTAL", self.cache.max_memory_mb)
        self.assertIn(key, self.cache.cache_data)
        print("VALOR DA ULTIMA KEY QUE TENTEI ADICIONAR", self.cache.get(key))
        # Adiciona outro item grande, o primeiro deve ser removido
        self.cache.put("new_key", TEST_VALUE)
        print("VALOR DA KEY GRANDE QUE ADICIONEI AGORA", self.cache.get(key))
        self.assertNotIn("key_0", self.cache.cache_data)
        print("CONFIRMA QUE A KEY NAO EXISTE: ", self.cache.get("key_0"))
        self.assertIn("new_key", self.cache.cache_data)
        print("CONFIRMA QUE A KEY NOVA FOI ADICIONADA: ", self.cache.get("new_key"), '\n')

    def test_get_returns_none_for_non_existent_key(self):
        """Testa se get retorna None para uma chave inexistente."""
        print("TESTE DE GET PARA CHAVE INEXISTENTE...")
        self.assertIsNone(self.cache.get("chave_inexistente"))
        print("CHAVE NAO EXISTE: ", self.cache.get("chave_inexistente"), '\n')

    def test_get_updates_access_count_and_last_access_time(self):
        """Testa se o acesso a um item atualiza seus metadados."""
        print("TESTE DE ATUALIZAÇÃO DE METADADOS AO ACESSAR...")
        self.cache.put(TEST_KEY, TEST_VALUE, policy=CachePolicy(ttl=300, max_access=5, tti=100))
        self.cache.get(TEST_KEY)  # Primeiro acesso

        initial_count = len(self.cache.access_timestamps[TEST_KEY])
        initial_time = datetime.fromtimestamp(self.cache.access_timestamps[TEST_KEY][-1])

        print("VERIFICANDO QUANTIDADE DE ACESSOS...", len(self.cache.access_timestamps[TEST_KEY]))
        print("VERIFICANDO ULTIMO ACESSO", self.cache.access_timestamps[TEST_KEY][-1])
        time.sleep(1)  # Garante que o tempo mude
        self.cache.get(TEST_KEY)
        self.cache.get(TEST_KEY)

        print("VERIFICANDO QUANTIDADE DE ACESSOS POS CLIQUE...", len(self.cache.access_timestamps[TEST_KEY]))
        print("VERIFICANDO ULTIMO ACESSO POS CLIQUE...", self.cache.access_timestamps[TEST_KEY][-1], '\n')

        self.assertEqual(len(self.cache.access_timestamps[TEST_KEY]), initial_count + 2)
        self.assertGreater(datetime.fromtimestamp(self.cache.access_timestamps[TEST_KEY][-1]), initial_time)

    def test_put_and_get(self):
        self.cache.put(TEST_KEY, TEST_VALUE)
        self.assertEqual(self.cache.get(TEST_KEY), TEST_VALUE)
        self.assertIn(TEST_KEY, self.cache.cache_data)
        
    def test_get_non_existent_key(self):
        self.assertIsNone(self.cache.get("non_existent_key"))
        
    def test_put_updates_existing_key(self):
        self.cache.put(TEST_KEY, "old_value")
        self.assertEqual(self.cache.get(TEST_KEY), "old_value")
        self.cache.put(TEST_KEY, "new_value")
        self.assertEqual(self.cache.get(TEST_KEY), "new_value")
    
    def test_lru_eviction(self):
        self.cache.put("key1", "data1")
        self.cache.put("key2", "data2")
        self.cache.get("key1") # Faz key1 ser a mais recente
        self.cache.put("key4", "data4") # Força a remoção de key2 (a mais antiga)
        self.assertIn("key1", self.cache.lru_queue)
        self.assertIn("key4", self.cache.lru_queue)
        self.assertNotIn("key2", self.cache.lru_queue)

    def test_memory_eviction(self):
        # Define um cache pequeno para forçar a remoção
        small_cache = AdaptiveCache(max_memory_mb=0.001, compression_threshold_kb=10)
        
        # Adiciona 5 itens de 20KB cada
        for i in range(5):
            small_cache.put(f"key{i}", generate_random_data(size_kb=20))
            
        # O cache tem capacidade para no máximo 4 itens de 20KB.
        # Adicionar o 5º item (key4) deve remover o 1º (key0)
        self.assertNotIn("key0", small_cache.cache_data)
        self.assertIn("key4", small_cache.cache_data)

    def test_compression_logic(self):
        self.cache.put("large_key", LARGE_VALUE)
        # O valor deve ser comprimido
        data_info = self.cache.cache_data["large_key"]
        self.assertTrue(data_info['compressed'])
        self.assertIsInstance(data_info['data'], bytes)
        self.assertEqual(self.cache.get("large_key"), LARGE_VALUE)
        
    def test_no_compression_for_small_data(self):
        self.cache.put("small_key", SMALL_VALUE)
        data_info = self.cache.cache_data["small_key"]
        self.assertFalse(data_info.get('compressed', False))
        self.assertIsInstance(data_info['data'], str)
        self.assertEqual(self.cache.get("small_key"), SMALL_VALUE)
    
    def test_predictive_load_hot_key(self):
        self.cache.put("key_tenis", "hot_value")
        self.cache.configure_adaptive_behavior(hot_key_threshold=1, enable_predictive_loading=True, compression_ratio_target=0.7)
        
        # Simula o monitoramento
        self.cache.get("key_tenis")
        self.cache.get("key_tenis")
        print(self.cache.hot_keys)
        time.sleep(5) # Espera o monitor rodar
        
        self.assertIn("key_meia", self.cache.cache_data)

class TestCachePolicy(unittest.TestCase):
    
    def test_with_ttl(self):
        policy = CachePolicy().with_ttl(timedelta(seconds=10))
        self.assertEqual(policy.ttl, timedelta(seconds=10))
        
    def test_with_tti(self):
        policy = CachePolicy().with_tti(timedelta(minutes=5))
        self.assertEqual(policy.tti, timedelta(minutes=5))

    def test_with_max_access(self):
        policy = CachePolicy().with_max_access(50)
        self.assertEqual(policy.max_access, 50)
    
    def test_is_expired_ttl(self):
        # Congela o tempo para testar a expiração
        with freeze_time("2025-01-01 12:00:00"):
            creation_time = datetime.now()
            policy = CachePolicy(ttl=timedelta(minutes=1))
        
        with freeze_time("2025-01-01 12:00:30"):
            self.assertFalse(creation_time + policy.ttl < datetime.now())
        
        with freeze_time("2025-01-01 12:01:01"):
            self.assertTrue(creation_time + policy.ttl < datetime.now())

    def test_is_expired_tti(self):
        with freeze_time("2025-01-01 12:00:00"):
            last_access_time = datetime.now()
            policy = CachePolicy(tti=timedelta(minutes=1))
            
        with freeze_time("2025-01-01 12:00:30"):
            self.assertFalse(last_access_time + policy.tti < datetime.now())
            
        with freeze_time("2025-01-01 12:01:01"):
            self.assertTrue(last_access_time + policy.tti < datetime.now())

class TestBatchOperation(unittest.TestCase):
    
    def setUp(self):
        self.cache = AdaptiveCache(max_memory_mb=1, compression_threshold_kb=1)

    def test_batch_put_success(self):
        with self.cache.batch_operation() as batch:
            batch.put("batch_key1", "value1")
            batch.put("batch_key2", "value2")
            
        self.assertIn("batch_key1", self.cache.cache_data)
        self.assertIn("batch_key2", self.cache.cache_data)
        
    def test_batch_put_updates(self):
        self.cache.put("batch_key1", "old_value")
        
        with self.cache.batch_operation() as batch:
            batch.put("batch_key1", "new_value")
            
        self.assertEqual(self.cache.get("batch_key1"), "new_value")
        
if __name__ == '__main__':
    unittest.main()

if __name__ == '__main__':
    unittest.main()