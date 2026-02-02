from db import get_engine
from sqlalchemy import text

engine = get_engine()

with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS movimentos CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS products CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS filiais CASCADE;"))

print("Banco resetado.")
