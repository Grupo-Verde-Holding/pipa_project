import streamlit as st
import pandas as pd
from datetime import date
from database.db import (
    listar_veiculos, listar_pneus, listar_movimentacoes,
    inserir_movimentacao, deletar_movimentacao,
)

st.set_page_config(page_title="Movimentação de Pneus", page_icon="🔄")
st.title("Movimentação de Pneus")

TIPOS = ["Instalação", "Remoção", "Rodízio", "Recapagem", "Descarte"]
POSICOES = [
    "Dianteiro Esquerdo",
    "Dianteiro Direito",
    "Traseiro Esquerdo",
    "Traseiro Direito",
    "Estepe",
]

pneus    = listar_pneus()
veiculos = listar_veiculos()

if not pneus:
    st.warning("Nenhum pneu cadastrado. Cadastre um pneu primeiro.")
    st.stop()

opcoes_pneus    = {f"{p['codigo']} — {p['marca']} {p['modelo']}": p["id"] for p in pneus}
opcoes_veiculos = {f"{v['placa']} — {v['modelo']}": v for v in veiculos}

# --- Formulário ---
with st.expander("Registrar movimentação", expanded=True):
    with st.form("form_movimentacao", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        pneu_label = col1.selectbox("Pneu", list(opcoes_pneus.keys()))
        tipo       = col2.selectbox("Tipo", TIPOS)
        data_mov   = col3.date_input("Data", value=date.today())

        requer_veiculo = tipo in ["Instalação", "Remoção", "Rodízio"]

        col4, col5, col6 = st.columns(3)
        veiculo_opcoes = ["— Nenhum —"] + list(opcoes_veiculos.keys())
        veiculo_label  = col4.selectbox("Veículo", veiculo_opcoes, disabled=not requer_veiculo)
        posicao        = col5.selectbox("Posição", ["—"] + POSICOES, disabled=not requer_veiculo)
        km_veiculo     = col6.number_input("KM do Veículo", min_value=0.0, step=1.0, disabled=not requer_veiculo)

        observacao = st.text_input("Observação (opcional)")

        submitted = st.form_submit_button("Salvar", use_container_width=True)

    if submitted:
        vid = opcoes_veiculos[veiculo_label]["id"] if veiculo_label != "— Nenhum —" else None
        pos = posicao if posicao != "—" else None
        km  = km_veiculo if km_veiculo > 0 else None

        inserir_movimentacao(
            pneu_id=opcoes_pneus[pneu_label],
            tipo=tipo,
            data=str(data_mov),
            veiculo_id=vid,
            posicao=pos,
            km_veiculo=km,
            observacao=observacao or None,
        )
        st.success("Movimentação registrada com sucesso!")
        st.rerun()

# --- Histórico ---
st.divider()
st.subheader("Histórico de movimentações")

dados = listar_movimentacoes()

if not dados:
    st.info("Nenhuma movimentação registrada ainda.")
else:
    df = pd.DataFrame(dados)
    df["pneu"]    = df["pneus"].apply(lambda p: f"{p['codigo']} — {p['marca']} {p['modelo']}" if p else "—")
    df["veiculo"] = df["veiculos"].apply(lambda v: f"{v['placa']} — {v['modelo']}" if v else "—")

    col_f1, col_f2, col_f3 = st.columns(3)
    filtro_pneu    = col_f1.selectbox("Pneu", ["Todos"] + list(opcoes_pneus.keys()), label_visibility="collapsed")
    filtro_tipo    = col_f2.selectbox("Tipo", ["Todos"] + TIPOS, label_visibility="collapsed")
    filtro_veiculo = col_f3.selectbox("Veículo", ["Todos"] + list(opcoes_veiculos.keys()), label_visibility="collapsed")

    if filtro_pneu != "Todos":
        pid = opcoes_pneus[filtro_pneu]
        df = df[df["pneu_id"] == pid]
    if filtro_tipo != "Todos":
        df = df[df["tipo"] == filtro_tipo]
    if filtro_veiculo != "Todos":
        vid = opcoes_veiculos[filtro_veiculo]["id"]
        df = df[df["veiculo_id"] == vid]

    df_exibir = df[["data", "tipo", "pneu", "veiculo", "posicao", "km_veiculo", "observacao"]].rename(columns={
        "data": "Data",
        "tipo": "Tipo",
        "pneu": "Pneu",
        "veiculo": "Veículo",
        "posicao": "Posição",
        "km_veiculo": "KM Veículo",
        "observacao": "Observação",
    })
    st.dataframe(df_exibir, use_container_width=True, hide_index=True)

    # --- Ações ---
    st.divider()
    st.subheader("Ações")

    opcoes_mov = {f"{r['data']} | {r['tipo']} | {r['pneu']}": r for _, r in df.iterrows()}
    if opcoes_mov:
        selecionado_label = st.selectbox("Selecionar registro", list(opcoes_mov.keys()))
        mov = opcoes_mov[selecionado_label]

        if st.button("Excluir registro", type="primary", use_container_width=True):
            deletar_movimentacao(mov["id"])
            st.success("Registro excluído.")
            st.rerun()
