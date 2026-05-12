import streamlit as st
import pandas as pd
from database.db import listar_pneus, inserir_pneu, atualizar_status_pneu, deletar_pneu

st.set_page_config(page_title="Pneus", page_icon="🔵")
st.title("Pneus")

TIPOS = ["Radial", "Diagonal", "Run Flat", "Off Road"]

# --- Formulário ---
with st.expander("Cadastrar pneu", expanded=True):
    with st.form("form_pneu", clear_on_submit=True):
        col1, col2 = st.columns(2)
        codigo = col1.text_input("Código", placeholder="ex: PNE-001")
        tipo   = col2.selectbox("Tipo", TIPOS)

        col3, col4, col5 = st.columns(3)
        marca  = col3.text_input("Marca")
        modelo = col4.text_input("Modelo")
        dot    = col5.text_input("DOT", placeholder="ex: 2324")

        status = st.selectbox("Status", ["Ativo", "Substituído"])

        submitted = st.form_submit_button("Salvar", use_container_width=True)

    if submitted:
        if not codigo or not marca or not tipo:
            st.error("Preencha código, marca e tipo.")
        else:
            inserir_pneu(
                codigo=codigo.upper(),
                marca=marca,
                modelo=modelo,
                dot=dot,
                tipo=tipo,
                status=status,
            )
            st.success(f"Pneu {codigo.upper()} cadastrado com sucesso!")
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
    busca         = col_f1.text_input("Buscar por código ou marca", label_visibility="collapsed", placeholder="Buscar por código ou marca...")
    filtro_tipo   = col_f2.selectbox("Tipo", ["Todos"] + TIPOS, label_visibility="collapsed")
    filtro_status = col_f3.selectbox("Status", ["Todos", "Ativo", "Substituído"], label_visibility="collapsed")

    if busca:
        df = df[df["codigo"].str.contains(busca, case=False) | df["marca"].str.contains(busca, case=False)]
    if filtro_tipo != "Todos":
        df = df[df["tipo"] == filtro_tipo]
    if filtro_status != "Todos":
        df = df[df["status"] == filtro_status]

    df_exibir = df[["codigo", "marca", "modelo", "dot", "tipo", "status"]].rename(columns={
        "codigo": "Código",
        "marca": "Marca",
        "modelo": "Modelo",
        "dot": "DOT",
        "tipo": "Tipo",
        "status": "Status",
    })
    st.dataframe(df_exibir, use_container_width=True, hide_index=True)

    # --- Ações ---
    st.divider()
    st.subheader("Ações")

    opcoes_pneu = {f"{r['codigo']} — {r['marca']} {r['modelo']}": r for _, r in df.iterrows()}
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
