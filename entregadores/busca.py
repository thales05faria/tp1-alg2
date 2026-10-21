#Consulta: Geohash -> Trie 
import time

from .geohash import encode, escolher_precisao, vizinhos
from .geometria import haversine_km, tempo_minutos

VELOCIDADE_MEDIA_KMH = 25  # velocidade assumida para estimar o tempo de chegada


def buscar(trie, posicoes, lat, lon, raio_km, velocidade_kmh=VELOCIDADE_MEDIA_KMH):
    """posicoes"""
    inicio = time.perf_counter()

    geohash = encode(lat, lon, 8)
    precisao = escolher_precisao(lat, raio_km)
    prefixo = geohash[:precisao]
    prefixos = {prefixo} | vizinhos(prefixo)  # elimina o problema de borda

    candidatos = []
    for p in prefixos:
        candidatos.extend(trie.buscar_prefixo(p))

    dentro, fora = [], []
    for eid in candidatos:
        e_lat, e_lon = posicoes[eid]
        d = haversine_km(lat, lon, e_lat, e_lon)
        item = {"id": eid, "lat": e_lat, "lon": e_lon, "distancia_km": d,
                "tempo_min": tempo_minutos(d, velocidade_kmh)}
        (dentro if d <= raio_km else fora).append(item)
    dentro.sort(key=lambda x: x["distancia_km"])

    tempo_ms = (time.perf_counter() - inicio) * 1000
    return {"geohash": geohash, "prefixo": prefixo, "precisao": precisao,
            "n_prefixos": len(prefixos), "candidatos": len(candidatos),
            "dentro": dentro, "fora": fora, "tempo_ms": tempo_ms}


def buscar_forca_bruta(posicoes, lat, lon, raio_km):
    return sorted(eid for eid, (a, b) in posicoes.items()
                  if haversine_km(lat, lon, a, b) <= raio_km)
