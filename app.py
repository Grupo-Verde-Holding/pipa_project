import streamlit as st
import pandas as pd
import plotly.express as px
from database.db import listar_veiculos, listar_manutencoes


# ── Formatadores ─────────────────────────────────────────────────────────────
def fmt_km(val):
    try:
        return f"{float(val):,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "—"


def fmt_brl(val):
    try:
        v = f"R$ {float(val):,.2f}"
        return v.replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "—"


# ── Config ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard — Frota",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
<style>
/* Metric cards */
[data-testid="metric-container"] {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 16px 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
[data-testid="metric-container"] label {
    color: #64748B !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
[data-testid="stMetricValue"] {
    font-size: 28px !important;
    font-weight: 700 !important;
    color: #0F172A !important;
}
/* Plotly chart background */
.js-plotly-plot .plotly .bg { fill: transparent !important; }
/* Section label */
.section-label {
    font-size: 11px;
    font-weight: 700;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
}
</style>
""", unsafe_allow_html=True)

# ── Dados ────────────────────────────────────────────────────────────────────
dados_veiculos    = listar_veiculos()
dados_manutencoes = listar_manutencoes()

st.title("Dashboard — Gestão de Frota")

if not dados_veiculos:
    st.info("Nenhum veículo cadastrado. Acesse a página **Veículos** para começar.")
    st.stop()

df_v = pd.DataFrame(dados_veiculos)
df_m = pd.DataFrame(dados_manutencoes) if dados_manutencoes else pd.DataFrame()

# ── KPIs de Veículos ─────────────────────────────────────────────────────────
st.subheader("Frota")
total    = len(df_v)
ativos   = int(df_v["ativo"].sum())
inativos = total - ativos

col_k1, col_k2, col_k3, col_k4 = st.columns(4)
col_k1.metric("Total de Veículos", total)
col_k2.metric("Ativos", ativos)
col_k3.metric("Inativos", inativos)

if not df_m.empty:
    col_k4.metric("Total em Manutenções", fmt_brl(df_m["custo"].sum()))
else:
    col_k4.metric("Total em Manutenções", "R$ 0,00")

st.divider()

# ── Gráfico: Status da Frota ─────────────────────────────────────────────────
col_donut, col_km = st.columns(2)

with col_donut:
    st.subheader("Status da Frota")
    fig_donut = px.pie(
        values=[ativos, inativos],
        names=["Ativos", "Inativos"],
        hole=0.55,
        color_discrete_sequence=["#1D4ED8", "#E2E8F0"],
    )
    fig_donut.update_traces(
        textposition="outside",
        textinfo="percent+label",
        textfont_size=12,
        marker=dict(line=dict(color="white", width=2)),
    )
    fig_donut.update_layout(
        showlegend=False,
        height=260,
        margin=dict(l=20, r=20, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_donut, use_container_width=True)

with col_km:
    st.subheader("KM Atual por Veículo")
    df_km = df_v[["placa", "km_atual"]].sort_values("km_atual", ascending=True).head(10)
    fig_km = px.bar(
        df_km, x="km_atual", y="placa",
        orientation="h",
        labels={"km_atual": "KM", "placa": ""},
        color_discrete_sequence=["#3B82F6"],
    )
    fig_km.update_layout(
        height=260,
        margin=dict(l=0, r=20, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="#F1F5F9", tickformat=",.0f"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
    )
    fig_km.update_traces(marker_line_width=0)
    st.plotly_chart(fig_km, use_container_width=True)

st.divider()

# ── Seção de Manutenções ──────────────────────────────────────────────────────
st.subheader("Manutenções")

if df_m.empty:
    st.info("Nenhuma manutenção registrada ainda.")
else:
    df_m["veiculo"]  = df_m["veiculos"].apply(lambda v: v["placa"] if v else "—")
    df_m["data_dt"]  = pd.to_datetime(df_m["data"], errors="coerce")

    # ── Filtro de período ────────────────────────────────────────────────────
    data_min = df_m["data_dt"].min().date()
    data_max = df_m["data_dt"].max().date()

    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
    with col_f1:
        data_inicio = st.date_input("De", value=data_min, min_value=data_min, max_value=data_max)
    with col_f2:
        data_fim = st.date_input("Até", value=data_max, min_value=data_min, max_value=data_max)

    mask = (df_m["data_dt"].dt.date >= data_inicio) & (df_m["data_dt"].dt.date <= data_fim)
    df_m = df_m[mask]

    if df_m.empty:
        st.info("Nenhuma manutenção no período selecionado.")
        st.stop()

    # ── KPIs de Manutenção ───────────────────────────────────────────────────
    custo_total  = df_m["custo"].sum()
    custo_medio  = df_m["custo"].mean()
    total_reg    = len(df_m)
    servico_caro = (
        df_m.loc[df_m["custo"].idxmax(), "tipo"]
        if not df_m["custo"].isna().all() else "—"
    )

    cm1, cm2, cm3, cm4 = st.columns(4)
    cm1.metric("Registros no período", total_reg)
    cm2.metric("Custo Total", fmt_brl(custo_total))
    cm3.metric("Custo Médio por Serviço", fmt_brl(custo_medio))
    cm4.metric(
        "Serviço mais caro",
        servico_caro[:28] + "…" if len(servico_caro) > 28 else servico_caro,
    )

    st.divider()

    # ── Evolução mensal ──────────────────────────────────────────────────────
    st.subheader("Evolução de Gastos")
    df_m["mes"] = df_m["data_dt"].dt.to_period("M").astype(str)
    custo_mes   = df_m.groupby("mes")["custo"].sum().reset_index()
    custo_mes.columns = ["Mês", "Custo (R$)"]

    fig_line = px.line(
        custo_mes, x="Mês", y="Custo (R$)",
        markers=True,
        color_discrete_sequence=["#1D4ED8"],
        labels={"Mês": "", "Custo (R$)": "R$"},
    )
    fig_line.update_traces(
        line=dict(width=2.5),
        marker=dict(size=8, color="#1D4ED8", line=dict(width=2, color="white")),
    )
    fig_line.update_layout(
        height=280,
        margin=dict(l=0, r=20, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="#F1F5F9"),
        yaxis=dict(gridcolor="#F1F5F9", tickprefix="R$ ", tickformat=",.0f"),
    )
    st.plotly_chart(fig_line, use_container_width=True)

    st.divider()

    # ── Gráficos de barras ───────────────────────────────────────────────────
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("Gasto por Veículo (R$)")
        custo_v = (
            df_m.groupby("veiculo")["custo"]
            .sum()
            .sort_values()
            .reset_index()
        )
        custo_v.columns = ["Placa", "Custo"]
        fig_v = px.bar(
            custo_v, x="Custo", y="Placa",
            orientation="h",
            labels={"Custo": "R$", "Placa": ""},
            color_discrete_sequence=["#1D4ED8"],
        )
        fig_v.update_layout(
            height=max(200, len(custo_v) * 36),
            margin=dict(l=0, r=20, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="#F1F5F9", tickprefix="R$ ", tickformat=",.0f"),
            yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        )
        fig_v.update_traces(marker_line_width=0)
        st.plotly_chart(fig_v, use_container_width=True)

    with col_g2:
        st.subheader("Top 10 Serviços por Custo (R$)")
        custo_s = (
            df_m.groupby("tipo")["custo"]
            .sum()
            .sort_values()
            .tail(10)
            .reset_index()
        )
        custo_s.columns = ["Serviço", "Custo"]
        custo_s["Serviço"] = custo_s["Serviço"].str[:40]
        fig_s = px.bar(
            custo_s, x="Custo", y="Serviço",
            orientation="h",
            labels={"Custo": "R$", "Serviço": ""},
            color_discrete_sequence=["#3B82F6"],
        )
        fig_s.update_layout(
            height=max(200, len(custo_s) * 36),
            margin=dict(l=0, r=20, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="#F1F5F9", tickprefix="R$ ", tickformat=",.0f"),
            yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        )
        fig_s.update_traces(marker_line_width=0)
        st.plotly_chart(fig_s, use_container_width=True)

    col_g3, col_g4 = st.columns(2)

    with col_g3:
        st.subheader("Qtd. de Serviços por Veículo")
        qtd_v = df_m["veiculo"].value_counts().sort_values().reset_index()
        qtd_v.columns = ["Placa", "Qtd"]
        fig_q = px.bar(
            qtd_v, x="Qtd", y="Placa",
            orientation="h",
            labels={"Qtd": "Serviços", "Placa": ""},
            color_discrete_sequence=["#6366F1"],
        )
        fig_q.update_layout(
            height=max(200, len(qtd_v) * 36),
            margin=dict(l=0, r=20, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="#F1F5F9", dtick=1),
            yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        )
        fig_q.update_traces(marker_line_width=0)
        st.plotly_chart(fig_q, use_container_width=True)

    with col_g4:
        st.subheader("Top 5 Serviços mais Frequentes")
        freq_s = df_m["tipo"].value_counts().head(5).reset_index()
        freq_s.columns = ["Serviço", "Qtd"]
        freq_s["Serviço"] = freq_s["Serviço"].str[:35]
        fig_f = px.bar(
            freq_s, x="Qtd", y="Serviço",
            orientation="h",
            labels={"Qtd": "Ocorrências", "Serviço": ""},
            color_discrete_sequence=["#0EA5E9"],
        )
        fig_f.update_layout(
            height=280,
            margin=dict(l=0, r=20, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="#F1F5F9", dtick=1),
            yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        )
        fig_f.update_traces(marker_line_width=0)
        st.plotly_chart(fig_f, use_container_width=True)

    st.divider()

    # ── Ranking de gastos ────────────────────────────────────────────────────
    st.subheader("Ranking de Gastos por Veículo")
    ranking = (
        df_m.groupby("veiculo")
        .agg(
            servicos=("tipo", "count"),
            custo_total=("custo", "sum"),
            custo_medio=("custo", "mean"),
        )
        .sort_values("custo_total", ascending=False)
        .reset_index()
    )
    ranking["custo_total"] = ranking["custo_total"].apply(fmt_brl)
    ranking["custo_medio"] = ranking["custo_medio"].apply(fmt_brl)
    ranking.columns = ["Placa", "Qtd Serviços", "Custo Total", "Custo Médio"]
    st.dataframe(ranking, use_container_width=True, hide_index=True)

    st.divider()

    # ── Últimas manutenções ──────────────────────────────────────────────────
    st.subheader("Últimas 10 Manutenções")
    df_m["Veículo"] = df_m["veiculos"].apply(
        lambda v: f"{v['placa']} — {v['modelo']}" if v else "—"
    )
    df_m["KM"]   = df_m["km_na_data"].apply(fmt_km)
    df_m["Custo"] = df_m["custo"].apply(fmt_brl)
    df_exibir = (
        df_m[["Veículo", "tipo", "data", "KM", "Custo", "descricao"]]
        .head(10)
        .rename(columns={
            "tipo": "Serviço", "data": "Data", "descricao": "Observação",
        })
    )
    st.dataframe(df_exibir, use_container_width=True, hide_index=True)

st.divider()

# ── Tabela de veículos ────────────────────────────────────────────────────────
st.subheader("Todos os Veículos")
df_v_exibir = df_v[["placa", "modelo", "marca", "km_atual", "ativo"]].copy()
df_v_exibir["km_atual"] = df_v_exibir["km_atual"].apply(fmt_km)
df_v_exibir["ativo"]    = df_v_exibir["ativo"].map({1: "Ativo", 0: "Inativo"})
df_v_exibir.rename(columns={
    "placa": "Placa", "modelo": "Modelo", "marca": "Marca",
    "km_atual": "KM Atual", "ativo": "Status",
}, inplace=True)
st.dataframe(df_v_exibir, use_container_width=True, hide_index=True)
