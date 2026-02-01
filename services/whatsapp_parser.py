import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


TIPOS_DE_BOLO = {"RETANGULAR", "XODÓ", "XODO", "CASEIROS", "CASEIRO"}

CORRECOES = {
    "OREO": "ÓREO",
    "ORÉO": "ÓREO",
    "RED VELTE": "RED VELVET",
    "REDVELTE": "RED VELVET",
    "REDVELVET": "RED VELVET",
    "FERREIRO": "FERRERO ROCHER",
    "FERRERO": "FERRERO ROCHER",
    "LIMAO": "LIMÃO",
    "ACUCARADO": "AÇUCARADO",
    "SUICO": "SUÍÇO",
    "SUIÇO": "SUÍÇO",
}

IGNORAR_HEADERS = {
    "BOM DIA", "OK", "OBRIGADO", "OBRIGADA", "VALEU", "SHOW",
    "CÂMARA", "CAMARA", "CALL CENTER", "CALLCENTER"
}


def upper_clean(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s.upper()


def aplicar_correcoes(txt: str) -> str:
    t = upper_clean(txt)
    for de, para in CORRECOES.items():
        t = re.sub(rf"\b{re.escape(de)}\b", para, t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _extrair_mensagem_linha_export(raw: str) -> str:
    line = raw.strip()
    if not line:
        return ""

    if " - " in line:
        _, rest = line.split(" - ", 1)
    else:
        rest = line

    if ": " in rest:
        _, msg = rest.split(": ", 1)
    else:
        msg = rest

    return msg.strip()


def is_header_line(line: str) -> bool:
    l = line.strip()
    if not l:
        return False
    if re.search(r"\d", l):
        return False
    return True


def parse_item_line(line: str) -> Tuple[Optional[str], Optional[float]]:
    l = line.strip()
    if not l:
        return None, None

    l = l.replace("–", "-").replace("—", "-")

    m = re.match(r"^(.*?)[\:\-]\s*(\d+(?:[\,\.]\d+)?)\s*$", l)
    if m:
        nome = m.group(1).strip()
        qtd = m.group(2).replace(",", ".")
        return nome, float(qtd)

    m = re.match(r"^(\d+(?:[\,\.]\d+)?)\s+(.*)$", l)
    if m:
        qtd = m.group(1).replace(",", ".")
        nome = m.group(2).strip()
        return nome, float(qtd)

    m = re.match(r"^(.*\D)\s+(\d+(?:[\,\.]\d+)?)\s*$", l)
    if m:
        nome = m.group(1).strip()
        qtd = m.group(2).replace(",", ".")
        return nome, float(qtd)

    return None, None


def normalizar_header(header: str) -> Tuple[str, Optional[str]]:
    h = aplicar_correcoes(header)

    if h in IGNORAR_HEADERS:
        return "IGNORAR", None

    if h in {"BOLOS", "BOLO"}:
        return "BOLOS", None

    if h in TIPOS_DE_BOLO:
        if h == "XODO":
            h = "XODÓ"
        return "BOLOS", h

    if h in {"ROCAMBOLE", "ROCABMOLE", "ROCAMBOLO"}:
        return "ROCAMBOLE", None

    return h, None


@dataclass
class ParsedItem:
    categoria: str
    produto: str
    quantidade: float


def parse_whatsapp_text(texto: str) -> List[ParsedItem]:
    linhas_raw = texto.splitlines()

    grupo_atual = "GERAL"
    tipo_atual: Optional[str] = None
    itens: List[ParsedItem] = []

    for raw in linhas_raw:
        msg = _extrair_mensagem_linha_export(raw)
        if not msg:
            continue

        if "MÍDIA" in msg.upper():
            continue

        if is_header_line(msg):
            grupo, tipo = normalizar_header(msg)
            if grupo == "IGNORAR":
                continue
            grupo_atual, tipo_atual = grupo, tipo
            continue

        nome, qtd = parse_item_line(msg)
        if nome is None or qtd is None:
            continue

        produto = aplicar_correcoes(nome)

        if grupo_atual == "BOLOS" and tipo_atual:
            categoria = f"BOLOS - {tipo_atual}"
        else:
            categoria = grupo_atual

        categoria = aplicar_correcoes(categoria)

        if not produto:
            continue

        itens.append(ParsedItem(categoria=categoria, produto=produto, quantidade=float(qtd)))

    return itens
