import math
import os
import time

import dash_leaflet as dl
from dash import Dash, Input, Output, State, dash_table, dcc, html,no_update
from dash.exceptions import PreventUpdate

from entregadores.busca import VELOCIDADE_MEDIA_KMH, buscar
from entregadores.dados import carregar_bares
from entregadores.gerador import carregar_grafo, gerar_posicoes, projetar_na_rua
from entregadores.geohash import encode
from entregadores.trie import TrieCompacta

CSV_BARES = os.environ.get("CSV_BARES", "data/bares.csv")
CACHE_GRAFO = os.environ.get("CACHE_GRAFO", "data/grafo.graphml")

BARES = carregar_bares(CSV_BARES)

ESTADO = {"trie": TrieCompacta(), "posicoes": {}, "grafo": None}

app = Dash(__name__, title="Entregadores próximos")
server = app.server


def cartao(titulo, valor):
    return html.Div([html.Div(titulo, className="cartao-titulo"),
                     html.Div(valor, className="cartao-valor")], className="cartao")


app.layout = html.Div([
    html.Header(html.H1("TP1 - Entregadores próximos")),
    html.Div([
        html.Aside([
            html.H3("Consulta"),
            html.Label("Restaurante / bar"),
            dcc.Dropdown(id="restaurante", clearable=False,
                         options=[{"label": b["nome"], "value": i} for i, b in enumerate(BARES)],
                         value=0),
            html.Label("Raio de atendimento (km)"),
            dcc.Input(id="raio", type="text", value="2", debounce=True),
            html.Hr(),
            html.H3("Simulação da frota"),
            html.Label("Quantidade de entregadores (N)"),
            dcc.Input(id="n-entregadores", type="text", value="200"),
            html.Button("Gerar Entregadores", id="btn-gerar", n_clicks=0),
            dcc.Loading(html.Div(id="msg-gerar", className="msg")),
            html.Hr(),
            html.H3("Legenda"),
            html.Div([html.Span(className="ponto vermelho"), " Dentro do raio"]),
            html.Div([html.Span(className="ponto cinza"), " Candidato descartado"]),
            html.Div([html.Span(className="ponto azul"), " Restaurante / raio"]),
            html.Small(f"Tempo estimado a {VELOCIDADE_MEDIA_KMH} km/h (linha reta)."),
        ], className="painel"),
        html.Main([
            html.Div(id="metricas", className="metricas"),
            dl.Map([dl.TileLayer(url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                                 attribution="© OpenStreetMap contributors"),
                    dl.LayerGroup(id="camada")],
                   id="mapa", center=[BARES[0]["lat"], BARES[0]["lon"]], zoom=14,
                   style={"height": "480px"}),
            html.H3("Entregadores dentro do raio (mais próximos primeiro)"),
            dash_table.DataTable(
                id="tabela", page_size=10, sort_action="native",
                columns=[{"name": "ID do entregador", "id": "id"},
                         {"name": "Distância (km)", "id": "distancia_km"},
                         {"name": "Tempo estimado (min)", "id": "tempo_min"}],
                style_header={"fontWeight": "600", "backgroundColor": "#f1f5f9"},
                style_cell={"padding": "8px", "fontFamily": "inherit", "textAlign": "left"}),
        ], className="principal"),
    ], className="conteudo"),
    dcc.Store(id="versao", data=0),
])



@app.callback(Output("versao", "data"), Output("msg-gerar", "children"),
              Input("btn-gerar", "n_clicks"), State("n-entregadores", "value"),
              prevent_initial_call=True)
def gerar(_, n):
    try:
        n = int(str(n).strip())
    except (TypeError, ValueError):
        return no_update, "Informe um número inteiro de entregadores."
    if n < 1:
        return no_update, "Informe um número inteiro de entregadores."
    n = min(n, 5000)
    inicio = time.perf_counter()

    ESTADO["trie"] = TrieCompacta()
    ESTADO["posicoes"] = {}

    pontos = gerar_posicoes(BARES, n)
    aviso = ""
    try:
        if ESTADO["grafo"] is None:
            ESTADO["grafo"] = carregar_grafo(BARES, CACHE_GRAFO)
        pontos = projetar_na_rua(ESTADO["grafo"], pontos)
    except Exception as erro:
        aviso = f" Sem correção viária ({type(erro).__name__}: {erro})."

    for eid, (lat, lon) in enumerate(pontos):
        ESTADO["posicoes"][eid] = (lat, lon)
        ESTADO["trie"].inserir(encode(lat, lon, 8), eid)

    seg = time.perf_counter() - inicio
    return time.time(), f"{n} entregadores gerados em {seg:.1f} s.{aviso}"


@app.callback(Output("camada", "children"), Output("mapa", "viewport"),
              Output("tabela", "data"), Output("metricas", "children"),
              Input("restaurante", "value"), Input("raio", "value"), Input("versao", "data"))
def atualizar(idx, raio, _versao):
    if idx is None:
        raise PreventUpdate
    bar = BARES[idx]
    try:
        raio = float(str(raio).replace(",", "."))
    except (TypeError, ValueError):
        raio = 2
    if raio <= 0:
        raio = 2
    raio = min(raio, 20)
    zoom = int(max(11, min(15, 15 - math.log2(max(raio, 0.5)))))
    viewport = {"center": [bar["lat"], bar["lon"]], "zoom": zoom, "transition": "flyTo"}

    camada = [
        dl.Circle(center=[bar["lat"], bar["lon"]], radius=raio * 1000,
                  color="#2563eb", weight=2, fillOpacity=0.05),
        dl.Marker(position=[bar["lat"], bar["lon"]], children=dl.Tooltip(bar["nome"])),
    ]
    if not ESTADO["posicoes"]:
        msg = cartao("Frota", "Clique em “Gerar Entregadores” para começar")
        return camada, viewport, [], [msg]

    r = buscar(ESTADO["trie"], ESTADO["posicoes"], bar["lat"], bar["lon"], raio)

    def pino(e, cor):
        return dl.CircleMarker(
            center=[e["lat"], e["lon"]], radius=6, color=cor, fillColor=cor, fillOpacity=0.9,
            weight=1, children=dl.Tooltip(
                f"Entregador {e['id']} · {e['distancia_km']:.2f} km · {e['tempo_min']:.1f} min"))

    camada += [pino(e, "#9ca3af") for e in r["fora"]]
    camada += [pino(e, "#dc2626") for e in r["dentro"]]

    tabela = [{"id": e["id"], "distancia_km": round(e["distancia_km"], 2),
               "tempo_min": round(e["tempo_min"], 1)} for e in r["dentro"]]
    dist = [e["distancia_km"] for e in r["dentro"]]
    metricas = [
        cartao("Entregadores na frota", len(ESTADO["posicoes"])),
        cartao("Dentro do raio", len(r["dentro"])),
        cartao("Descartados", len(r["fora"])),
        cartao("Distância média", f"{sum(dist) / len(dist):.2f} km" if dist else "—"),
        cartao("Mais próximo", f"{min(dist):.2f} km" if dist else "—"),
        cartao("Tempo da consulta", f"{r['tempo_ms']:.2f} ms"),
    ]
    print(f"[consulta] {bar['nome']} raio={raio} km -> {len(r['dentro'])} entregadores, "
          f"{r['tempo_ms']:.3f} ms")
    return camada, viewport, tabela, metricas


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
