from db import get_engine, reset_db

if __name__ == "__main__":
    engine = get_engine()
    reset_db(engine)
    print("OK: banco resetado e tabelas recriadas.")
