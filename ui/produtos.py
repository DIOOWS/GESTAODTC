def render(st, qdf, qexec, garantir_produto):
    st.header("Produtos")

    col1, col2 = st.columns([2, 1])

    with col1:
        df = qdf("""
        SELECT
          p.id,
          COALESCE(c.nome,'(SEM CATEGORIA)') AS categoria,
          p.nome AS produto,
          p.ativo
        FROM produtos p
        LEFT JOIN categorias c ON c.id = p.categoria_id
        ORDER BY c.nome NULLS LAST, p.nome;
        """)
        st.dataframe(df, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Adicionar")
        categoria = st.text_input("Categoria (ex: BOLO RETANGULAR)")
        produto = st.text_input("Produto (ex: FERREIRO ROCHER)")

        if st.button("Salvar produto"):
            if produto.strip():
                garantir_produto(categoria, produto)
                st.success("Salvo!")
                st.rerun()
            else:
                st.warning("Produto é obrigatório.")

        st.divider()
        st.subheader("Desativar / Ativar")
        pid = st.number_input("ID do produto", min_value=1, step=1)
        ac = st.selectbox("Ação", ["Ativar", "Desativar"])
        if st.button("Aplicar"):
            qexec("UPDATE produtos SET ativo=:a WHERE id=:id", {"a": (ac == "Ativar"), "id": int(pid)})
            st.success("OK")
            st.rerun()
