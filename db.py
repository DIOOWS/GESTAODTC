import os
from sqlalchemy import create_engine, text


def get_engine():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL não definida (configure no Render).")

    # Render às vezes fornece postgres://
    url = url.replace("postgres://", "postgresql://", 1)
    return create_engine(url, pool_pre_ping=True)


def init_db(engine):
    with engine.begin() as conn:
        # Produtos (categoria + produto/sabor)
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

        # Filiais
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS filiais (
          id SERIAL PRIMARY KEY,
          nome TEXT NOT NULL UNIQUE
        );
        """))

        # Movimentações (controle diário por filial e produto)
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
          id SERIAL PRIMARY KEY,
          dia DATE NOT NULL,
          filial_id INT NOT NULL REFERENCES filiais(id) ON DELETE CASCADE,
          produto_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,

          estoque NUMERIC(12,2) DEFAULT 0,
          produzido_planejado NUMERIC(12,2) DEFAULT 0,
          produzido_real NUMERIC(12,2) DEFAULT 0,
          vendido NUMERIC(12,2) DEFAULT 0,
          desperdicio NUMERIC(12,2) DEFAULT 0,

          observacoes TEXT,
          UNIQUE (dia, filial_id, produto_id)
        );
        """))

        # Transferências (Austin -> Queimados, e também o inverso se ocorrer)
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS transferencias (
          id SERIAL PRIMARY KEY,
          dia DATE NOT NULL,
          de_filial_id INT NOT NULL REFERENCES filiais(id) ON DELETE CASCADE,
          para_filial_id INT NOT NULL REFERENCES filiais(id) ON DELETE CASCADE,
          produto_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
          quantidade NUMERIC(12,2) NOT NULL DEFAULT 0,
          observacoes TEXT
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
