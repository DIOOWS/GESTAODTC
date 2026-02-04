from datetime import date
import pandas as pd
import streamlit as st


def _to_num(x):
    try:
        if x is None:
            return 0.0
        if isinstance(x, str):
            x = x.replace(",", ".").strip()
        return float(x)
    except Exception:
        return 0.0


def render(st, qdf, qexec, get_filial_id):
    st.header("Estoque (editável)")

    col1, col2 = st.columns(2)
    filial = col1.selectbox("Filial", ["AUSTIN", "QUEIMADOS"], index=0)
    d = col2.date_input("Data", value=date.today())

    filial_id = get_filial_id(filial)

    df = qdf("""
        SELECT
          p.id AS product_id,
          p.categoria,
          p.produto,
          COALESCE(m.estoque,0) AS estoque,
          COALESCE(m.produzido_planejado,0) AS produzido_planejado,
          COALESCE(m.produzido_real,0) AS produzido_real,
          COALESCE(m.vendido,0) AS vendido,
          COALESCE(m.desperdicio,0) AS desperdicio
        FROM products p
        LEFT JOIN movimentos m
          ON m.product_id = p.id
         AND m.filial_id = :f
         AND m.data = :d
        WHERE p.ativo = TRUE
        ORDER BY p.categoria, p.produto;
    """, {"f": filial_id, "d": d})

    st.caption("Edite os números e clique em **Salvar estoque do dia**.")

    edited = st.data_editor(
        df,
        width="stretch",
        hide_index=True,
        disabled=["product_id", "categoria", "produto"],
        column_config={
            "estoque": st.column_config.NumberColumn("estoque", step=1),
            "produzido_planejado": st.column_config.NumberColumn("produzido_planejado", step=1),
            "produzido_real": st.column_config.NumberColumn("produzido_real", step=1),
            "vendido": st.column_config.NumberColumn("vendido", step=1),
            "desperdicio": st.column_config.NumberColumn("desperdicio", step=1),
        },
        key="estoque_editor",
    )

    if st.button("Salvar estoque do dia"):
        try:
            for _, r in edited.iterrows():
                pid = int(r["product_id"])
                estoque = _to_num(r.get("estoque", 0))
                pp = _to_num(r.get("produzido_planejado", 0))
                pr = _to_num(r.get("produzido_real", 0))
                vendido = _to_num(r.get("vendido", 0))
                desp = _to_num(r.get("desperdicio", 0))

                qexec("""
                    INSERT INTO movimentos
                      (data, filial_id, product_id, estoque, produzido_planejado, produzido_real, vendido, desperdicio)
                    VALUES
                      (:data, :filial, :pid, :e, :pp, :pr, :v, :d)
                    ON CONFLICT (data, filial_id, product_id)
                    DO UPDATE SET
                      estoque = EXCLUDED.estoque,
                      produzido_planejado = EXCLUDED.produzido_planejado,
                      produzido_real = EXCLUDED.produzido_real,
                      vendido = EXCLUDED.vendido,
                      desperdicio = EXCLUDED.desperdicio;
                """, {
                    "data": d,
                    "filial": filial_id,
                    "pid": pid,
                    "e": estoque,
                    "pp": pp,
                    "pr": pr,
                    "v": vendido,
                    "d": desp
                })

            st.success("Salvo com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")
