import streamlit as st
import pandas as pd
from database.db import listar_pneus, inserir_pneu, atualizar_pneu, atualizar_status_pneu, deletar_pneu

st.set_page_config(page_title="Pneus", page_icon="🔵")
st.title("Pneus")

LOCALIDADES = [
    "Quissamã", "Macaé", "Base", "Itaperuna", "Italva",
    "Varre Sai", "Porciúncula", "São João da Barra", "Muriaé", "Cardoso Moreira",
]

# --- Formulário ---
with st.expander("Cadastrar pneu", expanded=True):
    with st.form("form_pneu", clear_on_submit=True):
        dot = st.text_input("DOT", placeholder="ex: 2324")

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
        "id":                 "ID",
        "dot":                "DOT",
        "condicao":           "Condição",
        "status":             "Status",
        "localidade_servico": "Localidade de Serviço",
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
        col_a, col_b, col_c = st.columns(3)

        if col_a.button("Editar", use_container_width=True, key="btn_editar_pneu"):
            st.session_state["editando_pneu"] = pneu["id"]

        if col_b.button(f"Marcar como {novo_status}", use_container_width=True):
            atualizar_status_pneu(pneu["id"], novo_status)
            st.rerun()

        if col_c.button("Excluir registro", type="primary", use_container_width=True):
            deletar_pneu(pneu["id"])
            st.success(f"Pneu ID {pneu['id']} excluído.")
            st.rerun()

        # Formulário de edição
        if st.session_state.get("editando_pneu") == pneu["id"]:
            st.divider()
            st.subheader(f"Editando pneu ID {pneu['id']}")
            with st.form("form_editar_pneu"):
                novo_dot = st.text_input("DOT", value=pneu.get("dot", ""))

                col1, col2, col3 = st.columns(3)
                nova_condicao = col1.selectbox(
                    "Condição", ["Novo", "Usado"],
                    index=["Novo", "Usado"].index(pneu.get("condicao", "Novo"))
                    if pneu.get("condicao") in ["Novo", "Usado"] else 0
                )
                novo_status_edit = col2.selectbox(
                    "Status", ["Ativo", "Substituído"],
                    index=["Ativo", "Substituído"].index(pneu.get("status", "Ativo"))
                    if pneu.get("status") in ["Ativo", "Substituído"] else 0
                )
                loc_atual = pneu.get("localidade_servico") or LOCALIDADES[0]
                nova_localidade = col3.selectbox(
                    "Localidade de serviço", LOCALIDADES,
                    index=LOCALIDADES.index(loc_atual) if loc_atual in LOCALIDADES else 0
                )

                col_s, col_c2 = st.columns(2)
                salvar   = col_s.form_submit_button("Salvar alterações", use_container_width=True)
                cancelar = col_c2.form_submit_button("Cancelar", use_container_width=True)

            if salvar:
                atualizar_pneu(
                    pneu_id=pneu["id"],
                    dot=novo_dot.strip().lower(),
                    condicao=nova_condicao,
                    status=novo_status_edit,
                    localidade_servico=nova_localidade or None,
                )
                st.success("Pneu atualizado com sucesso!")
                del st.session_state["editando_pneu"]
                st.rerun()
            if cancelar:
                del st.session_state["editando_pneu"]
                st.rerun()
