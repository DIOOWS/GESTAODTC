import re
from unidecode import unidecode


def _clean(s: str) -> str:
    s = (s or "").strip()
    s = s.replace("\u00a0", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _has_number(line: str) -> bool:
    return re.search(r"\d", line) is not None


def _is_header(line: str) -> bool:
    """
    Detecta categorias:
    - "*BRIOCHES*"
    - "BOLO RETANGULAR" (caps)
    - "Padaria" (linha curta sem número)
    """
    t = _clean(line)
    if not t:
        return False

    # Entre asteriscos
    if t.startswith("*") and t.endswith("*") and len(t) >= 3:
        return True

    # Se tiver número, não é header
    if _has_number(t):
        return False

    # Se for “quase tudo” maiúsculo
    letters = re.sub(r"[^A-Za-zÀ-ÿ]", "", t)
    if letters and letters.upper() == letters and len(letters) >= 4:
        return True

    # Linha curta sem número (ex: "Padaria")
    # (evita pegar frases longas como categoria)
    if len(t) <= 25:
        return True

    return False


def _normalize_category(line: str) -> str:
    t = _clean(line)
    if t.startswith("*") and t.endswith("*"):
        t = t[1:-1]
    t = _clean(t)
    return t.upper()


def _to_number(q: str) -> float:
    q = _clean(q).replace(",", ".")
    try:
        return float(q)
    except Exception:
        return 0.0


def _normalize_product_name(name: str) -> str:
    name = _clean(name)
    name = name.lstrip("-•").strip()
    name = name.rstrip(":").strip()
    return name.upper()


def parse_whatsapp_text(texto: str):
    """
    Retorna:
      { "categoria": "...", "produto": "...", "quantidade": 12.0 }

    Aceita:
      - "24 torrada temperada" (qtd no começo)
      - "torrada temperada 24" (qtd no fim)
    Mantém números finais no produto quando o número inicial já é a quantidade
    (ex: "3 broa de coco com 6" -> qtd=3, produto="BROA DE COCO COM 6")
    """
    texto = texto or ""
    linhas = texto.splitlines()

    itens = []
    categoria_atual = "(SEM)"

    rx_ini = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s+(.+?)\s*$")  # 24 pão...
    rx_fim = re.compile(r"^\s*(.+?)\s+(\d+(?:[.,]\d+)?)\s*$")  # pão... 24

    for raw in linhas:
        line = _clean(raw)
        if not line:
            continue

        # Categoria
        if _is_header(line):
            categoria_atual = _normalize_category(line)
            continue

        # Quantidade no início
        m = rx_ini.match(line)
        if m:
            qtd = _to_number(m.group(1))
            prod = _normalize_product_name(m.group(2))
            if qtd > 0 and prod:
                itens.append({"categoria": categoria_atual, "produto": prod, "quantidade": qtd})
            continue

        # Quantidade no fim (fallback)
        m = rx_fim.match(line)
        if m:
            prod = _normalize_product_name(m.group(1))
            qtd = _to_number(m.group(2))
            if qtd > 0 and prod:
                itens.append({"categoria": categoria_atual, "produto": prod, "quantidade": qtd})
            continue

        # Linha sem número: ignora (comentários soltos)
        continue

    return itens
