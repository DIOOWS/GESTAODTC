from datetime import date


def render(st, qdf, qexec, garantir_produto, get_filial_id):
    st.header("Lançamentos (manual)")

    col1, col2 = st.columns(2)
    filial = col1.selectbox("Filial", ["AUSTIN", "QUEIMADOS"], index=0)
    dia = col2.date_input("Data", value=date.today())

    filial_id = get_filial_id(filial)

    produtos = qdf("""
        SELECT id, categoria, produto
        FROM products
        WHERE ativo = TRUE
        ORDER BY categoria, produto
    """)

    if produtos.empty:
        st.info("Cadastre produtos primeiro.")
        st.stop()

    produtos["label"] = produtos["categoria"] + " - " + produtos["produto"]
    label = st.selectbox("Produto", produtos["label"])
    produto_id = int(produtos.loc[produtos["label"] == label, "id"].iloc[0])

    st.subheader("Valores")
    c1, c2, c3, c4, c5 = st.columns(5)
    estoque = c1.number_input("Estoque", min_value=0.0, step=1.0)
    prod_plan = c2.number_input("Produzido planejado", min_value=0.0, step=1.0)
    prod_real = c3.number_input("Produzido real", min_value=0.0, step=1.0)
    vendido = c4.number_input("Vendido", min_value=0.0, step=1.0)
    desperdicio = c5.number_input("Desperdício", min_value=0.0, step=1.0)

    obs = st.text_input("Observações (opcional)")

    if st.button("Salvar lançamento"):
        qexec("""
        INSERT INTO movimentacoes (dia, filial_id, produto_id, estoque, produzido_planejado, produzido_real, vendido, desperdicio, observacoes)
        VALUES (:dia, :filial, :pid, :estoque, :pp, :pr, :vend, :desp, :obs)
        ON CONFLICT (dia, filial_id, produto_id)
        DO UPDATE SET
          estoque=EXCLUDED.estoque,
          produzido_planejado=EXCLUDED.produzido_planejado,
          produzido_real=EXCLUDED.produzido_real,
          vendido=EXCLUDED.vendido,
          desperdicio=EXCLUDED.desperdicio,
          observacoes=EXCLUDED.observacoes;
        """, {
            "dia": dia,
            "filial": filial_id,
            "pid": produto_id,
            "estoque": estoque,
            "pp": prod_plan,
            "pr": prod_real,
            "vend": vendido,
            "desp": desperdicio,
            "obs": obs or None
        })
        st.success("Salvo!")
        st.rerun()

    st.divider()
    st.subheader("Lançamentos do dia (filial selecionada)")

    df = qdf("""
        SELECT m.dia, f.nome AS filial, p.categoria, p.produto,
               m.estoque, m.produzido_planejado, m.produzido_real, m.vendido, m.desperdicio, m.observacoes
        FROM movimentacoes m
        JOIN filiais f ON f.id = m.filial_id
        JOIN products p ON p.id = m.produto_id
        WHERE m.dia = :dia AND m.filial_id = :filial
        ORDER BY p.categoria, p.produto;
    """, {"dia": dia, "filial": filial_id})

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("Excluir 1 lançamento")
    del_id = st.number_input("ID da movimentação", min_value=1, step=1)
    if st.button("Excluir"):
        qexec("DELETE FROM movimentacoes WHERE id=:id;", {"id": int(del_id)})
        st.success("Excluído!")
        st.rerun()
