from datetime import date, timedelta
import pandas as pd


def _to_num(x):
    if x is None:
        return 0
    try:
        if isinstance(x, float) and pd.isna(x):
            return 0
    except Exception:
        pass
    try:
        return int(round(float(x)))
    except Exception:
        return 0


def _one(qdf, sql, params):
    df = qdf(sql, params)
    if df is None or df.empty:
        return 0
    return _to_num(df.iloc[0, 0])


def _sum_range(qdf, d1, d2):
    vendido = _one(qdf, "SELECT COALESCE(SUM(vendido),0) FROM movimentos WHERE data BETWEEN :d1 AND :d2;", {"d1": d1, "d2": d2})
    produzido_real = _one(qdf, "SELECT COALESCE(SUM(produzido_real),0) FROM movimentos WHERE data BETWEEN :d1 AND :d2;", {"d1": d1, "d2": d2})
    desperdicio = _one(qdf, "SELECT COALESCE(SUM(desperdicio),0) FROM movimentos WHERE data BETWEEN :d1 AND :d2;", {"d1": d1, "d2": d2})
    estoque = _one(qdf, "SELECT COALESCE(SUM(estoque),0) FROM movimentos WHERE data BETWEEN :d1 AND :d2;", {"d1": d1, "d2": d2})
    return {"vendido": vendido, "produzido_real": produzido_real, "desperdicio": desperdicio, "estoque": estoque}


def _bloco(st, titulo, k):
    st.subheader(titulo)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Vendas", _to_num(k["vendido"]))
    c2.metric("Produzido (real)", _to_num(k["produzido_real"]))
    c3.metric("Desperdício", _to_num(k["desperdicio"]))
    c4.metric("Estoque (contagem)", _to_num(k["estoque"]))


def render(st, qdf):
    st.header("Painel")

    hoje = date.today()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    inicio_mes = hoje.replace(day=1)

    _bloco(st, "Hoje", _sum_range(qdf, hoje, hoje))
    _bloco(st, "Semana (segunda → hoje)", _sum_range(qdf, inicio_semana, hoje))
    _bloco(st, "Mês (1º dia → hoje)", _sum_range(qdf, inicio_mes, hoje))

    st.caption("Totais atualizam conforme você lança movimentos.")
