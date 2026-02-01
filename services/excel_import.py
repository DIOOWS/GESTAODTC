import pandas as pd

def _up(s):
    return (str(s).strip().upper() if s is not None else "")

def load_products_from_excel(file) -> pd.DataFrame:
    df = pd.read_excel(file)
    cols = {c.strip().upper(): c for c in df.columns}

    if "PRODUTO" not in cols or "CATEGORIA" not in cols:
        raise ValueError("Planilha precisa ter colunas PRODUTO e CATEGORIA.")

    out = pd.DataFrame({
        "produto": df[cols["PRODUTO"]].map(_up),
        "categoria": df[cols["CATEGORIA"]].map(_up),
    })

    out = out[(out["produto"] != "")].copy()
    out["categoria"] = out["categoria"].replace({"": None})
    out = out.drop_duplicates(subset=["produto","categoria"])
    return out
