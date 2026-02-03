# ui/lancamentos.py
from datetime import date
import pandas as pd


def _to_float(x):
    try:
        if x is None:
            return 0.0
        if isinstance(x, float) and pd.isna(x):
            return 0.0
        return float(x)
    except Exception:
        return 0.0


def render(st, qdf, qexec, garantir_produto, get_filial_id):
    st.header("Lançamentos (manual)")

    col1, col2 = st.columns(2)
    filial = col1.selectbox("Filial", ["AUSTIN", "QUEIMADOS"], index=0)
    d = col2.date_input("Data", value=date.today())
    filial_id = get_filial_id(filial)

    st.divider()

    # Seleção do produto (cadastro)
    produtos = qdf("""
        SELECT id, categoria, produto
        FROM products
        WHERE ativo = TRUE
        ORDER BY categoria, produto;
    """)

    if produtos.empty:
        st.warning("Nenhum produto cadastrado. Cadastre em **Produtos** ou use **Importar Excel**.")
        st.stop()

    # Label bonito
    produtos["label"] = produtos["categoria"].astype(str) + " — " + produtos["produto"].astype(str)
    escolhido = st.selectbox("Produto", produtos["label"].tolist(), index=0)
    row = produtos.loc[produtos["label"] == escolhido].iloc[0]
    product_id = int(row["id"])

    # Carrega valores atuais do dia/filial/produto (se existir)
    atual = qdf("""
        SELECT estoque, produzido_planejado, produzido_real, vendido, desperdicio, observacoes
        FROM movimentos
        WHERE data = :d AND filial_id = :f AND product_id = :p
        LIMIT 1;
    """, {"d": d, "f": filial_id, "p": product_id})

    if atual.empty:
        base = {
            "estoque": 0.0,
            "produzido_planejado": 0.0,
            "produzido_real": 0.0,
            "vendido": 0.0,
            "desperdicio": 0.0,
            "observacoes": ""
        }
    else:
        r = atual.iloc[0].to_dict()
        base = {
            "estoque": _to_float(r.get("estoque")),
            "produzido_planejado": _to_float(r.get("produzido_planejado")),
            "produzido_real": _to_float(r.get("produzido_real")),
            "vendido": _to_float(r.get("vendido")),
            "desperdicio": _to_float(r.get("desperdicio")),
            "observacoes": r.get("observacoes") or ""
        }

    st.caption("Dica: você pode corrigir qualquer número aqui manualmente. Ao salvar, sobrescreve os valores do dia.")

    c1, c2, c3 = st.columns(3)
    estoque = c1.number_input("Estoque (contagem)", value=float(base["estoque"]), step=1.0)
    produzido_planejado = c2.number_input("Produzido (planejado)", value=float(base["produzido_planejado"]), step=1.0)
    produzido_real = c3.number_input("Produzido (real)", value=float(base["produzido_real"]), step=1.0)

    c4, c5, c6 = st.columns(3)
    vendido = c4.number_input("Vendido", value=float(base["vendido"]), step=1.0)
    desperdicio = c5.number_input("Desperdício", value=float(base["desperdicio"]), step=1.0)
    obs = c6.text_input("Obs", value=base["observacoes"])

    if st.button("Salvar lançamento"):
        qexec("""
            INSERT INTO movimentos
              (data, filial_id, product_id, estoque, produzido_planejado, produzido_real, vendido, desperdicio, observacoes)
            VALUES
              (:data, :filial_id, :product_id, :estoque, :pp, :pr, :vend, :desp, :obs)
            ON CONFLICT (data, filial_id, product_id)
            DO UPDATE SET
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
            "estoque": _to_float(estoque),
            "pp": _to_float(produzido_planejado),
            "pr": _to_float(produzido_real),
            "vend": _to_float(vendido),
            "desp": _to_float(desperdicio),
            "obs": (obs or None),
        })

        st.success("Lançamento salvo!")
        st.rerun()
