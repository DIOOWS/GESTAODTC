from datetime import date
import pandas as pd

def render(st, qdf, qexec, garantir_produto, get_filial_id):
    st.header("Lançamentos")

    filiais = qdf("SELECT nome FROM filiais ORDER BY nome;")["nome"].tolist()
    if not filiais:
        st.error("Sem filiais cadastradas.")
        return

    # Produtos ativos
    produtos = qdf("""
    SELECT p.id, COALESCE(c.nome,'(SEM)') AS categoria, p.nome AS produto
    FROM produtos p
    LEFT JOIN categorias c ON c.id = p.categoria_id
    WHERE p.ativo = TRUE
    ORDER BY c.nome NULLS LAST, p.nome;
    """)

    if produtos.empty:
        st.info("Cadastre produtos primeiro.")
        return

    st.caption("Use esta tela para lançar números (manual). Para lote, use Importar WhatsApp/Excel.")

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        dia = st.date_input("Data", value=date.today())
    with c2:
        filial_nome = st.selectbox("Filial", filiais)
        filial_id = get_filial_id(filial_nome)
    with c3:
        # Mostra "CATEGORIA | PRODUTO"
        produtos["label"] = produtos["categoria"].astype(str) + " | " + produtos["produto"].astype(str)
        label = st.selectbox("Produto", produtos["label"].tolist())
        pid = int(produtos.loc[produtos["label"] == label, "id"].iloc[0])

    st.subheader("Quantidades")
    a, b, c, d, e, f = st.columns(6)
    estoque = a.number_input("Estoque", min_value=0.0, step=1.0)
    prod_real = b.number_input("Produzido (real)", min_value=0.0, step=1.0)
    prod_plan = c.number_input("Produzido (planejado)", min_value=0.0, step=1.0)
    enviado = d.number_input("Enviado", min_value=0.0, step=1.0)
    vendido = e.number_input("Vendido", min_value=0.0, step=1.0)
    desperd = f.number_input("Desperdício", min_value=0.0, step=1.0)
    obs = st.text_input("Observações")

    if st.button("Salvar lançamento"):
        qexec("""
        INSERT INTO movimentos(dia, filial_id, produto_id, estoque, produzido_real, produzido_planejado, enviado, vendido, desperdicio, observacoes)
        VALUES (:dia, :fid, :pid, :est, :pr, :pp, :env, :ven, :des, :obs)
        ON CONFLICT (dia, filial_id, produto_id)
        DO UPDATE SET
          estoque=EXCLUDED.estoque,
          produzido_real=EXCLUDED.produzido_real,
          produzido_planejado=EXCLUDED.produzido_planejado,
          enviado=EXCLUDED.enviado,
          vendido=EXCLUDED.vendido,
          desperdicio=EXCLUDED.desperdicio,
          observacoes=EXCLUDED.observacoes;
        """, {
            "dia": dia, "fid": filial_id, "pid": pid,
            "est": estoque, "pr": prod_real, "pp": prod_plan,
            "env": enviado, "ven": vendido, "des": desperd,
            "obs": (obs.strip() or None)
        })
        st.success("Salvo!")
        st.rerun()

    st.divider()
    st.subheader("Lançamentos do dia (filial selecionada)")
    df = qdf("""
    SELECT
      m.id,
      m.dia,
      f.nome AS filial,
      COALESCE(c.nome,'(SEM)') AS categoria,
      p.nome AS produto,
      m.estoque,
      m.produzido_real,
      m.produzido_planejado,
      m.enviado,
      m.vendido,
      m.desperdicio,
      m.observacoes
    FROM movimentos m
    JOIN filiais f ON f.id=m.filial_id
    JOIN produtos p ON p.id=m.produto_id
    LEFT JOIN categorias c ON c.id=p.categoria_id
    WHERE m.dia=:dia AND m.filial_id=:fid
    ORDER BY c.nome NULLS LAST, p.nome;
    """, {"dia": dia, "fid": filial_id})

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.caption("Para excluir/editar em lote, use a aba ESTOQUE.")

def render_transferencias(st, qdf, qexec, garantir_produto, get_filial_id):
    st.header("Transferências entre filiais")

    filiais = qdf("SELECT nome FROM filiais ORDER BY nome;")["nome"].tolist()

    produtos = qdf("""
    SELECT p.id, COALESCE(c.nome,'(SEM)') AS categoria, p.nome AS produto
    FROM produtos p
    LEFT JOIN categorias c ON c.id = p.categoria_id
    WHERE p.ativo = TRUE
    ORDER BY c.nome NULLS LAST, p.nome;
    """)
    if produtos.empty:
        st.info("Cadastre produtos primeiro.")
        return

    produtos["label"] = produtos["categoria"].astype(str) + " | " + produtos["produto"].astype(str)

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        dia = st.date_input("Data", value=date.today())
    with c2:
        de_nome = st.selectbox("De", filiais, index=0)
        para_nome = st.selectbox("Para", filiais, index=min(1, len(filiais)-1))
    with c3:
        label = st.selectbox("Produto", produtos["label"].tolist())
        pid = int(produtos.loc[produtos["label"] == label, "id"].iloc[0])

    if de_nome == para_nome:
        st.warning("De e Para não podem ser iguais.")
        return

    qtd = st.number_input("Quantidade", min_value=0.0, step=1.0)
    obs = st.text_input("Observações (opcional)")

    if st.button("Salvar transferência"):
        qexec("""
        INSERT INTO transferencias(dia, produto_id, de_filial_id, para_filial_id, quantidade, observacoes)
        VALUES (:dia, :pid, :de, :para, :qtd, :obs);
        """, {
            "dia": dia,
            "pid": pid,
            "de": get_filial_id(de_nome),
            "para": get_filial_id(para_nome),
            "qtd": qtd,
            "obs": (obs.strip() or None)
        })
        st.success("OK!")
        st.rerun()

    st.divider()
    st.subheader("Transferências do dia")
    df = qdf("""
    SELECT
      t.id,
      t.dia,
      f1.nome AS de,
      f2.nome AS para,
      COALESCE(c.nome,'(SEM)') AS categoria,
      p.nome AS produto,
      t.quantidade,
      t.observacoes
    FROM transferencias t
    JOIN filiais f1 ON f1.id=t.de_filial_id
    JOIN filiais f2 ON f2.id=t.para_filial_id
    JOIN produtos p ON p.id=t.produto_id
    LEFT JOIN categorias c ON c.id=p.categoria_id
    WHERE t.dia=:dia
    ORDER BY f1.nome, f2.nome, c.nome NULLS LAST, p.nome;
    """, {"dia": dia})
    st.dataframe(df, use_container_width=True, hide_index=True)

    del_id = st.number_input("Excluir transferência (ID)", min_value=0, step=1)
    if st.button("Excluir transferência"):
        if int(del_id) > 0:
            qexec("DELETE FROM transferencias WHERE id=:id", {"id": int(del_id)})
            st.success("Excluída.")
            st.rerun()
