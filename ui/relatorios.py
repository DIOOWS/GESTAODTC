from datetime import date, timedelta

def render(st, qdf):
    st.header("Relatórios")

    col1, col2 = st.columns(2)
    d2 = col2.date_input("Até", value=date.today())
    d1 = col1.date_input("De", value=d2 - timedelta(days=7))

    df = qdf("""
        SELECT
          m.data,
          f.nome AS filial,
          p.categoria,
          p.produto,
          COALESCE(m.estoque,0) AS estoque,
          COALESCE(m.produzido_planejado,0) AS produzido_planejado,
          COALESCE(m.produzido_real,0) AS produzido_real,
          COALESCE(m.vendido,0) AS vendido,
          COALESCE(m.desperdicio,0) AS desperdicio,
          m.observacoes
        FROM movimentos m
        JOIN filiais f ON f.id = m.filial_id
        JOIN products p ON p.id = m.product_id
        WHERE m.data BETWEEN :d1 AND :d2
        ORDER BY m.data DESC, f.nome, p.categoria, p.produto;
    """, {"d1": d1, "d2": d2})

    st.dataframe(df, use_container_width=True, hide_index=True)
