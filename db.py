import os
from sqlalchemy import create_engine, text


def get_engine():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL não definida. Configure a variável de ambiente DATABASE_URL.")
    url = url.replace("postgres://", "postgresql://", 1)
    return create_engine(url, pool_pre_ping=True)


def init_db(engine):
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS produtos (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL UNIQUE,
            categoria TEXT,
            ativo BOOLEAN NOT NULL DEFAULT TRUE
        );
        """))

        # Internamente é "locais", mas na UI chamamos de "filiais"
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS locais (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL UNIQUE
        );
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS registros_diarios (
            id SERIAL PRIMARY KEY,
            data DATE NOT NULL,
            produto_id INT NOT NULL REFERENCES produtos(id) ON DELETE CASCADE,
            local_id   INT NOT NULL REFERENCES locais(id)   ON DELETE CASCADE,

            estoque NUMERIC(12,2),
            produzido NUMERIC(12,2),
            vendido NUMERIC(12,2),
            desperdicio NUMERIC(12,2),
            total NUMERIC(12,2),

            produzido_planejado NUMERIC(12,2),
            observacoes TEXT,

            UNIQUE (data, produto_id, local_id)
        );
        """))

        conn.execute(text("""
        ALTER TABLE registros_diarios
        ADD COLUMN IF NOT EXISTS produzido_planejado NUMERIC(12,2);
        """))

        # Transferências (Envio origem -> destino)
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS transferencias (
            id SERIAL PRIMARY KEY,
            data DATE NOT NULL,
            produto_id INT NOT NULL REFERENCES produtos(id) ON DELETE CASCADE,
            origem_local_id INT NOT NULL REFERENCES locais(id) ON DELETE CASCADE,
            destino_local_id INT NOT NULL REFERENCES locais(id) ON DELETE CASCADE,
            quantidade NUMERIC(12,2) NOT NULL,
            observacoes TEXT,
            UNIQUE (data, produto_id, origem_local_id, destino_local_id)
        );
        """))

        # Filiais fixas (você não cadastra nada)
        conn.execute(text("INSERT INTO locais(nome) VALUES ('AUSTIN') ON CONFLICT (nome) DO NOTHING;"))
        conn.execute(text("INSERT INTO locais(nome) VALUES ('QUEIMADOS') ON CONFLICT (nome) DO NOTHING;"))
