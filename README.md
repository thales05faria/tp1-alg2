# TP1 – Indexação Geoespacial e Geometria Computacional Híbrida (DCC207 – Algoritmos 2)

Motor de busca de entregadores próximos a um restaurante em Belo Horizonte, usando
**Geohash (8 níveis, Base32)** + **Trie compacta** + **filtragem geométrica por raio**,
com mapa interativo em Dash/Leaflet.

Autor: Thales Faria Almeida

## Como executar

Requer Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate          
pip install -r requirements.txt
python app.py
```

Abra http://localhost:8050.


### Preparando o CSV de bares
O CSV original só tem endereços (`DESC_LOGRADOURO`, `NOME_LOGRADOURO`, `NUMERO_IMOVEL`, `NOME_BAIRRO`,
`NOME_FANTASIA`...), sem coordenadas. O script abaixo geocodifica os endereços (Nominatim/OpenStreetMap,
~1 requisição por segundo) e gera o `data/bares.csv` com `nome,latitude,longitude`, que é o que o app lê.

```bash
# 1. salve o CSV original como data/bares_original.csv
# 2. geocodifique 
python -m scripts.geocodificar --limite 60
python -m scripts.geocodificar --bairro SAVASSI --limite 40
python -m scripts.geocodificar --cnae "BARES" --limite 60
```
O nome usado é `NOME_FANTASIA` (ou `NOME`, se estiver vazio). Os resultados ficam em
`data/geocache.json`, então se o script for interrompido basta rodar de novo.
O `data/bares.csv` que acompanha o projeto é apenas um exemplo.


### Uso da interface
1. Informe **N** e clique em **Gerar Entregadores** (descarta a frota anterior e cria uma nova).
   Na primeira vez o grafo viário do OpenStreetMap é baixado e fica em
   cache em `data/grafo.graphml`.
2. Escolha o **restaurante** e o **raio**: mapa, tabela e métricas atualizam sozinhos.

Se o grafo não puder ser baixado, a frota é gerada **sem** correção viária e a interface avisa.

## Estrutura

| Arquivo | Conteúdo |
|---|---|
| `entregadores/geohash.py` | encode/decode, vizinhos, escolha da precisão |
| `entregadores/trie.py` | Trie compacta (radix) com busca por prefixo O(m + k) |
| `entregadores/busca.py` | consulta completa: Geohash → Trie (célula + 8 vizinhas) → filtro por raio |
| `entregadores/gerador.py` | distribuição normal por bar + projeção na rua (osmnx) |
| `entregadores/dados.py` | leitura do CSV de bares |
| `scripts/geocodificar.py` | endereços do CSV original → `data/bares.csv` com lat/lon |
| `app.py`, `assets/style.css` | interface |
| `tests/test_core.py` | testes (inclui comparação com força bruta) |
| `scripts/benchmark.py` | tempos Trie × força bruta para vários N e raios |
| `RELATORIO.md` | relatório |

## Testes e benchmark

```bash
python -m tests.test_core
python -m scripts.benchmark
```
