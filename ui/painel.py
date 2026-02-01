from datetime import date, timedelta

def _int(v):
    try:
        if v is None:
            return 0
        return int(float(v))
    except Exception:
        return 0

def _sum_range(qdf, d1, d2):
    # d1 e d2 inclusivos
    df = qdf("""
    SELECT
      COALESCE(SUM(vendido),0) AS vendido,
      COALESCE(SUM(produzido_real),0) AS produzido_real,
      COALESCE(SUM(desperdicio),0) AS desperdicio,
      COALESCE(SUM(estoque),0) AS estoque
    FROM movimentos
    WHERE dia BETWEEN :d1 AND :d2;
    """, {"d1": d1, "d2": d2})

    tf = qdf("""
    SELECT COALESCE(SUM(quantidade),0) AS transferido
    FROM transferencias
    WHERE dia BETWEEN :d1 AND :d2;
    """, {"d1": d1, "d2": d2})

    return {
        "vendido": _int(df["vendido"].iloc[0]),
        "produzido_real": _int(df["produzido_real"].iloc[0]),
        "desperdicio": _int(df["desperdicio"].iloc[0]),
        "estoque": _int(df["estoque"].iloc[0]),
        "transferido": _int(tf["transferido"].iloc[0]),
    }

def render(st, qdf):
    st.header("Painel")

    hoje = date.today()
    # Semana: segunda -> hoje
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    # Mês: dia 1 -> hoje
    inicio_mes = hoje.replace(day=1)

    st.subheader("Hoje")
    k = _sum_range(qdf, hoje, hoje)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Vendas", k["vendido"])
    c2.metric("Produzido (real)", k["produzido_real"])
    c3.metric("Desperdício", k["desperdicio"])
    c4.metric("Estoque (soma)", k["estoque"])
    c5.metric("Transferido", k["transferido"])

    st.subheader("Semana (segunda → hoje)")
    k = _sum_range(qdf, inicio_semana, hoje)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Vendas", k["vendido"])
    c2.metric("Produzido (real)", k["produzido_real"])
    c3.metric("Desperdício", k["desperdicio"])
    c4.metric("Estoque (soma)", k["estoque"])
    c5.metric("Transferido", k["transferido"])

    st.subheader("Mês (1º dia → hoje)")
    k = _sum_range(qdf, inicio_mes, hoje)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Vendas", k["vendido"])
    c2.metric("Produzido (real)", k["produzido_real"])
    c3.metric("Desperdício", k["desperdicio"])
    c4.metric("Estoque (soma)", k["estoque"])
    c5.metric("Transferido", k["transferido"])
