from adaptive_cache import AdaptiveCache, CachePolicy
from datetime import timedelta

cache = AdaptiveCache(max_memory_mb=100)

# Item com TTL de 5 minutos E TTI de 1 minuto
cache.put(
    key="user:123",
    value=user_data,
    policy=CachePolicy().with_ttl(timedelta(minutes=5)).with_tti(timedelta(minutes=1)),
)

# Item que expira após 100 acessos
cache.put(key="config:app", value=config, policy=CachePolicy().with_max_access(100))

# Renovar TTL sem recriar o objeto
cache.refresh_policy(
    key="user:123", policy=CachePolicy().with_ttl(timedelta(minutes=10))
)

# Cache warming baseado em padrões
cache.predictive_load()  # Analisa histórico e pré-carrega

# Uso com context manager para auto-cleanup
with cache.batch_operation() as batch:
    batch.put("product:456", product_data)
    batch.put("product:789", another_product)
    # Commit automático ao sair do contexto
