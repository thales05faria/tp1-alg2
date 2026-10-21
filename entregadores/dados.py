"""Leitura do csv de bares"""
import csv
import io

COLUNAS_NOME = ("nome", "name", "bar", "restaurante", "estabelecimento")
COLUNAS_LAT = ("latitude", "lat", "y")
COLUNAS_LON = ("longitude", "lon", "lng", "long", "x")


def _achar(colunas, candidatos):
    por_minusculo = {c.strip().lower(): c for c in colunas}
    for cand in candidatos:
        if cand in por_minusculo:
            return por_minusculo[cand]
    return None


def _numero(texto):
    return float(str(texto).strip().replace(",", "."))


def ler_csv(caminho):
    """Lê o CSv e retorna (colunas, linhas)"""
    texto = None
    for codificacao in ("utf-8-sig", "latin-1"):
        try:
            with open(caminho, encoding=codificacao, newline="") as f:
                texto = f.read()
            break
        except UnicodeDecodeError:
            continue
    if texto is None:
        raise ValueError(f"Não foi possível ler {caminho}")
    primeira_linha = texto.splitlines()[0]
    try:
        delimitador = csv.Sniffer().sniff(primeira_linha, delimiters=",;\t").delimiter
    except csv.Error:
        delimitador = ","
    leitor = csv.DictReader(io.StringIO(texto), delimiter=delimitador)
    return leitor.fieldnames, list(leitor)


def carregar_bares(caminho):
    #Retorna lista {"nome", "lat", "lon"}
    colunas, linhas = ler_csv(caminho)
    col_nome = _achar(colunas, COLUNAS_NOME)
    col_lat = _achar(colunas, COLUNAS_LAT)
    col_lon = _achar(colunas, COLUNAS_LON)
    if col_lat is None or col_lon is None:
        raise ValueError(
            f"Colunas de latitude/longitude não encontradas. Colunas do CSV: {colunas}. "
            f"Ajuste COLUNAS_LAT/COLUNAS_LON em entregadores/dados.py."
        )

    bares = []
    for i, linha in enumerate(linhas, start=1):
        try:
            lat = _numero(linha[col_lat])
            lon = _numero(linha[col_lon])
        except (ValueError, TypeError):
            continue  # ignora linhas sem coordenadas válidas
        nome = (linha.get(col_nome) or "").strip() if col_nome else ""
        bares.append({"nome": nome or f"Bar {i}", "lat": lat, "lon": lon})
    if not bares:
        raise ValueError("Nenhum bar com coordenadas válidas no CSV.")
    return bares
