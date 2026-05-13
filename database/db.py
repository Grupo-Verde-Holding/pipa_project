import streamlit as st
from supabase import create_client
import httpx


@st.cache_resource(ttl=600)
def get_cliente():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def _erro_conexao(e: Exception):
    st.error(
        "Sem conexão com o banco de dados. Verifique sua internet ou as configurações do Supabase.\n\n"
        f"Detalhe: {e}"
    )
    st.stop()


# --- Veículos ---

def listar_veiculos():
    try:
        supabase = get_cliente()
        response = supabase.table("veiculos").select("*").order("modelo").execute()
        return response.data
    except (httpx.ConnectError, Exception) as e:
        _erro_conexao(e)


def inserir_veiculo(placa: str, modelo: str, marca: str, km_atual: float):
    try:
        supabase = get_cliente()
        supabase.table("veiculos").insert({
            "placa": placa.upper(),
            "modelo": modelo,
            "marca": marca,
            "km_atual": km_atual,
            "ativo": 1,
        }).execute()
    except (httpx.ConnectError, Exception) as e:
        _erro_conexao(e)


def atualizar_km(veiculo_id: int, km_atual: float):
    try:
        supabase = get_cliente()
        supabase.table("veiculos").update({"km_atual": km_atual}).eq("id", veiculo_id).execute()
    except (httpx.ConnectError, Exception) as e:
        _erro_conexao(e)


def alternar_status(veiculo_id: int, ativo: bool):
    try:
        supabase = get_cliente()
        supabase.table("veiculos").update({"ativo": 1 - ativo}).eq("id", veiculo_id).execute()
    except (httpx.ConnectError, Exception) as e:
        _erro_conexao(e)


def atualizar_veiculo(veiculo_id: int, modelo: str, marca: str, km_atual: float):
    try:
        supabase = get_cliente()
        supabase.table("veiculos").update({
            "modelo": modelo,
            "marca": marca,
            "km_atual": km_atual,
        }).eq("id", veiculo_id).execute()
    except (httpx.ConnectError, Exception) as e:
        _erro_conexao(e)


def deletar_veiculo(veiculo_id: int):
    try:
        supabase = get_cliente()
        supabase.table("veiculos").delete().eq("id", veiculo_id).execute()
    except (httpx.ConnectError, Exception) as e:
        _erro_conexao(e)


# --- Manutenções ---

def listar_manutencoes():
    try:
        supabase = get_cliente()
        response = (
            supabase.table("manutencoes")
            .select("*, veiculos(placa, modelo)")
            .order("data", desc=True)
            .execute()
        )
        return response.data
    except (httpx.ConnectError, Exception) as e:
        _erro_conexao(e)


def inserir_manutencao(veiculo_id: int, tipo: str, data: str, km_na_data: float, custo: float, descricao: str, proxima_km: float | None):
    try:
        supabase = get_cliente()
        supabase.table("manutencoes").insert({
            "veiculo_id": veiculo_id,
            "tipo": tipo,
            "data": data,
            "km_na_data": km_na_data,
            "custo": custo,
            "descricao": descricao,
            "proxima_km": proxima_km,
        }).execute()
    except (httpx.ConnectError, Exception) as e:
        _erro_conexao(e)


def atualizar_manutencao(manutencao_id: int, tipo: str, data: str, km_na_data: float, proxima_km: float | None, descricao: str | None):
    try:
        supabase = get_cliente()
        supabase.table("manutencoes").update({
            "tipo": tipo,
            "data": data,
            "km_na_data": km_na_data,
            "proxima_km": proxima_km,
            "descricao": descricao,
        }).eq("id", manutencao_id).execute()
    except (httpx.ConnectError, Exception) as e:
        _erro_conexao(e)


def deletar_manutencao(manutencao_id: int):
    try:
        supabase = get_cliente()
        supabase.table("manutencoes").delete().eq("id", manutencao_id).execute()
    except (httpx.ConnectError, Exception) as e:
        _erro_conexao(e)


# --- Pneus ---

def listar_pneus():
    try:
        supabase = get_cliente()
        response = supabase.table("pneus").select("*").order("dot").execute()
        return response.data
    except (httpx.ConnectError, Exception) as e:
        _erro_conexao(e)


def inserir_pneu(dot: str, condicao: str, status: str, localidade_servico: str | None):
    try:
        supabase = get_cliente()
        supabase.table("pneus").insert({
            "dot": dot.lower() if dot else "",
            "condicao": condicao,
            "status": status,
            "localidade_servico": localidade_servico or None,
        }).execute()
    except (httpx.ConnectError, Exception) as e:
        _erro_conexao(e)


def atualizar_status_pneu(pneu_id: int, status: str):
    try:
        supabase = get_cliente()
        supabase.table("pneus").update({"status": status}).eq("id", pneu_id).execute()
    except (httpx.ConnectError, Exception) as e:
        _erro_conexao(e)


def atualizar_pneu(pneu_id: int, dot: str, condicao: str, status: str, localidade_servico: str | None):
    try:
        supabase = get_cliente()
        supabase.table("pneus").update({
            "dot": dot.lower() if dot else "",
            "condicao": condicao,
            "status": status,
            "localidade_servico": localidade_servico or None,
        }).eq("id", pneu_id).execute()
    except (httpx.ConnectError, Exception) as e:
        _erro_conexao(e)


def deletar_pneu(pneu_id: int):
    try:
        supabase = get_cliente()
        supabase.table("pneus").delete().eq("id", pneu_id).execute()
    except (httpx.ConnectError, Exception) as e:
        _erro_conexao(e)


# --- Movimentação de Pneus ---

def listar_movimentacoes():
    try:
        supabase = get_cliente()
        response = (
            supabase.table("movimentacao_pneus")
            .select("*, pneus(id, dot, condicao), veiculos(placa, modelo)")
            .order("data", desc=True)
            .execute()
        )
        return response.data
    except (httpx.ConnectError, Exception) as e:
        _erro_conexao(e)


def inserir_movimentacao(pneu_id: int, tipo: str, data: str, veiculo_id: int | None, posicao: str | None, km_veiculo: float | None, observacao: str | None):
    try:
        supabase = get_cliente()
        supabase.table("movimentacao_pneus").insert({
            "pneu_id": pneu_id,
            "tipo": tipo,
            "data": data,
            "veiculo_id": veiculo_id,
            "posicao": posicao,
            "km_veiculo": km_veiculo,
            "observacao": observacao,
        }).execute()
    except (httpx.ConnectError, Exception) as e:
        _erro_conexao(e)


def atualizar_movimentacao(mov_id: int, tipo: str, data: str, veiculo_id: int | None, observacao: str | None):
    try:
        supabase = get_cliente()
        supabase.table("movimentacao_pneus").update({
            "tipo": tipo,
            "data": data,
            "veiculo_id": veiculo_id,
            "observacao": observacao,
        }).eq("id", mov_id).execute()
    except (httpx.ConnectError, Exception) as e:
        _erro_conexao(e)


def deletar_movimentacao(movimentacao_id: int):
    try:
        supabase = get_cliente()
        supabase.table("movimentacao_pneus").delete().eq("id", movimentacao_id).execute()
    except (httpx.ConnectError, Exception) as e:
        _erro_conexao(e)
