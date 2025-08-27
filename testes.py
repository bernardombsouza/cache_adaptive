import unittest
from datetime import datetime, timedelta
from freezegun import freeze_time
import time

# Substitua 'adaptive_cache' pelo nome do seu arquivo.
from new_adaptive_cache import AdaptiveCache, CachePolicy 

# Dados de teste para reutilização
TEST_KEY = "test_key"
TEST_VALUE = "test_value"
LARGE_VALUE = "a" * 1024 # Valor grande para teste de memória (1MB)

class TestAdaptiveCache(unittest.TestCase):
    
    def setUp(self):
        """Prepara o ambiente para cada teste."""
        # Cria uma nova instância do cache para cada teste
        self.cache = AdaptiveCache(max_memory_mb=1000, compression_threshold_kb=1)

# -----------------
# Testes do método put()
# -----------------
    def test_put_adds_new_item(self):
        """Testa se o método put adiciona um novo item ao cache."""
        print('''TESTE DE INSERÇÃO DE VALOR...''')
        self.cache.put(key=TEST_KEY, value=TEST_VALUE)
        print("VALOR DENTRO DO CACHE TEM QUE SER test_value: ", self.cache.get(TEST_KEY), '\n')
        self.assertIn(TEST_KEY, self.cache.cache_data)
        self.assertEqual(self.cache.get(TEST_KEY), TEST_VALUE)
    
    def test_put_updates_existing_item(self):
        """Testa se o método put atualiza um item existente."""
        print("TESTE DE ATUALIZAÇÃO DE VALOR...")
        self.cache.put(TEST_KEY, "valor_antigo")
        print("VALOR ANTIGO ", self.cache.get(TEST_KEY))
        self.cache.put(TEST_KEY, "valor_novo")
        print("VALOR NOVO ", self.cache.get(TEST_KEY), '\n')
        self.assertEqual(self.cache.get(TEST_KEY), "valor_novo")
    
    def test_put_enforces_memory_limit(self):
        """Testa se o cache remove itens quando atinge o limite de memória."""
        print("TESTE DE LIMITE DE MEMÓRIA...")
        for i in range(0, 150):
            self.cache.put(f"key_{i}", TEST_VALUE)
            key = f"key_{i}"
        self.assertIn(key, self.cache.cache_data)
        print("VALOR DA ULTIMA KEY QUE TENTEI ADICIONAR", self.cache.get(key))
        # Adiciona outro item grande, o primeiro deve ser removido
        self.cache.put("new_key", TEST_VALUE)
        print("VALOR DA KEY GRANDE QUE ADICIONEI AGORA", self.cache.get(key))
        self.assertNotIn("key_0", self.cache.cache_data)
        print("CONFIRMA QUE A KEY NAO EXISTE: ", self.cache.get("key_0"))
        self.assertIn("new_key", self.cache.cache_data)
        print("CONFIRMA QUE A KEY NOVA FOI ADICIONADA: ", self.cache.get("new_key"), '\n')

if __name__ == '__main__':
    unittest.main()