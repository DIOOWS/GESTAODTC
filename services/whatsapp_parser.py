import re
import unicodedata


def _clean(s: str) -> str:
    if not s:
        return ""
    s = "".join(
        c for c in unicodedata.normalize("NFKD", s)
        if not unicodedata.combining(c)
    )
    s = s.replace("\t", " ").replace("–", "-").replace("—", "-")
    s = re.sub(r"\s+", " ", s).strip()
    return s.upper()


NUM_FIM = re.compile(r"^(.*?)(?:\s*[:=\-]\s*|\s+)(\d+(?:[.,]\d+)?)\s*$")


def parse_whatsapp_text(texto: str):
    """
    Converte texto do WhatsApp em lista de dict:
    [
      {categoria, produto, quantidade}
    ]
    """
    linhas = texto.splitlines()
    categoria_atual = "(SEM)"
    itens = []

    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue

        linha = _clean(linha)
        m = NUM_FIM.match(linha)

        # se NÃO termina com número → é categoria
        if not m:
            categoria_atual = linha
            continue

        produto = _clean(m.group(1))
        qtd = float(m.group(2).replace(",", "."))

        itens.append({
            "categoria": categoria_atual,
            "produto": produto,
            "quantidade": qtd
        })

    return itens
