# ui/importar_excel.py
import streamlit as st
from services.excel_import import load_products_from_excel


def render(st, qdf, qexec, garantir_produto=None):
    st.header("Importar Excel (Produtos)")

    st.caption("Importa apenas **cadastro de produtos** (categoria + produto). Não cria movimentações.")

    up = st.file_uploader("Escolha o Excel", type=["xlsx"])
    if not up:
        st.stop()

    try:
        df = load_products_from_excel(up)

        # Streamlit novo: width="stretch" no lugar de use_container_width=True
        st.dataframe(df, width="stretch", hide_index=True)

        if st.button("Importar para o banco"):
            for _, row in df.iterrows():
                categoria = str(row.get("CATEGORIA", "")).strip()
                produto = str(row.get("PRODUTO", "")).strip()

                if not categoria or not produto:
                    continue

                # Se você passou garantir_produto pelo app.py, usamos ele (padrão do projeto)
                if garantir_produto is not None:
                    garantir_produto(categoria, produto)
                else:
                    # fallback: insere direto
                    qexec("""
                        INSERT INTO products(categoria, produto)
                        VALUES (:c, :p)
                        ON CONFLICT (categoria, produto) DO NOTHING;
                    """, {"c": categoria.upper(), "p": produto.upper()})

            st.success("Produtos importados!")
            st.rerun()

    except Exception as e:
        st.error(f"Erro ao importar: {e}")
