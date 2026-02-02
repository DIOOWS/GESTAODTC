import pandas as pd

def render(st, qdf, qexec):
    st.header("Produtos")

    col1, col2 = st.columns([2, 1])

    with col1:
        df = qdf("""
            SELECT id, categoria, produto, ativo
            FROM products
            ORDER BY categoria, produto;
        """)
        st.dataframe(df, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Adicionar produto")
        categoria = st.text_input("Categoria (ex: BOLO RETANGULAR)")
        produto = st.text_input("Produto (ex: FERRERO ROCHER)")
        ativo = st.checkbox("Ativo", value=True)

        if st.button("Salvar"):
            if not categoria.strip() or not produto.strip():
                st.warning("Categoria e Produto são obrigatórios.")
            else:
                qexec("""
                    INSERT INTO products(categoria, produto, ativo)
                    VALUES (:c, :p, :a)
                    ON CONFLICT (categoria, produto) DO UPDATE SET ativo=EXCLUDED.ativo;
                """, {
                    "c": categoria.strip().upper(),
                    "p": produto.strip().upper(),
                    "a": bool(ativo),
                })
                st.success("Salvo!")
                st.rerun()
