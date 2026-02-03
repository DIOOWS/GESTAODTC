import os
from sqlalchemy import create_engine, text


def get_engine():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL não definida (configure no Render).")
    # Render às vezes entrega postgres://
    url = url.replace("postgres://", "postgresql://", 1)
    return create_engine(url, pool_pre_ping=True)


def _table_exists(conn, table: str) -> bool:
    r = conn.execute(text("""
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema='public' AND table_name=:t
        LIMIT 1;
    """), {"t": table}).fetchone()
    return r is not None


def _col_exists(conn, table: str, col: str) -> bool:
    r = conn.execute(text("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name=:t AND column_name=:c
        LIMIT 1;
    """), {"t": table, "c": col}).fetchone()
    return r is not None


def _rename_table_if_exists(conn, old: str, new: str):
    if _table_exists(conn, old) and not _table_exists(conn, new):
        conn.execute(text(f'ALTER TABLE "{old}" RENAME TO "{new}";'))


def _rename_col_if_exists(conn, table: str, old: str, new: str):
    if _table_exists(conn, table) and _col_exists(conn, table, old) and not _col_exists(conn, table, new):
        conn.execute(text(f'ALTER TABLE "{table}" RENAME COLUMN "{old}" TO "{new}";'))


def init_db(engine):
    with engine.begin() as conn:
        # --- Migração (se você já tinha o esquema antigo) ---
        # movimentacoes -> movimentos
        _rename_table_if_exists(conn, "movimentacoes", "movimentos")
        _rename_col_if_exists(conn, "movimentos", "dia", "data")
        _rename_col_if_exists(conn, "movimentos", "day", "data")
        _rename_col_if_exists(conn, "movimentos", "produto_id", "product_id")

        # produtos -> products
        _rename_table_if_exists(conn, "produtos", "products")
        # Se products antigo tinha "nome", tenta renomear para "produto"
        _rename_col_if_exists(conn, "products", "nome", "produto")
        # Se tinha categoria_id, você provavelmente resetou o banco — aqui não dá pra migrar com segurança.
        # O caminho certo é rodar reset_db em produção (se for ok perder os dados de teste).

        # transferencias: padroniza data + product_id
        _rename_col_if_exists(conn, "transferencias", "dia", "data")
        _rename_col_if_exists(conn, "transferencias", "day", "data")
        _rename_col_if_exists(conn, "transferencias", "produto_id", "product_id")

        # --- Tabelas base (novo padrão) ---
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS filiais (
          id SERIAL PRIMARY KEY,
          nome TEXT NOT NULL UNIQUE
        );
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS products (
          id SERIAL PRIMARY KEY,
          categoria TEXT NOT NULL,
          produto TEXT NOT NULL,
          ativo BOOLEAN NOT NULL DEFAULT TRUE,
          UNIQUE (categoria, produto)
        );
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS movimentos (
          id SERIAL PRIMARY KEY,
          data DATE NOT NULL,
          filial_id INT NOT NULL REFERENCES filiais(id) ON DELETE CASCADE,
          product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,

          estoque INTEGER NOT NULL DEFAULT 0,
          produzido_planejado INTEGER NOT NULL DEFAULT 0,
          produzido_real INTEGER NOT NULL DEFAULT 0,
          vendido INTEGER NOT NULL DEFAULT 0,
          desperdicio INTEGER NOT NULL DEFAULT 0,

          observacoes TEXT,
          UNIQUE (data, filial_id, product_id)
        );
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS transferencias (
          id SERIAL PRIMARY KEY,
          data DATE NOT NULL,
          de_filial_id INT NOT NULL REFERENCES filiais(id) ON DELETE CASCADE,
          para_filial_id INT NOT NULL REFERENCES filiais(id) ON DELETE CASCADE,
          product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
          quantidade INTEGER NOT NULL DEFAULT 0,
          observacoes TEXT
        );
        """))

        # Seeds
        conn.execute(text("""
        INSERT INTO filiais(nome) VALUES ('AUSTIN')
        ON CONFLICT (nome) DO NOTHING;
        """))
        conn.execute(text("""
        INSERT INTO filiais(nome) VALUES ('QUEIMADOS')
        ON CONFLICT (nome) DO NOTHING;
        """))


def reset_db(engine):
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS transferencias;"))
        conn.execute(text("DROP TABLE IF EXISTS movimentos;"))
        conn.execute(text("DROP TABLE IF EXISTS products;"))
        conn.execute(text("DROP TABLE IF EXISTS filiais;"))
    init_db(engine)
