from datetime import date
import pandas as pd
import io

def render(st, qdf):
    st.header("Relatórios")

    c1, c2 = st.columns(2)
    with c1:
        d1 = st.date_input("De", value=date.today().replace(day=1))
    with c2:
        d2 = st.date_input("Até", value=date.today())

    df = qdf("""
    SELECT
      m.dia,
      f.nome AS filial,
      COALESCE(c.nome,'(SEM)') AS categoria,
      p.nome AS produto,
      m.estoque,
      m.produzido_real,
      m.produzido_planejado,
      m.enviado,
      m.vendido,
      m.desperdicio,
      m.observacoes
    FROM movimentos m
    JOIN filiais f ON f.id=m.filial_id
    JOIN produtos p ON p.id=m.produto_id
    LEFT JOIN categorias c ON c.id=p.categoria_id
    WHERE m.dia BETWEEN :d1 AND :d2
    ORDER BY m.dia DESC, f.nome, c.nome NULLS LAST, p.nome;
    """, {"d1": d1, "d2": d2})

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
