import streamlit as st
import pandas as pd
from datetime import date
from database.db import (
    listar_veiculos, listar_pneus, listar_movimentacoes,
    inserir_movimentacao, atualizar_movimentacao, deletar_movimentacao,
)


def fmt_data(val):
    try:
        return pd.to_datetime(val).strftime("%d/%m/%Y")
    except Exception:
        return str(val) if val else "—"


st.set_page_config(page_title="Movimentação de Pneus", page_icon="🔄")
st.title("Movimentação de Pneus")

pneus    = listar_pneus() or []
veiculos = listar_veiculos() or []

if not pneus:
    st.warning("Nenhum pneu cadastrado. Cadastre um pneu primeiro.")
    st.stop()

if not veiculos:
    st.warning("Nenhum veículo cadastrado. Cadastre um veículo primeiro.")
    st.stop()

opcoes_pneus    = {f"DOT: {p.get('dot', '')} | ID: {p['id']}": p for p in pneus}
opcoes_veiculos = {f"{v['placa']} — {v['modelo']}": v for v in veiculos}

TIPOS_USADO = ["Recapagem", "Descarte", "Substituição"]

tab1, tab2 = st.tabs(["Movimentação", "Estoque"])

# ─────────────────────────────────────────────────────────────
# TAB 1 — Movimentação
# ─────────────────────────────────────────────────────────────
with tab1:
    with st.expander("Registrar movimentação", expanded=True):
        with st.form("form_movimentacao", clear_on_submit=True):
            veiculo_label = st.selectbox("Veículo (Placa)", list(opcoes_veiculos.keys()))
            veiculo_sel   = opcoes_veiculos[veiculo_label]

            pneu_label = st.selectbox("Pneu", list(opcoes_pneus.keys()))
            pneu_sel   = opcoes_pneus[pneu_label]
            condicao   = pneu_sel.get("condicao", "Novo")

            if condicao == "Usado":
                tipo = st.selectbox("Tipo de movimentação", TIPOS_USADO)
            else:
                st.info("Pneu novo — movimento registrado como Instalação.")
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
                veiculo_id=veiculo_sel["id"],
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
        df["pneu"]    = df["pneus"].apply(
            lambda p: f"DOT: {p.get('dot', '')} | ID: {p['id']}" if p else "—"
        )
        df["veiculo"] = df["veiculos"].apply(
            lambda v: f"{v['placa']} — {v['modelo']}" if v else "—"
        )

        df_mov = df[~df["tipo"].isin(["Entrada", "Saída"])].copy()

        col_f1, col_f2 = st.columns(2)
        filtro_veiculo = col_f1.selectbox(
            "Filtrar veículo", ["Todos"] + list(opcoes_veiculos.keys()),
            label_visibility="collapsed", key="f_veic_mov"
        )
        todos_tipos = sorted(df_mov["tipo"].dropna().unique().tolist())
        filtro_tipo = col_f2.selectbox(
            "Filtrar tipo", ["Todos"] + todos_tipos,
            label_visibility="collapsed", key="f_tipo_mov"
        )

        if filtro_veiculo != "Todos":
            vid = opcoes_veiculos[filtro_veiculo]["id"]
            df_mov = df_mov[df_mov["veiculo_id"] == vid]
        if filtro_tipo != "Todos":
            df_mov = df_mov[df_mov["tipo"] == filtro_tipo]

        df_exibir = df_mov[["data", "tipo", "pneu", "veiculo", "observacao"]].copy()
        df_exibir["data"] = df_exibir["data"].apply(fmt_data)
        df_exibir.rename(columns={
            "data":       "Data",
            "tipo":       "Tipo",
            "pneu":       "Pneu",
            "veiculo":    "Veículo",
            "observacao": "Observação",
        }, inplace=True)
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)

        # Ações
        st.divider()
        opcoes_mov = {
            f"{fmt_data(r['data'])} | {r['tipo']} | {r['pneu']}": r
            for _, r in df_mov.iterrows()
        }
        if opcoes_mov:
            selecionado = st.selectbox("Selecionar registro", list(opcoes_mov.keys()))
            mov = opcoes_mov[selecionado]

            col_e, col_d = st.columns(2)

            if col_e.button("Editar", use_container_width=True, key="btn_editar_mov"):
                st.session_state["editando_mov"] = mov["id"]

            if col_d.button("Excluir registro", type="primary", use_container_width=True, key="btn_excluir_mov"):
                deletar_movimentacao(mov["id"])
                st.success("Registro excluído.")
                st.rerun()

            # Formulário de edição
            if st.session_state.get("editando_mov") == mov["id"]:
                st.divider()
                st.subheader("Editando movimentação")

                # define tipo atual
                condicao_mov = mov["pneus"].get("condicao", "Novo") if mov.get("pneus") else "Novo"

                with st.form("form_editar_mov"):
                    novo_veiculo_label = st.selectbox(
                        "Veículo", list(opcoes_veiculos.keys()),
                        index=next((i for i, v in enumerate(opcoes_veiculos.values())
                                    if v["id"] == mov.get("veiculo_id")), 0)
                    )

                    if condicao_mov == "Usado":
                        novo_tipo = st.selectbox(
                            "Tipo", TIPOS_USADO,
                            index=TIPOS_USADO.index(mov["tipo"]) if mov["tipo"] in TIPOS_USADO else 0
                        )
                    else:
                        st.info("Pneu novo — tipo fixo: Instalação.")
                        novo_tipo = "Instalação"

                    col1, col2 = st.columns(2)
                    nova_data      = col1.date_input("Data", value=pd.to_datetime(mov["data"]).date())
                    nova_observacao = col2.text_input("Observação", value=mov.get("observacao") or "")

                    col_s, col_c = st.columns(2)
                    salvar   = col_s.form_submit_button("Salvar alterações", use_container_width=True)
                    cancelar = col_c.form_submit_button("Cancelar", use_container_width=True)

                if salvar:
                    atualizar_movimentacao(
                        mov_id=mov["id"],
                        tipo=novo_tipo,
                        data=str(nova_data),
                        veiculo_id=opcoes_veiculos[novo_veiculo_label]["id"],
                        observacao=nova_observacao or None,
                    )
                    st.success("Movimentação atualizada com sucesso!")
                    del st.session_state["editando_mov"]
                    st.rerun()
                if cancelar:
                    del st.session_state["editando_mov"]
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
