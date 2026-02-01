from sqlalchemy import text
from db import get_engine, init_db

engine = get_engine()

with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS transferencias CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS registros_diarios CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS produtos CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS locais CASCADE;"))

init_db(engine)
print("OK: banco resetado e tabelas recriadas.")
