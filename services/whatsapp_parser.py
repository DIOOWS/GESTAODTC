import re

def _clean(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s

def parse_whatsapp_text(texto: str):
    """
    Espera linhas tipo:
      BOLO RETANGULAR
      PRESTÍGIO 1
      LIMÃO: 2
      FERREIRO ROCHER - 1

    Regras:
    - Se a linha tem número no final, vira item
    - Categoria: última categoria vista (linha sem número)
    - Se não tiver categoria ainda: '(SEM)'
    """
    texto = (texto or "").replace("\r", "\n")
    linhas = [l.strip() for l in texto.split("\n") if l.strip()]

    itens = []
    categoria_atual = "(SEM)"

    # aceita "X 2", "X:2", "X - 2", "X = 2"
    pat = re.compile(r"^(.*?)(?:\s*[:=\-]\s*|\s+)(\d+(?:[.,]\d+)?)$")

    for ln in linhas:
        ln = _clean(ln)

        m = pat.match(ln)
        if not m:
            # categoria (linha sem número)
            categoria_atual = ln.upper()
            continue

        nome = _clean(m.group(1)).upper()
        qtd = float(m.group(2).replace(",", "."))

        # correção automática: remove duplicação "CATEGORIA - CATEGORIA - SABOR"
        if nome.startswith(categoria_atual + " - "):
            nome = nome[len(categoria_atual) + 3:].strip()

        itens.append({
            "categoria": categoria_atual.upper(),
            "produto": nome,
            "quantidade": qtd
        })

    return itens
