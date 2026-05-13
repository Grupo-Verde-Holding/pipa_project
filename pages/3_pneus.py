import streamlit as st
import pandas as pd
from database.db import listar_pneus, inserir_pneu, atualizar_status_pneu, deletar_pneu

st.set_page_config(page_title="Pneus", page_icon="🔵")
st.title("Pneus")

# --- Formulário ---
with st.expander("Cadastrar pneu", expanded=True):
    with st.form("form_pneu", clear_on_submit=True):
        dot = st.text_input("DOT", placeholder="ex: 2324")

        col1, col2 = st.columns(2)
        condicao = col1.selectbox("Condição", ["Novo", "Usado"])
        status   = col2.selectbox("Status", ["Ativo", "Substituído"])

        submitted = st.form_submit_button("Salvar", use_container_width=True)

    if submitted:
        if not dot.strip():
            st.error("Preencha o campo DOT.")
        else:
            dot_lower = dot.strip().lower()
            base_codigo = f"pne-{dot_lower}"

            # evitar duplicidade de código
            existentes = listar_pneus() or []
            codigos_existentes = {p["codigo"] for p in existentes}
            codigo = base_codigo
            sufixo = 2
            while codigo in codigos_existentes:
                codigo = f"{base_codigo}-{sufixo}"
                sufixo += 1

            inserir_pneu(
                codigo=codigo,
                dot=dot_lower,
                status=status,
                condicao=condicao,
            )
            st.success(f"Pneu {codigo} cadastrado com sucesso!")
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
    busca           = col_f1.text_input("Buscar por código ou DOT", label_visibility="collapsed", placeholder="Buscar por código ou DOT...")
    filtro_condicao = col_f2.selectbox("Condição", ["Todos", "Novo", "Usado"], label_visibility="collapsed")
    filtro_status   = col_f3.selectbox("Status", ["Todos", "Ativo", "Substituído"], label_visibility="collapsed")

    if busca:
        df = df[
            df["codigo"].str.contains(busca, case=False) |
            df["dot"].fillna("").str.contains(busca, case=False)
        ]
    if filtro_condicao != "Todos":
        df = df[df["condicao"] == filtro_condicao]
    if filtro_status != "Todos":
        df = df[df["status"] == filtro_status]

    colunas = [c for c in ["codigo", "dot", "condicao", "status"] if c in df.columns]
    df_exibir = df[colunas].rename(columns={
        "codigo":   "Código",
        "dot":      "DOT",
        "condicao": "Condição",
        "status":   "Status",
    })
    st.dataframe(df_exibir, use_container_width=True, hide_index=True)

    # --- Ações ---
    st.divider()
    st.subheader("Ações")

    opcoes_pneu = {f"{r['codigo']} — DOT: {r.get('dot', '')}": r for _, r in df.iterrows()}
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
            st.success(f"Pneu {pneu['codigo']} excluído.")
            st.rerun()
