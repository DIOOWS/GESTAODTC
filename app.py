import os
import streamlit as st
import pandas as pd
from sqlalchemy import text

from db import get_engine, init_db

import ui.painel as painel
import ui.produtos as produtos
import ui.lancamentos as lancamentos
import ui.transferencias as transferencias
import ui.estoque as estoque
import ui.relatorios as relatorios
import ui.importar_excel as importar_excel
import ui.importar_whatsapp as importar_whatsapp

st.set_page_config(page_title="Padaria | Controle", layout="wide")

# --- Tema ---
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

# --- Login simples (opcional) ---
APP_PASSWORD = os.getenv("APP_PASSWORD", "")
if APP_PASSWORD:
    pw = st.sidebar.text_input("Senha", type="password")
    if pw != APP_PASSWORD:
        st.sidebar.info("Digite a senha para acessar.")
        st.stop()

engine = get_engine()
init_db(engine)

def qdf(sql, params=None):
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})

def qexec(sql, params=None):
    with engine.begin() as conn:
        conn.execute(text(sql), params or {})

# Helpers: filiais e produto
def get_filial_id(nome: str) -> int:
    nome = (nome or "").strip().upper()
    df = qdf("SELECT id FROM filiais WHERE nome=:n;", {"n": nome})
    if not df.empty:
        return int(df.iloc[0]["id"])
    qexec("INSERT INTO filiais(nome) VALUES (:n) ON CONFLICT (nome) DO NOTHING;", {"n": nome})
    df = qdf("SELECT id FROM filiais WHERE nome=:n;", {"n": nome})
    return int(df.iloc[0]["id"])

def garantir_produto(categoria: str, produto_nome: str) -> int:
    categoria = (categoria or "").strip().upper()
    produto_nome = (produto_nome or "").strip().upper()
    if not categoria or not produto_nome:
        raise ValueError("categoria e produto são obrigatórios")

    df = qdf(
        "SELECT id FROM products WHERE categoria=:c AND produto=:p;",
        {"c": categoria, "p": produto_nome},
    )
    if not df.empty:
        return int(df.iloc[0]["id"])

    qexec("""
        INSERT INTO products(categoria, produto)
        VALUES (:c, :p)
        ON CONFLICT (categoria, produto) DO NOTHING;
    """, {"c": categoria, "p": produto_nome})

    df = qdf(
        "SELECT id FROM products WHERE categoria=:c AND produto=:p;",
        {"c": categoria, "p": produto_nome},
    )
    return int(df.iloc[0]["id"])

# --- Sidebar ---
st.sidebar.title("📦 Padaria")
page = st.sidebar.radio(
    "Menu",
    [
        "Painel",
        "Produtos",
        "Lançamentos",
        "Transferências",
        "Estoque",
        "Relatórios",
        "Importar Excel",
        "Importar WhatsApp",
    ],
)

# --- Router ---
if page == "Painel":
    painel.render(st, qdf)

elif page == "Produtos":
    produtos.render(st, qdf, qexec)

elif page == "Lançamentos":
    lancamentos.render(st, qdf, qexec, garantir_produto, get_filial_id)

elif page == "Transferências":
    transferencias.render(st, qdf, qexec, garantir_produto, get_filial_id)

elif page == "Estoque":
    estoque.render(st, qdf, qexec, get_filial_id)

elif page == "Relatórios":
    relatorios.render(st, qdf, get_filial_id)

elif page == "Importar Excel":
    importar_excel.render(st, qdf, qexec, garantir_produto)

elif page == "Importar WhatsApp":
    importar_whatsapp.render(st, qdf, qexec, garantir_produto, get_filial_id)
