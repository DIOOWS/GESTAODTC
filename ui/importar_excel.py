import streamlit as st
from services.excel_import import load_products_from_excel


def render(st, qdf, qexec):
    st.header("Importar Excel (Produtos)")

    st.caption("Importa apenas **cadastro de produtos** (categoria + produto). Não cria movimentações.")

    up = st.file_uploader("Escolha o Excel", type=["xlsx"])
    if not up:
        st.stop()

    try:
        df = load_products_from_excel(up)
        st.dataframe(df, use_container_width=True, hide_index=True)

        if st.button("Importar para o banco"):
            for _, row in df.iterrows():
                qexec("""
                    INSERT INTO products(categoria, produto)
                    VALUES (:c, :p)
                    ON CONFLICT (categoria, produto) DO NOTHING;
                """, {"c": row["CATEGORIA"], "p": row["PRODUTO"]})

            st.success("Produtos importados!")
            st.rerun()

    except Exception as e:
        st.error(f"Erro ao importar: {e}")
