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


def _sum_range(qdf, d1, d2):
    vendido = _one(qdf, """
        SELECT COALESCE(SUM(vendido),0) FROM movimentacoes
        WHERE dia BETWEEN :d1 AND :d2;
    """, {"d1": d1, "d2": d2})

    prod_real = _one(qdf, """
        SELECT COALESCE(SUM(produzido_real),0) FROM movimentacoes
        WHERE dia BETWEEN :d1 AND :d2;
    """, {"d1": d1, "d2": d2})

    desperdicio = _one(qdf, """
        SELECT COALESCE(SUM(desperdicio),0) FROM movimentacoes
        WHERE dia BETWEEN :d1 AND :d2;
    """, {"d1": d1, "d2": d2})

    transferido = _one(qdf, """
        SELECT COALESCE(SUM(quantidade),0) FROM transferencias
        WHERE dia BETWEEN :d1 AND :d2;
    """, {"d1": d1, "d2": d2})

    return {"vendido": vendido, "prod_real": prod_real, "desperdicio": desperdicio, "transferido": transferido}


def _bloco(st, titulo, k):
    st.subheader(titulo)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Vendas", int(round(_to_num(k["vendido"]))))
    c2.metric("Produzido (real)", int(round(_to_num(k["prod_real"]))))
    c3.metric("Desperdício", int(round(_to_num(k["desperdicio"]))))
    c4.metric("Transferido", int(round(_to_num(k["transferido"]))))


def render(st, qdf):
    st.header("Painel")

    hoje = date.today()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    inicio_mes = hoje.replace(day=1)

    _bloco(st, "Hoje", _sum_range(qdf, hoje, hoje))
    _bloco(st, "Semana (segunda → hoje)", _sum_range(qdf, inicio_semana, hoje))
    _bloco(st, "Mês (1º dia → hoje)", _sum_range(qdf, inicio_mes, hoje))

    st.caption("Totais atualizam conforme você lança movimentos e transferências.")
