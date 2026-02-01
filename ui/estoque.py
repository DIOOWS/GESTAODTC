from datetime import date
import pandas as pd

def render(st, qdf, qexec, garantir_produto, get_filial_id):
    st.header("Estoque (edição rápida)")

    filiais = qdf("SELECT nome FROM filiais ORDER BY nome;")["nome"].tolist()
    if not filiais:
        st.error("Sem filiais.")
        return

    c1, c2 = st.columns([1, 1])
    with c1:
        dia = st.date_input("Data", value=date.today())
    with c2:
        filial_nome = st.selectbox("Filial", filiais)
        filial_id = get_filial_id(filial_nome)

    df = qdf("""
    SELECT
      m.id,
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
    JOIN produtos p ON p.id=m.produto_id
    LEFT JOIN categorias c ON c.id=p.categoria_id
    WHERE m.dia=:dia AND m.filial_id=:fid
    ORDER BY c.nome NULLS LAST, p.nome;
    """, {"dia": dia, "fid": filial_id})

    st.caption("Edite direto na tabela e clique em **Salvar alterações**. Para apagar, marque a coluna Excluir.")

    if df.empty:
        st.info("Nenhum lançamento nesse dia/filial.")
        return

    df["Excluir"] = False
    edit = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "categoria": st.column_config.TextColumn("Categoria", disabled=True),
            "produto": st.column_config.TextColumn("Produto", disabled=True),
        },
        disabled=["categoria", "produto"]
    )

    if st.button("Salvar alterações"):
        # Atualiza
        for _, row in edit.iterrows():
            rid = int(row["id"])
            if bool(row.get("Excluir", False)):
                continue

            qexec("""
            UPDATE movimentos
               SET estoque=:e,
                   produzido_real=:pr,
                   produzido_planejado=:pp,
                   enviado=:env,
                   vendido=:ven,
                   desperdicio=:des,
                   observacoes=:obs
             WHERE id=:id;
            """, {
                "id": rid,
                "e": float(row["estoque"] or 0),
                "pr": float(row["produzido_real"] or 0),
                "pp": float(row["produzido_planejado"] or 0),
                "env": float(row["enviado"] or 0),
                "ven": float(row["vendido"] or 0),
                "des": float(row["desperdicio"] or 0),
                "obs": (str(row["observacoes"]).strip() if row["observacoes"] not in [None, "None"] else None),
            })

        # Exclui marcados
        ids_del = [int(r["id"]) for _, r in edit.iterrows() if bool(r.get("Excluir", False))]
        if ids_del:
            qexec("DELETE FROM movimentos WHERE id = ANY(:ids);", {"ids": ids_del})

        st.success("OK! Alterações salvas.")
        st.rerun()
