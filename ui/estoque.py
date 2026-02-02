from datetime import date
import pandas as pd


def render(st, qdf, qexec, get_filial_id):
    st.header("Estoque")

    c1, c2 = st.columns(2)
    filial = c1.selectbox("Filial", ["AUSTIN", "QUEIMADOS"], index=0)
    d = c2.date_input("Data", value=date.today())

    filial_id = get_filial_id(filial)

    df = qdf(
        """
        SELECT
          p.id AS produto_id,
          p.categoria,
          p.produto,
          COALESCE(m.estoque,0) AS estoque,
          COALESCE(m.produzido_planejado,0) AS produzido_planejado,
          COALESCE(m.produzido_real,0) AS produzido_real,
          COALESCE(m.vendido,0) AS vendido,
          COALESCE(m.desperdicio,0) AS desperdicio
        FROM products p
        LEFT JOIN movimentos m
          ON m.produto_id = p.id
         AND m.filial_id = :f
         AND m.data = :d
        WHERE p.ativo = TRUE
        ORDER BY p.categoria, p.produto;
        """,
        {"f": filial_id, "d": d},
    )

    st.caption("Você pode editar os valores e salvar (isso grava na tabela movimentos).")

    edited = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        disabled=["produto_id", "categoria", "produto"],
        num_rows="fixed",
        key="estoque_editor",
    )

    if st.button("Salvar alterações"):
        for _, r in edited.iterrows():
            pid = int(r["produto_id"])
            qexec(
                """
                INSERT INTO movimentos (data, filial_id, produto_id, estoque, produzido_planejado, produzido_real, vendido, desperdicio)
                VALUES (:data, :filial, :pid, :e, :pp, :pr, :v, :dsp)
                ON CONFLICT (data, filial_id, produto_id)
                DO UPDATE SET
                  estoque = EXCLUDED.estoque,
                  produzido_planejado = EXCLUDED.produzido_planejado,
                  produzido_real = EXCLUDED.produzido_real,
                  vendido = EXCLUDED.vendido,
                  desperdicio = EXCLUDED.desperdicio;
                """,
                {
                    "data": d,
                    "filial": filial_id,
                    "pid": pid,
                    "e": float(r["estoque"] or 0),
                    "pp": float(r["produzido_planejado"] or 0),
                    "pr": float(r["produzido_real"] or 0),
                    "v": float(r["vendido"] or 0),
                    "dsp": float(r["desperdicio"] or 0),
                },
            )

        st.success("Alterações salvas!")
