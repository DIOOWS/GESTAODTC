from datetime import date
import io
import pandas as pd

def render(st, qdf):
    st.header("Relatórios")

    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        d1 = st.date_input("De", value=date.today().replace(day=1))
    with c2:
        d2 = st.date_input("Até", value=date.today())
    with c3:
        filial = st.selectbox("Filial (filtro)", ["TODAS", "AUSTIN", "QUEIMADOS"])

    params = {"d1": d1, "d2": d2}
    filtro_filial = ""
    if filial != "TODAS":
        filtro_filial = " AND f.nome=:filial "
        params["filial"] = filial

    df = qdf(f"""
        SELECT m.data, f.nome AS filial, p.categoria, p.produto,
               m.estoque, m.produzido_planejado, m.produzido_real, m.vendido, m.desperdicio, m.observacoes
        FROM movimentos m
        JOIN filiais f ON f.id=m.filial_id
        JOIN products p ON p.id=m.produto_id
        WHERE m.data BETWEEN :d1 AND :d2
        {filtro_filial}
        ORDER BY m.data DESC, f.nome, p.categoria, p.produto;
    """, params)

    st.dataframe(df, use_container_width=True, hide_index=True)

    if not df.empty:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Movimentos")
        st.download_button(
            "Baixar Excel",
            data=buffer.getvalue(),
            file_name=f"relatorio_{d1}_a_{d2}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
