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
    external_stylesheets=[dbc.themes.FLATLY, "/assets/style.css"],
    suppress_callback_exceptions=True
)

server = app.server
app.title = "Recanto da Fé"

# =========================
# LAYOUT
# =========================
app.layout = dbc.Container(fluid=True, className="p-4", style={"backgroundColor": "#f8f9fa"}, children=[

    # =========================
    # TÍTULO
    # =========================
    dbc.Row(
        dbc.Col(
            html.H1(
                "Recanto da Fé – Dashboard de Vendas",
                className="text-center fw-bold mb-4 main-title"
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
            ], style={"box-shadow": "0 4px 6px rgba(0, 0, 0, 0.1)"}),
            className="text-center mb-4"
        )
    ),

    dcc.Store(id="pagina-atual", data="geral"),

    # =========================
    # PÁGINA GERAL
    # =========================
    html.Div(id="pagina-geral", children=[

        # META E FILTROS
        dbc.Row([
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        dbc.Row([
                            dbc.Col(html.Label("🎯 Meta Mensal (R$)", className="fw-semibold"), md="auto"),
                            dbc.Col(
                                dbc.Input(id="input-meta", type="number", value=50000, min=0, step=100),
                                md=4
                            )
                        ], align="center")
                    ), className="shadow-sm"
                ), md=3
            ),
            dbc.Col(
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
                                    display_format="DD/MM/YYYY"
                                )
                            ], md=4),
                            dbc.Col([
                                html.Label("🏷️ Categoria"),
                                dcc.Dropdown(
                                    id="filtro-categoria",
                                    options=[{"label": c, "value": c} for c in df_inicial["categoria"].unique()],
                                    multi=True, placeholder="Selecione"
                                )
                            ], md=4),
                            dbc.Col([
                                html.Label("👤 Vendedor"),
                                dcc.Dropdown(
                                    id="filtro-vendedor",
                                    options=[{"label": v, "value": v} for v in df_inicial["vendedor"].unique()],
                                    multi=True, placeholder="Selecione"
                                )
                            ], md=4),
                        ])
                    ),
                    className="shadow-sm",
                    style={"position": "relative", "z-index": "2"}
                ), md=9
            ),
        ], className="mb-4"),


        # KPIs
        dbc.Row(id="kpis", className="g-4 mb-4"),

        # GRÁFICOS
        dbc.Card(dbc.CardBody(dcc.Graph(id="grafico-faturamento-tempo")), className="mb-4 chart-card"),

        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id="grafico-categoria")), className="chart-card"), md=6),
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id="grafico-pagamento")), className="chart-card"), md=6),
        ], className="mb-4 g-4"),

        dbc.Card(dbc.CardBody(dcc.Graph(id="grafico-produtos")), className="mb-4 chart-card"),
        dbc.Card(dbc.CardBody(dcc.Graph(id="grafico-vendedores")), className="mb-4 chart-card"),
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

        dbc.Row(id="kpis-vendedor", className="g-4 mb-4"),
        dbc.Card(dbc.CardBody(dcc.Graph(id="grafico-vendedor-individual")), className="shadow-sm chart-card")
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


def criar_kpi_card(title, value, subtext="", color_class=""):
    return dbc.Col(
        dbc.Card(
            dbc.CardBody([
                html.P(title, className="kpi-title"),
                html.H3(value, className=f"kpi-value {color_class}"),
                html.P(subtext, className="kpi-subtext"),
            ])
        , className="kpi-card")
    )

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
        return [[] for _ in range(8)]

    df = pd.DataFrame(dados)
    df["data_venda"] = pd.to_datetime(df["data_venda"], errors='coerce')
    df = df.dropna(subset=["data_venda"])
    if df.empty:
        return [[] for _ in range(8)]

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

    df_vendedor = df_filtrado.groupby("vendedor")["valor_total_venda"].sum().reset_index()
    total_vendas = df_vendedor["valor_total_venda"].sum()
    df_vendedor["peso"] = (df_vendedor["valor_total_venda"] / total_vendas) if total_vendas > 0 else 0
    df_vendedor["meta_individual"] = df_vendedor["peso"] * meta_mensal
    df_vendedor["percentual_meta"] = (df_vendedor["valor_total_venda"] / df_vendedor["meta_individual"] * 100).replace([float("inf"), -float("inf")], 0).fillna(0)

    def status_vendedor(row):
        if row["percentual_meta"] >= 100: return "🟢 Meta batida"
        elif row["percentual_meta"] >= 70: return "🟠 Quase lá"
        else: return "🔴 Abaixo da meta"
    df_vendedor["status"] = df_vendedor.apply(status_vendedor, axis=1)

    df_vendedor = df_vendedor.sort_values("percentual_meta", ascending=False).reset_index(drop=True)
    df_vendedor["ranking"] = df_vendedor.index + 1
    vendedores_bateram = (df_vendedor["percentual_meta"] >= 100).sum()
    top_vendedor = df_vendedor.iloc[0] if not df_vendedor.empty else None

    # STATUS META GERAL
    if faturamento_mes >= meta_mensal:
        status_meta, cor_meta, icone_meta = "Meta Atingida!", "meta-ok", "🎉"
    elif percentual_meta >= 70:
        status_meta, cor_meta, icone_meta = "Quase lá!", "meta-warn", "⚠️"
    else:
        status_meta, cor_meta, icone_meta = "Abaixo da Meta", "meta-danger", "🚨"

    # KPIs GERAIS
    kpis = [
        criar_kpi_card("💰 FATURAMENTO TOTAL", f"R$ {faturamento:,.2f}"),
        criar_kpi_card("📈 LUCRO TOTAL", f"R$ {lucro:,.2f}"),
        criar_kpi_card("🧾 Nº DE VENDAS", f"{vendas}"),
        criar_kpi_card("🛒 TICKET MÉDIO", f"R$ {ticket:,.2f}"),
        criar_kpi_card("🎯 META MENSAL", f"{percentual_meta:.1f}%", f"{icone_meta} {status_meta}", cor_meta),
        criar_kpi_card("🥇 TOP VENDEDOR", top_vendedor["vendedor"] if top_vendedor is not None else "-", f"{top_vendedor['percentual_meta']:.1f}% da meta" if top_vendedor is not None else ""),
        criar_kpi_card("👥 VENDEDORES NA META", f"{vendedores_bateram}")
    ]

    # DASHBOARD INDIVIDUAL
    if vendedor_individual and vendedor_individual in df_vendedor["vendedor"].values:
        dados_v = df_vendedor[df_vendedor["vendedor"] == vendedor_individual].iloc[0]
        status_v_ind_text = dados_v['status'].split(' ')[1]
        
        if "batida" in status_v_ind_text: status_v_ind_color = "meta-ok"
        elif "Quase" in status_v_ind_text: status_v_ind_color = "meta-warn"
        else: status_v_ind_color = "meta-danger"

        kpis_vendedor = [
            criar_kpi_card("👤 VENDEDOR", vendedor_individual),
            criar_kpi_card("💰 FATURAMENTO", f"R$ {dados_v['valor_total_venda']:,.2f}"),
            criar_kpi_card("🎯 META INDIVIDUAL", f"R$ {dados_v['meta_individual']:,.2f}"),
            criar_kpi_card("📊 ATINGIMENTO", f"{dados_v['percentual_meta']:.1f}%", dados_v["status"], status_v_ind_color),
            criar_kpi_card("🏆 RANKING GERAL", f"{int(dados_v['ranking'])}º")
        ]
        df_v_ind = df_filtrado[df_filtrado["vendedor"] == vendedor_individual]
        fig_vendedor_individual = px.line(
            df_v_ind.groupby(df_v_ind['data_venda'].dt.date)["valor_total_venda"].sum().reset_index(),
            x="data_venda", y="valor_total_venda", title=f"📈 Evolução de Vendas – {vendedor_individual}", markers=True,
            template="plotly_white"
        )
        fig_vendedor_individual.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    else:
        kpis_vendedor = [dbc.Col(dbc.Alert("Selecione um vendedor para ver seu desempenho.", color="info"))]
        fig_vendedor_individual = {}

    # GRÁFICOS
    fig_tempo = px.line(
        df_filtrado.groupby(df['data_venda'].dt.date)["valor_total_venda"].sum().reset_index(),
        x="data_venda", y="valor_total_venda", title="Faturamento ao Longo do Tempo", markers=True, template="plotly_white")
    fig_categoria = px.bar(
        df_filtrado.groupby("categoria")["valor_total_venda"].sum().reset_index().sort_values("valor_total_venda", ascending=False),
        x="categoria", y="valor_total_venda", title="Faturamento por Categoria", color="categoria", template="plotly_white")
    fig_pagamento = px.pie(
        df_filtrado, names="forma_pagamento", values="valor_total_venda", title="Forma de Pagamento", hole=0.4, template="plotly_white")
    fig_produtos = px.bar(
        df_filtrado.groupby("produto")["quantidade_venda"].sum().sort_values(ascending=False).head(10).reset_index(),
        y="produto", x="quantidade_venda", title="Top 10 Produtos Mais Vendidos", color="produto", orientation='h', template="plotly_white")
    fig_vendedores = px.bar(df_vendedor, x="vendedor", y="valor_total_venda", color="status",
        text=df_vendedor["percentual_meta"].round(1).astype(str) + "%", title="🏆 Ranking de Vendedores vs. Meta Individual",
        color_discrete_map={"🟢 Meta batida": "#28a745", "🟠 Quase lá": "#ffc107", "🔴 Abaixo da meta": "#dc3545"},
        template="plotly_white")
    
    for fig in [fig_tempo, fig_categoria, fig_pagamento, fig_produtos, fig_vendedores, fig_vendedor_individual]:
        if fig:
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#343a40")

    fig_vendedores.update_traces(textposition="outside")
    fig_vendedores.update_layout(xaxis_categoryorder="total descending", yaxis_title=None, xaxis_title=None)
    fig_produtos.update_layout(yaxis_categoryorder='total ascending', xaxis_title=None, yaxis_title=None)
    fig_categoria.update_layout(xaxis_title=None, yaxis_title=None)

    return (
        kpis, fig_tempo, fig_categoria, fig_pagamento, fig_produtos, fig_vendedores, kpis_vendedor, fig_vendedor_individual
    )

if __name__ == "__main__":
    app.run(debug=True)
