def render(st, qdf, qexec):
    st.header("Produtos")

    st.subheader("Cadastrar produto")
    c1, c2 = st.columns(2)
    categoria = c1.text_input("Categoria (ex: BOLO RETANGULAR)")
    produto = c2.text_input("Produto (ex: PRESTÍGIO)")

    if st.button("Adicionar"):
        try:
            cat = (categoria or "").strip().upper()
            prod = (produto or "").strip().upper()
            if not cat or not prod:
                st.warning("Preencha categoria e produto.")
            else:
                qexec("""
                    INSERT INTO products(categoria, produto)
                    VALUES (:c, :p)
                    ON CONFLICT (categoria, produto) DO NOTHING;
                """, {"c": cat, "p": prod})
                st.success("Produto adicionado!")
        except Exception as e:
            st.error(f"Erro: {e}")

    st.subheader("Lista de produtos")
    df = qdf("""
        SELECT id, categoria, produto, ativo
        FROM products
        ORDER BY categoria, produto;
    """)

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.caption("Para desativar/ativar produtos depois, a gente adiciona botão de excluir/ativar na próxima rodada.")
