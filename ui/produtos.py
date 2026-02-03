def render(st, qdf, qexec):
    st.header("Produtos")

    st.subheader("Cadastrar")
    col1, col2 = st.columns(2)
    categoria = col1.text_input("Categoria (ex: BOLO RETANGULAR)").strip().upper()
    produto = col2.text_input("Produto (ex: FERRERO ROCHER)").strip().upper()

    if st.button("Adicionar"):
        if not categoria or not produto:
            st.warning("Preencha categoria e produto.")
        else:
            try:
                qexec("""
                    INSERT INTO products (categoria, produto)
                    VALUES (:c, :p)
                    ON CONFLICT (categoria, produto) DO NOTHING;
                """, {"c": categoria, "p": produto})
                st.success("Salvo!")
            except Exception as e:
                st.error(f"Erro: {e}")

    st.divider()
    st.subheader("Lista")
    df = qdf("""
        SELECT id, categoria, produto, ativo
        FROM products
        ORDER BY ativo DESC, categoria, produto;
    """)
    st.dataframe(df, width="stretch", hide_index=True)

    st.caption("Aqui o produto é só o SABOR/NOME. A categoria já aparece em coluna separada.")
