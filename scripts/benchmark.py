import random
import statistics
import time

from entregadores.busca import buscar, buscar_forca_bruta
from entregadores.dados import carregar_bares
from entregadores.gerador import gerar_posicoes
from entregadores.geohash import encode
from entregadores.trie import TrieCompacta

RAIOS_KM = (0.3, 2)
CONSULTAS = 100


def main():
    bares = carregar_bares("data/bares.csv")
    print(f"{'raio':>5} {'N':>8} {'trie (ms)':>10} {'bruta (ms)':>11} {'candidatos':>11} {'dentro':>7} {'nós':>8}")
    for raio, n in [(r, n) for r in RAIOS_KM for n in (1_000, 10_000, 100_000, 500_000)]:
        pontos = gerar_posicoes(bares, n, seed=42)
        posicoes = dict(enumerate(pontos))
        trie = TrieCompacta()
        for eid, (la, lo) in posicoes.items():
            trie.inserir(encode(la, lo, 8), eid)

        t_trie, t_bruta, cands, dentro = [], [], [], []
        for _ in range(CONSULTAS):
            bar = random.choice(bares)
            r = buscar(trie, posicoes, bar["lat"], bar["lon"], raio)
            t_trie.append(r["tempo_ms"])
            cands.append(r["candidatos"])
            dentro.append(len(r["dentro"]))
            t0 = time.perf_counter()
            ref = buscar_forca_bruta(posicoes, bar["lat"], bar["lon"], raio)
            t_bruta.append((time.perf_counter() - t0) * 1000)
            assert sorted(x["id"] for x in r["dentro"]) == ref
        print(f"{raio:>5} {n:>8} {statistics.mean(t_trie):>10.3f} {statistics.mean(t_bruta):>11.3f} "
              f"{statistics.mean(cands):>11.0f} {statistics.mean(dentro):>7.0f} {trie.contar_nos():>8}")


if __name__ == "__main__":
    main()
