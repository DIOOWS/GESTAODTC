import pandas as pd

def _col(df, nomes_possiveis):
    cols = {c.strip().upper(): c for c in df.columns}
    for n in nomes_possiveis:
        if n in cols:
            return cols[n]
    return None

def render(st, qdf, qexec, garantir_produto):
    st.header("Importar Excel")

    st.caption("Objetivo: importar apenas CADASTRO (Categoria + Produto). Quantidades você lança depois.")

    up = st.file_uploader("Envie um Excel", type=["xlsx"])
    if not up:
        return

    try:
        df = pd.read_excel(up)
    except Exception as e:
        st.error(f"Erro lendo Excel: {e}")
        return

    col_prod = _col(df, ["PRODUTO", "PRODUTOS", "NOME", "ITEM"])
    col_cat = _col(df, ["CATEGORIA", "CATEGORIAS", "TIPO", "GRUPO"])

    if not col_prod or not col_cat:
        st.error("Planilha precisa ter colunas de Produto e Categoria. (Ex: PRODUTO e CATEGORIA)")
        st.write("Colunas detectadas:", list(df.columns))
        return

    df = df[[col_prod, col_cat]].copy()
    df.columns = ["PRODUTO", "CATEGORIA"]
    df["PRODUTO"] = df["PRODUTO"].astype(str).str.strip()
    df["CATEGORIA"] = df["CATEGORIA"].astype(str).str.strip()

    df = df[(df["PRODUTO"] != "") & (df["PRODUTO"].str.lower() != "nan")]

    st.dataframe(df.head(50), use_container_width=True, hide_index=True)

    if st.button("Importar cadastro"):
        total = 0
        for _, r in df.iterrows():
            garantir_produto(r["CATEGORIA"], r["PRODUTO"])
            total += 1

        st.success(f"OK! {total} produtos cadastrados/validados.")
        st.rerun()
