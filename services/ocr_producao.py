import cv2
import numpy as np
from PIL import Image
import pytesseract
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass
class OCRItem:
    categoria: str
    produto: str
    quantidade: float

TIPOS_BOLO = {"BOLO RETANGULAR", "BOLO XODÓ", "BOLOS CASEIROS", "ROCAMBOLE", "CONFEITARIA", "BOLOS"}

def _up(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s.upper()

def ocr_image_to_text(pil_img: Image.Image) -> str:
    img = np.array(pil_img.convert("RGB"))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    h, w = img.shape[:2]
    img = cv2.resize(img, (w*2, h*2), interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)

    thr = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 35, 11
    )

    config = "--oem 1 --psm 6"
    return pytesseract.image_to_string(thr, lang="por", config=config)

def parse_producao_from_ocr_text(texto: str) -> List[OCRItem]:
    linhas = [l.strip() for l in (texto or "").splitlines() if l.strip()]
    categoria_atual = "GERAL"
    itens: List[OCRItem] = []

    for raw in linhas:
        line = _up(raw)

        # ignora lixo comum de tabela
        if line in {"COD", "CÓD", "PRODUTOS", "PROD", "AUSTIN", "QUEIMADOS"}:
            continue

        # header
        if not re.search(r"\d", line) and len(line) <= 40:
            categoria_atual = line
            continue

        # item: "NOME 10" ou "NOME : 10"
        m = re.match(r"^(.*?)(?:\s*[:\-]\s*|\s+)(\d+(?:[.,]\d+)?)\s*$", line)
        if not m:
            continue

        produto = _up(m.group(1))
        qtd = float(m.group(2).replace(",", "."))

        if produto:
            itens.append(OCRItem(categoria=categoria_atual, produto=produto, quantidade=qtd))

    return itens
