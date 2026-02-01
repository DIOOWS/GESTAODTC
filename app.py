import os
import streamlit as st
from sqlalchemy import text

from db import get_engine, init_db
from ui import painel, produtos, lancamentos, relatorios, importar_excel, importar_whatsapp, estoque

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

# Login simples
APP_PASSWORD = os.getenv("APP_PASSWORD", "")
if APP_PASSWORD:
    pw = st.sidebar.text_input("Senha", type="password")
    if pw != APP_PASSWORD:
        st.sidebar.info("Digite a senha para acessar.")
        st.stop()

engine = get_engine()
init_db(engine)

def get_branch_id(name: str) -> int:
    with engine.begin() as conn:
        r = conn.execute(text("SELECT id FROM branches WHERE name=:n"), {"n": name.upper().strip()}).fetchone()
        return int(r[0])

def garantir_produto(conn, produto: str, categoria: str | None):
    # produto sem repetir categoria
    p = (produto or "").strip().upper()
    c = (categoria or "").strip().upper() or None

    conn.execute(text("""
        INSERT INTO products(name, category)
        VALUES (:n,:c)
        ON CONFLICT (name, COALESCE(category,'')) DO NOTHING;
    """), {"n": p, "c": c})

    r = conn.execute(text("""
        SELECT id FROM products
        WHERE name=:n AND COALESCE(category,'') = COALESCE(:c,'')
    """), {"n": p, "c": c or ""}).fetchone()

    return int(r[0])

# Sidebar
st.sidebar.title("🍞 Padaria")
page = st.sidebar.radio("Menu", [
    "Painel",
    "Produtos",
    "Estoque",
    "Lançamentos",
    "Relatórios",
    "Importar Excel",
    "Importar WhatsApp"
])

if page == "Painel":
    painel.render(st, engine, get_branch_id)
elif page == "Produtos":
    produtos.render(st, engine)
elif page == "Estoque":
    estoque.render(st, engine, garantir_produto, get_branch_id)
elif page == "Lançamentos":
    lancamentos.render(st, engine, garantir_produto, get_branch_id)
elif page == "Relatórios":
    relatorios.render(st, engine)
elif page == "Importar Excel":
    importar_excel.render(st, engine)
else:
    importar_whatsapp.render(st, engine, garantir_produto, get_branch_id)
