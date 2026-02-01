import re
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ParsedItem:
    category: str
    product: str
    qty: float

def _clean(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s.upper()

def _is_header(line: str) -> bool:
    if not line:
        return False
    # header: não tem número no final
    return not re.search(r"\d", line)

def parse_whatsapp_text(text: str) -> List[ParsedItem]:
    lines = [l.strip() for l in (text or "").splitlines()]
    items: List[ParsedItem] = []
    current_category = "GERAL"

    for raw in lines:
        line = _clean(raw)
        if not line:
            continue

        # detecta header (categoria)
        if _is_header(line) and len(line) <= 40:
            current_category = line
            continue

        # tenta extrair "nome : 10" ou "nome 10"
        m = re.match(r"^(.*?)(?:\s*[:\-]\s*|\s+)(\d+(?:[.,]\d+)?)\s*$", line)
        if not m:
            continue

        product = _clean(m.group(1))
        qty = float(m.group(2).replace(",", "."))
        if not product:
            continue

        # produto não repete categoria
        items.append(ParsedItem(category=current_category, product=product, qty=qty))

    return items
