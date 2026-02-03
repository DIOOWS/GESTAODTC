import re
from unidecode import unidecode


def _norm(s: str) -> str:
    s = (s or "").strip()
    s = s.replace("\t", " ")
    s = re.sub(r"\s+", " ", s)
    # mantém acento para exibição, mas padroniza maiúscula
    return s.upper()


def parse_whatsapp_text(texto: str):
    """
    Aceita texto estilo:
    BOLO CASEIRO
    AIPIM CREMOSO 8
    PUDIM DE PÃO 6

    Se a linha NÃO termina em número => vira categoria atual.
    Se termina em número => vira item com (categoria, produto, quantidade)
    """
    if not texto:
        return []

    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    itens = []

    categoria_atual = "GERAL"

    for ln in linhas:
        l = ln.strip()

        # normaliza separadores comuns
        l = l.replace(":", " ")
        l = re.sub(r"\s+", " ", l)

        m = re.match(r"^(.*?)(\d+(?:[.,]\d+)?)\s*$", l)
        if not m:
            # categoria
            cat = _norm(l)
            # evita categorias tipo "ESSE É UM EXEMPLO..." se vier no texto
            if len(cat) >= 2:
                categoria_atual = cat
            continue

        produto_raw = m.group(1).strip()
        qtd_raw = m.group(2).replace(",", ".")

        try:
            qtd = float(qtd_raw)
        except Exception:
            continue

        produto = _norm(produto_raw)
        categoria = _norm(categoria_atual)

        if produto:
            itens.append({
                "categoria": categoria,
                "produto": produto,
                "quantidade": qtd
            })

    return itens
