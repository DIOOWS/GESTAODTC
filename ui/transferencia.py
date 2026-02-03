from datetime import date
import pandas as pd


def render(st, qdf, qexec, garantir_produto, get_filial_id):
    st.header("Transferências")

    col1, col2, col3 = st.columns(3)
    d = col1.date_input("Data", value=date.today())
    de_filial = col2.selectbox("De", ["AUSTIN", "QUEIMADOS"], index=0)
    para_filial = col3.selectbox("Para", ["QUEIMADOS", "AUSTIN"], index=0)

    if de_filial == para_filial:
        st.warning("Origem e destino não podem ser iguais.")
        st.stop()

    df_prod = qdf("""
        SELECT id, categoria, produto
        FROM products
        WHERE ativo=TRUE
        ORDER BY categoria, produto;
    """)
    if df_prod.empty:
        st.info("Cadastre produtos primeiro.")
        return

    opcoes = (df_prod["categoria"] + " | " + df_prod["produto"]).tolist()
    escolha = st.selectbox("Produto", opcoes, index=0)
    qtd = st.number_input("Quantidade", min_value=0, step=1, value=0)
    obs = st.text_input("Observações (opcional)")

    if st.button("Salvar transferência"):
        try:
            de_id = get_filial_id(de_filial)
            para_id = get_filial_id(para_filial)

            idx = opcoes.index(escolha)
            product_id = int(df_prod.iloc[idx]["id"])

            qexec("""
                INSERT INTO transferencias (data, de_filial_id, para_filial_id, product_id, quantidade, observacoes)
                VALUES (:data, :de, :para, :pid, :qtd, :obs);
            """, {"data": d, "de": de_id, "para": para_id, "pid": product_id, "qtd": int(qtd), "obs": obs})

            st.success("Transferência salva!")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

    st.divider()
    st.subheader("Histórico (últimos 30 dias)")
    df_hist = qdf("""
        SELECT t.data, f1.nome AS de, f2.nome AS para, p.categoria, p.produto, t.quantidade, t.observacoes
        FROM transferencias t
        JOIN filiais f1 ON f1.id = t.de_filial_id
        JOIN filiais f2 ON f2.id = t.para_filial_id
        JOIN products p ON p.id = t.product_id
        WHERE t.data >= (CURRENT_DATE - INTERVAL '30 days')
        ORDER BY t.data DESC, de, para, p.categoria, p.produto;
    """)
    st.dataframe(df_hist, width="stretch", hide_index=True)
