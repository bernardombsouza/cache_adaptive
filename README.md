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

### Prerequisites

What things you need to install the software and how to install them

```
Give examples
```

### Installing

A step by step series of examples that tell you how to get a development env running

Say what the step will be

```
Give the example
```

And repeat

```
until finished
```

End with an example of getting some data out of the system or using it for a little demo

## Running the tests

Explain how to run the automated tests for this system

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

