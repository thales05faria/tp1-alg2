"""Geohash """
import math

BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"
KM_POR_GRAU = 111.32


def encode(lat, lon, precisao=8):
    """Converte (lat, lon) em um geohash"""
    lat_i = [-90.0, 90.0]
    lon_i = [-180.0, 180.0]
    saida = []
    bits = 0
    n_bits = 0
    par = True  
    while len(saida) < precisao:
        intervalo, valor = (lon_i, lon) if par else (lat_i, lat)
        meio = (intervalo[0] + intervalo[1]) / 2
        if valor >= meio:
            bits = (bits << 1) | 1
            intervalo[0] = meio
        else:
            bits = bits << 1
            intervalo[1] = meio
        par = not par
        n_bits += 1
        if n_bits == 5:
            saida.append(BASE32[bits])
            bits = 0
            n_bits = 0
    return "".join(saida)


def decode_bbox(geohash):
    """Retorna (lat_min, lat_max, lon_min, lon_max) do geohash."""
    lat_i = [-90.0, 90.0]
    lon_i = [-180.0, 180.0]
    par = True
    for ch in geohash:
        valor = BASE32.index(ch)
        for mascara in (16, 8, 4, 2, 1):
            intervalo = lon_i if par else lat_i
            meio = (intervalo[0] + intervalo[1]) / 2
            if valor & mascara:
                intervalo[0] = meio
            else:
                intervalo[1] = meio
            par = not par
    return lat_i[0], lat_i[1], lon_i[0], lon_i[1]


def decode(geohash):
    #centro da célula
    lat_min, lat_max, lon_min, lon_max = decode_bbox(geohash)
    return (lat_min + lat_max) / 2, (lon_min + lon_max) / 2


def vizinhos(geohash):
    #Geohashes adjacentes
    lat_min, lat_max, lon_min, lon_max = decode_bbox(geohash)
    d_lat = lat_max - lat_min
    d_lon = lon_max - lon_min
    c_lat = (lat_min + lat_max) / 2
    c_lon = (lon_min + lon_max) / 2
    resultado = set()
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            if i == 0 and j == 0:
                continue
            lat = c_lat + i * d_lat
            lon = c_lon + j * d_lon
            if lat < -90 or lat > 90:
                continue
            lon = ((lon + 180) % 360) - 180
            resultado.add(encode(lat, lon, len(geohash)))
    resultado.discard(geohash)
    return resultado


def escolher_precisao(lat, raio_km, maximo=8):

    for p in range(maximo, 0, -1):
        bits_lon = (5 * p + 1) // 2
        bits_lat = (5 * p) // 2
        altura_km = (180 / 2 ** bits_lat) * KM_POR_GRAU
        largura_km = (360 / 2 ** bits_lon) * KM_POR_GRAU * math.cos(math.radians(lat))
        if min(altura_km, largura_km) >= raio_km:
            return p
    return 1
