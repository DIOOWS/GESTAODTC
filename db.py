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
    r = conn.execute(
        text(
            """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name=:t AND column_name=:c
        LIMIT 1;
    """
        ),
        {"t": table, "c": col},
    ).fetchone()
    return r is not None


def _rename_col_if_exists(conn, table, old, new):
    if _col_exists(conn, table, old) and not _col_exists(conn, table, new):
        conn.execute(text(f'ALTER TABLE "{table}" RENAME COLUMN "{old}" TO "{new}";'))


def init_db(engine):
    with engine.begin() as conn:
        # --- Tabelas base ---
        conn.execute(
            text(
                """
        CREATE TABLE IF NOT EXISTS products (
          id SERIAL PRIMARY KEY,
          categoria TEXT NOT NULL,
          produto TEXT NOT NULL,
          ativo BOOLEAN NOT NULL DEFAULT TRUE
        );
        """
            )
        )

        # único por categoria+produto
        conn.execute(
            text(
                """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_products_cat_prod
        ON products (categoria, produto);
        """
            )
        )

        conn.execute(
            text(
                """
        CREATE TABLE IF NOT EXISTS filiais (
          id SERIAL PRIMARY KEY,
          nome TEXT NOT NULL UNIQUE
        );
        """
            )
        )

        # Movimentos (registro diário por filial + produto)
        conn.execute(
            text(
                """
        CREATE TABLE IF NOT EXISTS movimentos (
          id SERIAL PRIMARY KEY,
          data DATE NOT NULL,
          filial_id INT NOT NULL REFERENCES filiais(id) ON DELETE CASCADE,
          product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,

          estoque NUMERIC(12,2) DEFAULT 0,
          produzido_planejado NUMERIC(12,2) DEFAULT 0,
          produzido_real NUMERIC(12,2) DEFAULT 0,
          vendido NUMERIC(12,2) DEFAULT 0,
          desperdicio NUMERIC(12,2) DEFAULT 0,

          observacoes TEXT,
          UNIQUE (data, filial_id, product_id)
        );
        """
            )
        )

        # --- Seeds ---
        conn.execute(
            text(
                "INSERT INTO filiais(nome) VALUES ('AUSTIN') ON CONFLICT (nome) DO NOTHING;"
            )
        )
        conn.execute(
            text(
                "INSERT INTO filiais(nome) VALUES ('QUEIMADOS') ON CONFLICT (nome) DO NOTHING;"
            )
        )

        # --- MIGRAÇÕES IMPORTANTES (corrige seu banco antigo) ---
        # data: dia/day -> data
        _rename_col_if_exists(conn, "movimentos", "day", "data")
        _rename_col_if_exists(conn, "movimentos", "dia", "data")

        # produto_id -> product_id (era o seu erro principal!)
        _rename_col_if_exists(conn, "movimentos", "produto_id", "product_id")

        # (se você tiver outras tabelas antigas, me fala o nome que eu incluo aqui)
