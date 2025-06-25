# Sistema de Monitoramento Inteligente de Preços

Este sistema realiza buscas automatizadas de produtos no Google Shopping e exibe os resultados de forma organizada em uma interface web local.

## Funcionalidades

- Pesquisar produtos individuais ou em lote
- Exibir resultados organizados por produto
- Visualizar relatórios de buscas anteriores
- Interface responsiva e amigável

## Requisitos

- Python 3.8+
- Chrome ou Chromium instalado no sistema
- Pacotes Python listados em requirements.txt

## Instalação

1. Clone o repositório ou baixe os arquivos
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

## Como Usar

### Modo Interface Web

1. Execute o servidor web:

```bash
python app.py
```

2. Abra seu navegador em: `http://localhost:5000`

3. Use a interface para realizar buscas individuais ou em massa.

### Modo Linha de Comando

Para executar via linha de comando:

```bash
# Para buscar um único produto
python main.py

# Para buscar múltiplos produtos
python multi_buscador.py
```

## Estrutura de Arquivos

- `app.py`: Aplicativo Flask para a interface web
- `main.py`: Script principal para busca de produtos
- `multi_buscador.py`: Gerencia buscas múltiplas em paralelo
- `templates/`: Arquivos HTML da interface web
- `static/`: Arquivos CSS e JavaScript
- `resultados/`: Resultados das buscas em formato JSON
- `produtos.txt`: Lista padrão de produtos para busca

## Notas

- O sistema usa o Chrome em modo headless para realizar as buscas
- Os resultados são armazenados em arquivos JSON na pasta "resultados"
- Os relatórios das buscas são gerados na pasta raiz

---

Desenvolvido em 2025 - Sistema de Monitoramento Inteligente de Preços.
