from datetime import date


def render(st, qdf, qexec, garantir_produto, get_filial_id):
    st.header("Lançamentos (manual)")

    col1, col2 = st.columns(2)
    filial = col1.selectbox("Filial", ["AUSTIN", "QUEIMADOS"], index=0)
    d = col2.date_input("Data", value=date.today())
    filial_id = get_filial_id(filial)

    # lista produtos
    produtos = qdf("""
        SELECT id, categoria, produto
        FROM products
        WHERE ativo = TRUE
        ORDER BY categoria, produto;
    """)

    if produtos.empty:
        st.warning("Nenhum produto cadastrado ainda. Vá em Produtos ou importe via Excel/WhatsApp.")
        return

    # seletor
    produtos["label"] = produtos["categoria"] + " | " + produtos["produto"]
    label = st.selectbox("Produto", produtos["label"].tolist())
    row = produtos[produtos["label"] == label].iloc[0]
    product_id = int(row["id"])

    # carregar valores atuais do dia
    atual = qdf("""
        SELECT estoque, produzido_planejado, produzido_real, vendido, desperdicio, observacoes
        FROM movimentos
        WHERE data=:d AND filial_id=:f AND product_id=:p;
    """, {"d": d, "f": filial_id, "p": product_id})

    def getv(col):
        if atual.empty:
            return 0.0
        v = atual.iloc[0][col]
        return float(v or 0)

    estoque_v = getv("estoque")
    pp_v = getv("produzido_planejado")
    pr_v = getv("produzido_real")
    vend_v = getv("vendido")
    desp_v = getv("desperdicio")
    obs_v = "" if atual.empty else (atual.iloc[0]["observacoes"] or "")

    c1, c2, c3 = st.columns(3)
    estoque = c1.number_input("Estoque", min_value=0.0, step=1.0, value=float(estoque_v))
    produzido_planejado = c2.number_input("Produzido (planejado)", min_value=0.0, step=1.0, value=float(pp_v))
    produzido_real = c3.number_input("Produzido (real)", min_value=0.0, step=1.0, value=float(pr_v))

    c4, c5 = st.columns(2)
    vendido = c4.number_input("Vendido", min_value=0.0, step=1.0, value=float(vend_v))
    desperdicio = c5.number_input("Desperdício", min_value=0.0, step=1.0, value=float(desp_v))

    obs = st.text_input("Observações", value=obs_v)

    if st.button("Salvar lançamento"):
        try:
            qexec("""
                INSERT INTO movimentos(
                    data, filial_id, product_id,
                    estoque, produzido_planejado, produzido_real, vendido, desperdicio, observacoes
                ) VALUES (
                    :data, :filial_id, :product_id,
                    :estoque, :pp, :pr, :vendido, :desp, :obs
                )
                ON CONFLICT (data, filial_id, product_id) DO UPDATE SET
                    estoque = EXCLUDED.estoque,
                    produzido_planejado = EXCLUDED.produzido_planejado,
                    produzido_real = EXCLUDED.produzido_real,
                    vendido = EXCLUDED.vendido,
                    desperdicio = EXCLUDED.desperdicio,
                    observacoes = EXCLUDED.observacoes;
            """, {
                "data": d,
                "filial_id": filial_id,
                "product_id": product_id,
                "estoque": float(estoque),
                "pp": float(produzido_planejado),
                "pr": float(produzido_real),
                "vendido": float(vendido),
                "desp": float(desperdicio),
                "obs": obs,
            })
            st.success("Lançamento salvo!")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")
