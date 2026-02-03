from datetime import date

def render(st, qdf, qexec, garantir_produto, get_filial_id):
    st.header("Transferências (ex: Austin → Queimados)")

    col1, col2, col3 = st.columns(3)
    de_filial = col1.selectbox("De", ["AUSTIN", "QUEIMADOS"], index=0)
    para_filial = col2.selectbox("Para", ["QUEIMADOS", "AUSTIN"], index=0)
    d = col3.date_input("Data", value=date.today())

    col4, col5 = st.columns(2)
    categoria = col4.text_input("Categoria", placeholder="ASSADOS")
    produto = col5.text_input("Produto", placeholder="BAGUETE")

    qtd = st.number_input("Quantidade", min_value=0.0, value=0.0, step=1.0)
    obs = st.text_input("Observações (opcional)")

    if st.button("Salvar transferência"):
        de_id = get_filial_id(de_filial)
        para_id = get_filial_id(para_filial)
        pid = garantir_produto(categoria, produto)

        qexec("""
            INSERT INTO transferencias(data, de_filial_id, para_filial_id, product_id, quantidade, observacoes)
            VALUES (:data, :de, :para, :pid, :qtd, :obs);
        """, {"data": d, "de": de_id, "para": para_id, "pid": pid, "qtd": qtd, "obs": obs})

        st.success("Transferência salva!")

    st.subheader("Histórico (últimos 50)")
    df = qdf("""
        SELECT t.data, f1.nome AS de, f2.nome AS para, p.categoria, p.produto, t.quantidade, t.observacoes
        FROM transferencias t
        JOIN filiais f1 ON f1.id = t.de_filial_id
        JOIN filiais f2 ON f2.id = t.para_filial_id
        JOIN products p ON p.id = t.product_id
        ORDER BY t.data DESC, t.id DESC
        LIMIT 50;
    """)
    st.dataframe(df, use_container_width=True, hide_index=True)
