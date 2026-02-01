import io
from datetime import date
import pandas as pd


def render(st, qdf):
    st.header("Relatórios")

    c1, c2 = st.columns(2)
    with c1:
        d1 = st.date_input("De", value=date.today().replace(day=1))
    with c2:
        d2 = st.date_input("Até", value=date.today())

    df = qdf("""
        SELECT r.data AS "Data",
               l.nome AS "Filial",
               p.categoria AS "Categoria",
               p.nome AS "Produto",
               COALESCE(r.estoque,0) AS "Estoque",
               COALESCE(r.produzido,0) AS "Produzido (real)",
               COALESCE(r.produzido_planejado,0) AS "Produzido (planejado)",
               COALESCE(r.enviado,0) AS "Enviado",
               COALESCE(r.vendido,0) AS "Vendido",
               COALESCE(r.desperdicio,0) AS "Desperdício",
               COALESCE(r.total,0) AS "Total",
               r.observacoes AS "Observações"
        FROM registros_diarios r
        JOIN produtos p ON p.id = r.produto_id
        JOIN locais l ON l.id = r.local_id
        WHERE r.data BETWEEN :d1 AND :d2
        ORDER BY r.data DESC, l.nome, p.nome;
    """, {"d1": d1, "d2": d2})

    st.dataframe(df, use_container_width=True, hide_index=True)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Relatório")

    st.download_button(
        "Baixar Excel",
        data=buffer.getvalue(),
        file_name=f"relatorio_{d1}_a_{d2}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
