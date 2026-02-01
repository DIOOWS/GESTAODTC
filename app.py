import os
import re

import streamlit as st
import pandas as pd
from sqlalchemy import text

from db import get_engine, init_db

from ui import painel, produtos, lancamentos, relatorios, importar_excel, importar_whatsapp


st.set_page_config(page_title="Padaria | Controle", layout="wide")

# Tema (paleta)
st.markdown("""
<style>
:root{
  --bg: #020204;
  --panel: #1B1922;
  --panel2: #373033;
  --muted: #4F3D3D;
  --accent: #E86942;
  --paper: #ECD7C3;
}
html, body, [class*="css"] { background: var(--bg) !important; color: var(--paper) !important; }
section[data-testid="stSidebar"] { background: var(--panel) !important; }
div[data-testid="stMetric"] { background: var(--panel); padding: 12px; border-radius: 12px; border: 1px solid rgba(236,215,195,0.12); }
.stButton>button { background: var(--accent) !important; color: #020204 !important; border: none; font-weight: 700; }
div[data-testid="stDataFrame"] { background: var(--panel); border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# Login opcional
APP_PASSWORD = os.getenv("APP_PASSWORD", "")
if APP_PASSWORD:
    senha = st.sidebar.text_input("Senha", type="password")
    if senha != APP_PASSWORD:
        st.sidebar.info("Digite a senha para acessar.")
        st.stop()

engine = get_engine()
init_db(engine)


def qdf(sql: str, params=None) -> pd.DataFrame:
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


def qexec(sql: str, params=None) -> None:
    with engine.begin() as conn:
        conn.execute(text(sql), params or {})


def normalizar_upper(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip()).upper()


def get_filial_id(nome_filial: str) -> int:
    nome = normalizar_upper(nome_filial)
    df = qdf("SELECT id FROM locais WHERE nome=:n;", {"n": nome})
    return int(df["id"].iloc[0])


def garantir_produto(nome_produto: str, categoria: str | None = None) -> int:
    nome = normalizar_upper(nome_produto)
    cat = normalizar_upper(categoria) if categoria else None
    qexec("""
        INSERT INTO produtos(nome, categoria, ativo)
        VALUES (:n, :c, TRUE)
        ON CONFLICT (nome)
        DO UPDATE SET categoria = COALESCE(EXCLUDED.categoria, produtos.categoria),
                      ativo = TRUE;
    """, {"n": nome, "c": cat})
    df = qdf("SELECT id FROM produtos WHERE nome = :n;", {"n": nome})
    return int(df["id"].iloc[0])


st.sidebar.title("📦 Padaria")

menu = st.sidebar.radio(
    "Menu",
    ["Painel", "Produtos", "Lançamentos", "Relatórios", "Importar Excel", "Importar WhatsApp"]
)

if menu == "Painel":
    painel.render(st, qdf)

elif menu == "Produtos":
    produtos.render(st, qdf, garantir_produto, qexec)

elif menu == "Lançamentos":
    lancamentos.render(st, qdf, qexec, garantir_produto, get_filial_id)

elif menu == "Relatórios":
    relatorios.render(st, qdf)

elif menu == "Importar Excel":
    importar_excel.render(st, qdf, qexec)

elif menu == "Importar WhatsApp":
    importar_whatsapp.render(st, qdf, qexec, garantir_produto, get_filial_id)
