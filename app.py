import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
import plotly.express as px
from datetime import datetime

# =========================
# CARREGAMENTO DOS DADOS
# =========================
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1yVuRDq2HL-ee4wmUxwXRM2icsMAWjIllcXHHISzpze8/export?format=csv"
    df = pd.read_csv(url)
    df["data_venda"] = pd.to_datetime(df["data_venda"], errors="coerce")
    df = df.dropna(subset=["data_venda"])
    return df


df_inicial = carregar_dados()

# =========================
# APP
# =========================
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True
)

server = app.server
app.title = "Recanto da Fé"

# =========================
# LAYOUT
# =========================
app.layout = dbc.Container(fluid=True, className="p-4", children=[

    # =========================
    # TÍTULO
    # =========================
    dbc.Row(
        dbc.Col(
            html.H1(
                "Recanto da Fé – Dashboard de Vendas",
                className="text-center fw-bold mb-4"
            )
        )
    ),

    # =========================
    # NAVEGAÇÃO
    # =========================
    dbc.Row(
        dbc.Col(
            dbc.ButtonGroup([
                dbc.Button("📊 Dashboard Geral", id="btn-geral", n_clicks=0, color="primary"),
                dbc.Button("👤 Dashboard por Vendedor", id="btn-vendedor", n_clicks=0, color="secondary"),
            ]),
            className="text-center mb-4"
        )
    ),

    dcc.Store(id="pagina-atual", data="geral"),

    # =========================
    # PÁGINA GERAL
    # =========================
    html.Div(id="pagina-geral", children=[

        # META
        dbc.Card(
            dbc.CardBody(
                dbc.Row([
                    dbc.Col(html.Label("🎯 Meta Mensal (R$)", className="fw-semibold"), md="auto"),
                    dbc.Col(
                        dbc.Input(id="input-meta", type="number", value=50000, min=0, step=100),
                        md=3
                    )
                ], align="center")
            ),
            className="mb-4 shadow-sm"
        ),

        # FILTROS
        dbc.Card(
            dbc.CardBody(
                dbc.Row([
                    dbc.Col([
                        html.Label("📅 Período"),
                        dcc.DatePickerRange(
                            id="filtro-data",
                            min_date_allowed=df_inicial["data_venda"].min(),
                            max_date_allowed=df_inicial["data_venda"].max(),
                            start_date=df_inicial["data_venda"].min(),
                            end_date=df_inicial["data_venda"].max(),
                            display_format="DD/MM/YYYY",
                            with_portal=True
                        )
                    ], md=4),

                    dbc.Col([
                        html.Label("🏷️ Categoria"),
                        dcc.Dropdown(
                            id="filtro-categoria",
                            options=[{"label": c, "value": c} for c in df_inicial["categoria"].unique()],
                            multi=True,
                            placeholder="Selecione",
                            menuPortalTarget="body",
                            menuPosition="fixed"
                        )
                    ], md=4),

                    dbc.Col([
                        html.Label("👤 Vendedor"),
                        dcc.Dropdown(
                            id="filtro-vendedor",
                            options=[{"label": v, "value": v} for v in df_inicial["vendedor"].unique()],
                            multi=True,
                            placeholder="Selecione",
                            menuPortalTarget="body",
                            menuPosition="fixed"
                        )
                    ], md=4),
                ])
            ),
            className="mb-4 shadow-sm"
        ),

        # KPIs
        dbc.Row(id="kpis", className="g-3 mb-4"),

        # GRÁFICOS
        dbc.Card(dbc.CardBody(dcc.Graph(id="grafico-faturamento-tempo")), className="mb-4 shadow-sm"),

        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id="grafico-categoria")), className="shadow-sm"), md=6),
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id="grafico-pagamento")), className="shadow-sm"), md=6),
        ], className="mb-4"),

        dbc.Card(dbc.CardBody(dcc.Graph(id="grafico-produtos")), className="mb-4 shadow-sm"),
        dbc.Card(dbc.CardBody(dcc.Graph(id="grafico-vendedores")), className="mb-4 shadow-sm"),
    ]),

    # =========================
    # PÁGINA VENDEDOR
    # =========================
    html.Div(id="pagina-vendedor", style={"display": "none"}, children=[

        dbc.Card(
            dbc.CardBody([
                html.H4("👤 Dashboard Individual do Vendedor", className="fw-bold mb-3"),
                dbc.Row(
                    dbc.Col(
                        dcc.Dropdown(
                            id="vendedor-individual",
                            options=[{"label": v, "value": v} for v in df_inicial["vendedor"].unique()],
                            placeholder="Escolha o vendedor"
                        ),
                        md=4
                    )
                )
            ]),
            className="mb-4 shadow-sm"
        ),

        dbc.Row(id="kpis-vendedor", className="g-3 mb-4"),
        dbc.Card(dbc.CardBody(dcc.Graph(id="grafico-vendedor-individual")), className="shadow-sm")
    ]),

    dcc.Interval(id="interval-atualizacao", interval=1800000),
    dcc.Store(id="dados-vendas"),
    dcc.Store(id="store-meta", data=50000)
])

# =========================
# CALLBACKS
# =========================
@app.callback(
    Output("pagina-atual", "data"),
    Input("btn-geral", "n_clicks"),
    Input("btn-vendedor", "n_clicks"),
    prevent_initial_call=True
)
def trocar_pagina(btn_geral, btn_vendedor):
    ctx = dash.callback_context
    botao = ctx.triggered[0]["prop_id"].split(".")[0]
    return "vendedor" if botao == "btn-vendedor" else "geral"


@app.callback(
    Output("pagina-geral", "style"),
    Output("pagina-vendedor", "style"),
    Input("pagina-atual", "data")
)
def mostrar_paginas(pagina):
    if pagina == "vendedor":
        return {"display": "none"}, {"display": "block"}
    return {"display": "block"}, {"display": "none"}


@app.callback(Output("store-meta", "data"), Input("input-meta", "value"))
def atualizar_meta(valor):
    return valor if valor and valor > 0 else 50000


@app.callback(Output("dados-vendas", "data"), Input("interval-atualizacao", "n_intervals"))
def atualizar_dados(_):
    return carregar_dados().to_dict("records")


@app.callback(
    Output("kpis", "children"),
    Output("grafico-faturamento-tempo", "figure"),
    Output("grafico-categoria", "figure"),
    Output("grafico-pagamento", "figure"),
    Output("grafico-produtos", "figure"),
    Output("grafico-vendedores", "figure"),
    Output("kpis-vendedor", "children"),
    Output("grafico-vendedor-individual", "figure"),
    Input("dados-vendas", "data"),
    Input("filtro-data", "start_date"),
    Input("filtro-data", "end_date"),
    Input("filtro-categoria", "value"),
    Input("filtro-vendedor", "value"),
    Input("store-meta", "data"),
    Input("vendedor-individual", "value")
)
def atualizar_dashboard(dados, data_ini, data_fim, categorias, vendedores, meta_mensal, vendedor_individual):

    if not dados:
        return dash.no_update

    df = pd.DataFrame(dados)
    df["data_venda"] = pd.to_datetime(df["data_venda"], errors='coerce')
    df = df.dropna(subset=["data_venda"])
    if df.empty:
        return dash.no_update

    # FILTROS
    df_filtrado = df[(df["data_venda"] >= data_ini) & (df["data_venda"] <= data_fim)]
    if categorias:
        df_filtrado = df_filtrado[df_filtrado["categoria"].isin(categorias)]
    if vendedores:
        df_filtrado = df_filtrado[df_filtrado["vendedor"].isin(vendedores)]

    # KPIs GERAIS
    faturamento = df_filtrado["valor_total_venda"].sum()
    lucro = df_filtrado["lucro"].sum()
    vendas = df_filtrado["id_venda"].nunique()
    ticket = faturamento / vendas if vendas > 0 else 0

    faturamento_mes = faturamento
    percentual_meta = (faturamento_mes / meta_mensal) * 100 if meta_mensal > 0 else 0

    # =========================
    # META INDIVIDUAL + RANKING
    # =========================
    df_vendedor = (
        df_filtrado
        .groupby("vendedor")["valor_total_venda"]
        .sum()
        .reset_index()
    )

    total_vendas = df_vendedor["valor_total_venda"].sum()

    df_vendedor["peso"] = (
        df_vendedor["valor_total_venda"] / total_vendas
        if total_vendas > 0 else 0
    )

    df_vendedor["meta_individual"] = df_vendedor["peso"] * meta_mensal

    df_vendedor["percentual_meta"] = (
        df_vendedor["valor_total_venda"] / df_vendedor["meta_individual"] * 100
    ).replace([float("inf"), -float("inf")], 0).fillna(0)

    def status_vendedor(row):
        if row["percentual_meta"] >= 100:
            return "🟢 Meta batida"
        elif row["percentual_meta"] >= 70:
            return "🟠 Quase lá"
        else:
            return "🔴 Abaixo da meta"

    df_vendedor["status"] = df_vendedor.apply(status_vendedor, axis=1)

    df_vendedor = df_vendedor.sort_values("percentual_meta", ascending=False).reset_index(drop=True)
    df_vendedor["ranking"] = df_vendedor.index + 1

    vendedores_bateram = (df_vendedor["percentual_meta"] >= 100).sum()
    top_vendedor = df_vendedor.iloc[0] if not df_vendedor.empty else None

    # STATUS META GERAL
    if faturamento_mes >= meta_mensal:
        status_meta = "🎉 Meta batida! Excelente trabalho!"
        cor_meta = "green"
        icone_meta = "⬆️"
    elif percentual_meta >= 70:
        status_meta = "⚠️ Meta próxima! Intensifique as vendas"
        cor_meta = "orange"
        icone_meta = "⚠️"
    else:
        status_meta = "🚨 Meta distante! Ação necessária"
        cor_meta = "red"
        icone_meta = "⬇️"

    # KPIs GERAIS
    kpis = [
        html.Div([html.H3("💰 Faturamento"), html.H4(f"R$ {faturamento:,.2f}")], className="card"),
        html.Div([html.H3("📈 Lucro"), html.H4(f"R$ {lucro:,.2f}")], className="card"),
        html.Div([html.H3("🧾 Vendas"), html.H4(vendas)], className="card"),
        html.Div([html.H3("🛒 Ticket Médio"), html.H4(f"R$ {ticket:,.2f}")], className="card"),
        html.Div([
            html.H3("🎯 Meta Mensal"),
            html.H4(f"R$ {faturamento_mes:,.2f} / R$ {meta_mensal:,.2f}"),
            html.P(f"{icone_meta} {status_meta}", style={"color": cor_meta, "fontWeight": "bold"})
        ], className="card"),
        html.Div([
            html.H3("🥇 Top Vendedor"),
            html.H4(top_vendedor["vendedor"] if top_vendedor is not None else "-"),
            html.P(f"{top_vendedor['percentual_meta']:.1f}% da meta" if top_vendedor is not None else "")
        ], className="card"),
        html.Div([
            html.H3("👥 Vendedores na Meta"),
            html.H4(vendedores_bateram)
        ], className="card")
    ]

    # =========================
    # DASHBOARD INDIVIDUAL
    # =========================
    if vendedor_individual and vendedor_individual in df_vendedor["vendedor"].values:
        dados_v = df_vendedor[df_vendedor["vendedor"] == vendedor_individual].iloc[0]

        kpis_vendedor = [
            html.Div([html.H3("👤 Vendedor"), html.H4(vendedor_individual)], className="card"),
            html.Div([html.H3("💰 Faturamento"), html.H4(f"R$ {dados_v['valor_total_venda']:,.2f}")], className="card"),
            html.Div([html.H3("🎯 Meta Individual"), html.H4(f"R$ {dados_v['meta_individual']:,.2f}")], className="card"),
            html.Div([
                html.H3("📊 Atingimento"),
                html.H4(f"{dados_v['percentual_meta']:.1f}%"),
                html.P(dados_v["status"])
            ], className="card"),
            html.Div([html.H3("🏆 Ranking"), html.H4(f"{int(dados_v['ranking'])}º lugar")], className="card")
        ]

        df_v_ind = df_filtrado[df_filtrado["vendedor"] == vendedor_individual]
        fig_vendedor_individual = px.line(
            df_v_ind.groupby("data_venda")["valor_total_venda"].sum().reset_index(),
            x="data_venda",
            y="valor_total_venda",
            title=f"📈 Evolução de Vendas – {vendedor_individual}",
            markers=True
        )
    else:
        kpis_vendedor = html.Div("Selecione um vendedor para visualizar o desempenho individual.")
        fig_vendedor_individual = px.line(title="Selecione um vendedor")

    # =========================
    # GRÁFICOS
    # =========================
    fig_tempo = px.line(
        df_filtrado.groupby("data_venda")["valor_total_venda"].sum().reset_index(),
        x="data_venda", y="valor_total_venda",
        title="Faturamento ao Longo do Tempo",
        markers=True
    )

    fig_categoria = px.bar(
        df_filtrado.groupby("categoria")["valor_total_venda"].sum().reset_index(),
        x="categoria", y="valor_total_venda",
        title="Faturamento por Categoria",
        color="categoria"
    )

    fig_pagamento = px.pie(
        df_filtrado,
        names="forma_pagamento",
        values="valor_total_venda",
        title="Forma de Pagamento"
    )

    fig_produtos = px.bar(
        df_filtrado.groupby("produto")["quantidade_venda"].sum()
        .sort_values(ascending=False).head(10).reset_index(),
        x="produto", y="quantidade_venda",
        title="Top 10 Produtos",
        color="produto"
    )

    fig_vendedores = px.bar(
        df_vendedor,
        x="vendedor",
        y="valor_total_venda",
        color="status",
        text=df_vendedor["percentual_meta"].round(1).astype(str) + "%",
        title="🏆 Ranking de Vendedores – Meta Individual",
        color_discrete_map={
            "🟢 Meta batida": "#2ecc71",
            "🟠 Quase lá": "#f1c40f",
            "🔴 Abaixo da meta": "#e74c3c"
        }
    )

    fig_vendedores.update_traces(textposition="outside")
    fig_vendedores.update_layout(xaxis_categoryorder="total descending")

    return (
        kpis,
        fig_tempo,
        fig_categoria,
        fig_pagamento,
        fig_produtos,
        fig_vendedores,
        kpis_vendedor,
        fig_vendedor_individual
    )

if __name__ == "__main__":
    app.run(debug=True)
