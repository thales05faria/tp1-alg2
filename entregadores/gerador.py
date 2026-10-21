#Gerador de entregadores
import math
import os
import random

SIGMA_PADRAO_M = 500  # desvio padrão da distribuição normal, em metros
M_POR_GRAU = 111_320


def gerar_posicoes(bares, n, sigma_m=SIGMA_PADRAO_M, seed=None):
    rng = random.Random(seed)
    base, resto = divmod(n, len(bares))
    pontos = []
    for i, bar in enumerate(bares):
        quantidade = base + (1 if i < resto else 0)
        for _ in range(quantidade):
            d_lat = rng.gauss(0, sigma_m) / M_POR_GRAU
            d_lon = rng.gauss(0, sigma_m) / (M_POR_GRAU * math.cos(math.radians(bar["lat"])))
            pontos.append((bar["lat"] + d_lat, bar["lon"] + d_lon))
    return pontos


def carregar_grafo(bares, caminho_cache="data/grafo.graphml", margem_graus=0.02):
    """Baixa o grafo da região dos bares e guarda em cache"""
    import osmnx as ox

    if os.path.exists(caminho_cache):
        return ox.load_graphml(caminho_cache)
    oeste = min(b["lon"] for b in bares) - margem_graus
    leste = max(b["lon"] for b in bares) + margem_graus
    sul = min(b["lat"] for b in bares) - margem_graus
    norte = max(b["lat"] for b in bares) + margem_graus
    grafo = ox.graph_from_bbox((oeste, sul, leste, norte), network_type="drive")
    ox.save_graphml(grafo, caminho_cache)
    return grafo


def projetar_na_rua(grafo, pontos):
    #Move cada (lat, lon) para o nó  mais próximo
    import osmnx as ox

    lats = [p[0] for p in pontos]
    lons = [p[1] for p in pontos]
    nos = ox.distance.nearest_nodes(grafo, X=lons, Y=lats)
    return [(grafo.nodes[no]["y"], grafo.nodes[no]["x"]) for no in nos]
