def render(st, qdf, qexec):
    st.header("Produtos")

    col1, col2 = st.columns([2, 1])

    with col1:
        df = qdf("""
            SELECT id, categoria, produto, ativo
            FROM products
            ORDER BY categoria, produto
        """)
        st.dataframe(df, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Adicionar produto")
        categoria = st.text_input("Categoria (ex: BOLO RETANGULAR)")
        produto = st.text_input("Produto / Sabor (ex: FERRERO ROCHER)")
        if st.button("Salvar produto"):
            cat = (categoria or "").strip().upper()
            prod = (produto or "").strip().upper()
            if not cat or not prod:
                st.warning("Categoria e Produto são obrigatórios.")
            else:
                qexec("""
                    INSERT INTO products(categoria, produto)
                    VALUES (:c, :p)
                    ON CONFLICT (categoria, produto) DO NOTHING;
                """, {"c": cat, "p": prod})
                st.success("Salvo!")
                st.rerun()

        st.divider()
        st.subheader("Ativar/Desativar")
        pid = st.number_input("ID do produto", min_value=1, step=1)
        ativo = st.selectbox("Status", [True, False], index=0)
        if st.button("Atualizar status"):
            qexec("UPDATE products SET ativo=:a WHERE id=:id;", {"a": ativo, "id": int(pid)})
            st.success("Atualizado!")
            st.rerun()
