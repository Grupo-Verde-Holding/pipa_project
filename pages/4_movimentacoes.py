import streamlit as st
import pandas as pd
from datetime import date
from database.db import (
    listar_veiculos, listar_pneus, listar_movimentacoes,
    inserir_movimentacao, deletar_movimentacao,
)

st.set_page_config(page_title="Movimentação de Pneus", page_icon="🔄")
st.title("Movimentação de Pneus")

TIPOS_USADO = ["Recapagem", "Descarte", "Substituição"]

pneus    = listar_pneus() or []
veiculos = listar_veiculos() or []

if not pneus:
    st.warning("Nenhum pneu cadastrado. Cadastre um pneu primeiro.")
    st.stop()

opcoes_pneus    = {f"{p['codigo']} — DOT: {p.get('dot', '')}": p for p in pneus}
opcoes_veiculos = {f"{v['placa']} — {v['modelo']}": v for v in veiculos}

tab1, tab2 = st.tabs(["Movimentação", "Estoque"])

# ─────────────────────────────────────────────────────────────
# TAB 1 — Movimentação
# ─────────────────────────────────────────────────────────────
with tab1:
    with st.expander("Registrar movimentação", expanded=True):
        with st.form("form_movimentacao", clear_on_submit=True):
            pneu_label = st.selectbox("Pneu", list(opcoes_pneus.keys()))
            pneu_sel   = opcoes_pneus[pneu_label]
            condicao   = pneu_sel.get("condicao", "Novo")

            if condicao == "Usado":
                tipo = st.selectbox("Tipo de movimentação", TIPOS_USADO)
            else:
                st.info("Pneu novo — nenhuma opção de movimentação necessária.")
                tipo = "Instalação"

            col1, col2 = st.columns(2)
            data_mov   = col1.date_input("Data", value=date.today())
            observacao = col2.text_input("Observação (opcional)")

            submitted = st.form_submit_button("Salvar", use_container_width=True)

        if submitted:
            inserir_movimentacao(
                pneu_id=pneu_sel["id"],
                tipo=tipo,
                data=str(data_mov),
                veiculo_id=None,
                posicao=None,
                km_veiculo=None,
                observacao=observacao or None,
            )
            st.success("Movimentação registrada com sucesso!")
            st.rerun()

    # Histórico
    st.divider()
    st.subheader("Histórico")

    dados = listar_movimentacoes()
    if not dados:
        st.info("Nenhuma movimentação registrada ainda.")
    else:
        df = pd.DataFrame(dados)
        df["pneu"] = df["pneus"].apply(
            lambda p: f"{p['codigo']} — DOT: {p.get('dot', '')}" if p else "—"
        )

        # filtrar apenas movimentações (excluir Entrada/Saída de estoque)
        df_mov = df[~df["tipo"].isin(["Entrada", "Saída"])].copy()

        col_f1, col_f2 = st.columns(2)
        filtro_pneu = col_f1.selectbox(
            "Filtrar pneu", ["Todos"] + list(opcoes_pneus.keys()),
            label_visibility="collapsed", key="f_pneu_mov"
        )
        todos_tipos = sorted(df_mov["tipo"].dropna().unique().tolist())
        filtro_tipo = col_f2.selectbox(
            "Filtrar tipo", ["Todos"] + todos_tipos,
            label_visibility="collapsed", key="f_tipo_mov"
        )

        if filtro_pneu != "Todos":
            pid = opcoes_pneus[filtro_pneu]["id"]
            df_mov = df_mov[df_mov["pneu_id"] == pid]
        if filtro_tipo != "Todos":
            df_mov = df_mov[df_mov["tipo"] == filtro_tipo]

        df_exibir = df_mov[["data", "tipo", "pneu", "observacao"]].rename(columns={
            "data":       "Data",
            "tipo":       "Tipo",
            "pneu":       "Pneu",
            "observacao": "Observação",
        })
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)

        # Ação de exclusão
        st.divider()
        opcoes_mov = {
            f"{r['data']} | {r['tipo']} | {r['pneu']}": r
            for _, r in df_mov.iterrows()
        }
        if opcoes_mov:
            selecionado = st.selectbox("Selecionar registro", list(opcoes_mov.keys()))
            if st.button("Excluir registro", type="primary", use_container_width=True):
                deletar_movimentacao(opcoes_mov[selecionado]["id"])
                st.success("Registro excluído.")
                st.rerun()

# ─────────────────────────────────────────────────────────────
# TAB 2 — Estoque
# ─────────────────────────────────────────────────────────────
with tab2:
    with st.expander("Registrar entrada / saída", expanded=True):
        with st.form("form_estoque", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            pneu_est_label = col1.selectbox("Pneu", list(opcoes_pneus.keys()), key="sel_est")
            tipo_est       = col2.selectbox("Movimento", ["Entrada", "Saída"])
            data_est       = col3.date_input("Data", value=date.today(), key="data_est")
            obs_est        = st.text_input("Observação (opcional)", key="obs_est")

            submitted_est = st.form_submit_button("Registrar", use_container_width=True)

        if submitted_est:
            pneu_est = opcoes_pneus[pneu_est_label]
            inserir_movimentacao(
                pneu_id=pneu_est["id"],
                tipo=tipo_est,
                data=str(data_est),
                veiculo_id=None,
                posicao=None,
                km_veiculo=None,
                observacao=obs_est or None,
            )
            st.success(f"{tipo_est} de {pneu_est_label} registrada!")
            st.rerun()

    # Saldo de estoque
    st.divider()
    st.subheader("Saldo de estoque")

    todos_mov = listar_movimentacoes() or []

    # calcular saldo por pneu_id
    saldo = {}
    for m in todos_mov:
        pid = m.get("pneu_id")
        if pid is None:
            continue
        if m["tipo"] == "Entrada":
            saldo[pid] = saldo.get(pid, 0) + 1
        elif m["tipo"] == "Saída":
            saldo[pid] = saldo.get(pid, 0) - 1

    rows = []
    for p in pneus:
        s = saldo.get(p["id"], 0)
        rows.append({
            "Código":   p["codigo"],
            "DOT":      p.get("dot", ""),
            "Condição": p.get("condicao", ""),
            "Status":   p.get("status", ""),
            "Saldo":    s,
            "Situação": "Em estoque" if s > 0 else "Fora do estoque",
        })

    df_est = pd.DataFrame(rows)

    filtro_sit = st.radio(
        "Exibir", ["Todos", "Em estoque", "Fora do estoque"],
        horizontal=True
    )
    if filtro_sit != "Todos":
        df_est = df_est[df_est["Situação"] == filtro_sit]

    def _cor_situacao(val):
        if val == "Em estoque":
            return "background-color: #2d6a4f; color: #ffffff"
        return "background-color: #95d5b2; color: #1b4332"

    st.dataframe(
        df_est.style.map(_cor_situacao, subset=["Situação"]),
        use_container_width=True,
        hide_index=True,
    )
