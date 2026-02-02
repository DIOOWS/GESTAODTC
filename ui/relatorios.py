from datetime import date
import io
import pandas as pd

def render(st, qdf):
    st.header("Relatórios")

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        d1 = st.date_input("De", value=date.today().replace(day=1), key="rel_de")
    with c2:
        d2 = st.date_input("Até", value=date.today(), key="rel_ate")
    with c3:
        st.caption("Dica: o relatório já soma tudo que você lançou em Movimentos e Transferências.")

    # filtros
    filiais = qdf("SELECT id, nome FROM filiais ORDER BY nome;")
    categorias = qdf("SELECT DISTINCT categoria FROM products ORDER BY categoria;")

    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        filial_nome = st.selectbox("Filial (opcional)", ["(Todas)"] + filiais["nome"].tolist(), key="rel_filial")
    with fcol2:
        categoria = st.selectbox("Categoria (opcional)", ["(Todas)"] + categorias["categoria"].tolist(), key="rel_cat")
    with fcol3:
        mostrar_zeros = st.checkbox("Mostrar linhas zeradas", value=False, key="rel_zero")

    params = {"d1": d1, "d2": d2}

    filtro_filial = ""
    if filial_nome != "(Todas)":
        filtro_filial = " AND f.nome = :filial_nome "
        params["filial_nome"] = filial_nome

    filtro_cat = ""
    if categoria != "(Todas)":
        filtro_cat = " AND p.categoria = :cat "
        params["cat"] = categoria

    df_mov = qdf(f"""
        SELECT
          m.data,
          f.nome AS filial,
          p.categoria,
          p.produto,
          COALESCE(m.estoque,0) AS estoque,
          COALESCE(m.produzido_planejado,0) AS produzido_planejado,
          COALESCE(m.produzido_real,0) AS produzido_real,
          COALESCE(m.vendido,0) AS vendido,
          COALESCE(m.desperdicio,0) AS desperdicio
        FROM movimentos m
        JOIN filiais f ON f.id = m.filial_id
        JOIN products p ON p.id = m.product_id
        WHERE m.data BETWEEN :d1 AND :d2
          {filtro_filial}
          {filtro_cat}
        ORDER BY m.data DESC, f.nome, p.categoria, p.produto;
    """, params)

    df_trf = qdf(f"""
        SELECT
          t.data,
          f1.nome AS de_filial,
          f2.nome AS para_filial,
          p.categoria,
          p.produto,
          COALESCE(t.quantidade,0) AS quantidade
        FROM transferencias t
        JOIN filiais f1 ON f1.id = t.de_filial_id
        JOIN filiais f2 ON f2.id = t.para_filial_id
        JOIN products p ON p.id = t.product_id
        WHERE t.data BETWEEN :d1 AND :d2
          {"" if filial_nome == "(Todas)" else " AND (:filial_nome IN (f1.nome, f2.nome)) "}
          {filtro_cat}
        ORDER BY t.data DESC, f1.nome, f2.nome, p.categoria, p.produto;
    """, params)

    # opção de esconder linhas zeradas (no df_mov)
    if not df_mov.empty and not mostrar_zeros:
        df_mov = df_mov[
            (df_mov["estoque"] != 0) |
            (df_mov["produzido_planejado"] != 0) |
            (df_mov["produzido_real"] != 0) |
            (df_mov["vendido"] != 0) |
            (df_mov["desperdicio"] != 0)
        ]

    st.subheader("Movimentos (estoque / produção / vendas / desperdício)")
    if df_mov.empty:
        st.info("Nenhum movimento no período com esses filtros.")
    else:
        st.dataframe(df_mov, use_container_width=True, hide_index=True)

        # Totais
        tot = df_mov[["estoque","produzido_planejado","produzido_real","vendido","desperdicio"]].sum(numeric_only=True)
        t1, t2, t3, t4, t5 = st.columns(5)
        t1.metric("Estoque (soma)", int(round(float(tot["estoque"]))))
        t2.metric("Produz. planejada", int(round(float(tot["produzido_planejado"]))))
        t3.metric("Produz. real", int(round(float(tot["produzido_real"]))))
        t4.metric("Vendido", int(round(float(tot["vendido"]))))
        t5.metric("Desperdício", int(round(float(tot["desperdicio"]))))

    st.divider()

    st.subheader("Transferências (Austin ⇄ Queimados)")
    if df_trf.empty:
        st.info("Nenhuma transferência no período com esses filtros.")
    else:
        st.dataframe(df_trf, use_container_width=True, hide_index=True)
        st.metric("Total transferido (soma)", int(round(float(df_trf["quantidade"].sum()))))

    st.divider()
    st.subheader("Exportar Excel")

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_mov.to_excel(writer, index=False, sheet_name="Movimentos")
        df_trf.to_excel(writer, index=False, sheet_name="Transferencias")

    st.download_button(
        "Baixar Excel do período",
        data=buffer.getvalue(),
        file_name=f"relatorio_{d1}_a_{d2}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
