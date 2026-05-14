import streamlit as st
import pandas as pd
from database.db import listar_veiculos, inserir_veiculo, atualizar_veiculo, alternar_status, deletar_veiculo

st.set_page_config(page_title="Veículos", page_icon="🚗")
st.title("Veículos")

MARCAS = ["VW", "MBENZ"]

# --- Formulário de cadastro ---
with st.expander("Cadastrar novo veículo", expanded=True):
    with st.form("form_veiculo", clear_on_submit=True):
        col1, col2 = st.columns(2)
        placa  = col1.text_input("Placa", placeholder="ex: ABC1D23")
        marca  = col2.selectbox("Marca", MARCAS)

        col3, col4 = st.columns(2)
        modelo = col3.text_input("Modelo", placeholder="ex: Constellation 24.280")
        km     = col4.number_input("KM Atual", min_value=0.0, step=1.0, format="%.0f")

        submitted = st.form_submit_button("Salvar", use_container_width=True)

    if submitted:
        if not placa.strip():
            st.error("Preencha a placa do veículo.")
        elif not modelo.strip():
            st.error("Preencha o modelo do veículo.")
        else:
            inserir_veiculo(placa.strip().upper(), modelo.strip(), marca, km)
            st.success(f"Veículo {placa.strip().upper()} cadastrado com sucesso!")
            st.rerun()

# --- Lista de veículos ---
st.divider()
st.subheader("Frota cadastrada")

dados = listar_veiculos()

if not dados:
    st.info("Nenhum veículo cadastrado ainda.")
else:
    df = pd.DataFrame(dados)

    col_busca, col_status = st.columns([3, 1])
    busca        = col_busca.text_input("Buscar", label_visibility="collapsed", placeholder="Buscar por placa ou modelo...")
    filtro_ativo = col_status.selectbox("Status", ["Todos", "Ativos", "Inativos"], label_visibility="collapsed")

    if busca:
        df = df[df["placa"].str.contains(busca, case=False) | df["modelo"].str.contains(busca, case=False)]
    if filtro_ativo == "Ativos":
        df = df[df["ativo"] == 1]
    elif filtro_ativo == "Inativos":
        df = df[df["ativo"] == 0]

    df_exibir = df[["placa", "modelo", "marca", "km_atual", "ativo"]].copy()
    df_exibir["km_atual"] = df_exibir["km_atual"].apply(
        lambda v: f"{float(v):,.0f}".replace(",", ".")
    )
    df_exibir.rename(columns={
        "placa": "Placa", "modelo": "Modelo", "marca": "Marca",
        "km_atual": "KM Atual", "ativo": "Ativo",
    }, inplace=True)
    st.dataframe(df_exibir, use_container_width=True, hide_index=True)

    # --- Ações ---
    st.divider()
    st.subheader("Ações")
    opcoes = {f"{v['placa']} — {v['modelo']}": v for v in dados}
    selecionado_label = st.selectbox("Selecionar veículo", list(opcoes.keys()))
    veiculo = opcoes[selecionado_label]

    col_a, col_b, col_c = st.columns(3)

    if col_a.button("Editar", use_container_width=True):
        st.session_state["editando_veiculo"] = veiculo["id"]

    if col_b.button("Ativar / Desativar", use_container_width=True):
        alternar_status(veiculo["id"], veiculo["ativo"])
        st.rerun()

    if col_c.button("Excluir veículo", type="primary", use_container_width=True):
        deletar_veiculo(veiculo["id"])
        st.success(f"Veículo {veiculo['placa']} excluído.")
        st.rerun()

    # --- Formulário de edição ---
    if st.session_state.get("editando_veiculo") == veiculo["id"]:
        st.divider()
        st.subheader(f"Editando: {veiculo['placa']}")
        with st.form("form_editar_veiculo"):
            col1, col2 = st.columns(2)
            novo_modelo = col1.text_input("Modelo", value=veiculo.get("modelo", ""))
            marca_atual = veiculo.get("marca", MARCAS[0])
            nova_marca  = col2.selectbox(
                "Marca", MARCAS,
                index=MARCAS.index(marca_atual) if marca_atual in MARCAS else 0
            )
            novo_km = st.number_input("KM Atual", min_value=0.0, step=1.0, format="%.0f",
                                      value=float(veiculo.get("km_atual", 0)))

            col_s, col_c2 = st.columns(2)
            salvar   = col_s.form_submit_button("Salvar alterações", use_container_width=True)
            cancelar = col_c2.form_submit_button("Cancelar", use_container_width=True)

        if salvar:
            atualizar_veiculo(veiculo["id"], novo_modelo, nova_marca, novo_km)
            st.success("Veículo atualizado com sucesso!")
            del st.session_state["editando_veiculo"]
            st.rerun()
        if cancelar:
            del st.session_state["editando_veiculo"]
            st.rerun()
