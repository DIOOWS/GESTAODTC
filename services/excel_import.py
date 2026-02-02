import pandas as pd
from .helpers import norm

def _find_col(cols, needles):
    cols_u = {c: norm(str(c)) for c in cols}
    for c, cu in cols_u.items():
        for n in needles:
            if n in cu:
                return c
    return None

def import_produtos_from_excel(file, categoria_default="GERAL"):
    """
    Aceita planilhas com:
      - colunas tipo: PRODUTO / CATEGORIA
      - ou NOME / CATEGORIA
      - ou só 1 coluna (vira PRODUTO, categoria = default)
    Retorna lista de dicts: {categoria, produto}
    """
    df = pd.read_excel(file)
    df.columns = [str(c).strip() for c in df.columns]

    col_prod = _find_col(df.columns, ["PRODUTO", "NOME", "ITEM"])
    col_cat  = _find_col(df.columns, ["CATEGORIA", "GRUPO", "TIPO"])

    itens = []
    if col_prod is None:
        # se não achou, tenta usar a primeira coluna
        col_prod = df.columns[0]

    for _, row in df.iterrows():
        prod = norm(str(row.get(col_prod, "") or ""))
        if not prod or prod == "NAN":
            continue

        cat = categoria_default
        if col_cat is not None:
            cat_raw = row.get(col_cat, "")
            cat = norm(str(cat_raw or "")) or categoria_default

        itens.append({"categoria": cat, "produto": prod})

    # remove duplicados
    seen = set()
    out = []
    for it in itens:
        k = (it["categoria"], it["produto"])
        if k not in seen:
            seen.add(k)
            out.append(it)
    return out
