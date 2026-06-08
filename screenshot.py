"""
screenshot.py — Captura de tela e overlay de comentário.

Usa:
  - mss  → captura rápida sem dependência de pyautogui
  - Pillow (PIL) → composição do overlay de texto

NÃO usa: pyautogui.screenshot, OpenCV, OCR.
"""

from __future__ import annotations

import time
from pathlib import Path

import mss
import mss.tools
from PIL import Image, ImageDraw, ImageFont

import config
import utils


# ── Captura ───────────────────────────────────────────────────────────────────

def capturar_tela() -> Image.Image:
    """
    Captura o monitor primário usando MSS e retorna um objeto PIL Image.
    MSS é significativamente mais rápido que pyautogui.screenshot().
    """
    with mss.mss() as sct:
        monitor = sct.monitors[config.MONITOR_INDEX]
        raw = sct.grab(monitor)
        # mss retorna BGRA; converter para RGB
        img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
    utils.info("Tela capturada com MSS.")
    return img


# ── Fonte ─────────────────────────────────────────────────────────────────────

def _carregar_fonte(tamanho: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """
    Carrega a fonte TrueType configurada em config.FONT_PATH.
    Se o caminho estiver vazio ou inválido, usa a fonte padrão do Pillow.
    """
    if config.FONT_PATH:
        try:
            return ImageFont.truetype(config.FONT_PATH, tamanho)
        except (IOError, OSError):
            utils.warn(f"Fonte '{config.FONT_PATH}' não encontrada. Usando padrão.")
    # Pillow >= 10: load_default aceita size
    try:
        return ImageFont.load_default(size=tamanho)
    except TypeError:
        return ImageFont.load_default()


# ── Overlay de texto ──────────────────────────────────────────────────────────

def adicionar_comentario(img: Image.Image, comentario: str) -> Image.Image:
    """
    Desenha o comentário na parte inferior da imagem.

    Características:
      - Texto branco com contorno preto (para legibilidade em qualquer fundo).
      - Quebra automática de linha.
      - Alinhamento inferior-central.

    Args:
        img:        Imagem PIL de origem.
        comentario: Texto a ser inserido.

    Returns:
        Nova imagem PIL com o texto sobreposto.
    """
    # Trabalhar em cópia para não modificar o original
    img = img.copy()
    draw = ImageDraw.Draw(img)
    fonte = _carregar_fonte(config.FONT_SIZE)

    largura, altura = img.size
    linhas = utils.quebrar_texto(comentario)

    # Calcular altura total do bloco de texto
    line_height = config.FONT_SIZE + 6
    bloco_altura = len(linhas) * line_height

    # Posição Y inicial (alinhar bloco ao rodapé)
    y_inicio = altura - bloco_altura - config.TEXT_MARGIN_Y

    for i, linha in enumerate(linhas):
        # Centralizar horizontalmente
        try:
            bbox = draw.textbbox((0, 0), linha, font=fonte)
            text_w = bbox[2] - bbox[0]
        except AttributeError:
            text_w, _ = draw.textsize(linha, font=fonte)  # Pillow < 9

        x = (largura - text_w) // 2
        y = y_inicio + i * line_height

        # Contorno preto (deslocamento de ±2 px em 8 direções)
        offsets = [(-2, -2), (0, -2), (2, -2),
                   (-2,  0),          (2,  0),
                   (-2,  2), (0,  2), (2,  2)]
        for ox, oy in offsets:
            draw.text((x + ox, y + oy), linha, font=fonte, fill=config.TEXT_OUTLINE)

        # Texto principal
        draw.text((x, y), linha, font=fonte, fill=config.TEXT_COLOR)

    return img


# ── Salvar ────────────────────────────────────────────────────────────────────

def salvar_imagem(img: Image.Image, nome_arquivo: str) -> Path:
    """
    Salva a imagem final na pasta output configurada.

    Args:
        img:          Imagem PIL a salvar.
        nome_arquivo: Nome do arquivo (ex: "cena_001.png").

    Returns:
        Path do arquivo salvo.
    """
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    caminho = config.OUTPUT_DIR / nome_arquivo
    img.save(caminho, format="PNG")
    utils.info(f"Screenshot salva → {caminho}")
    return caminho


# ── Pipeline completo ─────────────────────────────────────────────────────────

def capturar_e_salvar(comentario: str, nome_arquivo: str) -> Path:
    """
    Captura a tela, adiciona o comentário e salva.
    Função de conveniência chamada pelo engine após ocultar o HUD.
    """
    img = capturar_tela()
    img = adicionar_comentario(img, comentario)
    return salvar_imagem(img, nome_arquivo)
