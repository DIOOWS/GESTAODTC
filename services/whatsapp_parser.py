import re
from dataclasses import dataclass

@dataclass
class Item:
    categoria: str
    produto: str
    quantidade: float

def normalizar(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s.upper()

def parse_whatsapp(texto: str):
    """
    Aceita textos no estilo:
      BOLOS CASEIROS
      AIPIM 8
      LARANJA 6

      BOLO RETANGULAR
      BRIGADEIRO: 4
      LEITE NINHO 2

    Regras:
      - Linha só com letras vira CATEGORIA
      - Linha com "nome + número" vira item
    """
    linhas = (texto or "").splitlines()
    categoria_atual = ""
    itens = []

    for ln in linhas:
        raw = ln.strip()
        if not raw:
            continue

        # remove bullets
        raw = raw.lstrip("-•* ").strip()
        up = normalizar(raw)

        # categoria: linha sem número e com poucas palavras? (aqui: sem dígitos)
        if not re.search(r"\d", up):
            # Ex: "BOLO RETANGULAR", "ROCÂMBOLE"
            categoria_atual = up
            continue

        # captura "produto ... numero"
        m = re.search(r"^(.*?)[\s:]+(\d+(?:[.,]\d+)?)\s*$", up)
        if not m:
            continue

        prod = normalizar(m.group(1))
        qtd = float(m.group(2).replace(",", "."))
        if not prod:
            continue

        itens.append(Item(categoria=categoria_atual or "(SEM)", produto=prod, quantidade=qtd))

    return itens
