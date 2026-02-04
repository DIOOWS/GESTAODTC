import re
from unidecode import unidecode
from difflib import get_close_matches

# item termina com quantidade (último token numérico)
RE_ITEM_QTD_END = re.compile(r"^(?P<txt>.+?)\s+(?P<qtd>-?\d+)\s*$")
# "CATEGORIA - PRODUTO 2" ou "CATEGORIA – PRODUTO 2"
RE_CAT_ITEM = re.compile(r"^(?P<cat>[^-–]+?)\s*[-–]\s*(?P<prod>.+?)\s+(?P<qtd>-?\d+)\s*$")

# remove coisas comuns que aparecem no texto do WhatsApp
RE_JUNK_PREFIX = re.compile(r"^(?:\d+\)|\d+\.)\s*")          # "1) " / "1. "
RE_WA_TIME = re.compile(r"^\[?\d{1,2}:\d{2}\]?\s*")          # "[08:31] "
RE_WA_DATE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}\s*-\s*")  # "02/02/2026 - "
RE_WA_SENDER = re.compile(r"^[^:]{1,30}:\s+")                # "Fulano: "
RE_ONLY_NUM = re.compile(r"^\d+$")


def _norm(s: str) -> str:
    s = (s or "").strip().upper()
    s = unidecode(s)
    s = re.sub(r"\s+", " ", s)
    # mantém letras/números/espaço (sem pontuação)
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _clean_line(raw: str) -> str:
    raw = (raw or "").strip()

    # remove bullets e numeradores
    raw = raw.lstrip("-•* ").strip()
    raw = RE_JUNK_PREFIX.sub("", raw)

    # remove prefixos típicos de export do WhatsApp
    raw = RE_WA_DATE.sub("", raw)
    raw = RE_WA_TIME.sub("", raw)
    raw = RE_WA_SENDER.sub("", raw)

    # remove "R$" etc
    raw = raw.replace("R$", " ").replace("RS", " ")
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw


def parse_whatsapp_text(texto: str):
    """
    Retorna itens [{categoria, produto, quantidade}]
    - Categoria pode vir como cabeçalho (linha sem número final)
    - Item é linha com quantidade no final
    - Aceita "CATEGORIA - PRODUTO 2"
    """
    if not texto:
        return []

    linhas = [l for l in texto.splitlines()]
    linhas = [_clean_line(l) for l in linhas]
    linhas = [l for l in linhas if l and not l.lower().startswith("http")]

    itens = []
    categoria_atual = ""

    for raw in linhas:
        # ignora linhas que são só números
        if RE_ONLY_NUM.match(raw):
            continue

        # caso "CATEGORIA - PRODUTO 2"
        m2 = RE_CAT_ITEM.match(raw)
        if m2:
            cat = _norm(m2.group("cat"))
            prod = _norm(m2.group("prod"))
            qtd = int(m2.group("qtd"))
            if cat and prod:
                itens.append({"categoria": cat, "produto": prod, "quantidade": qtd})
            continue

        # item normal "PRODUTO 2"
        m = RE_ITEM_QTD_END.match(raw)
        if m:
            txt = _norm(m.group("txt"))
            qtd = int(m.group("qtd"))

            # Se "txt" ficou vazio, ignora
            if not txt:
                continue

            # Se a "categoria_atual" estiver vazia, cai em SEM CATEGORIA
            cat = _norm(categoria_atual) or "SEM CATEGORIA"
            itens.append({"categoria": cat, "produto": txt, "quantidade": qtd})
            continue

        # senão, é cabeçalho de categoria
        cat = _norm(raw)
        if cat:
            categoria_atual = cat

    return itens


def corrigir_itens_com_base_no_banco(itens, produtos_existentes):
    """
    produtos_existentes: lista de dicts {id, categoria, produto}
    Retorna itens com:
      - categoria/produto padronizados pro que já existe
      - product_id se achou match
      - corrigido True/False
    """
    if not itens:
        return []

    by_cat_prod = {}
    by_cat = {}
    all_prod_norm = {}
    prod_norm_to_id = {}

    for p in produtos_existentes:
        cat = _norm(p["categoria"])
        prod = _norm(p["produto"])
        by_cat_prod[(cat, prod)] = (p["id"], p["categoria"], p["produto"])
        by_cat.setdefault(cat, []).append(prod)
        all_prod_norm[prod] = (p["id"], p["categoria"], p["produto"])
        prod_norm_to_id[prod] = p["id"]

    corrigidos = []
    for it in itens:
        cat_in = _norm(it.get("categoria"))
        prod_in = _norm(it.get("produto"))
        qtd = int(it.get("quantidade") or 0)

        product_id = None
        cat_out = (it.get("categoria") or "").strip().upper()
        prod_out = (it.get("produto") or "").strip().upper()
        ok = False

        # 1) match exato categoria+produto
        if (cat_in, prod_in) in by_cat_prod:
            product_id, cat_out, prod_out = by_cat_prod[(cat_in, prod_in)]
            ok = True
        else:
            # 2) close match dentro da categoria
            cand = by_cat.get(cat_in, [])
            cm = get_close_matches(prod_in, cand, n=1, cutoff=0.84)
            if cm:
                pid, cat_out, prod_out = by_cat_prod[(cat_in, cm[0])]
                product_id = pid
                ok = True
            else:
                # 3) close match global (produto)
                cm2 = get_close_matches(prod_in, list(all_prod_norm.keys()), n=1, cutoff=0.88)
                if cm2:
                    pid, cat_out, prod_out = all_prod_norm[cm2[0]]
                    product_id = pid
                    ok = True

        corrigidos.append({
            "product_id": product_id,
            "categoria": (cat_out or "").strip().upper(),
            "produto": (prod_out or "").strip().upper(),
            "quantidade": qtd,
            "corrigido": bool(ok),
        })

    return corrigidos
