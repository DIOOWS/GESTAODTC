def render(st, qdf, garantir_produto, qexec):
    st.header("Produtos")

    col1, col2 = st.columns([2, 1])
    with col1:
        df = qdf('SELECT id AS "ID", nome AS "Produto", categoria AS "Categoria", ativo AS "Ativo" FROM produtos ORDER BY nome;')
        st.dataframe(df, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Adicionar / Atualizar")
        nome = st.text_input("Nome do produto")
        categoria = st.text_input("Categoria")

        if st.button("Salvar produto"):
            if nome.strip():
                garantir_produto(nome, categoria if categoria.strip() else None)
                st.success("Produto salvo!")
                st.rerun()
            else:
                st.warning("O nome do produto é obrigatório.")

        st.divider()
        st.subheader("Excluir produto (cuidado)")
        dfp = qdf('SELECT id, nome FROM produtos ORDER BY nome;')
        if not dfp.empty:
            escolhido = st.selectbox("Produto para excluir", dfp["nome"].tolist())
            pid = int(dfp.loc[dfp["nome"] == escolhido, "id"].iloc[0])
            if st.button("Excluir produto"):
                qexec("DELETE FROM produtos WHERE id = :id;", {"id": pid})
                st.success("Produto excluído.")
                st.rerun()
