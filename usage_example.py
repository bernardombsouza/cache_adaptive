from new_adaptive_cache import AdaptiveCache, CachePolicy
from datetime import timedelta
import time
import random
import string
import sys

cache = AdaptiveCache(max_memory_mb=1000, compression_threshold_kb=1)

# # TESTE DOS POLICIES TTL, TTI e MAX_ACCESS

def generate_random_data(size_kb=10):
    """Gera uma string de dados aleatórios."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=size_kb * 1024))

teste = generate_random_data(100)
print('TAMANHO DO ARQUIVO', sys.getsizeof(teste))
print('TAMANHO QUE DEVE COMPRIMIR', cache.compression_threshold_kb)


cache.put(
    key=f"teste_ttl_6_segundos",
    value=generate_random_data(300),
    policy=CachePolicy().with_ttl(timedelta(minutes=0.1)).with_tti(timedelta(minutes=1))
)

cache.put(
    key=f"teste_tti_12_segundos",
    value=generate_random_data(100),
    policy=CachePolicy().with_ttl(timedelta(minutes=10)).with_tti(timedelta(minutes=0.2))
)

cache.put(
    key=f"teste_max_access_30",
    value=generate_random_data(20),
    policy=CachePolicy().with_ttl(timedelta(minutes=10)).with_tti(timedelta(minutes=1)).with_max_access(30)
)

cache.put(
    key=f"key_tenis",
    value=generate_random_data(18),
    policy=CachePolicy().with_ttl(timedelta(minutes=100)).with_tti(timedelta(minutes=100)).with_max_access(100000)
)

cache.get("teste_ttl_6_segundos")
cache.get("teste_tti_12_segundos")
cache.get("teste_max_access_30")
cache.get("key_tenis")
cache.get("key_nao_existe")

time.sleep(2)

# Configuração específica para Black Friday com 
cache.configure_adaptive_behavior(
    hot_key_threshold=100,  # acessos/minuto
    enable_predictive_loading=True,
    compression_ratio_target=0.7
)

for i in range(0,31):
    cache.get("teste_max_access_30")

for i in range(0,103):
    cache.get("key_tenis")

time.sleep(13)

# TESTE DE HOT KEYS E LRU
for i in range(0, 150):
    cache.put(
    key=f"user:{i}",
    value='teste',
    policy=CachePolicy().with_ttl(timedelta(minutes=0.1)).with_tti(timedelta(minutes=1))
)
    
print(cache.get("user:129"))

for i in range(0,150):
    cache.get("user:129")

cache.put( 
    key=f"O 129 tem que estar no final da lista",
    value=generate_random_data(100),
    policy=CachePolicy().with_ttl(timedelta(minutes=0.1)).with_tti(timedelta(minutes=1))
)


# Item que expira após 100 acessos
cache.put(key="config:app", value='Teste para saber se esta funcionando', policy=CachePolicy().with_max_access(100))

for i in range(0,110):
    cache.get("config:app")

# Renovar TTL sem recriar o objeto

cache.put( 
    key=f"renovando politica",
    value='teste',
    policy=CachePolicy().with_ttl(timedelta(minutes=0.1)).with_tti(timedelta(minutes=1))
)

cache.get("renovando politica")

cache.refresh_policy(
    key="renovando politica", policy=CachePolicy().with_ttl(timedelta(minutes=10))
)

cache.get("renovando politica")

# TESTE DE BATCH OPERATIONS
with cache.batch_operation() as batch:
    batch.put("product:456", 'teste_produto_456')
    batch.put("product:789", 'teste_produto_789')
    batch.put("product:124", 'teste_produto_124')
    batch.put("product:245", 'teste_produto_245')
    batch.put("product:678", 'teste_produto_678')
    batch.put("product:009", 'teste_produto_009')
    # Commit automático ao sair do contexto


print('CACHE DATA', cache.cache_data)
print('LRU_QUEUE', cache.lru_queue)
print('HOT_KEYS', cache.hot_keys)
