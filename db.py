import os
from sqlalchemy import create_engine, text

def get_engine():
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL não definida nas variáveis de ambiente.")
    url = url.replace("postgres://", "postgresql://", 1)
    return create_engine(url, pool_pre_ping=True)

def init_db(engine):
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS branches (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        );
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            active BOOLEAN NOT NULL DEFAULT TRUE,
            UNIQUE (name, COALESCE(category,''))
        );
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS daily_records (
            id SERIAL PRIMARY KEY,
            day DATE NOT NULL,
            branch_id INT NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
            product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,

            stock_qty NUMERIC(12,2) DEFAULT 0,
            produced_planned NUMERIC(12,2) DEFAULT 0,
            produced_real NUMERIC(12,2) DEFAULT 0,
            sold_qty NUMERIC(12,2) DEFAULT 0,
            waste_qty NUMERIC(12,2) DEFAULT 0,

            notes TEXT,
            UNIQUE (day, branch_id, product_id)
        );
        """))

        # (opcional, pra depois) transferências entre filiais
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS transfers (
            id SERIAL PRIMARY KEY,
            day DATE NOT NULL,
            from_branch_id INT NOT NULL REFERENCES branches(id),
            to_branch_id INT NOT NULL REFERENCES branches(id),
            product_id INT NOT NULL REFERENCES products(id),
            qty NUMERIC(12,2) NOT NULL DEFAULT 0,
            notes TEXT
        );
        """))

        # seed branches
        conn.execute(text("INSERT INTO branches(name) VALUES ('AUSTIN') ON CONFLICT(name) DO NOTHING;"))
        conn.execute(text("INSERT INTO branches(name) VALUES ('QUEIMADOS') ON CONFLICT(name) DO NOTHING;"))
