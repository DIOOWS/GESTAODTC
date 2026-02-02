from sqlalchemy import text

from db import _rename_col_if_exists


def init_db(engine):
    with engine.begin() as conn:

        # --- Tabelas base ---
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
            filial_id INT NOT NULL REFERENCES filiais(id),
            product_id INT NOT NULL REFERENCES products(id),

            estoque NUMERIC(12,2) DEFAULT 0,
            produzido_planejado NUMERIC(12,2) DEFAULT 0,
            produzido_real NUMERIC(12,2) DEFAULT 0,
            vendido NUMERIC(12,2) DEFAULT 0,
            desperdicio NUMERIC(12,2) DEFAULT 0,

            observacoes TEXT,
            UNIQUE (data, filial_id, product_id)
        );
        """))

        # --- MIGRAÇÕES AUTOMÁTICAS ---
        # dia/day -> data
        for old in ("dia", "day"):
            conn.execute(text(f"""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='movimentos' AND column_name='{old}'
                    ) THEN
                        ALTER TABLE movimentos RENAME COLUMN "{old}" TO data;
                    END IF;
                END$$;
            """))

        # produto_id -> product_id
        conn.execute(text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='movimentos' AND column_name='produto_id'
            ) THEN
                ALTER TABLE movimentos RENAME COLUMN produto_id TO product_id;
            END IF;
        END$$;
        """))

        # Seed filiais
        conn.execute(text("""
        INSERT INTO filiais(nome) VALUES ('AUSTIN'), ('QUEIMADOS')
        ON CONFLICT DO NOTHING;
        """))

        # movimentos: padronizar produto_id
        _rename_col_if_exists(conn, "movimentos", "product_id", "produto_id")

        # transferencias: padronizar produto_id (se existir)
        _rename_col_if_exists(conn, "transferencias", "product_id", "produto_id")

