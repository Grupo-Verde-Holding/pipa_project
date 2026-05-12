import streamlit as st
import pandas as pd
from datetime import date
from database.db import listar_veiculos, listar_manutencoes, inserir_manutencao, deletar_manutencao
from lista_veiculos import veiculos_VW, veiculos_mbenz
from lista_servicos import servicos

st.set_page_config(page_title="Manutenção", page_icon="🔧", layout="wide")
st.title("Manutenção")

MARCAS = {"VW": veiculos_VW, "MBENZ": veiculos_mbenz}


def fmt_km(val):
    try:
        return f"{float(val):,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "—"


# ── Dados ─────────────────────────────────────────────────────────────────────
veiculos = listar_veiculos()

if not veiculos:
    st.warning("Nenhum veículo cadastrado. Cadastre um veículo primeiro.")
    st.stop()

veiculos_por_placa = {v["placa"]: v for v in veiculos}

# ── Formulário de registro ────────────────────────────────────────────────────
with st.expander("Registrar manutenção", expanded=True):
    col1, col2 = st.columns(2)
    marca_sel = col1.selectbox("Marca", list(MARCAS.keys()), key="marca_manut")

    placas_marca = [p for p in MARCAS[marca_sel] if p in veiculos_por_placa]
    if not placas_marca:
        st.warning(f"Nenhum veículo {marca_sel} cadastrado ainda.")
        st.stop()

    placa_sel   = col2.selectbox("Veículo (Placa)", placas_marca, key="placa_manut")
    veiculo_sel = veiculos_por_placa[placa_sel]

    with st.form("form_manutencao", clear_on_submit=True):
        servicos_sel = st.multiselect("Serviços realizados", servicos)

        data_manut = st.date_input("Data", value=date.today())

        col5, col6 = st.columns(2)
        km_na_data = col5.number_input("KM na Data", min_value=0.0, step=1.0,
                                       value=float(veiculo_sel["km_atual"]))
        proxima_km = col6.number_input("Próxima KM (opcional)", min_value=0.0, step=1.0, value=0.0)

        descricao = st.text_input("Observação (opcional)")

        submitted = st.form_submit_button("Salvar", use_container_width=True)

    if submitted:
        if not servicos_sel:
            st.error("Selecione ao menos um serviço.")
        elif km_na_data <= 0:
            st.error("Informe o KM na data da manutenção.")
        else:
            for servico in servicos_sel:
                inserir_manutencao(
                    veiculo_id=veiculo_sel["id"],
                    tipo=servico,
                    data=str(data_manut),
                    km_na_data=km_na_data,
                    custo=0.0,
                    descricao=descricao,
                    proxima_km=proxima_km if proxima_km > 0 else None,
                )
            st.success(f"{len(servicos_sel)} serviço(s) registrado(s) com sucesso!")
            st.rerun()

# ── Histórico ─────────────────────────────────────────────────────────────────
st.divider()
st.subheader("Histórico de Manutenções")

dados = listar_manutencoes()

if not dados:
    st.info("Nenhuma manutenção registrada ainda.")
else:
    df = pd.DataFrame(dados)
    df["veiculo"] = df["veiculos"].apply(
        lambda v: f"{v['placa']} — {v['modelo']}" if v else "—"
    )

    # Filtros
    opcoes_veiculos_hist = ["Todos"] + [f"{v['placa']} — {v['modelo']}" for v in veiculos]
    col_f1, col_f2 = st.columns(2)
    filtro_veiculo = col_f1.selectbox("Filtrar por veículo", opcoes_veiculos_hist)
    filtro_servico = col_f2.selectbox("Filtrar por serviço", ["Todos"] + servicos)

    if filtro_veiculo != "Todos":
        placa_filtro = filtro_veiculo.split(" — ")[0]
        if placa_filtro in veiculos_por_placa:
            df = df[df["veiculo_id"] == veiculos_por_placa[placa_filtro]["id"]]
    if filtro_servico != "Todos":
        df = df[df["tipo"] == filtro_servico]

    df_exibir = df[["veiculo", "tipo", "data", "km_na_data", "proxima_km", "descricao"]].copy()
    df_exibir["km_na_data"] = df_exibir["km_na_data"].apply(fmt_km)
    df_exibir["proxima_km"] = df_exibir["proxima_km"].apply(fmt_km)
    df_exibir.rename(columns={
        "veiculo":    "Veículo",
        "tipo":       "Serviço",
        "data":       "Data",
        "km_na_data": "KM na Data",
        "proxima_km": "Próxima KM",
        "descricao":  "Observação",
    }, inplace=True)
    st.dataframe(df_exibir, use_container_width=True, hide_index=True)

    # ── Ações ─────────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Excluir Registro")

    desc_label   = df["tipo"].str[:50]
    opcoes_manut = {
        f"{r['data']} | {r['veiculo']} | {desc_label[i]}": r
        for i, (_, r) in enumerate(df.iterrows())
    }

    if opcoes_manut:
        selecionado_label = st.selectbox("Selecionar registro", list(opcoes_manut.keys()))
        manut = opcoes_manut[selecionado_label]

        if "confirm_del_manut" not in st.session_state:
            st.session_state.confirm_del_manut = False

        if st.button("Excluir registro selecionado", use_container_width=True):
            st.session_state.confirm_del_manut = True

        if st.session_state.confirm_del_manut:
            st.warning(
                f"Confirmar exclusão de **{selecionado_label}**? "
                "Esta ação não pode ser desfeita."
            )
            col_y, col_n = st.columns(2)
            if col_y.button("Confirmar exclusão", type="primary", key="confirm_yes"):
                deletar_manutencao(manut["id"])
                st.session_state.confirm_del_manut = False
                st.success("Registro excluído.")
                st.rerun()
            if col_n.button("Cancelar", key="confirm_no"):
                st.session_state.confirm_del_manut = False
                st.rerun()
