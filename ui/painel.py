from datetime import date, timedelta


def render(st, qdf):
    st.header("Painel (Geral)")

    hoje = date.today()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    inicio_mes = hoje.replace(day=1)

    def resumo_registros(dt_ini, dt_fim):
        return qdf("""
            SELECT
              SUM(COALESCE(vendido,0))      AS vendido,
              SUM(COALESCE(produzido,0))    AS produzido,
              SUM(COALESCE(desperdicio,0))  AS desperdicio,
              SUM(COALESCE(estoque,0))      AS estoque
            FROM registros_diarios
            WHERE data BETWEEN :i AND :f;
        """, {"i": dt_ini, "f": dt_fim})

    def resumo_transferencias(dt_ini, dt_fim):
        return qdf("""
            SELECT SUM(COALESCE(quantidade,0)) AS transferido
            FROM transferencias
            WHERE data BETWEEN :i AND :f;
        """, {"i": dt_ini, "f": dt_fim})

    def bloco(titulo, dt_ini, dt_fim):
        r = resumo_registros(dt_ini, dt_fim)
        t = resumo_transferencias(dt_ini, dt_fim)

        vendido = float(r["vendido"].iloc[0] or 0)
        produzido = float(r["produzido"].iloc[0] or 0)
        desperdicio = float(r["desperdicio"].iloc[0] or 0)
        estoque = float(r["estoque"].iloc[0] or 0)
        transferido = float(t["transferido"].iloc[0] or 0)

        st.subheader(titulo)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Vendas", vendido)
        c2.metric("Produzido (real)", produzido)
        c3.metric("Desperdício", desperdicio)
        c4.metric("Estoque (soma)", estoque)
        c5.metric("Transferido", transferido)

    bloco("Hoje", hoje, hoje)
    bloco("Semana (segunda → hoje)", inicio_semana, hoje)
    bloco("Mês (1º dia → hoje)", inicio_mes, hoje)

    st.caption("Produção planejada fica em Lançamentos. Transferido soma a tabela de transferências.")
