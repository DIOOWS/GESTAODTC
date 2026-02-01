import re
import unicodedata
from datetime import date
from typing import Optional, Dict

import pandas as pd


def to_num(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if not s:
        return None
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None


def norm_col(s: str) -> str:
    s = str(s or "").strip().upper()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"[^A-Z0-9 ]+", "", s)
    return s


def map_cols(df: pd.DataFrame) -> dict:
    m = {}
    for c in df.columns:
        m[norm_col(c)] = c
    return m


def get_col(m: dict, *candidatas: str):
    for cand in candidatas:
        key = norm_col(cand)
        if key in m:
            return m[key]
    return None


def garantir_produto(qexec, qdf, nome_produto: str, categoria: Optional[str] = None) -> int:
    nome = re.sub(r"\s+", " ", (nome_produto or "").strip()).upper()
    cat = re.sub(r"\s+", " ", (categoria or "").strip()).upper() if categoria else None

    qexec("""
        INSERT INTO produtos(nome, categoria, ativo)
        VALUES (:n, :c, TRUE)
        ON CONFLICT (nome)
        DO UPDATE SET categoria = COALESCE(EXCLUDED.categoria, produtos.categoria),
                      ativo = TRUE;
    """, {"n": nome, "c": cat})

    df = qdf("SELECT id FROM produtos WHERE nome = :n;", {"n": nome})
    return int(df["id"].iloc[0])


def importar_cadastro_produtos_do_relatorio(qexec, qdf, arquivo_xlsx) -> Dict:
    xls = pd.ExcelFile(arquivo_xlsx)
    processados = 0
    ignorados = 0

    for aba in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=aba)
        df = df.copy()
        df.columns = [str(c).strip().upper() for c in df.columns]

        if "PRODUTO" not in df.columns:
            continue

        col_cat = "CATEGORIA" if "CATEGORIA" in df.columns else None

        for _, row in df.iterrows():
            nome = row.get("PRODUTO")
            if nome is None:
                ignorados += 1
                continue

            nome = str(nome).strip()
            if not nome or nome.upper().startswith("TOTAL"):
                ignorados += 1
                continue

            categoria = None
            if col_cat:
                categoria = row.get(col_cat)
                categoria = str(categoria).strip() if categoria is not None and str(categoria).strip() else None

            garantir_produto(qexec, qdf, nome, categoria)
            processados += 1

    total_no_banco = int(qdf("SELECT COUNT(*) AS n FROM produtos;")["n"].iloc[0])
    return {"abas": len(xls.sheet_names), "processados": processados, "ignorados": ignorados, "total": total_no_banco}


def importar_tortas_modelo_novo(qexec, qdf, arquivo_xlsx) -> Dict:
    """
    Torta entra APENAS como cadastro de produto.
    Não cria produção, não cria registro diário.
    """
    xls = pd.ExcelFile(arquivo_xlsx)
    aba = xls.sheet_names[0]

    df = None
    for header_row in [0, 1, 2]:
        temp = pd.read_excel(xls, sheet_name=aba, header=header_row)
        temp = temp.copy()
        temp.columns = [str(c).strip() for c in temp.columns]
        cols_map = map_cols(temp)
        col_produto = get_col(cols_map, "PRODUTO")
        col_categoria = get_col(cols_map, "CATEGORIA")
        if col_produto and col_categoria:
            df = temp
            break

    if df is None:
        raise ValueError("Não encontrei as colunas PRODUTO e CATEGORIA. Verifique o cabeçalho da planilha de tortas.")

    cols_map = map_cols(df)
    col_produto = get_col(cols_map, "PRODUTO")
    col_categoria = get_col(cols_map, "CATEGORIA")
    if not col_produto or not col_categoria:
        raise ValueError("Planilha de tortas precisa ter colunas PRODUTO e CATEGORIA.")

    processados = 0
    ignorados = 0

    for _, row in df.iterrows():
        prod = row.get(col_produto)
        cat = row.get(col_categoria)
        if prod is None or cat is None:
            ignorados += 1
            continue

        prod = str(prod).strip()
        cat = str(cat).strip()
        if not prod or prod.upper().startswith("TOTAL"):
            ignorados += 1
            continue

        nome_produto = f"{prod} - {cat}".upper()
        garantir_produto(qexec, qdf, nome_produto, "TORTAS")
        processados += 1

    return {"aba": aba, "produtos_cadastrados": processados, "ignorados": ignorados}
