"""Testes: python -m tests.test_core """
import randomgit 

from entregadores.busca import buscar, buscar_forca_bruta
from entregadores.geohash import decode, encode, vizinhos
from entregadores.trie import TrieCompacta


def test_geohash_conhecido():
    assert encode(57.64911, 10.40744, 8) == "u4pruydq"
    assert encode(-19.9191, -43.9386, 8).startswith("7h2y")  # região de BH


def test_decode_contem_ponto():
    lat, lon = -19.9191, -43.9386
    c_lat, c_lon = decode(encode(lat, lon, 8))
    assert abs(c_lat - lat) < 0.001 and abs(c_lon - lon) < 0.001


def test_vizinhos():
    v = vizinhos("7h2y8")
    assert len(v) == 8 and "7h2y8" not in v


def test_trie_prefixos():
    t = TrieCompacta()
    for i, chave in enumerate(["7h2y8abc", "7h2y8abd", "7h2y8xyz", "7h2y9aaa", "7h300000"]):
        t.inserir(chave, i)
    t.inserir("7h2y8abc", 99)  # duplicado: mesma chave, outro valor
    assert sorted(t.buscar_prefixo("7h2y8abc")) == [0, 99]
    assert sorted(t.buscar_prefixo("7h2y8ab")) == [0, 1, 99]
    assert sorted(t.buscar_prefixo("7h2y")) == [0, 1, 2, 3, 99]
    assert sorted(t.buscar_prefixo("7h")) == [0, 1, 2, 3, 4, 99]
    assert t.buscar_prefixo("7h2yz") == []
    assert t.buscar_prefixo("zzz") == []


def test_busca_igual_forca_bruta():
    rng = random.Random(1)
    posicoes = {i: (-19.92 + rng.uniform(-0.05, 0.05), -43.94 + rng.uniform(-0.05, 0.05))
                for i in range(3000)}
    trie = TrieCompacta()
    for eid, (la, lo) in posicoes.items():
        trie.inserir(encode(la, lo, 8), eid)
    for _ in range(50):
        lat = -19.92 + rng.uniform(-0.05, 0.05)
        lon = -43.94 + rng.uniform(-0.05, 0.05)
        raio = rng.choice([0.3, 1, 2, 4, 6])
        r = buscar(trie, posicoes, lat, lon, raio)
        assert sorted(x["id"] for x in r["dentro"]) == buscar_forca_bruta(posicoes, lat, lon, raio)


if __name__ == "__main__":
    for nome, fn in list(globals().items()):
        if nome.startswith("test_"):
            fn()
            print("ok", nome)
