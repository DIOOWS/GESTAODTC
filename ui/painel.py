from datetime import date, timedelta

def _one(qdf, sql, params):
    df = qdf(sql, params)
    if df is None or df.empty:
        return 0
    v = df.iloc[0, 0]
    return int(v or 0)

def _sum_range(qdf, d1, d2):
    vendido = _one(qdf, """
        SELECT COALESCE(SUM(vendido),0) FROM movimentos
        WHERE data BETWEEN :d1 AND :d2;
    """, {"d1": d1, "d2": d2})

    produzido = _one(qdf, """
        SELECT COALESCE(SUM(produzido_real),0) FROM movimentos
        WHERE data BETWEEN :d1 AND :d2;
    """, {"d1": d1, "d2": d2})

    desperdicio = _one(qdf, """
        SELECT COALESCE(SUM(desperdicio),0) FROM movimentos
        WHERE data BETWEEN :d1 AND :d2;
    """, {"d1": d1, "d2": d2})

    estoque = _one(qdf, """
        SELECT COALESCE(SUM(estoque),0) FROM movimentos
        WHERE data BETWEEN :d1 AND :d2;
    """, {"d1": d1, "d2": d2})

    return vendido, produzido, desperdicio, estoque

def _bloco(st, titulo, vals):
    vendido, produzido, desperdicio, estoque = vals
    st.subheader(titulo)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Vendas", vendido)
    c2.metric("Produzido (real)", produzido)
    c3.metric("Desperdício", desperdicio)
    c4.metric("Estoque (soma)", estoque)

def render(st, qdf):
    st.header("Painel")

    hoje = date.today()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    inicio_mes = hoje.replace(day=1)

    _bloco(st, "Hoje", _sum_range(qdf, hoje, hoje))
    _bloco(st, "Semana (segunda → hoje)", _sum_range(qdf, inicio_semana, hoje))
    _bloco(st, "Mês (1º dia → hoje)", _sum_range(qdf, inicio_mes, hoje))

    st.caption("Totais atualizam conforme você lança movimentos (manual, WhatsApp ou Excel).")
