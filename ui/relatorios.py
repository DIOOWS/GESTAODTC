from datetime import date, timedelta


def render(st, qdf):
    st.header("Relatórios")

    col1, col2 = st.columns(2)
    d1 = col1.date_input("De", value=date.today().replace(day=1))
    d2 = col2.date_input("Até", value=date.today())

    filial = st.selectbox("Filial (opcional)", ["(TODAS)", "AUSTIN", "QUEIMADOS"], index=0)

    params = {"d1": d1, "d2": d2}
    filtro_filial = ""
    if filial != "(TODAS)":
        filtro_filial = " AND f.nome = :filial "
        params["filial"] = filial

    df = qdf("""
    SELECT
        m.data,
        f.nome AS filial,
        p.categoria,
        p.produto,
        m.estoque,
        m.produzido_planejado,
        m.produzido_real,
        m.vendido,
        m.desperdicio,
        m.observacoes
    FROM movimentos m
    JOIN filiais f ON f.id = m.filial_id
    JOIN products p ON p.id = m.product_id
    WHERE m.data BETWEEN :d1 AND :d2
    ORDER BY m.data DESC, f.nome, p.categoria, p.produto;
    """, {"d1": d1, "d2": d2})

    st.dataframe(df, use_container_width=True, hide_index=True)
