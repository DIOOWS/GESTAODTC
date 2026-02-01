def render(st, qdf, garantir_local):
    st.header("Locais (Filiais)")
    st.caption("Por enquanto use só AUSTIN e QUEIMADOS.")

    col1, col2 = st.columns([2, 1])

    with col1:
        df = qdf('SELECT id AS "ID", nome AS "Filial" FROM locais ORDER BY nome;')
        st.dataframe(df, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Adicionar filial")
        nome_local = st.text_input("Nome da filial (ex.: AUSTIN)")
        if st.button("Salvar filial"):
            if nome_local.strip():
                garantir_local(nome_local)
                st.success("Filial salva!")
                st.rerun()
            else:
                st.warning("O nome é obrigatório.")
