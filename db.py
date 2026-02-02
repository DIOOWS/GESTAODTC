import os
from sqlalchemy import create_engine, text

def get_engine():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL não definida (configure no Render).")
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

def init_db(engine):
    with engine.begin() as conn:
        # ----------------------------
        # 1) TABELAS BASE
        # ----------------------------
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS products (
          id SERIAL PRIMARY KEY,
          categoria TEXT NOT NULL,
          produto TEXT NOT NULL,
          ativo BOOLEAN NOT NULL DEFAULT TRUE
        );
        """))

        conn.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_products_cat_prod
        ON products (categoria, produto);
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS filiais (
          id SERIAL PRIMARY KEY,
          nome TEXT NOT NULL UNIQUE
        );
        """))

        # Seed filiais padrão
        conn.execute(text("INSERT INTO filiais(nome) VALUES ('AUSTIN') ON CONFLICT (nome) DO NOTHING;"))
        conn.execute(text("INSERT INTO filiais(nome) VALUES ('QUEIMADOS') ON CONFLICT (nome) DO NOTHING;"))

        # Movimentos (cria se não existir)
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS movimentos (
          id SERIAL PRIMARY KEY,
          data DATE NOT NULL,
          filial_id INT NOT NULL REFERENCES filiais(id) ON DELETE CASCADE,

          -- padrão novo:
          product_id INT REFERENCES products(id) ON DELETE CASCADE,

          estoque NUMERIC(12,2) DEFAULT 0,
          produzido_planejado NUMERIC(12,2) DEFAULT 0,
          produzido_real NUMERIC(12,2) DEFAULT 0,
          vendido NUMERIC(12,2) DEFAULT 0,
          desperdicio NUMERIC(12,2) DEFAULT 0,

          observacoes TEXT
        );
        """))

        # Transferências (se existir/usar depois)
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS transferencias (
          id SERIAL PRIMARY KEY,
          data DATE NOT NULL,
          de_filial_id INT NOT NULL REFERENCES filiais(id) ON DELETE CASCADE,
          para_filial_id INT NOT NULL REFERENCES filiais(id) ON DELETE CASCADE,

          -- padrão novo:
          product_id INT REFERENCES products(id) ON DELETE CASCADE,

          quantidade NUMERIC(12,2) NOT NULL DEFAULT 0,
          observacoes TEXT
        );
        """))

        # ----------------------------
        # 2) MIGRAÇÕES: padronizar data
        # ----------------------------
        # movimentos: dia/day -> data (se existir)
        if _col_exists(conn, "movimentos", "dia") and not _col_exists(conn, "movimentos", "data"):
            conn.execute(text('ALTER TABLE movimentos RENAME COLUMN dia TO data;'))
        if _col_exists(conn, "movimentos", "day") and not _col_exists(conn, "movimentos", "data"):
            conn.execute(text('ALTER TABLE movimentos RENAME COLUMN day TO data;'))

        # transferencias: dia/day -> data (se existir)
        if _col_exists(conn, "transferencias", "dia") and not _col_exists(conn, "transferencias", "data"):
            conn.execute(text('ALTER TABLE transferencias RENAME COLUMN dia TO data;'))
        if _col_exists(conn, "transferencias", "day") and not _col_exists(conn, "transferencias", "data"):
            conn.execute(text('ALTER TABLE transferencias RENAME COLUMN day TO data;'))

        # ----------------------------
        # 3) MIGRAÇÃO FORÇADA: produto_id -> product_id
        # (resolve seu erro atual)
        # ----------------------------

        # MOVIMENTOS
        if _col_exists(conn, "movimentos", "produto_id") and not _col_exists(conn, "movimentos", "product_id"):
            # cria product_id
            conn.execute(text("ALTER TABLE movimentos ADD COLUMN product_id INT;"))
            # copia valores
            conn.execute(text("UPDATE movimentos SET product_id = produto_id WHERE product_id IS NULL;"))
            # cria FK (se ainda não existir)
            conn.execute(text("""
            DO $$
            BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_schema='public'
                  AND table_name='movimentos'
                  AND constraint_name='fk_movimentos_product_id'
              ) THEN
                ALTER TABLE movimentos
                  ADD CONSTRAINT fk_movimentos_product_id
                  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;
              END IF;
            END $$;
            """))
            # remove coluna antiga
            conn.execute(text("ALTER TABLE movimentos DROP COLUMN produto_id;"))

        # TRANSFERENCIAS
        if _col_exists(conn, "transferencias", "produto_id") and not _col_exists(conn, "transferencias", "product_id"):
            conn.execute(text("ALTER TABLE transferencias ADD COLUMN product_id INT;"))
            conn.execute(text("UPDATE transferencias SET product_id = produto_id WHERE product_id IS NULL;"))
            conn.execute(text("""
            DO $$
            BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_schema='public'
                  AND table_name='transferencias'
                  AND constraint_name='fk_transferencias_product_id'
              ) THEN
                ALTER TABLE transferencias
                  ADD CONSTRAINT fk_transferencias_product_id
                  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;
              END IF;
            END $$;
            """))
            conn.execute(text("ALTER TABLE transferencias DROP COLUMN produto_id;"))

        # ----------------------------
        # 4) GARANTIR ÍNDICE ÚNICO pro UPSERT funcionar
        # ----------------------------
        conn.execute(text("""
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1
            FROM pg_indexes
            WHERE schemaname='public'
              AND indexname='ux_movimentos_data_filial_product'
          ) THEN
            CREATE UNIQUE INDEX ux_movimentos_data_filial_product
              ON movimentos (data, filial_id, product_id);
          END IF;
        END $$;
        """))
