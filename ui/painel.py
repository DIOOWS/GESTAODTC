from datetime import date, timedelta
import pandas as pd


def _to_num(x):
    if x is None:
        return 0.0
    try:
        if isinstance(x, float) and pd.isna(x):
            return 0.0
    except Exception:
        pass
    try:
        return float(x)
    except Exception:
        return 0.0


def _one(qdf, sql, params):
    df = qdf(sql, params)
    if df is None or df.empty:
        return 0.0
    return _to_num(df.iloc[0, 0])


def _sum_range(qdf, d1, d2, filial_id=None):
    filtro = ""
    params = {"d1": d1, "d2": d2}
    if filial_id is not None:
        filtro = " AND filial_id = :f "
        params["f"] = filial_id

    vendido = _one(qdf, f"""
        SELECT COALESCE(SUM(vendido),0)
        FROM movimentos
        WHERE data BETWEEN :d1 AND :d2
        {filtro};
    """, params)

    produzido_real = _one(qdf, f"""
        SELECT COALESCE(SUM(produzido_real),0)
        FROM movimentos
        WHERE data BETWEEN :d1 AND :d2
        {filtro};
    """, params)

    desperdicio = _one(qdf, f"""
        SELECT COALESCE(SUM(desperdicio),0)
        FROM movimentos
        WHERE data BETWEEN :d1 AND :d2
        {filtro};
    """, params)

    return {
        "vendido": vendido,
        "produzido_real": produzido_real,
        "desperdicio": desperdicio,
    }


def _estoque_atual(qdf, ref_date, filial_id=None):
    """
    Estoque = CONTAGEM.
    Regra: pega a ÚLTIMA data disponível <= ref_date (por filial) e soma os estoques daquela data.
    - Se filial_id for definido: usa a última data dessa filial.
    - Se filial_id for None (todas): pega última data por filial e soma tudo.
    """

    if filial_id is not None:
        return _one(qdf, """
            SELECT COALESCE(SUM(m.estoque),0) AS estoque
            FROM movimentos m
            WHERE m.filial_id = :f
              AND m.data = (
                SELECT MAX(data) FROM movimentos
                WHERE filial_id = :f AND data <= :d
              );
        """, {"f": filial_id, "d": ref_date})

    # TODAS: última data por filial (cada filial pode ter data diferente)
    return _one(qdf, """
        WITH ult AS (
          SELECT filial_id, MAX(data) AS data
          FROM movimentos
          WHERE data <= :d
          GROUP BY filial_id
        )
        SELECT COALESCE(SUM(m.estoque),0) AS estoque
        FROM ult
        JOIN movimentos m
          ON m.filial_id = ult.filial_id
         AND m.data = ult.data;
    """, {"d": ref_date})


def _bloco(st, titulo, k, estoque_contagem):
    st.subheader(titulo)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Vendas", int(round(_to_num(k["vendido"]))))
    c2.metric("Produzido (real)", int(round(_to_num(k["produzido_real"]))))
    c3.metric("Desperdício", int(round(_to_num(k["desperdicio"]))))
    c4.metric("Estoque (contagem)", int(round(_to_num(estoque_contagem))))


def render(st, qdf, get_filial_id):
    st.header("Painel")

    col1, col2 = st.columns(2)
    filial = col1.selectbox("Filial", ["TODAS", "AUSTIN", "QUEIMADOS"], index=0)
    hoje = col2.date_input("Data de referência", value=date.today())

    filial_id = None
    if filial != "TODAS":
        filial_id = get_filial_id(filial)

    inicio_semana = hoje - timedelta(days=hoje.weekday())
    inicio_mes = hoje.replace(day=1)

    # Entradas/saídas do período
    k_hoje = _sum_range(qdf, hoje, hoje, filial_id)
    k_semana = _sum_range(qdf, inicio_semana, hoje, filial_id)
    k_mes = _sum_range(qdf, inicio_mes, hoje, filial_id)

    # Estoque (contagem) = última contagem disponível até a data (não soma por período)
    estoque_ref = _estoque_atual(qdf, hoje, filial_id)

    _bloco(st, "Hoje", k_hoje, estoque_ref)
    _bloco(st, "Semana (segunda → hoje)", k_semana, estoque_ref)
    _bloco(st, "Mês (1º dia → hoje)", k_mes, estoque_ref)

    st.caption("Obs: Estoque (contagem) mostra a última contagem disponível até a data selecionada (não é soma do período).")
