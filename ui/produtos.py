import pandas as pd
from sqlalchemy import text

def render(st, engine):
    st.header("Produtos")

    with engine.begin() as conn:
        df = pd.read_sql(text("""
            SELECT id, name AS produto, category AS categoria, active AS ativo
            FROM products
            ORDER BY category NULLS LAST, name;
        """), conn)

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("Adicionar produto")
    c1,c2 = st.columns(2)
    with c1:
        prod = st.text_input("Produto (somente nome/sabor)")
    with c2:
        cat = st.text_input("Categoria (ex: BOLO RETANGULAR, ASSADOS, TORTAS)")

    if st.button("Salvar produto"):
        p = (prod or "").strip().upper()
        c = (cat or "").strip().upper() or None
        if not p:
            st.warning("Produto é obrigatório.")
            return
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO products(name, category)
                VALUES (:n, :c)
                ON CONFLICT (name, COALESCE(category,'')) DO NOTHING;
            """), {"n": p, "c": c})
        st.success("Salvo!")
        st.rerun()
