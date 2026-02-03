from datetime import date


def render(st, qdf, qexec, get_filial_id):
    st.header("Transferências")

    col1, col2, col3 = st.columns(3)
    de_filial = col1.selectbox("De (origem)", ["AUSTIN", "QUEIMADOS"], index=0)
    para_filial = col2.selectbox("Para (destino)", ["QUEIMADOS", "AUSTIN"], index=0)
    dia = col3.date_input("Data", value=date.today())

    if de_filial == para_filial:
        st.warning("Origem e destino não podem ser iguais.")
        st.stop()

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

    qtd = st.number_input("Quantidade transferida", min_value=0.0, step=1.0)
    obs = st.text_input("Observações (opcional)")

    if st.button("Registrar transferência"):
        de_id = get_filial_id(de_filial)
        para_id = get_filial_id(para_filial)

        # registra transferência
        qexec("""
            INSERT INTO transferencias (dia, de_filial_id, para_filial_id, produto_id, quantidade, observacoes)
            VALUES (:dia, :de, :para, :pid, :qtd, :obs);
        """, {"dia": dia, "de": de_id, "para": para_id, "pid": produto_id, "qtd": qtd, "obs": obs or None})

        # aplica efeito no estoque do dia (delta):
        # - origem: diminui estoque
        qexec("""
            INSERT INTO movimentacoes (dia, filial_id, produto_id, estoque)
            VALUES (:dia, :filial, :pid, 0)
            ON CONFLICT (dia, filial_id, produto_id) DO NOTHING;
        """, {"dia": dia, "filial": de_id, "pid": produto_id})
        qexec("""
            UPDATE movimentacoes
            SET estoque = COALESCE(estoque,0) - :qtd
            WHERE dia=:dia AND filial_id=:filial AND produto_id=:pid;
        """, {"dia": dia, "filial": de_id, "pid": produto_id, "qtd": qtd})

        # + destino: aumenta estoque
        qexec("""
            INSERT INTO movimentacoes (dia, filial_id, produto_id, estoque)
            VALUES (:dia, :filial, :pid, 0)
            ON CONFLICT (dia, filial_id, produto_id) DO NOTHING;
        """, {"dia": dia, "filial": para_id, "pid": produto_id})
        qexec("""
            UPDATE movimentacoes
            SET estoque = COALESCE(estoque,0) + :qtd
            WHERE dia=:dia AND filial_id=:filial AND produto_id=:pid;
        """, {"dia": dia, "filial": para_id, "pid": produto_id, "qtd": qtd})

        st.success("Transferência registrada e estoque ajustado.")
        st.rerun()

    st.divider()
    st.subheader("Histórico (últimas 200)")

    hist = qdf("""
        SELECT t.id, t.dia,
               f1.nome AS origem,
               f2.nome AS destino,
               p.categoria, p.produto,
               t.quantidade, t.observacoes
        FROM transferencias t
        JOIN filiais f1 ON f1.id = t.de_filial_id
        JOIN filiais f2 ON f2.id = t.para_filial_id
        JOIN products p ON p.id = t.produto_id
        ORDER BY t.dia DESC, t.id DESC
        LIMIT 200;
    """)

    st.dataframe(hist, use_container_width=True, hide_index=True)

    st.subheader("Excluir transferência (se errou)")
    del_id = st.number_input("ID da transferência", min_value=1, step=1)
    st.caption("Obs: excluir não reverte o estoque automaticamente (pra evitar bagunça). Ajuste no Estoque se precisar.")
    if st.button("Excluir transferência"):
        qexec("DELETE FROM transferencias WHERE id=:id;", {"id": int(del_id)})
        st.success("Excluída!")
        st.rerun()
