import os
from sqlalchemy import create_engine, text

def get_engine():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL não definida (configure no Render).")
    # Render às vezes entrega postgres://
    url = url.replace("postgres://", "postgresql://", 1)
    return create_engine(url, pool_pre_ping=True)

def _col_exists(conn, table, col):
    r = conn.execute(text("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name=:t AND column_name=:c
        LIMIT 1;
    """), {"t": table, "c": col}).fetchone()
    return r is not None

def _table_exists(conn, table):
    r = conn.execute(text("""
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema='public' AND table_name=:t
        LIMIT 1;
    """), {"t": table}).fetchone()
    return r is not None

def _rename_col_if_exists(conn, table, old, new):
    if _table_exists(conn, table) and _col_exists(conn, table, old) and not _col_exists(conn, table, new):
        conn.execute(text(f'ALTER TABLE "{table}" RENAME COLUMN "{old}" TO "{new}";'))

def init_db(engine):
    with engine.begin() as conn:
        # --- Produtos ---
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS products (
          id SERIAL PRIMARY KEY,
          categoria TEXT NOT NULL,
          produto TEXT NOT NULL,
          ativo BOOLEAN NOT NULL DEFAULT TRUE
        );
        """))

        # índice único pra evitar duplicar produto na mesma categoria
        conn.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_products_cat_prod
        ON products (categoria, produto);
        """))

        # --- Filiais ---
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS filiais (
          id SERIAL PRIMARY KEY,
          nome TEXT NOT NULL UNIQUE
        );
        """))

        # --- Movimentos ---
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS movimentos (
          id SERIAL PRIMARY KEY,
          data DATE NOT NULL,
          filial_id INT NOT NULL REFERENCES filiais(id) ON DELETE CASCADE,
          product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,

          estoque NUMERIC(12,2) DEFAULT 0,
          produzido_planejado NUMERIC(12,2) DEFAULT 0,
          produzido_real NUMERIC(12,2) DEFAULT 0,
          enviado NUMERIC(12,2) DEFAULT 0,
          vendido NUMERIC(12,2) DEFAULT 0,
          desperdicio NUMERIC(12,2) DEFAULT 0,

          observacoes TEXT,
          UNIQUE (data, filial_id, product_id)
        );
        """))

        # Seed filiais padrão
        conn.execute(text("""
        INSERT INTO filiais(nome) VALUES ('AUSTIN')
        ON CONFLICT (nome) DO NOTHING;
        """))
        conn.execute(text("""
        INSERT INTO filiais(nome) VALUES ('QUEIMADOS')
        ON CONFLICT (nome) DO NOTHING;
        """))

        # --- Migração: padronizar coluna data (se existir 'day' ou 'dia') ---
        _rename_col_if_exists(conn, "movimentos", "day", "data")
        _rename_col_if_exists(conn, "movimentos", "dia", "data")
