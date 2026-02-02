import os
from sqlalchemy import create_engine, text

def get_engine():
    url = (os.getenv("DATABASE_URL") or "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL não definida (configure no Render).")
    url = url.replace("postgres://", "postgresql://", 1)
    return create_engine(url, pool_pre_ping=True)

def init_db(engine):
    """
    RECRIA o schema (apaga tabelas antigas).
    Padronização:
      - data (DATE)
      - filiais(id,nome)
      - products(id,categoria,produto,ativo)
      - movimentos(id,data,filial_id,produto_id,estoque,produzido_planejado,produzido_real,vendido,desperdicio,observacoes)
    """
    with engine.begin() as conn:
        # --- DROPS (como você aceitou perder dados) ---
        conn.execute(text("DROP TABLE IF EXISTS transferencias CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS movimentacoes CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS movimentos CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS produtos CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS categorias CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS products CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS filiais CASCADE;"))

        # --- CREATE ---
        conn.execute(text("""
        CREATE TABLE filiais (
          id SERIAL PRIMARY KEY,
          nome TEXT NOT NULL UNIQUE
        );
        """))

        conn.execute(text("""
        CREATE TABLE products (
          id SERIAL PRIMARY KEY,
          categoria TEXT NOT NULL,
          produto TEXT NOT NULL,
          ativo BOOLEAN NOT NULL DEFAULT TRUE
        );
        """))

        conn.execute(text("""
        CREATE UNIQUE INDEX ux_products_categoria_produto
        ON products (categoria, produto);
        """))

        conn.execute(text("""
        CREATE TABLE movimentos (
          id SERIAL PRIMARY KEY,
          data DATE NOT NULL,
          filial_id INT NOT NULL REFERENCES filiais(id) ON DELETE CASCADE,
          produto_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,

          estoque INT NOT NULL DEFAULT 0,
          produzido_planejado INT NOT NULL DEFAULT 0,
          produzido_real INT NOT NULL DEFAULT 0,
          vendido INT NOT NULL DEFAULT 0,
          desperdicio INT NOT NULL DEFAULT 0,

          observacoes TEXT,
          UNIQUE (data, filial_id, produto_id)
        );
        """))

        # Seeds de filiais
        conn.execute(text("INSERT INTO filiais(nome) VALUES ('AUSTIN') ON CONFLICT (nome) DO NOTHING;"))
        conn.execute(text("INSERT INTO filiais(nome) VALUES ('QUEIMADOS') ON CONFLICT (nome) DO NOTHING;"))
