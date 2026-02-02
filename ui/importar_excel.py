import pandas as pd
from services.excel_import import import_products_from_excel


def render(st, qdf, qexec, garantir_produto):
    st.header("Importar Excel")

    st.caption("Importa cadastro de produtos (colunas: PRODUTO, CATEGORIA).")

    up = st.file_uploader("Selecione o arquivo (.xlsx)", type=["xlsx"])
    if not up:
        return

    if st.button("Importar produtos"):
        try:
            itens = import_products_from_excel(up)
            for it in itens:
                garantir_produto(it["categoria"], it["produto"])
            st.success(f"Importado! ({len(itens)} produtos)")
        except Exception as e:
            st.error(f"Erro ao importar: {e}")
