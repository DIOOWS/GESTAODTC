from datetime import date
import pandas as pd


def render(st, qdf, qexec, garantir_produto, get_filial_id):
    st.header("Transferências (AUSTIN → QUEIMADOS)")

    col1, col2 = st.columns(2)
    d = col1.date_input("Data", value=date.today())
    obs = col2.text_input("Observações (opcional)", value="")

    st.caption("Registra o que saiu do AUSTIN e entrou no QUEIMADOS. Ajusta o estoque dos dois no mesmo dia.")

    produtos = qdf("""
        SELECT id, categoria, produto
        FROM products
        WHERE ativo = TRUE
        ORDER BY categoria, produto;
    """)

    if produtos.empty:
        st.warning("Nenhum produto cadastrado ainda.")
        return

    produto_id = st.selectbox(
        "Produto",
        options=produtos["id"].tolist(),
        format_func=lambda pid: f"{produtos.loc[produtos['id']==pid,'categoria'].iloc[0]} - {produtos.loc[produtos['id']==pid,'produto'].iloc[0]}",
    )

    qtd = st.number_input("Quantidade", min_value=0.0, value=0.0, step=1.0)

    if st.button("Registrar transferência"):
        try:
            if qtd <= 0:
                st.warning("Quantidade precisa ser maior que 0.")
                st.stop()

            de_id = get_filial_id("AUSTIN")
            para_id = get_filial_id("QUEIMADOS")

            # histórico
            qexec("""
                INSERT INTO transferencias (data, de_filial_id, para_filial_id, product_id, quantidade, observacoes)
                VALUES (:data, :de, :para, :pid, :qtd, :obs);
            """, {"data": d, "de": de_id, "para": para_id, "pid": int(produto_id), "qtd": float(qtd), "obs": obs})

            # aplica no estoque: AUSTIN -, QUEIMADOS +
            qexec("""
                INSERT INTO movimentos (data, filial_id, product_id, estoque)
                VALUES (:data, :filial, :pid, :delta)
                ON CONFLICT (data, filial_id, product_id)
                DO UPDATE SET estoque = COALESCE(movimentos.estoque,0) + EXCLUDED.estoque;
            """, {"data": d, "filial": de_id, "pid": int(produto_id), "delta": -float(qtd)})

            qexec("""
                INSERT INTO movimentos (data, filial_id, product_id, estoque)
                VALUES (:data, :filial, :pid, :delta)
                ON CONFLICT (data, filial_id, product_id)
                DO UPDATE SET estoque = COALESCE(movimentos.estoque,0) + EXCLUDED.estoque;
            """, {"data": d, "filial": para_id, "pid": int(produto_id), "delta": float(qtd)})

            st.success("Transferência registrada e estoque ajustado.")
            st.rerun()

        except Exception as e:
            st.error(f"Erro ao registrar: {e}")

    st.divider()
    st.subheader("Histórico (últimas 200)")

    df = qdf("""
        SELECT
          t.id,
          t.data,
          f1.nome AS de_filial,
          f2.nome AS para_filial,
          p.categoria,
          p.produto,
          t.quantidade,
          t.observacoes
        FROM transferencias t
        JOIN filiais f1 ON f1.id = t.de_filial_id
        JOIN filiais f2 ON f2.id = t.para_filial_id
        JOIN products p ON p.id = t.product_id
        ORDER BY t.data DESC, t.id DESC
        LIMIT 200;
    """)

    st.dataframe(df, width="stretch", hide_index=True)