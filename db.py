import os
from sqlalchemy import create_engine, text

def get_engine():
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL não definida (adicione no Render / ambiente).")

    # Render às vezes usa postgres://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    # Se for URL do Render sem sslmode, adiciona (bom pra produção)
    if "sslmode=" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}sslmode=require"

    return create_engine(url, pool_pre_ping=True)

def init_db(engine):
    with engine.begin() as conn:
        # Filiais fixas (AUSTIN e QUEIMADOS)
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS filiais (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL UNIQUE
        );
        """))

        # Categorias (ex: BOLO RETANGULAR, BOLOS CASEIROS, ASSADOS, etc.)
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS categorias (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL UNIQUE
        );
        """))

        # Produtos (produto = nome/sabor; categoria separada)
        # CORREÇÃO: nada de COALESCE dentro do UNIQUE
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS produtos (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            categoria_id INTEGER REFERENCES categorias(id) ON DELETE SET NULL,
            ativo BOOLEAN NOT NULL DEFAULT TRUE,
            UNIQUE (categoria_id, nome)
        );
        """))

        # Movimentação diária por filial e produto
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS movimentos (
            id SERIAL PRIMARY KEY,
            dia DATE NOT NULL,
            filial_id INTEGER NOT NULL REFERENCES filiais(id) ON DELETE CASCADE,
            produto_id INTEGER NOT NULL REFERENCES produtos(id) ON DELETE CASCADE,

            estoque NUMERIC(12,2) DEFAULT 0,
            produzido_real NUMERIC(12,2) DEFAULT 0,
            produzido_planejado NUMERIC(12,2) DEFAULT 0,
            enviado NUMERIC(12,2) DEFAULT 0,
            vendido NUMERIC(12,2) DEFAULT 0,
            desperdicio NUMERIC(12,2) DEFAULT 0,
            observacoes TEXT,

            UNIQUE (dia, filial_id, produto_id)
        );
        """))

        # Transferências entre filiais (AUSTIN -> QUEIMADOS e vice-versa)
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS transferencias (
            id SERIAL PRIMARY KEY,
            dia DATE NOT NULL,
            produto_id INTEGER NOT NULL REFERENCES produtos(id) ON DELETE CASCADE,
            de_filial_id INTEGER NOT NULL REFERENCES filiais(id) ON DELETE CASCADE,
            para_filial_id INTEGER NOT NULL REFERENCES filiais(id) ON DELETE CASCADE,
            quantidade NUMERIC(12,2) NOT NULL DEFAULT 0,
            observacoes TEXT
        );
        """))

        # Seed de filiais se não existir
        conn.execute(text("""
        INSERT INTO filiais(nome) VALUES ('AUSTIN') ON CONFLICT (nome) DO NOTHING;
        """))
        conn.execute(text("""
        INSERT INTO filiais(nome) VALUES ('QUEIMADOS') ON CONFLICT (nome) DO NOTHING;
        """))

def reset_db(engine):
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS transferencias;"))
        conn.execute(text("DROP TABLE IF EXISTS movimentos;"))
        conn.execute(text("DROP TABLE IF EXISTS produtos;"))
        conn.execute(text("DROP TABLE IF EXISTS categorias;"))
        conn.execute(text("DROP TABLE IF EXISTS filiais;"))
    init_db(engine)
