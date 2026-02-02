from datetime import date
import pandas as pd

def render(st, qdf, qexec):
    st.header("Estoque")

    col1, col2 = st.columns(2)
    filial = col1.selectbox("Filial", ["AUSTIN", "QUEIMADOS"], index=0)
    d = col2.date_input("Data", value=date.today())

    # pega filial_id
    df_f = qdf("SELECT id FROM filiais WHERE nome=:n;", {"n": filial.strip().upper()})
    if df_f.empty:
        st.error("Filial não encontrada no banco.")
        return
    filial_id = int(df_f.iloc[0]["id"])

    # lista estoque do dia por filial
    df = qdf("""
        SELECT
          p.id AS product_id,
          p.categoria,
          p.produto,
          COALESCE(m.estoque, 0) AS estoque
        FROM products p
        LEFT JOIN movimentos m
          ON m.produto_id = p.id
         AND m.filial_id = :f
         AND m.data = :d
        WHERE p.ativo = TRUE
        ORDER BY p.categoria, p.produto;
    """, {"f": filial_id, "d": d})

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Ajustar estoque manualmente")

    # edição simples via select + input
    if not df.empty:
        opcoes = (df["categoria"] + " | " + df["produto"]).tolist()
        escolha = st.selectbox("Produto", opcoes, index=0)
        idx = opcoes.index(escolha)
        pid = int(df.iloc[idx]["product_id"])

        novo = st.number_input("Novo estoque", min_value=0.0, step=1.0, value=float(df.iloc[idx]["estoque"]))

        if st.button("Salvar ajuste"):
            try:
                qexec("""
                    INSERT INTO movimentos (data, filial_id, produto_id, estoque)
                    VALUES (:data, :filial, :pid, :qtd)
                    ON CONFLICT (data, filial_id, produto_id)
                    DO UPDATE SET estoque = EXCLUDED.estoque;
                """, {"data": d, "filial": filial_id, "pid": pid, "qtd": float(novo)})

                st.success("Estoque ajustado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao salvar ajuste: {e}")
