from datetime import date

def render(st, qdf, qexec, get_filial_id):
    st.header("Estoque (edição rápida)")

    c1, c2 = st.columns([1,1])
    with c1:
        dia = st.date_input("Data", value=date.today())
    with c2:
        filial = st.selectbox("Filial", ["AUSTIN", "QUEIMADOS"])
        filial_id = get_filial_id(filial)

    df = qdf("""
        SELECT
          p.id AS produto_id,
          p.categoria,
          p.produto,
          COALESCE(m.estoque,0) AS estoque,
          COALESCE(m.produzido_planejado,0) AS produzido_planejado,
          COALESCE(m.produzido_real,0) AS produzido_real,
          COALESCE(m.vendido,0) AS vendido,
          COALESCE(m.desperdicio,0) AS desperdicio
        FROM products p
        LEFT JOIN movimentos m
          ON m.produto_id=p.id AND m.filial_id=:f AND m.data=:d
        WHERE p.ativo=TRUE
        ORDER BY p.categoria, p.produto;
    """, {"f": filial_id, "d": dia})

    if df.empty:
        st.info("Sem produtos cadastrados.")
        return

    edit = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        disabled=["produto_id", "categoria", "produto"],
        num_rows="fixed"
    )

    if st.button("Salvar alterações"):
        for _, r in edit.iterrows():
            qexec("""
                INSERT INTO movimentos(data, filial_id, produto_id, estoque, produzido_planejado, produzido_real, vendido, desperdicio)
                VALUES (:data, :filial_id, :produto_id, :estoque, :pp, :pr, :vend, :desp)
                ON CONFLICT (data, filial_id, produto_id)
                DO UPDATE SET
                  estoque=EXCLUDED.estoque,
                  produzido_planejado=EXCLUDED.produzido_planejado,
                  produzido_real=EXCLUDED.produzido_real,
                  vendido=EXCLUDED.vendido,
                  desperdicio=EXCLUDED.desperdicio;
            """, {
                "data": dia, "filial_id": filial_id, "produto_id": int(r["produto_id"]),
                "estoque": int(r["estoque"] or 0),
                "pp": int(r["produzido_planejado"] or 0),
                "pr": int(r["produzido_real"] or 0),
                "vend": int(r["vendido"] or 0),
                "desp": int(r["desperdicio"] or 0),
            })
        st.success("Salvo!")
        st.rerun()
