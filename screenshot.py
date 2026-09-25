"""
screenshot.py — Captura de tela e overlay de comentário.

Usa:
  - mss  → captura rápida sem dependência de pyautogui
  - Pillow (PIL) → composição do overlay de texto

NÃO usa: pyautogui.screenshot, OpenCV, OCR.
"""

from __future__ import annotations

import math
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
    Sem fonte configurada, tenta Arial/Segoe UI e depois o padrao do Pillow.
    """
    if config.FONT_PATH:
        try:
            return ImageFont.truetype(config.FONT_PATH, tamanho)
        except (IOError, OSError):
            utils.warn(f"Fonte '{config.FONT_PATH}' nao encontrada. Tentando fontes do sistema.")
    for caminho in ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf"):
        if Path(caminho).is_file():
            try:
                return ImageFont.truetype(caminho, tamanho)
            except OSError:
                pass
    # Pillow >= 10: load_default aceita size
    try:
        return ImageFont.load_default(size=tamanho)
    except TypeError:
        return ImageFont.load_default()


# ── Overlay de texto ──────────────────────────────────────────────────────────

def adicionar_comentario(img: Image.Image, comentario: str) -> Image.Image:
    """
    Retorna uma copia com legenda e caixa no canto inferior esquerdo.
    As margens se aplicam a caixa; padding e borda ficam dentro dela.
    Preserva quebras manuais e mede o texto incluindo seu contorno.
    """
    if not comentario.strip():
        return img.copy()

    margem_x = max(0, int(config.TEXT_MARGIN_X))
    margem_y = max(0, int(config.TEXT_MARGIN_Y))
    borda = max(0, int(config.TEXT_BOX_BORDER_WIDTH)) if config.TEXT_BOX_ENABLED else 0
    padding_x = max(0, int(config.TEXT_BOX_PADDING_X)) + borda if config.TEXT_BOX_ENABLED else 0
    padding_y = max(0, int(config.TEXT_BOX_PADDING_Y)) + borda if config.TEXT_BOX_ENABLED else 0
    proporcao = float(config.TEXT_MAX_WIDTH_RATIO)
    if not 0 < proporcao <= 1:
        raise ValueError("TEXT_MAX_WIDTH_RATIO deve estar entre 0 (exclusivo) e 1.")
    max_w = min(img.width - 2 * margem_x, int(img.width * proporcao)) - 2 * padding_x
    max_h = img.height - margem_y - 2 * padding_y
    if max_w <= 0 or max_h <= 0:
        raise ValueError("Margens e padding nao deixam espaco para a legenda.")

    resultado = img.convert("RGBA")
    draw = ImageDraw.Draw(resultado)
    estilo = {
        "spacing": config.TEXT_LINE_SPACING,
        "align": config.TEXT_ALIGN,
        "stroke_width": config.TEXT_STROKE_WIDTH,
    }
    tamanho_minimo = max(1, min(config.FONT_SIZE, config.TEXT_MIN_FONT_SIZE))
    for tamanho in range(config.FONT_SIZE, tamanho_minimo - 1, -1):
        fonte = _carregar_fonte(tamanho)
        linhas = _quebrar_texto_por_pixels(
            comentario, draw, fonte, max_w, config.TEXT_STROKE_WIDTH,
        )
        texto = "\n".join(linhas)
        bbox = draw.multiline_textbbox((0, 0), texto, font=fonte, **estilo)
        largura_texto = math.ceil(bbox[2] - bbox[0])
        altura_texto = math.ceil(bbox[3] - bbox[1])
        if largura_texto <= max_w and altura_texto <= max_h:
            break
    else:
        raise ValueError(
            "Comentario nao cabe na imagem. Reduza a fala, as margens "
            "ou TEXT_MIN_FONT_SIZE."
        )

    largura_caixa = max_w + 2 * padding_x
    altura_caixa = altura_texto + 2 * padding_y
    esquerda = margem_x
    inferior = img.height - margem_y
    superior = inferior - altura_caixa

    if config.TEXT_BOX_ENABLED:
        opacidade = int(config.TEXT_BOX_OPACITY)
        if not 0 <= opacidade <= 255:
            raise ValueError("TEXT_BOX_OPACITY deve estar entre 0 e 255.")
        camada = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(camada).rectangle(
            (esquerda, superior, esquerda + largura_caixa - 1, inferior - 1),
            fill=(*config.TEXT_BOX_COLOR, opacidade),
            outline=(*config.TEXT_BOX_BORDER_COLOR, 255) if borda else None,
            width=borda,
        )
        resultado = Image.alpha_composite(resultado, camada)

    # Compensa os offsets da fonte para manter contorno e acentos dentro do padding.
    origem = (esquerda + padding_x - bbox[0], superior + padding_y - bbox[1])
    ImageDraw.Draw(resultado).multiline_text(
        origem, texto, font=fonte, fill=config.TEXT_COLOR,
        stroke_fill=config.TEXT_OUTLINE, **estilo,
    )
    return resultado.convert(img.mode)


def _quebrar_texto_por_pixels(
    texto: str,
    draw: ImageDraw.ImageDraw,
    fonte: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    largura_maxima: int,
    contorno: int,
) -> list[str]:
    """Mantem paragrafos e linhas vazias; divide palavras apenas se nao couberem."""
    def cabe(trecho: str) -> bool:
        bbox = draw.textbbox((0, 0), trecho, font=fonte, stroke_width=contorno)
        return bbox[2] - bbox[0] <= largura_maxima

    linhas = []
    for bloco in texto.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        linha = ""
        for palavra in bloco.split():
            tentativa = f"{linha} {palavra}" if linha else palavra
            if cabe(tentativa):
                linha = tentativa
                continue
            if linha:
                linhas.append(linha)
            while not cabe(palavra) and len(palavra) > 1:
                inicio, fim, corte = 1, len(palavra) - 1, 1
                while inicio <= fim:
                    meio = (inicio + fim) // 2
                    if cabe(palavra[:meio]):
                        corte = meio
                        inicio = meio + 1
                    else:
                        fim = meio - 1
                linhas.append(palavra[:corte])
                palavra = palavra[corte:]
            linha = palavra
        linhas.append(linha)
    return linhas


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
