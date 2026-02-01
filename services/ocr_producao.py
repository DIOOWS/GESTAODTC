import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image
import pytesseract


CORRECOES = {
    "OREO": "ÓREO",
    "ORÉO": "ÓREO",
    "RED VELTE": "RED VELVET",
    "FERREIRO": "FERRERO ROCHER",
    "FERRERO": "FERRERO ROCHER",
    "LIMAO": "LIMÃO",
    "SUICO": "SUÍÇO",
    "SUIÇO": "SUÍÇO",
    "XODO": "XODÓ",
}

TIPOS_DE_BOLO = {"RETANGULAR", "XODÓ", "XODO", "CASEIROS", "CASEIRO"}

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

def normalizar_header(header: str) -> Tuple[str, Optional[str]]:
    h = aplicar_correcoes(header)

    if h in {"BOLOS", "BOLO"}:
        return "BOLOS", None
    if h in TIPOS_DE_BOLO:
        if h == "XODO":
            h = "XODÓ"
        return "BOLOS", h
    if h in {"ROCAMBOLE", "ROCABMOLE", "ROCAMBOLO"}:
        return "ROCAMBOLE", None

    # outras categorias impressas (ex.: CONFEITARIA, MOUSSE, DOCINHOS...)
    return h, None

def parse_item_line(line: str) -> Tuple[Optional[str], Optional[float]]:
    """
    Linhas do OCR costumam vir como:
      "LIMÃO 3"
      "CHOC. C/ GALAK 3"
      "FERRERO ROCHER 6"
    Pegamos o último número como quantidade.
    """
    l = line.strip()
    if not l:
        return None, None

    # remove caracteres estranhos
    l = re.sub(r"[|_]+", " ", l)
    l = re.sub(r"\s+", " ", l).strip()

    m = re.match(r"^(.*\D)\s+(\d+(?:[\,\.]\d+)?)\s*$", l)
    if m:
        nome = m.group(1).strip()
        qtd = m.group(2).replace(",", ".")
        return nome, float(qtd)

    return None, None


@dataclass
class OCRItem:
    categoria: str
    produto: str
    quantidade: float


def ocr_image_to_text(pil_img: Image.Image) -> str:
    """
    Pré-processamento simples (melhora bastante a leitura).
    """
    img = np.array(pil_img.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # aumenta contraste
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY, 31, 7)

    # OCR (português + números)
    config = "--oem 1 --psm 6"
    txt = pytesseract.image_to_string(thr, lang="por", config=config)
    return txt


def parse_producao_from_ocr_text(texto: str) -> List[OCRItem]:
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]

    grupo_atual = "GERAL"
    tipo_atual: Optional[str] = None
    itens: List[OCRItem] = []

    for raw in linhas:
        line = aplicar_correcoes(raw)

        # ignora cabeçalhos de colunas
        if line in {"COD", "CÓD", "PRODUTOS", "PROD", "AUSTIN", "QUEIMADOS"}:
            continue

        # header se não tem número
        if not re.search(r"\d", line):
            grupo, tipo = normalizar_header(line)
            grupo_atual, tipo_atual = grupo, tipo
            continue

        nome, qtd = parse_item_line(line)
        if nome is None or qtd is None:
            continue

        produto = aplicar_correcoes(nome)

        if grupo_atual == "BOLOS" and tipo_atual:
            categoria = f"BOLOS - {tipo_atual}"
        else:
            categoria = grupo_atual

        categoria = aplicar_correcoes(categoria)

        # produto final (organizado, sem conflitos)
        itens.append(OCRItem(categoria=categoria, produto=produto, quantidade=float(qtd)))

    return itens
