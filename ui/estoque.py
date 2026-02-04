from datetime import date
import pandas as pd


def render(st, qdf, qexec, get_filial_id):
    st.header("Estoque (por dia e filial)")

    col1, col2, col3 = st.columns([2, 2, 2])
    filial = col1.selectbox("Filial", ["AUSTIN", "QUEIMADOS"], index=0)
    d = col2.date_input("Data", value=date.today())
    modo_edicao = col3.checkbox("Modo edição", value=True)

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

    if df.empty:
        st.info("Nenhum produto cadastrado.")
        return

    st.caption("Você pode editar os números e também corrigir nomes/categorias. Clique em **Salvar alterações** no final.")

    if modo_edicao:
        edited = st.data_editor(
            df,
            width="stretch",
            hide_index=True,
            num_rows="fixed",
            column_config={
                "product_id": st.column_config.NumberColumn("product_id", disabled=True),
                "transf_in": st.column_config.NumberColumn("transf_in", disabled=True),
                "transf_out": st.column_config.NumberColumn("transf_out", disabled=True),
                "saldo_calculado": st.column_config.NumberColumn("saldo_calculado", disabled=True),
                "estoque": st.column_config.NumberColumn("estoque", step=1),
                "produzido_planejado": st.column_config.NumberColumn("produzido_planejado", step=1),
                "produzido_real": st.column_config.NumberColumn("produzido_real", step=1),
                "vendido": st.column_config.NumberColumn("vendido", step=1),
                "desperdicio": st.column_config.NumberColumn("desperdicio", step=1),
            },
        )

        if st.button("Salvar alterações"):
            try:
                # 1) Atualiza nomes/categorias em products
                # 2) Atualiza números em movimentos (upsert)
                for _, r in edited.iterrows():
                    pid = int(r["product_id"])
                    cat = str(r["categoria"]).strip().upper()
                    prod = str(r["produto"]).strip().upper()

                    # Atualiza o cadastro do produto (se mudou)
                    qexec("""
                        UPDATE products
                        SET categoria=:c, produto=:p
                        WHERE id=:id;
                    """, {"c": cat, "p": prod, "id": pid})

                    # Upsert dos números no dia/filial
                    qexec("""
                        INSERT INTO movimentos
                          (data, filial_id, product_id, estoque, produzido_planejado, produzido_real, vendido, desperdicio, observacoes)
                        VALUES
                          (:data, :filial, :pid, :e, :pp, :pr, :v, :d, :obs)
                        ON CONFLICT (data, filial_id, product_id)
                        DO UPDATE SET
                          estoque = EXCLUDED.estoque,
                          produzido_planejado = EXCLUDED.produzido_planejado,
                          produzido_real = EXCLUDED.produzido_real,
                          vendido = EXCLUDED.vendido,
                          desperdicio = EXCLUDED.desperdicio,
                          observacoes = EXCLUDED.observacoes;
                    """, {
                        "data": d,
                        "filial": filial_id,
                        "pid": pid,
                        "e": int(r["estoque"] or 0),
                        "pp": int(r["produzido_planejado"] or 0),
                        "pr": int(r["produzido_real"] or 0),
                        "v": int(r["vendido"] or 0),
                        "d": int(r["desperdicio"] or 0),
                        "obs": "Editado no Estoque"
                    })

                st.success("Alterações salvas! Recarregue a página para ver o saldo recalculado.")
                st.rerun()

            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
    else:
        st.dataframe(df, width="stretch", hide_index=True)

    st.caption("Saldo calculado = estoque + produção (planejada+real) - venda - desperdício - transf(saída) + transf(entrada).")
