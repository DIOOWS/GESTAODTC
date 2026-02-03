from datetime import date
from sqlalchemy import text
import pandas as pd


def render(st, qdf, qexec, garantir_produto, get_filial_id):
    st.header("Transferências (Austin ⇄ Queimados)")

    c1, c2 = st.columns(2)
    d = c1.date_input("Data", value=date.today())
    sentido = c2.selectbox("Sentido", ["AUSTIN → QUEIMADOS", "QUEIMADOS → AUSTIN"], index=0)

    if sentido.startswith("AUSTIN"):
        de_nome, para_nome = "AUSTIN", "QUEIMADOS"
    else:
        de_nome, para_nome = "QUEIMADOS", "AUSTIN"

    st.caption("Isso registra a transferência e ajusta o estoque do dia nas duas filiais.")

    # Produto
    df_prod = qdf("""
        SELECT id, categoria, produto
        FROM products
        WHERE ativo = TRUE
        ORDER BY categoria, produto;
    """)
    if df_prod.empty:
        st.warning("Nenhum produto cadastrado ainda. Importe pelo Excel/WhatsApp primeiro.")
        return

    df_prod["label"] = df_prod["categoria"] + " — " + df_prod["produto"]
    label = st.selectbox("Produto", df_prod["label"].tolist())
    produto_id = int(df_prod.loc[df_prod["label"] == label, "id"].iloc[0])

    qtd = st.number_input("Quantidade transferida", min_value=0.0, step=1.0, value=0.0)
    obs = st.text_input("Observações (opcional)")

    if st.button("Salvar transferência"):
        de_id = get_filial_id(de_nome)
        para_id = get_filial_id(para_nome)

        try:
            # 1) registra a transferência
            qexec("""
                INSERT INTO transferencias (data, de_filial_id, para_filial_id, produto_id, quantidade, observacoes)
                VALUES (:data, :de, :para, :pid, :qtd, :obs);
            """, {"data": d, "de": de_id, "para": para_id, "pid": produto_id, "qtd": float(qtd), "obs": obs or None})

            # 2) ajusta estoque do dia (de: -qtd, para: +qtd)
            # UPSERT em movimentos: se não existe, cria com estoque = +/-qtd
            qexec("""
                INSERT INTO movimentos (data, filial_id, produto_id, estoque)
                VALUES (:data, :filial, :pid, :delta)
                ON CONFLICT (data, filial_id, produto_id)
                DO UPDATE SET estoque = COALESCE(movimentos.estoque,0) + EXCLUDED.estoque;
            """, {"data": d, "filial": de_id, "pid": produto_id, "delta": -float(qtd)})

            qexec("""
                INSERT INTO movimentos (data, filial_id, produto_id, estoque)
                VALUES (:data, :filial, :pid, :delta)
                ON CONFLICT (data, filial_id, produto_id)
                DO UPDATE SET estoque = COALESCE(movimentos.estoque,0) + EXCLUDED.estoque;
            """, {"data": d, "filial": para_id, "pid": produto_id, "delta": float(qtd)})

            st.success("Transferência salva e estoque ajustado ✅")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar transferência: {e}")

    st.divider()
    st.subheader("Histórico (últimos 50)")

    df_hist = qdf("""
        SELECT
          t.data,
          f1.nome AS de,
          f2.nome AS para,
          p.categoria,
          p.produto,
          t.quantidade,
          t.observacoes
        FROM transferencias t
        JOIN filiais f1 ON f1.id = t.de_filial_id
        JOIN filiais f2 ON f2.id = t.para_filial_id
        JOIN products p ON p.id = t.produto_id
        ORDER BY t.data DESC, t.id DESC
        LIMIT 50;
    """)
    st.dataframe(df_hist, use_container_width=True, hide_index=True)
