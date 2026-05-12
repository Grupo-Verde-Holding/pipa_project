import streamlit as st
import pandas as pd
from database.db import listar_veiculos, inserir_veiculo, alternar_status, deletar_veiculo
from lista_veiculos import veiculos_VW, veiculos_mbenz

st.set_page_config(page_title="Veículos", page_icon="🚗")
st.title("Veículos")

MARCAS = {"VW": veiculos_VW, "MBENZ": veiculos_mbenz}

# --- Formulário de cadastro ---
with st.expander("Cadastrar novo veículo", expanded=True):
    marca_sel = st.selectbox("Marca", list(MARCAS.keys()), key="marca_veiculo")
    placas_disponiveis = MARCAS[marca_sel]

    with st.form("form_veiculo", clear_on_submit=True):
        col1, col2 = st.columns(2)
        placa  = col1.selectbox("Placa", placas_disponiveis)
        modelo = col2.text_input("Modelo")
        km     = col1.number_input("KM Atual", min_value=0.0, step=1.0)

        submitted = st.form_submit_button("Salvar", use_container_width=True)

    if submitted:
        if not modelo:
            st.error("Preencha o modelo do veículo.")
        else:
            inserir_veiculo(placa, modelo, marca_sel, km)
            st.success(f"Veículo {placa} cadastrado com sucesso!")
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

    col_a, col_b = st.columns(2)
    if col_a.button("Ativar / Desativar", use_container_width=True):
        alternar_status(veiculo["id"], veiculo["ativo"])
        st.rerun()

    if col_b.button("Excluir veículo", type="primary", use_container_width=True):
        deletar_veiculo(veiculo["id"])
        st.success(f"Veículo {veiculo['placa']} excluído.")
        st.rerun()
