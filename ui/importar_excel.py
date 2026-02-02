from services.excel_import import import_produtos_from_excel

def render(st, qdf, qexec):
    st.header("Importar Excel")

    st.subheader("1) Importar CADASTRO de produtos (categoria + produto)")
    up = st.file_uploader("Selecione um Excel", type=["xlsx"])

    categoria_default = st.text_input("Categoria padrão (se a planilha não tiver coluna de categoria)", value="GERAL")

    if up is not None:
        try:
            itens = import_produtos_from_excel(up, categoria_default=categoria_default.strip().upper() or "GERAL")
            st.write(f"Foram lidos **{len(itens)}** produtos.")
            st.dataframe(itens, use_container_width=True, hide_index=True)

            if st.button("Salvar no banco"):
                for it in itens:
                    qexec("""
                        INSERT INTO products(categoria, produto)
                        VALUES (:c, :p)
                        ON CONFLICT (categoria, produto) DO NOTHING;
                    """, {"c": it["categoria"], "p": it["produto"]})
                st.success("Produtos importados!")
                st.rerun()

        except Exception as e:
            st.error(f"Erro ao importar: {e}")
