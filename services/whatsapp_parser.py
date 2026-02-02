# services/whatsapp_parser.py
import re
import unicodedata
from typing import List, Dict, Tuple, Optional

_NUM_RE = re.compile(r"(\d+(?:[.,]\d+)?)")

def _upper_clean(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    # normaliza unicode e remove caracteres invisíveis
    s = unicodedata.normalize("NFKC", s)
    # troca tabs por espaço
    s = s.replace("\t", " ")
    # remove múltiplos espaços
    s = re.sub(r"\s+", " ", s)
    return s.upper().strip()

def _normalize_spaces_punct(s: str) -> str:
    s = _upper_clean(s)
    # normaliza separadores comuns
    s = s.replace("–", "-").replace("—", "-")
    s = s.replace("|", " ")
    # remove duplicação de pontuação
    s = re.sub(r"\s*:\s*", ": ", s)
    s = re.sub(r"\s*-\s*", " - ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def _to_float(num_str: str) -> float:
    if num_str is None:
        return 0.0
    num_str = num_str.strip().replace(".", "").replace(",", ".")  # "1.234" -> "1234" / "1,5" -> "1.5"
    try:
        return float(num_str)
    except Exception:
        return 0.0

def _is_header(line: str) -> bool:
    """
    Heurística: cabeçalho/categoria costuma ser uma linha sem número no fim,
    ou com poucas palavras e com letras (ex: "BOLO RETANGULAR", "ROCABOMBLE", etc).
    """
    if not line:
        return False
    # se a linha tem número no final, é item, não header
    if _extract_item(line)[0]:
        return False
    # curta demais e só pontuação -> ignora
    if len(line) < 2:
        return False
    # se tem só letras e espaços e tamanho razoável, pode ser header
    letters = re.sub(r"[^A-ZÇÃÕÁÉÍÓÚÂÊÔ ]", "", line)
    if len(letters.replace(" ", "")) >= 3:
        return True
    return False

def _extract_item(line: str) -> Tuple[bool, Optional[str], Optional[float]]:
    """
    Tenta extrair: "PRODUTO 10" / "PRODUTO: 10" / "PRODUTO - 10"
    Retorna (ok, nome_produto, quantidade)
    """
    line = _normalize_spaces_punct(line)

    # remove bullets comuns
    line = re.sub(r"^[•\-\*]+\s*", "", line).strip()

    if not line:
        return (False, None, None)

    # padrões comuns: "NOME: 10", "NOME - 10", "NOME 10"
    m = re.search(r"^(.*?)(?:\s*[:\-]\s*|\s+)(\d+(?:[.,]\d+)?)\s*$", line)
    if m:
        nome = _upper_clean(m.group(1))
        qtd = _to_float(m.group(2))
        if nome and qtd is not None:
            return (True, nome, qtd)

    return (False, None, None)

def parse_whatsapp_text(texto: str) -> List[Dict]:
    """
    Parser principal.
    Retorna lista de itens:
    [
      {"categoria": "BOLO RETANGULAR", "produto": "PRESTÍGIO", "quantidade": 2.0},
      ...
    ]
    Regras:
    - Categoria vem de cabeçalho (linha sem número)
    - Item vem de linha com número no final (com ou sem ":" / "-")
    - Tudo fica em caixa alta
    """
    texto = texto or ""
    linhas = texto.splitlines()

    itens: List[Dict] = []
    categoria_atual = "(SEM)"

    for raw in linhas:
        line = _normalize_spaces_punct(raw)

        # ignora linhas vazias
        if not line:
            continue

        # ignora separadores/traços
        if re.fullmatch(r"[-_=\s]+", line):
            continue

        ok, nome, qtd = _extract_item(line)
        if ok and nome is not None and qtd is not None:
            # se ainda não tem categoria válida, mantém "(SEM)"
            itens.append({
                "categoria": categoria_atual,
                "produto": nome,
                "quantidade": float(qtd),
            })
            continue

        # se não é item, pode ser categoria/cabeçalho
        if _is_header(line):
            categoria_atual = _upper_clean(line)
            continue

        # se chegou aqui: linha "solta" (nem item nem header) -> ignora
        # (ex: "BOLOS CASEIROS" com erro de OCR pode cair aqui; se quiser, melhoramos depois)

    return itens

# compatibilidade: se seu código antigo chamava outro nome
def parse_text(texto: str) -> List[Dict]:
    return parse_whatsapp_text(texto)

def parse_whatsapp(texto: str) -> List[Dict]:
    return parse_whatsapp_text(texto)
