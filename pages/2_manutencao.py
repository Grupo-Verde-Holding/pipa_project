import streamlit as st
import pandas as pd
from datetime import date
from database.db import listar_veiculos, listar_manutencoes, inserir_manutencao, atualizar_manutencao, deletar_manutencao, atualizar_km
from lista_servicos import servicos

st.set_page_config(page_title="Manutenção", page_icon="🔧", layout="wide")
st.title("Manutenção")


def fmt_km(val):
    try:
        return f"{float(val):,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "—"


def fmt_data(val):
    try:
        return pd.to_datetime(val).strftime("%d/%m/%Y")
    except Exception:
        return str(val) if val else "—"


# ── Dados ─────────────────────────────────────────────────────────────────────
veiculos = listar_veiculos()

if not veiculos:
    st.warning("Nenhum veículo cadastrado. Cadastre um veículo primeiro.")
    st.stop()

veiculos_por_placa = {v["placa"]: v for v in veiculos}
veiculos_por_id    = {v["id"]: v for v in veiculos}

marcas_disponiveis = sorted({v["marca"] for v in veiculos if v.get("marca")})

# ── Formulário de registro ────────────────────────────────────────────────────
with st.expander("Registrar manutenção", expanded=True):
    col1, col2 = st.columns(2)
    marca_sel = col1.selectbox("Marca", marcas_disponiveis, key="marca_manut")

    veiculos_marca = [v for v in veiculos if v.get("marca") == marca_sel]
    if not veiculos_marca:
        col2.warning(f"Nenhum veículo {marca_sel} cadastrado ainda.")
        st.stop()

    opcoes_placa = {f"{v['placa']} — {v['modelo']}": v for v in veiculos_marca}
    placa_label  = col2.selectbox("Veículo", list(opcoes_placa.keys()), key="placa_manut")
    veiculo_sel  = opcoes_placa[placa_label]

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
            atualizar_km(veiculo_sel["id"], km_na_data)
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
    df_exibir["data"]       = df_exibir["data"].apply(fmt_data)
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
    st.subheader("Ações")

    desc_label   = df["tipo"].str[:50]
    opcoes_manut = {
        f"{fmt_data(r['data'])} | {r['veiculo']} | {desc_label[i]}": r
        for i, (_, r) in enumerate(df.iterrows())
    }

    if opcoes_manut:
        selecionado_label = st.selectbox("Selecionar registro", list(opcoes_manut.keys()))
        manut = opcoes_manut[selecionado_label]

        col_e, col_d = st.columns(2)

        if col_e.button("Editar", use_container_width=True, key="btn_editar_manut"):
            st.session_state["editando_manut"] = manut["id"]

        if col_d.button("Excluir registro", type="primary", use_container_width=True, key="btn_excluir_manut"):
            st.session_state["confirm_del_manut"] = True

        # Formulário de edição
        if st.session_state.get("editando_manut") == manut["id"]:
            st.divider()
            st.subheader("Editando registro")
            with st.form("form_editar_manut"):
                novo_servico = st.selectbox("Serviço", servicos,
                                            index=servicos.index(manut["tipo"]) if manut["tipo"] in servicos else 0)
                col1, col2 = st.columns(2)
                nova_data      = col1.date_input("Data", value=pd.to_datetime(manut["data"]).date())
                novo_km        = col2.number_input("KM na Data", min_value=0.0, step=1.0,
                                                   value=float(manut.get("km_na_data") or 0))
                col3, col4 = st.columns(2)
                nova_prox_km   = col3.number_input("Próxima KM", min_value=0.0, step=1.0,
                                                   value=float(manut.get("proxima_km") or 0))
                nova_descricao = col4.text_input("Observação", value=manut.get("descricao") or "")

                col_s, col_c = st.columns(2)
                salvar   = col_s.form_submit_button("Salvar alterações", use_container_width=True)
                cancelar = col_c.form_submit_button("Cancelar", use_container_width=True)

            if salvar:
                atualizar_manutencao(
                    manutencao_id=manut["id"],
                    tipo=novo_servico,
                    data=str(nova_data),
                    km_na_data=novo_km,
                    proxima_km=nova_prox_km if nova_prox_km > 0 else None,
                    descricao=nova_descricao or None,
                )
                st.success("Registro atualizado com sucesso!")
                del st.session_state["editando_manut"]
                st.rerun()
            if cancelar:
                del st.session_state["editando_manut"]
                st.rerun()

        # Confirmação de exclusão
        if st.session_state.get("confirm_del_manut"):
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
