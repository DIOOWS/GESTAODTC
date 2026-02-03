from datetime import date
import io
import pandas as pd


def render(st, qdf):
    st.header("Relatórios")

    c1, c2, c3 = st.columns(3)
    d1 = c1.date_input("De", value=date.today().replace(day=1))
    d2 = c2.date_input("Até", value=date.today())
    filial = c3.selectbox("Filial (opcional)", ["TODAS", "AUSTIN", "QUEIMADOS"], index=0)

    params = {"d1": d1, "d2": d2}

    filtro = ""
    if filial != "TODAS":
        filtro = "AND f.nome = :filial"
        params["filial"] = filial

    df_mov = qdf(f"""
        SELECT m.dia, f.nome AS filial, p.categoria, p.produto,
               COALESCE(m.estoque,0) AS estoque,
               COALESCE(m.produzido_planejado,0) AS produzido_planejado,
               COALESCE(m.produzido_real,0) AS produzido_real,
               COALESCE(m.vendido,0) AS vendido,
               COALESCE(m.desperdicio,0) AS desperdicio,
               m.observacoes
        FROM movimentacoes m
        JOIN filiais f ON f.id = m.filial_id
        JOIN products p ON p.id = m.produto_id
        WHERE m.dia BETWEEN :d1 AND :d2
        {filtro}
        ORDER BY m.dia DESC, f.nome, p.categoria, p.produto;
    """, params)

    st.subheader("Movimentações")
    st.dataframe(df_mov, use_container_width=True, hide_index=True)

    st.subheader("Transferências")
    df_tr = qdf(f"""
        SELECT t.id, t.dia,
               f1.nome AS origem,
               f2.nome AS destino,
               p.categoria, p.produto,
               t.quantidade, t.observacoes
        FROM transferencias t
        JOIN filiais f1 ON f1.id = t.de_filial_id
        JOIN filiais f2 ON f2.id = t.para_filial_id
        JOIN products p ON p.id = t.produto_id
        WHERE t.dia BETWEEN :d1 AND :d2
        ORDER BY t.dia DESC, t.id DESC;
    """, {"d1": d1, "d2": d2})

    st.dataframe(df_tr, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Exportar Excel")

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_mov.to_excel(writer, index=False, sheet_name="Movimentacoes")
        df_tr.to_excel(writer, index=False, sheet_name="Transferencias")

    st.download_button(
        "Baixar Excel",
        data=buffer.getvalue(),
        file_name=f"relatorio_{d1}_a_{d2}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
