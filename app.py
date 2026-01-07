import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# =========================
# CARREGAMENTO DOS DADOS
# =========================
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1yVuRDq2HL-ee4wmUxwXRM2icsMAWjIllcXHHISzpze8/export?format=csv"
    try:
        df = pd.read_csv(url)
        df["data_venda"] = pd.to_datetime(df["data_venda"], errors="coerce")
        df = df.dropna(subset=["data_venda"])
        return df
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

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
    dbc.Row(dbc.Col(html.H1("Recanto da Fé – Dashboard de Vendas", className="text-center fw-bold mb-4 main-title"))),
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

    html.Div(id="pagina-geral", children=[
        dbc.Card(
            dbc.CardBody([
                dbc.Row([
                     dbc.Col([
                        html.Label("🎯 Meta Mensal (R$)"),
                        dbc.Input(id="input-meta", type="number", value=50000, min=0, step=100),
                    ], md=2),
                    dbc.Col([
                        html.Label("📅 Período"),
                        dcc.DatePickerRange(
                            id="filtro-data",
                            min_date_allowed=df_inicial["data_venda"].min() if not df_inicial.empty else None,
                            max_date_allowed=df_inicial["data_venda"].max() if not df_inicial.empty else None,
                            start_date=df_inicial["data_venda"].min() if not df_inicial.empty else None,
                            end_date=df_inicial["data_venda"].max() if not df_inicial.empty else None,
                            display_format="DD/MM/YYYY"
                        )
                    ], md=3),
                    dbc.Col([
                        html.Label("🏷️ Categoria"),
                        dcc.Dropdown(id="filtro-categoria", options=[{"label": c, "value": c} for c in df_inicial["categoria"].unique()] if not df_inicial.empty else [], multi=True, placeholder="Selecione")
                    ], md=3),
                    dbc.Col([
                        html.Label("👤 Vendedor"),
                        dcc.Dropdown(id="filtro-vendedor", options=[{"label": v, "value": v} for v in df_inicial["vendedor"].unique()] if not df_inicial.empty else [], multi=True, placeholder="Selecione")
                    ], md=2),
                    dbc.Col([
                        html.Label("🔁 Comparar com"),
                        dcc.Dropdown(id="filtro-comparacao", options=[
                            {"label": "Sem Comparação", "value": "sem"},
                            {"label": "Período Anterior", "value": "anterior"}
                        ], value="sem", clearable=False)
                    ], md=2),
                ], align="end")
            ]), className="shadow-sm mb-4", style={"position": "relative", "z-index": "2"}
        ),
        dbc.Row(id="kpis", className="g-4 mb-4"),
        dbc.Card(dbc.CardBody(dcc.Graph(id="grafico-faturamento-tempo")), className="mb-4 chart-card"),
        dbc.Card(dbc.CardBody(dcc.Graph(id="grafico-lucro-custo")), className="mb-4 chart-card"),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id="grafico-categoria")), className="chart-card"), md=6),
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id="grafico-pagamento")), className="chart-card"), md=6),
        ], className="mb-4 g-4"),
        dbc.Card(dbc.CardBody(dcc.Graph(id="grafico-produtos")), className="mb-4 chart-card"),
        dbc.Card(dbc.CardBody(dcc.Graph(id="grafico-vendedores")), className="mb-4 chart-card"),
    ]),

    html.Div(id="pagina-vendedor", style={"display": "none"}, children=[
        dbc.Card(dbc.CardBody([
            html.H4("👤 Dashboard Individual do Vendedor", className="fw-bold mb-3"),
            dbc.Row(dbc.Col(dcc.Dropdown(id="vendedor-individual", options=[{"label": v, "value": v} for v in df_inicial["vendedor"].unique()] if not df_inicial.empty else [], placeholder="Escolha o vendedor"), md=4))
        ]), className="mb-4 shadow-sm"),
        dbc.Row(id="kpis-vendedor", className="g-4 mb-4"),
        dbc.Card(dbc.CardBody(dcc.Graph(id="grafico-vendedor-individual")), className="shadow-sm chart-card")
    ]),

    dcc.Interval(id="interval-atualizacao", interval=1800000),
    dcc.Store(id="dados-vendas", data=df_inicial.to_dict("records") if not df_inicial.empty else []),
    dcc.Store(id="store-meta", data=50000),
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
    if not ctx.triggered:
        return "geral"
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

def criar_kpi_card(title, value, subtext="", color_class="", comparison_text="", comparison_color=""):
    body = [
        html.P(title, className="kpi-title"),
        html.H3(value, className=f"kpi-value {color_class}"),
    ]
    if subtext:
        body.append(html.P(subtext, className="kpi-subtext"))
    
    body.append(html.P(comparison_text, className=f"kpi-comparison {comparison_color}"))

    return dbc.Col(
        dbc.Card(dbc.CardBody(body), className="kpi-card")
    )

@app.callback(
    Output("kpis", "children"),
    Output("grafico-faturamento-tempo", "figure"),
    Output("grafico-lucro-custo", "figure"),
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
    Input("vendedor-individual", "value"),
    Input("filtro-comparacao", "value")
)
def atualizar_dashboard(dados, data_ini, data_fim, categorias, vendedores, meta_mensal, vendedor_individual, comparacao):
    empty_fig = go.Figure()
    empty_return = ([], empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, [], empty_fig)
    
    if not dados or data_ini is None or data_fim is None:
        return empty_return

    df = pd.DataFrame(dados)

    # --- Proteção de Colunas ---
    required_cols = {
        "valor_total_venda": "numeric", "lucro": "numeric", "id_venda": "object", 
        "categoria": "object", "vendedor": "object", "forma_pagamento": "object", 
        "produto": "object", "quantidade_venda": "numeric", "valor_mercadoria": "numeric"
    }
    for col, type in required_cols.items():
        if col not in df.columns:
            if type == "numeric":
                df[col] = 0
            else:
                df[col] = "N/A"
    
    df["data_venda"] = pd.to_datetime(df["data_venda"])
    df = df.dropna(subset=["data_venda"])

    data_ini = pd.to_datetime(data_ini)
    data_fim = pd.to_datetime(data_fim)

    df_filtrado = df[(df["data_venda"] >= data_ini) & (df["data_venda"] <= data_fim)]
    
    if categorias:
        df_filtrado = df_filtrado[df_filtrado["categoria"].isin(categorias)]
    if vendedores:
        df_filtrado = df_filtrado[df_filtrado["vendedor"].isin(vendedores)]

    if df_filtrado.empty:
        return empty_return

    # --- Lógica de Comparação ---
    df_anterior = pd.DataFrame()
    if comparacao == "anterior":
        dias_periodo = (data_fim - data_ini).days
        data_fim_ant = data_ini - timedelta(days=1)
        data_ini_ant = data_fim_ant - timedelta(days=dias_periodo)
        df_anterior = df[(df["data_venda"] >= data_ini_ant) & (df["data_venda"] <= data_fim_ant)]
        if categorias:
            df_anterior = df_anterior[df_anterior["categoria"].isin(categorias)]
        if vendedores:
            df_anterior = df_anterior[df_anterior["vendedor"].isin(vendedores)]

    # --- KPIs ---
    faturamento = df_filtrado["valor_total_venda"].sum()
    lucro = df_filtrado["lucro"].sum()
    vendas = df_filtrado["id_venda"].nunique()
    ticket = faturamento / vendas if vendas > 0 else 0
    fat_ant = df_anterior["valor_total_venda"].sum() if not df_anterior.empty else 0
    lucro_ant = df_anterior["lucro"].sum() if not df_anterior.empty else 0
    vendas_ant = df_anterior["id_venda"].nunique() if not df_anterior.empty else 0
    ticket_ant = fat_ant / vendas_ant if vendas_ant > 0 else 0
    margem_lucro = (lucro / faturamento) * 100 if faturamento > 0 else 0

    def get_comparison(current, previous):
        if previous == 0: return "N/A", "text-muted"
        diff = ((current - previous) / previous) * 100
        color = "text-success" if diff >= 0 else "text-danger"
        arrow = "🔼" if diff >= 0 else "🔽"
        return f"{arrow} {diff:.2f}%", color

    comp_fat_text, comp_fat_color = get_comparison(faturamento, fat_ant) if comparacao == 'anterior' else ("", "")
    comp_lucro_text, comp_lucro_color = get_comparison(lucro, lucro_ant) if comparacao == 'anterior' else ("", "")
    comp_vendas_text, comp_vendas_color = get_comparison(vendas, vendas_ant) if comparacao == 'anterior' else ("", "")
    comp_ticket_text, comp_ticket_color = get_comparison(ticket, ticket_ant) if comparacao == 'anterior' else ("", "")

    percentual_meta = (faturamento / meta_mensal) * 100 if meta_mensal > 0 else 0
    if faturamento >= meta_mensal: status_meta, cor_meta, icone_meta = "Meta Atingida!", "meta-ok", "🎉"
    elif percentual_meta >= 70: status_meta, cor_meta, icone_meta = "Quase lá!", "meta-warn", "⚠️"
    else: status_meta, cor_meta, icone_meta = "Abaixo da Meta", "meta-danger", "🚨"
    
    df_vendedor = df_filtrado.groupby("vendedor")["valor_total_venda"].sum().reset_index()
    total_vendas_vendedores = df_vendedor["valor_total_venda"].sum()
    df_vendedor["peso"] = (df_vendedor["valor_total_venda"] / total_vendas_vendedores) if total_vendas_vendedores > 0 else 0
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

    kpis = [
        criar_kpi_card("💰 FATURAMENTO", f"R$ {faturamento:,.2f}", comparison_text=comp_fat_text, comparison_color=comp_fat_color),
        criar_kpi_card("📈 LUCRO", f"R$ {lucro:,.2f}", comparison_text=comp_lucro_text, comparison_color=comp_lucro_color),
        criar_kpi_card("📊 MARGEM DE LUCRO", f"{margem_lucro:.2f}%"),
        criar_kpi_card("🧾 VENDAS", f"{vendas}", comparison_text=comp_vendas_text, comparison_color=comp_vendas_color),
        criar_kpi_card("🛒 TICKET MÉDIO", f"R$ {ticket:,.2f}", comparison_text=comp_ticket_text, comparison_color=comp_ticket_color),
        criar_kpi_card("🎯 META MENSAL", f"R$ {faturamento:,.2f} / R$ {meta_mensal:,.2f}", subtext=f"{icone_meta} {status_meta}", color_class=cor_meta),
        criar_kpi_card("🥇 TOP VENDEDOR", top_vendedor["vendedor"] if top_vendedor is not None else "-", subtext=f"{top_vendedor['percentual_meta']:.1f}% da meta" if top_vendedor is not None else ""),
        criar_kpi_card("👥 VENDEDORES NA META", f"{vendedores_bateram}"),
    ]
    
    # --- Correção do Locale ---
    dias_semana_map = {0: 'Segunda', 1: 'Terça', 2: 'Quarta', 3: 'Quinta', 4: 'Sexta', 5: 'Sábado', 6: 'Domingo'}
    df_filtrado['dia_semana_num'] = df_filtrado['data_venda'].dt.dayofweek
    df_filtrado['dia_semana_nome'] = df_filtrado['dia_semana_num'].map(dias_semana_map)
    vendas_por_dia = df_filtrado.groupby('dia_semana_nome')["valor_total_venda"].sum()
    if not vendas_por_dia.empty:
        melhor_dia = vendas_por_dia.idxmax()
        melhor_dia_valor = vendas_por_dia.max()
        kpis.append(criar_kpi_card("☀️ MELHOR DIA", melhor_dia, subtext=f"R$ {melhor_dia_valor:,.2f}"))
    else:
        kpis.append(criar_kpi_card("☀️ MELHOR DIA", "N/A"))

    # --- Dashboard Individual ---
    kpis_vendedor, fig_vendedor_individual = [dbc.Col(dbc.Alert("Selecione um vendedor.", color="info"))], go.Figure()
    if vendedor_individual:
        df_v_ind = df_filtrado[df_filtrado["vendedor"] == vendedor_individual]
        if not df_v_ind.empty:
            fat_v_ind = df_v_ind["valor_total_venda"].sum()
            lucro_v_ind = df_v_ind["lucro"].sum()
            vendas_v_ind = df_v_ind["id_venda"].nunique()
            ticket_v_ind = fat_v_ind / vendas_v_ind if vendas_v_ind > 0 else 0
            kpis_vendedor = [
                criar_kpi_card("💰 FATURAMENTO", f"R$ {fat_v_ind:,.2f}"),
                criar_kpi_card("📈 LUCRO", f"R$ {lucro_v_ind:,.2f}"),
                criar_kpi_card("🧾 VENDAS", f"{vendas_v_ind}"),
                criar_kpi_card("🛒 TICKET MÉDIO", f"R$ {ticket_v_ind:,.2f}"),
            ]
            fig_vendedor_individual = px.line(
                df_v_ind.groupby(df_v_ind['data_venda'].dt.date)["valor_total_venda"].sum().reset_index(),
                x="data_venda", y="valor_total_venda", title=f"📈 Evolução de Vendas – {vendedor_individual}", markers=True, template="plotly_white")
    
    # --- Gráficos ---
    fig_tempo = px.line(df_filtrado.groupby(df_filtrado['data_venda'].dt.date)["valor_total_venda"].sum().reset_index(), x="data_venda", y="valor_total_venda", title="Faturamento ao Longo do Tempo", markers=True, template="plotly_white")
    
    df_filtrado['custo'] = df_filtrado['valor_mercadoria']
    df_lucro_custo = df_filtrado.groupby(df_filtrado['data_venda'].dt.date)[['lucro', 'custo']].sum().reset_index()
    df_lucro_custo = df_lucro_custo.melt(id_vars='data_venda', value_vars=['lucro', 'custo'], var_name='Métrica', value_name='Valor')
    fig_lucro_custo = px.bar(
        df_lucro_custo, x='data_venda', y='Valor', color='Métrica', title='Composição do Faturamento (Lucro e Custo)',
        template='plotly_white', color_discrete_map={'lucro': '#28a745', 'custo': '#dc3545'})
    fig_lucro_custo.update_layout(barmode='stack')

    fig_categoria = px.bar(df_filtrado.groupby("categoria")["valor_total_venda"].sum().reset_index().sort_values("valor_total_venda", ascending=False), x="categoria", y="valor_total_venda", title="Faturamento por Categoria", color="categoria", template="plotly_white")
    fig_pagamento = px.pie(df_filtrado, names="forma_pagamento", values="valor_total_venda", title="Forma de Pagamento", hole=0.4, template="plotly_white")
    fig_produtos = px.bar(df_filtrado.groupby("produto")["quantidade_venda"].sum().sort_values(ascending=False).head(10).reset_index(), y="produto", x="quantidade_venda", title="Top 10 Produtos Mais Vendidos", color="produto", orientation='h', template="plotly_white")
    fig_vendedores = px.bar(df_vendedor, x="vendedor", y="valor_total_venda", color="status", text=df_vendedor["percentual_meta"].round(1).astype(str) + "%", title="🏆 Ranking de Vendedores vs. Meta Individual", color_discrete_map={"🟢 Meta batida": "#28a745", "🟠 Quase lá": "#ffc107", "🔴 Abaixo da meta": "#dc3545"}, template="plotly_white")
    
    for fig in [fig_tempo, fig_lucro_custo, fig_categoria, fig_pagamento, fig_produtos, fig_vendedores, fig_vendedor_individual]:
        if fig:
             fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#343a40")

    fig_vendedores.update_traces(textposition="outside")
    fig_vendedores.update_layout(xaxis_categoryorder="total descending", yaxis_title=None, xaxis_title=None)
    fig_produtos.update_layout(yaxis_categoryorder='total ascending', xaxis_title=None, yaxis_title=None)
    fig_categoria.update_layout(xaxis_title=None, yaxis_title=None)
    fig_lucro_custo.update_layout(yaxis_title=None, xaxis_title="Data")

    return (kpis, fig_tempo, fig_lucro_custo, fig_categoria, fig_pagamento, fig_produtos, fig_vendedores, kpis_vendedor, fig_vendedor_individual)

if __name__ == "__main__":
    app.run(debug=False)
