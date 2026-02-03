from datetime import date

def render(st, qdf, qexec, get_filial_id):
    st.header("Estoque")

    col1, col2 = st.columns(2)
    filial = col1.selectbox("Filial", ["AUSTIN", "QUEIMADOS"], index=0)
    d = col2.date_input("Data", value=date.today())

    filial_id = get_filial_id(filial)

    df = qdf("""
        SELECT
          p.id AS product_id,
          p.categoria,
          p.produto,
          COALESCE(m.estoque,0) AS estoque,
          COALESCE(m.produzido_planejado,0) AS produzido_planejado,
          COALESCE(m.produzido_real,0) AS produzido_real,
          COALESCE(m.vendido,0) AS vendido,
          COALESCE(m.desperdicio,0) AS desperdicio
        FROM products p
        LEFT JOIN movimentos m
          ON m.product_id = p.id
         AND m.filial_id = :f
         AND m.data = :d
        WHERE p.ativo = TRUE
        ORDER BY p.categoria, p.produto;
    """, {"f": filial_id, "d": d})

    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption("Esse é o estoque do dia/filial selecionados (vem dos movimentos).")
