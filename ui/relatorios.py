from datetime import date, timedelta


def render(st, qdf, get_filial_id):
    st.header("Relatórios")

    col1, col2, col3 = st.columns(3)
    d2 = col2.date_input("Até", value=date.today())
    d1 = col1.date_input("De", value=d2 - timedelta(days=7))
    filial = col3.selectbox("Filial (opcional)", ["TODAS", "AUSTIN", "QUEIMADOS"], index=0)

    filtro_filial = ""
    params = {"d1": d1, "d2": d2}
    if filial != "TODAS":
        filtro_filial = " AND m.filial_id = :f "
        params["f"] = get_filial_id(filial)

    df = qdf(f"""
        WITH tin AS (
            SELECT data, para_filial_id AS filial_id, product_id, COALESCE(SUM(quantidade),0) AS transf_in
            FROM transferencias
            WHERE data BETWEEN :d1 AND :d2
            GROUP BY data, para_filial_id, product_id
        ),
        tout AS (
            SELECT data, de_filial_id AS filial_id, product_id, COALESCE(SUM(quantidade),0) AS transf_out
            FROM transferencias
            WHERE data BETWEEN :d1 AND :d2
            GROUP BY data, de_filial_id, product_id
        )
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
          ) AS saldo_calculado,
          m.observacoes
        FROM movimentos m
        JOIN filiais f ON f.id = m.filial_id
        JOIN products p ON p.id = m.product_id
        LEFT JOIN tin ti ON ti.data = m.data AND ti.filial_id = m.filial_id AND ti.product_id = m.product_id
        LEFT JOIN tout to2 ON to2.data = m.data AND to2.filial_id = m.filial_id AND to2.product_id = m.product_id
        WHERE m.data BETWEEN :d1 AND :d2
        {filtro_filial}
        ORDER BY m.data DESC, f.nome, p.categoria, p.produto;
    """, params)

    st.dataframe(df, width="stretch", hide_index=True)

    st.dataframe(df, width="stretch", hide_index=True)

    # --- Export CSV (Excel PT-BR) ---
    csv = df.to_csv(
        sep=";",              # Excel PT-BR abre em colunas
        index=False,
        encoding="utf-8-sig", # mantém acentos no Excel
        decimal=","           # opcional (números com vírgula)
    )

    st.download_button(
        "⬇️ Baixar CSV (Excel)",
        data=csv,
        file_name=f"relatorio_{d1}_{d2}.csv",
        mime="text/csv"
    )

    st.dataframe(df, width="stretch", hide_index=True)

    # ---------- EXPORTAR EXCEL ----------
    df = qdf(""" 
       ... query grande ...
    """, params)

    st.dataframe(df, width="stretch", hide_index=True)

    # 👇 SÓ ISSO AQUI É NOVO
    if not df.empty:
        from io import BytesIO
        import pandas as pd

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Relatório", index=False)

        st.download_button(
            label="⬇️ Baixar Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name=f"relatorio_{d1}_{d2}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )



