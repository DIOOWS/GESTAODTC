from sqlalchemy import text
from db import get_engine, init_db

def reset_all():
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS transfers;"))
        conn.execute(text("DROP TABLE IF EXISTS daily_records;"))
        conn.execute(text("DROP TABLE IF EXISTS products;"))
        conn.execute(text("DROP TABLE IF EXISTS branches;"))
    init_db(engine)
    print("OK: banco resetado e tabelas recriadas.")

if __name__ == "__main__":
    reset_all()
