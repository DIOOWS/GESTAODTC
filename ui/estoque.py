from datetime import date


def render(st, qdf, qexec, get_filial_id):
    st.header("Estoque (por dia e filial)")

    col1, col2 = st.columns(2)
    filial = col1.selectbox("Filial", ["AUSTIN", "QUEIMADOS"], index=0)
    d = col2.date_input("Data", value=date.today())
    filial_id = get_filial_id(filial)

    df = qdf("""
        WITH mov AS (
            SELECT *
            FROM movimentos
            WHERE filial_id = :f AND data = :d
        ),
        tin AS (
            SELECT product_id, COALESCE(SUM(quantidade),0) AS transf_in
            FROM transferencias
            WHERE para_filial_id = :f AND data = :d
            GROUP BY product_id
        ),
        tout AS (
            SELECT product_id, COALESCE(SUM(quantidade),0) AS transf_out
            FROM transferencias
            WHERE de_filial_id = :f AND data = :d
            GROUP BY product_id
        )
        SELECT
          p.id AS product_id,
          p.categoria,
          p.produto,
          COALESCE(m.estoque,0) AS estoque,
          COALESCE(m.produzido_planejado,0) AS produzido_planejado,
          COALESCE(m.produzido_real,0) AS produzido_real,
          COALESCE(m.vendido,0) AS vendido,
          COALESCE(m.desperdicio,0) AS desperdicio,
          COALESCE(ti.transf_in,0) AS transf_in,
          COALESCE(to2.transf_out,0) AS transf_out,
          (
            COALESCE(m.estoque,0)
            + COALESCE(m.produzido_planejado,0)
            + COALESCE(m.produzido_real,0)
            - COALESCE(m.vendido,0)
            - COALESCE(m.desperdicio,0)
            - COALESCE(to2.transf_out,0)
            + COALESCE(ti.transf_in,0)
          ) AS saldo_calculado
        FROM products p
        LEFT JOIN mov m ON m.product_id = p.id
        LEFT JOIN tin ti ON ti.product_id = p.id
        LEFT JOIN tout to2 ON to2.product_id = p.id
        WHERE p.ativo = TRUE
        ORDER BY p.categoria, p.produto;
    """, {"f": filial_id, "d": d})

    st.dataframe(df, width="stretch", hide_index=True)
    st.caption("Saldo calculado = estoque + produção (planejada+real) - venda - desperdício - transferências (saída) + transferências (entrada).")
