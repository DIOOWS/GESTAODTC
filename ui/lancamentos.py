from datetime import date

def render(st, qdf, qexec, garantir_produto, get_filial_id):
    st.header("Lançamentos")

    c1, c2 = st.columns([1, 1])
    with c1:
        filial = st.selectbox("Filial", ["AUSTIN", "QUEIMADOS"])
    with c2:
        data_ref = st.date_input("Data", value=date.today())

    filial_id = get_filial_id(filial)

    produtos_df = qdf("""
        SELECT id, categoria, produto
        FROM products
        WHERE ativo = TRUE
        ORDER BY categoria, produto;
    """)
    if produtos_df.empty:
        st.info("Cadastre produtos primeiro em Produtos.")
        return

    produtos_df["label"] = produtos_df["categoria"] + " | " + produtos_df["produto"]
    label = st.selectbox("Produto", produtos_df["label"].tolist())
    row = produtos_df.loc[produtos_df["label"] == label].iloc[0]
    produto_id = int(row["id"])

    st.subheader("Quantidades (manual)")

    existente = qdf("""
        SELECT estoque, produzido_planejado, produzido_real, vendido, desperdicio, observacoes
        FROM movimentos
        WHERE data=:d AND filial_id=:f AND produto_id=:p;
    """, {"d": data_ref, "f": filial_id, "p": produto_id})

    def _get(col, default=0.0):
        if existente.empty:
            return default
        v = existente.iloc[0][col]
        try:
            return float(v) if v is not None else default
        except Exception:
            return default

    estoque = st.number_input("Estoque (contagem)", min_value=0.0, step=1.0, value=_get("estoque", 0.0))
    prod_plan = st.number_input("Produzido (planejado)", min_value=0.0, step=1.0, value=_get("produzido_planejado", 0.0))
    prod_real = st.number_input("Produzido (real)", min_value=0.0, step=1.0, value=_get("produzido_real", 0.0))
    vendido = st.number_input("Vendido", min_value=0.0, step=1.0, value=_get("vendido", 0.0))
    desperd = st.number_input("Desperdício", min_value=0.0, step=1.0, value=_get("desperdicio", 0.0))
    obs = st.text_input("Observações", value=(existente.iloc[0]["observacoes"] if not existente.empty else "") or "")

    if st.button("Salvar lançamento"):
        qexec("""
            INSERT INTO movimentos(data, filial_id, produto_id, estoque, produzido_planejado, produzido_real, vendido, desperdicio, observacoes)
            VALUES (:d, :f, :p, :e, :pp, :pr, :v, :w, :o)
            ON CONFLICT (data, filial_id, produto_id)
            DO UPDATE SET
              estoque=EXCLUDED.estoque,
              produzido_planejado=EXCLUDED.produzido_planejado,
              produzido_real=EXCLUDED.produzido_real,
              vendido=EXCLUDED.vendido,
              desperdicio=EXCLUDED.desperdicio,
              observacoes=EXCLUDED.observacoes;
        """, {
            "d": data_ref, "f": filial_id, "p": produto_id,
            "e": estoque, "pp": prod_plan, "pr": prod_real,
            "v": vendido, "w": desperd, "o": obs.strip() or None
        })
        st.success("Salvo!")
        st.rerun()

    st.divider()
    st.subheader("Lançamentos do dia (filial selecionada)")

    df = qdf("""
        SELECT m.data, f.nome AS filial, p.categoria, p.produto,
               m.estoque, m.produzido_planejado, m.produzido_real,
               m.vendido, m.desperdicio, m.observacoes
        FROM movimentos m
        JOIN filiais f ON f.id = m.filial_id
        JOIN products p ON p.id = m.produto_id
        WHERE m.data=:d AND m.filial_id=:f
        ORDER BY p.categoria, p.produto;
    """, {"d": data_ref, "f": filial_id})

    st.dataframe(df, use_container_width=True, hide_index=True)
