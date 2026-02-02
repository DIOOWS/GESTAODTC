import re
from dataclasses import dataclass
from typing import List
from .helpers import norm

# Regras:
# - Linha sem número -> vira CATEGORIA (se curta)
# - Linha com "NOME 10" ou "NOME: 10" -> ITEM
# - Tudo vira MAIÚSCULO

@dataclass
class Item:
    categoria: str
    produto: str
    quantidade: int

_num_re = re.compile(r"^(.*?)(?:\s*[:\-]\s*|\s+)(\d+)\s*$")

def parse_whatsapp_text(texto: str, categoria_default: str = "GERAL") -> List[Item]:
    linhas = (texto or "").splitlines()
    cat_atual = norm(categoria_default) or "GERAL"
    itens: List[Item] = []

    for ln in linhas:
        raw = (ln or "").strip()
        if not raw:
            continue

        # categoria: sem número, curta
        if not re.search(r"\d", raw) and len(raw) >= 3:
            cand = norm(raw)
            # evita pegar frases enormes
            if len(cand) <= 40:
                cat_atual = cand
                continue

        m = _num_re.match(raw)
        if not m:
            continue

        nome = norm(m.group(1))
        qtd = int(m.group(2))
        if nome:
            itens.append(Item(categoria=cat_atual, produto=nome, quantidade=qtd))

    return itens

# compat: se algum lugar chamar parse_whatsapp()
parse_whatsapp = parse_whatsapp_text
