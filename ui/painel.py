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

def _pick_date_col(qdf, table_name: str):
    """
    Descobre qual coluna de data existe na tabela (day/dia/data).
    """
    cols = qdf(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name=:t;
        """,
        {"t": table_name},
    )["column_name"].tolist()

    # prioridade
    for c in ("day", "dia", "data"):
        if c in cols:
            return c

    raise RuntimeError(
        f"Não achei coluna de data em '{table_name}'. Colunas encontradas: {cols}"
    )

def _sum_range(qdf, d1, d2):
    mov_date_col = _pick_date_col(qdf, "movimentos")
    trf_date_col = _pick_date_col(qdf, "transferencias")

    vendido = _one(qdf, f"""
        SELECT COALESCE(SUM(vendido),0) AS vendido
        FROM movimentos
        WHERE {mov_date_col} BETWEEN :d1 AND :d2;
    """, {"d1": d1, "d2": d2})

    produzido_real = _one(qdf, f"""
        SELECT COALESCE(SUM(produzido_real),0) AS produzido_real
        FROM movimentos
        WHERE {mov_date_col} BETWEEN :d1 AND :d2;
    """, {"d1": d1, "d2": d2})

    desperdicio = _one(qdf, f"""
        SELECT COALESCE(SUM(desperdicio),0) AS desperdicio
        FROM movimentos
        WHERE {mov_date_col} BETWEEN :d1 AND :d2;
    """, {"d1": d1, "d2": d2})

    estoque_soma = _one(qdf, f"""
        SELECT COALESCE(SUM(estoque),0) AS estoque
        FROM movimentos
        WHERE {mov_date_col} BETWEEN :d1 AND :d2;
    """, {"d1": d1, "d2": d2})

    transferido = _one(qdf, f"""
        SELECT COALESCE(SUM(quantidade),0) AS transferido
        FROM transferencias
        WHERE {trf_date_col} BETWEEN :d1 AND :d2;
    """, {"d1": d1, "d2": d2})

    return {
        "vendido": vendido,
        "produzido_real": produzido_real,
        "desperdicio": desperdicio,
        "estoque_soma": estoque_soma,
        "transferido": transferido,
    }

def _bloco(st, titulo, k):
    st.subheader(titulo)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Vendas", int(round(_to_num(k["vendido"]))))
    c2.metric("Produzido (real)", int(round(_to_num(k["produzido_real"]))))
    c3.metric("Desperdício", int(round(_to_num(k["desperdicio"]))))
    c4.metric("Estoque (soma)", int(round(_to_num(k["estoque_soma"]))))
    c5.metric("Transferido", int(round(_to_num(k["transferido"]))))

def render(st, qdf):
    st.header("Painel")

    hoje = date.today()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    inicio_mes = hoje.replace(day=1)

    _bloco(st, "Hoje", _sum_range(qdf, hoje, hoje))
    _bloco(st, "Semana (segunda → hoje)", _sum_range(qdf, inicio_semana, hoje))
    _bloco(st, "Mês (1º dia → hoje)", _sum_range(qdf, inicio_mes, hoje))

    st.caption("Totais atualizam conforme você lança Movimentos e Transferências.")
