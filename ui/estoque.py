from datetime import date

def render(st, qdf, qexec):
    st.header("Estoque (editar rápido)")

    c1, c2 = st.columns([1, 1])
    with c1:
        filial = st.selectbox("Filial", ["AUSTIN", "QUEIMADOS"])
    with c2:
        data_ref = st.date_input("Data", value=date.today())

    # pegar id filial
    filial_id = int(qdf("SELECT id FROM filiais WHERE nome=:n;", {"n": filial}).iloc[0]["id"])

    df = qdf("""
        SELECT
            p.id AS produto_id,
            p.categoria,
            p.produto,
            COALESCE(m.estoque,0) AS estoque
        FROM products p
        LEFT JOIN movimentos m
          ON m.produto_id = p.id AND m.filial_id=:f AND m.data=:d
        WHERE p.ativo = TRUE
        ORDER BY p.categoria, p.produto;
    """, {"f": filial_id, "d": data_ref})

    st.caption("Edite o ESTOQUE e clique em Salvar alterações. (Grava na tabela movimentos)")

    edited = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        disabled=["produto_id", "categoria", "produto"],
        key="estoque_editor"
    )

    if st.button("Salvar alterações de estoque"):
        for _, r in edited.iterrows():
            qexec("""
                INSERT INTO movimentos(data, filial_id, produto_id, estoque)
                VALUES (:d, :f, :p, :e)
                ON CONFLICT (data, filial_id, produto_id)
                DO UPDATE SET estoque=EXCLUDED.estoque;
            """, {
                "d": data_ref,
                "f": filial_id,
                "p": int(r["produto_id"]),
                "e": float(r["estoque"] or 0),
            })
        st.success("Estoque atualizado!")
        st.rerun()
