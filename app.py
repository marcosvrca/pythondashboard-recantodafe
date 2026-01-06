import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
from datetime import datetime

# FUNÇÃO PARA CARREGAR DADOS
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1yVuRDq2HL-ee4wmUxwXRM2icsMAWjIllcXHHISzpze8/export?format=csv"
    df = pd.read_csv(url)
    df["data_venda"] = pd.to_datetime(df["data_venda"], errors='coerce')
    df = df.dropna(subset=["data_venda"])
    return df

df_inicial = carregar_dados()

# INICIALIZAÇÃO DO APP
app = dash.Dash(__name__)
app.title = "Recanto da Fé"

# LAYOUT
app.layout = html.Div(style={"padding": "20px"}, children=[

    html.H1("🏪 Recanto da Fé – Dashboard de Vendas"),
    html.Div(className="meta-container", children=[
        html.Label("💡 Defina a Meta Mensal (R$):"),
        dcc.Input(
            id="input-meta",
            type="number",
            value=50000,
            min=0,
            step=100,
            style={"width": "150px"}
        )
    ]),

    # FILTROS
    html.Div(className="filtros", children=[
        html.Div(style={"flex": "1"}, children=[
            html.Label("📅 Filtrar por período"),
            dcc.DatePickerRange(
                id="filtro-data",
                min_date_allowed=df_inicial["data_venda"].min(),
                max_date_allowed=df_inicial["data_venda"].max(),
                start_date=df_inicial["data_venda"].min(),
                end_date=df_inicial["data_venda"].max(),
                display_format="DD/MM/YYYY",
                style={"width": "100%"}
            )
        ]),
        html.Div(style={"flex": "1"}, children=[
            html.Label("🏷️ Filtrar por categoria"),
            dcc.Dropdown(
                id="filtro-categoria",
                options=[{"label": c, "value": c} for c in df_inicial["categoria"].unique()],
                placeholder="Filtrar por tipo...",
                multi=True
            )
        ]),
        html.Div(style={"flex": "1"}, children=[
            html.Label("👤 Filtrar por vendedor"),
            dcc.Dropdown(
                id="filtro-vendedor",
                options=[{"label": v, "value": v} for v in df_inicial["vendedor"].unique()],
                placeholder="Filtrar por...",
                multi=True
            )
        ])
    ]),

    # KPIs
    html.Div(id="kpis"),

    # GRÁFICOS
    html.Div(dcc.Graph(id="grafico-faturamento-tempo")),
    html.Div(style={"display": "flex", "gap": "20px", "flexWrap": "wrap"}, children=[
        html.Div(dcc.Graph(id="grafico-categoria"), style={"flex": "1"}),
        html.Div(dcc.Graph(id="grafico-pagamento"), style={"flex": "1"})
    ]),
    html.Div(dcc.Graph(id="grafico-produtos")),
    html.Div(dcc.Graph(id="grafico-vendedores")),

    # INTERVALO DE ATUALIZAÇÃO
    dcc.Interval(id="interval-atualizacao", interval=1800000, n_intervals=0),
    dcc.Store(id="dados-vendas"),
    dcc.Store(id="store-meta", data=50000)
])


# Callbacks
@app.callback(Output("store-meta", "data"), Input("input-meta", "value"))
def atualizar_meta(valor):
    return valor if valor and valor > 0 else 50000

@app.callback(Output("dados-vendas", "data"), Input("interval-atualizacao", "n_intervals"))
def atualizar_dados(n):
    df = carregar_dados()
    return df.to_dict("records")

@app.callback(
    Output("kpis", "children"),
    Output("grafico-faturamento-tempo", "figure"),
    Output("grafico-categoria", "figure"),
    Output("grafico-pagamento", "figure"),
    Output("grafico-produtos", "figure"),
    Output("grafico-vendedores", "figure"),
    Input("dados-vendas", "data"),
    Input("filtro-data", "start_date"),
    Input("filtro-data", "end_date"),
    Input("filtro-categoria", "value"),
    Input("filtro-vendedor", "value"),
    Input("store-meta", "data")
)
def atualizar_dashboard(dados, data_ini, data_fim, categorias, vendedores, meta_mensal):
    if not dados: return dash.no_update
    df = pd.DataFrame(dados)
    df["data_venda"] = pd.to_datetime(df["data_venda"], errors='coerce')
    df = df.dropna(subset=["data_venda"])
    if df.empty: return dash.no_update

    # FILTROS
    df_filtrado = df[(df["data_venda"] >= data_ini) & (df["data_venda"] <= data_fim)]
    if categorias: df_filtrado = df_filtrado[df_filtrado["categoria"].isin(categorias)]
    if vendedores: df_filtrado = df_filtrado[df_filtrado["vendedor"].isin(vendedores)]

    # KPIs
    faturamento = df_filtrado["valor_total_venda"].sum() if not df_filtrado.empty else 0
    lucro = df_filtrado["lucro"].sum() if not df_filtrado.empty else 0
    vendas = df_filtrado["id_venda"].nunique() if not df_filtrado.empty else 0
    ticket = faturamento / vendas if vendas > 0 else 0

    # META (baseada no período selecionado)
    faturamento_mes = df_filtrado["valor_total_venda"].sum() if not df_filtrado.empty else 0
    percentual_meta = (faturamento_mes / meta_mensal) * 100 if meta_mensal > 0 else 0

    # =========================
    # META POR VENDEDOR (ADICIONADO)
    # =========================
    df_vendedor = (
        df_filtrado
        .groupby("vendedor")["valor_total_venda"]
        .sum()
        .reset_index()
    )

    qtd_vendedores = df_vendedor["vendedor"].nunique()
    meta_por_vendedor = meta_mensal / qtd_vendedores if qtd_vendedores > 0 else 0

    df_vendedor["percentual_meta"] = (
        df_vendedor["valor_total_venda"] / meta_por_vendedor * 100
        if meta_por_vendedor > 0 else 0
    )

    def status_vendedor(row):
        if row["valor_total_venda"] >= meta_por_vendedor:
            return "🟢 Meta batida"
        elif row["percentual_meta"] >= 70:
            return "🟠 Quase lá"
        else:
            return "🔴 Abaixo da meta"

    df_vendedor["status"] = df_vendedor.apply(status_vendedor, axis=1)

    vendedores_bateram = (df_vendedor["valor_total_venda"] >= meta_por_vendedor).sum()
    # =========================

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

    # Cards KPI
    kpis = [
        html.Div([html.H3("💰 Faturamento"), html.H4(f"R$ {faturamento:,.2f}"), html.Div("📈", className="icone")], className="card"),
        html.Div([html.H3("📈 Lucro"), html.H4(f"R$ {lucro:,.2f}"), html.Div("💹", className="icone")], className="card"),
        html.Div([html.H3("🧾 Vendas"), html.H4(vendas), html.Div("🛒", className="icone")], className="card"),
        html.Div([html.H3("🛒 Ticket Médio"), html.H4(f"R$ {ticket:,.2f}"), html.Div("📝", className="icone")], className="card"),
        html.Div([
            html.H3("🏆 Meta Mensal"),
            html.H4(f"R$ {faturamento_mes:,.2f} / R$ {meta_mensal:,.2f}"),
            html.P(f"{icone_meta} {status_meta}", style={"color": cor_meta, "fontWeight": "bold"}),
            html.Div("🎯", className="icone")
        ], className="card"),
        html.Div([
            html.H3("👥 Vendedores na Meta"),
            html.H4(vendedores_bateram),
            html.Div("🏅", className="icone")
        ], className="card")
    ]

    # GRÁFICOS
    if df_filtrado.empty:
        fig_tempo = px.line(title="Faturamento ao Longo do Tempo (sem dados)")
        fig_categoria = px.bar(title="Faturamento por Categoria (sem dados)")
        fig_pagamento = px.pie(title="Forma de Pagamento (sem dados)")
        fig_produtos = px.bar(title="Top 10 Produtos (sem dados)")
        fig_vendedores = px.bar(title="Vendas por Vendedor (sem dados)")
        return kpis, fig_tempo, fig_categoria, fig_pagamento, fig_produtos, fig_vendedores

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

    # =========================
    # GRÁFICO META POR VENDEDOR (SUBSTITUÍDO)
    # =========================
    fig_vendedores = px.bar(
        df_vendedor,
        x="vendedor",
        y="valor_total_venda",
        text=df_vendedor["percentual_meta"].round(1).astype(str) + "%",
        title="Meta Mensal por Vendedor",
        color="status",
        color_discrete_map={
            "🟢 Meta batida": "#2ecc71",
            "🟠 Quase lá": "#f1c40f",
            "🔴 Abaixo da meta": "#e74c3c"
        }
    )

    fig_vendedores.update_traces(textposition="outside")
    fig_vendedores.update_layout(
        yaxis_title="Faturamento (R$)",
        xaxis_title="Vendedor",
        uniformtext_minsize=8,
        uniformtext_mode="hide"
    )
    # =========================

    return kpis, fig_tempo, fig_categoria, fig_pagamento, fig_produtos, fig_vendedores


# RUN
server = app.server

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
