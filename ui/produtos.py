def render(st, qdf, qexec):
    st.header("Produtos")

    col1, col2 = st.columns([2,1])

    with col1:
        df = qdf("""
            SELECT id, categoria, produto, ativo
            FROM products
            ORDER BY categoria, produto;
        """)
        st.dataframe(df, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Adicionar")
        categoria = st.text_input("Categoria (ex: BOLO RETANGULAR)")
        produto = st.text_input("Produto/Sabor (ex: FERRERO ROCHER)")
        if st.button("Salvar produto"):
            if categoria.strip() and produto.strip():
                qexec("""
                    INSERT INTO products(categoria, produto)
                    VALUES (:c, :p)
                    ON CONFLICT (categoria, produto) DO NOTHING;
                """, {"c": categoria.strip().upper(), "p": produto.strip().upper()})
                st.success("Salvo!")
                st.rerun()
            else:
                st.warning("Categoria e Produto são obrigatórios.")

        st.divider()
        st.subheader("Excluir (opcional)")
        pid = st.number_input("ID do produto para excluir", min_value=0, step=1)
        if st.button("Excluir produto"):
            if pid > 0:
                qexec("DELETE FROM products WHERE id=:id;", {"id": int(pid)})
                st.success("Excluído.")
                st.rerun()
