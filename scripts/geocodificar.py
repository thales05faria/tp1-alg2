"""Converte o CSV de endereços (sem lat/lon) em data/bares.csv com coordenadas.

Exemplos:
  python -m scripts.geocodificar --entrada data/bares_original.csv --limite 60
  python -m scripts.geocodificar --entrada data/bares_original.csv --bairro SAVASSI --limite 40
"""
import argparse
import csv
import json
import os
import time
import urllib.parse
import urllib.request

from entregadores.dados import ler_csv

URL = "https://nominatim.openstreetmap.org/search"
AGENTE = "tp1-alg2-ufmg/1.0 (trabalho academico)"
LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = -20.06, -19.77, -44.07, -43.85


def _col(colunas, nome):
    for c in colunas:
        if c.strip().lower() == nome:
            return c
    return None


def montar_consultas(linha, c):
    tipo = (linha.get(c["tipo"]) or "").strip()
    rua = (linha.get(c["rua"]) or "").strip()
    num = (linha.get(c["num"]) or "").strip()
    bairro = (linha.get(c["bairro"]) or "").strip()
    logradouro = f"{tipo} {rua}".strip()
    fim = "Belo Horizonte, Minas Gerais, Brasil"
    consultas = []
    if num and num not in ("0", "S/N", "SN"):
        consultas.append(f"{logradouro}, {num}, {bairro}, {fim}")
    consultas.append(f"{logradouro}, {bairro}, {fim}")
    return consultas


def geocodificar(consulta):
    params = urllib.parse.urlencode(
        {"q": consulta, "format": "json", "limit": 1, "countrycodes": "br"})
    req = urllib.request.Request(f"{URL}?{params}", headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(req, timeout=20) as resposta:
        dados = json.load(resposta)
    if dados:
        return float(dados[0]["lat"]), float(dados[0]["lon"])
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default="data/bares_original.csv")
    ap.add_argument("--saida", default="data/bares.csv")
    ap.add_argument("--cache", default="data/geocache.json")
    ap.add_argument("--limite", type=int, default=60, help="máximo de bares na saída")
    ap.add_argument("--bairro", help="mantém só bares cujo bairro contém este texto")
    ap.add_argument("--cnae", help="mantém só linhas cuja DESCRICAO_CNAE_PRINCIPAL contém este texto")
    args = ap.parse_args()

    colunas, linhas = ler_csv(args.entrada)
    c = {"tipo": _col(colunas, "desc_logradouro"), "rua": _col(colunas, "nome_logradouro"),
         "num": _col(colunas, "numero_imovel"), "bairro": _col(colunas, "nome_bairro"),
         "fantasia": _col(colunas, "nome_fantasia"), "nome": _col(colunas, "nome"),
         "cnae": _col(colunas, "descricao_cnae_principal")}
    if not c["rua"] or not c["bairro"]:
        raise SystemExit(f"Colunas de endereço não encontradas: {colunas}")

    cache = {}
    if os.path.exists(args.cache):
        with open(args.cache, encoding="utf-8") as f:
            cache = json.load(f)

    resultado, vistos = [], set()
    for linha in linhas:
        if len(resultado) >= args.limite:
            break
        if args.bairro and args.bairro.lower() not in (linha.get(c["bairro"]) or "").lower():
            continue
        if args.cnae and c["cnae"] and args.cnae.lower() not in (linha.get(c["cnae"]) or "").lower():
            continue
        nome = ((linha.get(c["fantasia"]) if c["fantasia"] else "") or
                (linha.get(c["nome"]) if c["nome"] else "") or "").strip()
        if not nome:
            continue

        coord = None
        for consulta in montar_consultas(linha, c):
            if consulta not in cache:
                try:
                    achado = geocodificar(consulta)
                except Exception as erro:
                    print(f"  erro de rede ({erro}); tente novamente mais tarde")
                    achado = None
                cache[consulta] = list(achado) if achado else None
                with open(args.cache, "w", encoding="utf-8") as f:
                    json.dump(cache, f, ensure_ascii=False)
                time.sleep(1.1)  # limite do Nominatim: 1 requisição/segundo
            if cache[consulta]:
                coord = cache[consulta]
                break

        if not coord or not (LAT_MIN <= coord[0] <= LAT_MAX and LON_MIN <= coord[1] <= LON_MAX):
            print(f"  sem coordenada: {nome}")
            continue
        chave = (nome, round(coord[0], 5), round(coord[1], 5))
        if chave in vistos:
            continue
        vistos.add(chave)
        resultado.append({"nome": nome, "latitude": coord[0], "longitude": coord[1]})
        print(f"[{len(resultado)}/{args.limite}] {nome} -> {coord[0]:.5f}, {coord[1]:.5f}")

    with open(args.saida, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["nome", "latitude", "longitude"])
        w.writeheader()
        w.writerows(resultado)
    print(f"\n{len(resultado)} bares salvos em {args.saida}")


if __name__ == "__main__":
    main()
