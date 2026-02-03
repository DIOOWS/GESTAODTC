import pandas as pd


def _find_col(cols, candidates):
    cols_u = {c.upper(): c for c in cols}
    for cand in candidates:
        if cand.upper() in cols_u:
            return cols_u[cand.upper()]
    return None


def load_products_from_excel(file) -> pd.DataFrame:
    df = pd.read_excel(file)
    df.columns = [str(c).strip() for c in df.columns]

    c_prod = _find_col(df.columns, ["PRODUTO", "PRODUTOS", "NOME", "ITEM"])
    c_cat = _find_col(df.columns, ["CATEGORIA", "CATEGORIAS", "TIPO", "GRUPO"])

    if not c_prod or not c_cat:
        raise ValueError("Planilha precisa ter colunas PRODUTO e CATEGORIA (ou nomes equivalentes).")

    out = df[[c_cat, c_prod]].copy()
    out.columns = ["CATEGORIA", "PRODUTO"]
    out["CATEGORIA"] = out["CATEGORIA"].astype(str).str.strip().str.upper()
    out["PRODUTO"] = out["PRODUTO"].astype(str).str.strip().str.upper()
    out = out[(out["CATEGORIA"] != "") & (out["PRODUTO"] != "")]
    out = out.dropna()
    out = out.drop_duplicates()
    return out
