import re
from unidecode import unidecode
from difflib import get_close_matches

# Linha com quantidade no final (ex: "FERRERO ROCHER 2" / "TORTA G 10")
RE_ITEM = re.compile(r"^(?P<txt>.+?)\s+(?P<qtd>-?\d+)\s*$")

# Linha "categoria - produto 2"
RE_CAT_ITEM = re.compile(r"^(?P<cat>[^-]+?)\s*[-–]\s*(?P<prod>.+?)\s+(?P<qtd>-?\d+)\s*$")


def _norm(s: str) -> str:
    s = (s or "").strip().upper()
    s = unidecode(s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_whatsapp_text(texto: str):
    """
    Retorna lista de dicts: {categoria, produto, quantidade}
    Regras:
      - Categoria pode vir como cabeçalho (linha sem número no final)
      - Itens são linhas que terminam com número
      - Também aceita "CATEGORIA - PRODUTO 2"
    """
    if not texto:
        return []

    linhas = [l.strip() for l in texto.splitlines()]
    linhas = [l for l in linhas if l and not l.lower().startswith("http")]

    itens = []
    categoria_atual = ""

    for raw in linhas:
        # remove bullets comuns
        raw = raw.lstrip("-•* ").strip()

        if not raw:
            continue

        m2 = RE_CAT_ITEM.match(raw)
        if m2:
            cat = _norm(m2.group("cat"))
            prod = _norm(m2.group("prod"))
            qtd = int(m2.group("qtd"))
            if cat and prod:
                itens.append({"categoria": cat, "produto": prod, "quantidade": qtd})
            continue

        m = RE_ITEM.match(raw)
        if m:
            prod_txt = _norm(m.group("txt"))
            qtd = int(m.group("qtd"))
            if prod_txt:
                itens.append({"categoria": _norm(categoria_atual) or "SEM CATEGORIA", "produto": prod_txt, "quantidade": qtd})
            continue

        # Se não é item, trata como cabeçalho de categoria
        cat = _norm(raw)
        if cat:
            categoria_atual = cat

    return itens


def corrigir_itens_com_base_no_banco(itens, produtos_existentes):
    """
    produtos_existentes: lista de dicts {id, categoria, produto}
    Faz:
      - tenta bater (categoria, produto) exato por normalização
      - se não bater, tenta bater por "produto" dentro da mesma categoria (close match)
      - se ainda não bater, tenta bater por produto global (close match)
    Retorna itens corrigidos (categoria/produto padronizados) + flags.
    """
    if not itens:
        return []

    # mapas normalizados
    by_cat_prod = {}
    by_cat = {}
    all_prod_norm = {}

    for p in produtos_existentes:
        cat = _norm(p["categoria"])
        prod = _norm(p["produto"])
        by_cat_prod[(cat, prod)] = (p["categoria"], p["produto"])
        by_cat.setdefault(cat, []).append(prod)
        all_prod_norm[prod] = (p["categoria"], p["produto"])

    corrigidos = []
    for it in itens:
        cat_in = _norm(it.get("categoria"))
        prod_in = _norm(it.get("produto"))
        qtd = int(it.get("quantidade") or 0)

        ok = False
        cat_out, prod_out = it.get("categoria"), it.get("produto")

        # 1) match exato categoria+produto
        if (cat_in, prod_in) in by_cat_prod:
            cat_out, prod_out = by_cat_prod[(cat_in, prod_in)]
            ok = True
        else:
            # 2) close match dentro da categoria
            cand = by_cat.get(cat_in, [])
            cm = get_close_matches(prod_in, cand, n=1, cutoff=0.84)
            if cm:
                prod_match = cm[0]
                cat_out, prod_out = by_cat_prod.get((cat_in, prod_match), (cat_out, prod_out))
                ok = True
            else:
                # 3) close match global
                cm2 = get_close_matches(prod_in, list(all_prod_norm.keys()), n=1, cutoff=0.88)
                if cm2:
                    cat_out, prod_out = all_prod_norm[cm2[0]]
                    ok = True

        corrigidos.append({
            "categoria": (cat_out or "").strip().upper(),
            "produto": (prod_out or "").strip().upper(),
            "quantidade": qtd,
            "corrigido": bool(ok),
        })

    return corrigidos
