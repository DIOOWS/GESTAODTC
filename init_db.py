from sqlalchemy import text

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
            enviado NUMERIC(12,2),
            vendido NUMERIC(12,2),
            desperdicio NUMERIC(12,2),
            observacoes TEXT,

            UNIQUE (data, produto_id, local_id)
        );
        """))
