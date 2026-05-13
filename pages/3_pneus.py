import streamlit as st
import pandas as pd
from database.db import listar_pneus, inserir_pneu, atualizar_status_pneu, deletar_pneu

st.set_page_config(page_title="Pneus", page_icon="🔵")
st.title("Pneus")

# --- Formulário ---
with st.expander("Cadastrar pneu", expanded=True):
    with st.form("form_pneu", clear_on_submit=True):
        dot = st.text_input("DOT", placeholder="ex: 2324")

        LOCALIDADES = [
            "Quissamã", "Macaé", "Base", "Itaperuna", "Italva",
            "Varre Sai", "Porciúncula", "São João da Barra", "Muriaé", "Cardoso Moreira",
        ]

        col1, col2, col3 = st.columns(3)
        condicao           = col1.selectbox("Condição", ["Novo", "Usado"])
        status             = col2.selectbox("Status", ["Ativo", "Substituído"])
        localidade_servico = col3.selectbox("Localidade de serviço", LOCALIDADES)

        submitted = st.form_submit_button("Salvar", use_container_width=True)

    if submitted:
        if not dot.strip():
            st.error("Preencha o campo DOT.")
        else:
            inserir_pneu(
                dot=dot.strip().lower(),
                condicao=condicao,
                status=status,
                localidade_servico=localidade_servico.strip() or None,
            )
            st.success(f"Pneu DOT {dot.strip().lower()} cadastrado com sucesso!")
            st.rerun()

# --- Lista ---
st.divider()
st.subheader("Pneus cadastrados")

dados = listar_pneus()

if not dados:
    st.info("Nenhum pneu cadastrado ainda.")
else:
    df = pd.DataFrame(dados)

    col_f1, col_f2, col_f3 = st.columns(3)
    busca           = col_f1.text_input("Buscar por DOT ou localidade", label_visibility="collapsed", placeholder="Buscar por DOT ou localidade...")
    filtro_condicao = col_f2.selectbox("Condição", ["Todos", "Novo", "Usado"], label_visibility="collapsed")
    filtro_status   = col_f3.selectbox("Status", ["Todos", "Ativo", "Substituído"], label_visibility="collapsed")

    if busca:
        df = df[
            df["dot"].fillna("").str.contains(busca, case=False) |
            df["localidade_servico"].fillna("").str.contains(busca, case=False)
        ]
    if filtro_condicao != "Todos":
        df = df[df["condicao"] == filtro_condicao]
    if filtro_status != "Todos":
        df = df[df["status"] == filtro_status]

    colunas = [c for c in ["id", "dot", "condicao", "status", "localidade_servico"] if c in df.columns]
    df_exibir = df[colunas].rename(columns={
        "id":                  "ID",
        "dot":                 "DOT",
        "condicao":            "Condição",
        "status":              "Status",
        "localidade_servico":  "Localidade de Serviço",
    })
    st.dataframe(df_exibir, use_container_width=True, hide_index=True)

    # --- Ações ---
    st.divider()
    st.subheader("Ações")

    opcoes_pneu = {f"DOT: {r['dot']} | ID: {r['id']}": r for _, r in df.iterrows()}
    if opcoes_pneu:
        selecionado_label = st.selectbox("Selecionar pneu", list(opcoes_pneu.keys()))
        pneu = opcoes_pneu[selecionado_label]

        novo_status = "Substituído" if pneu["status"] == "Ativo" else "Ativo"
        col_a, col_b = st.columns(2)

        if col_a.button(f"Marcar como {novo_status}", use_container_width=True):
            atualizar_status_pneu(pneu["id"], novo_status)
            st.rerun()

        if col_b.button("Excluir registro", type="primary", use_container_width=True):
            deletar_pneu(pneu["id"])
            st.success(f"Pneu ID {pneu['id']} excluído.")
            st.rerun()
