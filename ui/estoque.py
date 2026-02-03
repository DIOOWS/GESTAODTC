from datetime import date
import pandas as pd


def render(st, qdf, qexec, get_filial_id):
    st.header("Estoque (ajuste manual)")

    col1, col2 = st.columns(2)
    filial = col1.selectbox("Filial", ["AUSTIN", "QUEIMADOS"], index=0)
    dia = col2.date_input("Data", value=date.today())

    filial_id = get_filial_id(filial)

    df = qdf("""
        SELECT p.id AS produto_id, p.categoria, p.produto,
               COALESCE(m.estoque,0) AS estoque
        FROM products p
        LEFT JOIN movimentacoes m
          ON m.produto_id = p.id AND m.filial_id = :f AND m.dia = :d
        WHERE p.ativo = TRUE
        ORDER BY p.categoria, p.produto;
    """, {"f": filial_id, "d": dia})

    st.caption("Edite o estoque e clique em **Salvar ajustes**.")
    edited = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        disabled=["produto_id", "categoria", "produto"],
        num_rows="fixed"
    )

    if st.button("Salvar ajustes"):
        try:
            for _, row in edited.iterrows():
                pid = int(row["produto_id"])
                estoque = float(row["estoque"] or 0)

                qexec("""
                    INSERT INTO movimentacoes (dia, filial_id, produto_id, estoque)
                    VALUES (:dia, :filial, :pid, :estoque)
                    ON CONFLICT (dia, filial_id, produto_id)
                    DO UPDATE SET estoque = EXCLUDED.estoque;
                """, {"dia": dia, "filial": filial_id, "pid": pid, "estoque": estoque})

            st.success("Estoque salvo!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

    st.divider()
    st.subheader("Resumo")

    total_filial = float(edited["estoque"].fillna(0).sum())
    st.metric(f"Total estoque ({filial})", int(round(total_filial)))

    # total geral (Austin + Queimados)
    geral = qdf("""
        SELECT COALESCE(SUM(estoque),0) AS total
        FROM movimentacoes
        WHERE dia = :d;
    """, {"d": dia})
    total_geral = float(geral.iloc[0]["total"] or 0)
    st.metric("Total estoque (geral)", int(round(total_geral)))
