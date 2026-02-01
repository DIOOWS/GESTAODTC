import pandas as pd
from sqlalchemy import text
from datetime import date, timedelta

def render(st, engine, get_branch_id):
    st.header("Painel")

    today = date.today()
    start_week = today - timedelta(days=today.weekday())
    start_month = today.replace(day=1)

    def agg(d1, d2):
        with engine.begin() as conn:
            df = pd.read_sql(text("""
                SELECT
                  SUM(COALESCE(sold_qty,0)) as sold,
                  SUM(COALESCE(produced_real,0)) as produced_real,
                  SUM(COALESCE(produced_planned,0)) as produced_planned,
                  SUM(COALESCE(waste_qty,0)) as waste
                FROM daily_records
                WHERE day BETWEEN :d1 AND :d2;
            """), conn, params={"d1": d1, "d2": d2})
        return df.iloc[0].to_dict()

    day = agg(today, today)
    week = agg(start_week, today)
    month = agg(start_month, today)

    st.subheader("Hoje")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Vendido", float(day["sold"] or 0))
    c2.metric("Produção real", float(day["produced_real"] or 0))
    c3.metric("Produção planejada", float(day["produced_planned"] or 0))
    c4.metric("Desperdício", float(day["waste"] or 0))

    st.subheader("Semana")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Vendido", float(week["sold"] or 0))
    c2.metric("Produção real", float(week["produced_real"] or 0))
    c3.metric("Produção planejada", float(week["produced_planned"] or 0))
    c4.metric("Desperdício", float(week["waste"] or 0))

    st.subheader("Mês")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Vendido", float(month["sold"] or 0))
    c2.metric("Produção real", float(month["produced_real"] or 0))
    c3.metric("Produção planejada", float(month["produced_planned"] or 0))
    c4.metric("Desperdício", float(month["waste"] or 0))

    st.caption("O estoque editável fica na aba **Estoque**.")
