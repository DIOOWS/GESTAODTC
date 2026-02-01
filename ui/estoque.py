import pandas as pd
from sqlalchemy import text
from datetime import date

def render(st, engine, garantir_produto, get_branch_id):
    st.header("Estoque (editável)")

    branch = st.selectbox("Filial", ["AUSTIN", "QUEIMADOS"])
    branch_id = get_branch_id(branch)

    day = st.date_input("Data", value=date.today())

    with engine.begin() as conn:
        df = pd.read_sql(text("""
            SELECT
              p.id AS product_id,
              COALESCE(p.category,'') AS categoria,
              p.name AS produto,
              COALESCE(r.stock_qty,0) AS estoque
            FROM products p
            LEFT JOIN daily_records r
              ON r.product_id = p.id
             AND r.branch_id = :bid
             AND r.day = :day
            WHERE p.active = TRUE
            ORDER BY p.category NULLS LAST, p.name;
        """), conn, params={"bid": branch_id, "day": day})

    st.caption("Edite o estoque e clique em **Salvar estoque**. Isso corrige qualquer erro de contagem/importação.")
    edited = st.data_editor(
        df[["categoria","produto","estoque"]],
        use_container_width=True,
        hide_index=True,
        num_rows="fixed"
    )

    if st.button("Salvar estoque"):
        with engine.begin() as conn:
            for _, row in edited.iterrows():
                produto = str(row["produto"]).strip().upper()
                categoria = str(row["categoria"]).strip().upper() or None
                pid = garantir_produto(conn, produto, categoria)

                conn.execute(text("""
                    INSERT INTO daily_records(day, branch_id, product_id, stock_qty)
                    VALUES (:day,:bid,:pid,:stock)
                    ON CONFLICT (day, branch_id, product_id)
                    DO UPDATE SET stock_qty = EXCLUDED.stock_qty;
                """), {"day": day, "bid": branch_id, "pid": pid, "stock": float(row["estoque"] or 0)})

        st.success("Estoque salvo!")
        st.rerun()
