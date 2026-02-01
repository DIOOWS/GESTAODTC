import os
import streamlit as st
from db import get_engine, init_db

from ui import painel, produtos, lancamentos, relatorios, importar_excel, importar_whatsapp, estoque

st.set_page_config(page_title="Padaria | Controle", layout="wide")

# --- Tema (sua paleta) ---
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
APP_PASSWORD = os.getenv("APP_PASSWORD", "").strip()
if APP_PASSWORD:
    pw = st.sidebar.text_input("Senha", type="password")
    if pw != APP_PASSWORD:
        st.sidebar.info("Digite a senha para acessar.")
        st.stop()

engine = get_engine()
init_db(engine)

# Helpers SQL
import pandas as pd
from sqlalchemy import text

def qdf(sql, params=None):
    with engine.begin() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})

def qexec(sql, params=None):
    with engine.begin() as conn:
        conn.execute(text(sql), params or {})

def get_filial_id(nome: str) -> int:
    df = qdf("SELECT id FROM filiais WHERE nome=:n", {"n": nome})
    return int(df["id"].iloc[0])

def garantir_categoria(nome_cat: str):
    nome_cat = (nome_cat or "").strip().upper()
    if not nome_cat:
        return None
    qexec("INSERT INTO categorias(nome) VALUES (:n) ON CONFLICT (nome) DO NOTHING;", {"n": nome_cat})
    df = qdf("SELECT id FROM categorias WHERE nome=:n", {"n": nome_cat})
    return int(df["id"].iloc[0])

def garantir_produto(categoria: str, produto: str) -> int:
    cat_id = garantir_categoria(categoria)
    nome = (produto or "").strip().upper()
    if not nome:
        raise ValueError("Produto vazio")

    qexec("""
        INSERT INTO produtos(nome, categoria_id)
        VALUES (:nome, :cat)
        ON CONFLICT (categoria_id, nome) DO NOTHING;
    """, {"nome": nome, "cat": cat_id})

    df = qdf("SELECT id FROM produtos WHERE nome=:nome AND categoria_id IS NOT DISTINCT FROM :cat",
             {"nome": nome, "cat": cat_id})
    return int(df["id"].iloc[0])

# --- Sidebar ---
st.sidebar.title("📦 Padaria")
page = st.sidebar.radio(
    "Menu",
    ["Painel", "Produtos", "Lançamentos", "Transferências", "Estoque", "Relatórios", "Importar Excel", "Importar WhatsApp"]
)

if page == "Painel":
    painel.render(st, qdf)

elif page == "Produtos":
    produtos.render(st, qdf, qexec, garantir_produto)

elif page == "Lançamentos":
    lancamentos.render(st, qdf, qexec, garantir_produto, get_filial_id)

elif page == "Transferências":
    lancamentos.render_transferencias(st, qdf, qexec, garantir_produto, get_filial_id)

elif page == "Estoque":
    estoque.render(st, qdf, qexec, garantir_produto, get_filial_id)

elif page == "Relatórios":
    relatorios.render(st, qdf)

elif page == "Importar Excel":
    importar_excel.render(st, qdf, qexec, garantir_produto)

elif page == "Importar WhatsApp":
    importar_whatsapp.render(st, qdf, qexec, garantir_produto, get_filial_id)
