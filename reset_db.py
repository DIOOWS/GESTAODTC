from db import get_engine, init_db
from sqlalchemy import text


def reset_db():
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS transferencias CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS movimentacoes CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS products CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS filiais CASCADE;"))
    init_db(engine)
    print("OK: banco resetado e tabelas recriadas.")


if __name__ == "__main__":
    reset_db()
