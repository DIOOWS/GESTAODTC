from sqlalchemy import text
from services.excel_import import load_products_from_excel

def render(st, engine):
    st.header("Importar Excel (cadastro de produtos)")

    st.caption("Importa PRODUTO + CATEGORIA e grava em Produtos. Não cria lançamentos.")

    f = st.file_uploader("Selecione o Excel", type=["xlsx"])
    if not f:
        return

    try:
        df = load_products_from_excel(f)
    except Exception as e:
        st.error(f"Erro ao ler Excel: {e}")
        return

    st.dataframe(df, use_container_width=True, hide_index=True)

    if st.button("Importar produtos"):
        with engine.begin() as conn:
            for _, r in df.iterrows():
                conn.execute(text("""
                    INSERT INTO products(name, category)
                    VALUES (:n, :c)
                    ON CONFLICT (name, COALESCE(category,'')) DO NOTHING;
                """), {"n": r["produto"], "c": r["categoria"]})
        st.success("Produtos importados com sucesso!")
        st.rerun()
