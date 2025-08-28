# CACHE ADAPTATIVO

AdaptiveCache: Gerenciador de Cache Inteligente em Python
Este projeto implementa um gerenciador de cache adaptativo em memória para aplicações Python. Ele utiliza diversas estratégias de otimização, como políticas de expiração (TTL e TTI), compressão de dados, identificação de chaves "quentes" e carregamento preditivo, para melhorar o desempenho e o uso de memória.

Funcionalidades Principais
Políticas de Expiração: Itens são removidos do cache com base em:

TTL (Time-to-Live): Tempo de vida máximo desde a criação.

TTI (Time-to-Idle): Tempo máximo de inatividade desde o último acesso.

Max Access: Número máximo de acessos permitidos.

Gerenciamento de Memória: O cache remove automaticamente os itens menos recentemente usados (LRU) quando o limite de memória é atingido.

Compressão de Dados: Dados maiores que um limite configurável são comprimidos com zlib para economizar memória.

Chaves "Quentes" (Hot Keys): O cache monitora a frequência de acesso e identifica chaves populares, protegendo-as da remoção por LRU.

Carregamento Preditivo: Com base em chaves "quentes" identificadas, o cache pode pré-carregar dados relacionados para otimizar o tempo de acesso.

Operações em Lote: O uso de context manager permite agrupar operações (put) para processamento em lote, melhorando a eficiência em cenários de alta carga.

## Instalação

Para rodar o projeto, você precisa instalar as seguintes dependências.

```
pip install pydantic
pip install freezegun
```

A biblioteca pydantic é usada para a validação de dados da classe CachePolicy. A freezegun é utilizada nos testes para simular o tempo.

### Como Utilizar

O código principal reside na classe AdaptiveCache. Você pode instanciá-la e usar seus métodos para interagir com o cache.

```
# Exemplo de uso
from seu_modulo_aqui import AdaptiveCache, CachePolicy, BatchOperation
from datetime import timedelta

# Instancia o cache com limite de 100MB e compressão a partir de 50KB
cache = AdaptiveCache(max_memory_mb=100, compression_threshold_kb=50)

# 1. Adicionar um item com política de TTL de 60 segundos
policy_ttl = CachePolicy().with_ttl(timedelta(seconds=60))
cache.put("user:123", "Dados do usuario 123", policy=policy_ttl)

# 2. Ler um item do cache
dados_usuario = cache.get("user:123")
print(f"Dados do cache: {dados_usuario}")

# 3. Usar operações em lote para adicionar vários itens
with cache.batch_operation() as batch:
    batch.put("product:456", "Dados do produto 456")
    batch.put("product:789", "Dados do produto 789")
# As operações são executadas automaticamente ao sair do bloco 'with'

# 4. Habilitar o carregamento preditivo e o monitoramento
cache.configure_adaptive_behavior(
    hot_key_threshold=10, 
    enable_predictive_loading=True, 
    compression_ratio_target=0.7
)
```

## Como Rodar os Testes

Verifique se o seu código está em um arquivo que possa ser importado.

No arquivo testes.py, ajuste o import:

```
from seu_modulo_aqui import AdaptiveCache, CachePolicy, BatchOperation
```

Execute o arquivo de teste a partir do seu terminal:

```
python -m unittest testes.py
```

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
```

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [Dropwizard](http://www.dropwizard.io/1.0.2/docs/) - The web framework used
* [Maven](https://maven.apache.org/) - Dependency Management
* [ROME](https://rometools.github.io/rome/) - Used to generate RSS Feeds

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Billie Thompson** - *Initial work* - [PurpleBooth](https://github.com/PurpleBooth)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc

