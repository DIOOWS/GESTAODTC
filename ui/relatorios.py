import pandas as pd
from sqlalchemy import text
from datetime import date
import io

def render(st, engine):
    st.header("Relatórios")

    c1, c2 = st.columns(2)
    with c1:
        d1 = st.date_input("De", value=date.today().replace(day=1))
    with c2:
        d2 = st.date_input("Até", value=date.today())

    with engine.begin() as conn:
        df = pd.read_sql(text("""
            SELECT
              r.day AS data,
              b.name AS filial,
              COALESCE(p.category,'') AS categoria,
              p.name AS produto,
              COALESCE(r.stock_qty,0) AS estoque,
              COALESCE(r.produced_planned,0) AS produzido_planejado,
              COALESCE(r.produced_real,0) AS produzido_real,
              COALESCE(r.sold_qty,0) AS vendido,
              COALESCE(r.waste_qty,0) AS desperdicio,
              COALESCE(r.notes,'') AS obs
            FROM daily_records r
            JOIN products p ON p.id = r.product_id
            JOIN branches b ON b.id = r.branch_id
            WHERE r.day BETWEEN :d1 AND :d2
            ORDER BY r.day DESC, b.name, p.category NULLS LAST, p.name;
        """), conn, params={"d1": d1, "d2": d2})

    st.dataframe(df, use_container_width=True, hide_index=True)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Relatorio")

    st.download_button(
        "Baixar Excel",
        data=buffer.getvalue(),
        file_name=f"relatorio_{d1}_a_{d2}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
