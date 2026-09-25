from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

import config
import utils


Box = tuple[int, int, int, int]


@dataclass
class RenderResult:
    caminho: Path
    canvas_size: tuple[int, int]
    react_box: Box
    message_box: Box
    text_box: Box | None
    character_boxes: dict[str, Box]


def carregar_layout(nome: str | None = None) -> dict[str, Any]:
    caminho = _layout_path(nome or config.LAYOUT_PRESET)
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def renderizar_cenas(cenas: list[dict[str, Any]]) -> list[RenderResult]:
    resultados: list[RenderResult] = []
    for indice, cena in enumerate(cenas, start=1):
        resultados.append(renderizar_cena(cena, indice))
    return resultados


def renderizar_cena(
    cena: dict[str, Any],
    indice: int,
    *,
    output_dir: Path | None = None,
    nome_arquivo: str | None = None,
    validar: bool = True,
) -> RenderResult:
    layout = carregar_layout(cena.get("layout"))
    canvas_cfg = layout["canvas"]
    largura = int(canvas_cfg["w"])
    altura = int(canvas_cfg["h"])

    img = Image.new("RGB", (largura, altura), _cor(canvas_cfg["background"]))
    draw = ImageDraw.Draw(img)

    _desenhar_cenario(draw, layout)
    _desenhar_area_react(draw, layout)
    _desenhar_qr_livepix(img, draw, layout)
    character_boxes = _desenhar_personagens(img, draw, layout, cena)
    _desenhar_area_mensagens(draw, layout)
    text_box = _desenhar_falas(draw, layout, cena)

    destino = output_dir or config.CENAS_DIR
    destino.mkdir(parents=True, exist_ok=True)
    caminho = destino / (nome_arquivo or _nome_arquivo(cena, indice))
    img.save(caminho, format="PNG")

    resultado = RenderResult(
        caminho=caminho,
        canvas_size=img.size,
        react_box=_box(layout["areas"]["react_video"]),
        message_box=_box(layout["areas"]["mensagens"]),
        text_box=text_box,
        character_boxes=character_boxes,
    )
    if validar:
        validar_renderizacao(img, resultado, layout)

    utils.info(f"Cena limpa salva em: {caminho}")
    return resultado


def validar_renderizacao(img: Image.Image, resultado: RenderResult, layout: dict[str, Any]) -> None:
    esperado = (int(layout["canvas"]["w"]), int(layout["canvas"]["h"]))
    if img.size != esperado:
        raise ValueError(f"PNG final tem {img.size}, esperado {esperado}.")

    react_cfg = layout["areas"]["react_video"]
    react_color = _cor(react_cfg["color"])
    crop = img.crop(resultado.react_box)
    extrema = crop.getextrema()
    if extrema != tuple((canal, canal) for canal in react_color):
        raise ValueError("Area do react nao esta 100% verde puro #00FF00.")

    if resultado.text_box and not _contem(resultado.message_box, resultado.text_box):
        raise ValueError("Texto saiu da area inferior de mensagens.")

    for personagem, bbox in resultado.character_boxes.items():
        if _intersecta(bbox, resultado.react_box):
            raise ValueError(f"{personagem} invade a area verde do react.")


def extrair_falas(cena: dict[str, Any]) -> dict[str, str]:
    fala = cena.get("fala")
    if isinstance(fala, dict):
        return {
            "pt": str(fala.get("pt", "")),
            "en": str(fala.get("en", "")),
            "es": str(fala.get("es", "")),
        }

    texto = str(cena.get("texto", ""))
    if not texto and isinstance(cena.get("personagens"), dict):
        for estado in cena["personagens"].values():
            texto_estado = str(estado.get("texto", ""))
            if texto_estado.strip():
                texto = texto_estado
                break

    linhas = texto.splitlines()
    return {
        "pt": linhas[0] if len(linhas) > 0 else "",
        "en": linhas[1] if len(linhas) > 1 else "",
        "es": linhas[2] if len(linhas) > 2 else "",
    }


def _layout_path(nome: str) -> Path:
    caminho = config.LAYOUTS_DIR / f"{nome}.json"
    if caminho.exists():
        return caminho

    caminho_direto = Path(nome)
    if caminho_direto.exists():
        return caminho_direto

    raise FileNotFoundError(f"Layout nao encontrado: {nome}")


def _desenhar_cenario(draw: ImageDraw.ImageDraw, layout: dict[str, Any]) -> None:
    area = layout["areas"]["personagens_cenario"]
    cenario = layout["cenario"]
    box = _box(area)
    draw.rectangle(box, fill=_cor(cenario["parede"]))

    piso_y = int(cenario["linha_piso_y"])
    draw.rectangle((box[0], piso_y, box[2], box[3]), fill=_cor(cenario["piso"]))

    sofa = cenario["sofa"]
    sx, sy, sw, sh = _xywh(sofa)
    draw.rounded_rectangle((sx + 18, sy + 32, sx + sw + 18, sy + sh + 22), radius=34, fill=_cor(sofa["sombra"]))
    draw.rounded_rectangle((sx, sy, sx + sw, sy + 170), radius=42, fill=_cor(sofa["encosto"]))
    draw.rounded_rectangle((sx - 28, sy + 120, sx + sw + 28, sy + sh), radius=44, fill=_cor(sofa["assento"]))
    draw.rounded_rectangle((sx - 48, sy + 135, sx + 48, sy + sh + 20), radius=34, fill=_cor(sofa["encosto"]))
    draw.rounded_rectangle((sx + sw - 48, sy + 135, sx + sw + 48, sy + sh + 20), radius=34, fill=_cor(sofa["encosto"]))


def _desenhar_area_react(draw: ImageDraw.ImageDraw, layout: dict[str, Any]) -> None:
    area = layout["areas"]["react_video"]
    _desenhar_retangulo(draw, area, _cor(area["color"]))


def _desenhar_qr_livepix(img: Image.Image, draw: ImageDraw.ImageDraw, layout: dict[str, Any]) -> None:
    area_cfg = layout["areas"]["qr_livepix"]
    qr_cfg = layout.get("qr_livepix", {})
    area = _box(area_cfg)
    _desenhar_retangulo(draw, area_cfg, _cor(qr_cfg.get("background", layout["canvas"]["background"])))

    imagem = str(qr_cfg.get("imagem", "")).strip()
    if imagem:
        qr_path = Path(imagem)
        if not qr_path.is_absolute():
            qr_path = config.BASE_DIR / qr_path
        if qr_path.exists():
            padding = int(qr_cfg.get("padding", 0))
            destino = (area[0] + padding, area[1] + padding, area[2] - padding, area[3] - padding)
            qr_img = Image.open(qr_path).convert("RGBA")
            qr_img.thumbnail((destino[2] - destino[0], destino[3] - destino[1]), Image.Resampling.LANCZOS)
            x = destino[0] + (destino[2] - destino[0] - qr_img.width) // 2
            y = destino[1] + (destino[3] - destino[1] - qr_img.height) // 2
            img.paste(qr_img, (x, y), qr_img)
            return

    if qr_cfg.get("placeholder", False):
        fonte = _carregar_fonte(28, bold=True)
        texto = "QR Live Pix"
        bbox = draw.textbbox((0, 0), texto, font=fonte)
        x = area[0] + (area[2] - area[0] - (bbox[2] - bbox[0])) // 2
        y = area[1] + (area[3] - area[1] - (bbox[3] - bbox[1])) // 2
        draw.text((x, y), texto, fill=(80, 86, 92), font=fonte)


def _desenhar_personagens(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    layout: dict[str, Any],
    cena: dict[str, Any],
) -> dict[str, Box]:
    personagens = cena.get("personagens", {})
    slots = layout["personagens"]["slots"]
    fonte_nome = _carregar_fonte(int(layout["personagens"].get("fonte_nome", 26)), bold=True)
    bboxes: dict[str, Box] = {}

    for nome, slot in slots.items():
        estado = personagens.get(nome, {})
        bbox = _desenhar_personagem(img, draw, slot, nome, estado, fonte_nome)
        bboxes[nome] = bbox

    return bboxes


def _desenhar_personagem(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    slot: dict[str, Any],
    nome: str,
    estado: dict[str, Any],
    fonte_nome: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> Box:
    x, y, w, h = _xywh(slot)
    imagem_personagem = _carregar_imagem_opcional(slot.get("imagem", ""))
    if imagem_personagem:
        limite_h = max(1, h - 54)
        imagem_personagem.thumbnail((w, limite_h), Image.Resampling.LANCZOS)
        px = x + (w - imagem_personagem.width) // 2
        py = y + max(0, (limite_h - imagem_personagem.height) // 2)
        img.paste(imagem_personagem, (px, py), imagem_personagem)
        bbox_imagem = (px, py, px + imagem_personagem.width, py + imagem_personagem.height)
        _desenhar_nome_personagem(draw, slot, nome, fonte_nome)
        return bbox_imagem

    cor = _cor(slot["cor"])
    centro = x + w // 2
    intensidade = int(estado.get("intensidade", 1) or 1)
    emocao = str(estado.get("emocao", "neutro"))

    escala = 1 + min(max(intensidade, 1), 3) * 0.03
    cabeca_r = int(min(w * 0.34, 58) * escala)
    cabeca_y = y + 36
    corpo_top = cabeca_y + cabeca_r * 2 - 10
    corpo_bottom = y + h - 95
    corpo_w = int(w * 0.72 * escala)

    sombra = _misturar(cor, (0, 0, 0), 0.18)
    pele = (244, 204, 174)
    cabelo = _misturar(cor, (0, 0, 0), 0.42)

    draw.ellipse((centro - 48, corpo_bottom - 8, centro + 48, corpo_bottom + 16), fill=(88, 94, 98))
    draw.rounded_rectangle(
        (centro - corpo_w // 2, corpo_top, centro + corpo_w // 2, corpo_bottom),
        radius=38,
        fill=cor,
        outline=sombra,
        width=4,
    )
    draw.rounded_rectangle(
        (centro - corpo_w // 2 - 20, corpo_top + 42, centro - corpo_w // 2 + 22, corpo_bottom - 12),
        radius=22,
        fill=sombra,
    )
    draw.rounded_rectangle(
        (centro + corpo_w // 2 - 22, corpo_top + 42, centro + corpo_w // 2 + 20, corpo_bottom - 12),
        radius=22,
        fill=sombra,
    )
    draw.ellipse((centro - cabeca_r, cabeca_y, centro + cabeca_r, cabeca_y + cabeca_r * 2), fill=pele)
    draw.pieslice((centro - cabeca_r - 4, cabeca_y - 18, centro + cabeca_r + 4, cabeca_y + cabeca_r), 180, 360, fill=cabelo)
    _desenhar_rosto(draw, centro, cabeca_y + cabeca_r, cabeca_r, emocao)

    _desenhar_nome_personagem(draw, slot, nome, fonte_nome)

    return (x, y, x + w, y + h)


def _desenhar_nome_personagem(
    draw: ImageDraw.ImageDraw,
    slot: dict[str, Any],
    nome: str,
    fonte_nome: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> None:
    x, y, w, h = _xywh(slot)
    centro = x + w // 2
    label = str(slot.get("nome", nome.title().replace("_", " ")))
    label_bbox = draw.textbbox((0, 0), label, font=fonte_nome, stroke_width=2)
    label_w = label_bbox[2] - label_bbox[0]
    label_x = max(x, min(x + w - label_w, centro - label_w // 2))
    label_y = y + h - 58
    draw.text(
        (label_x, label_y),
        label,
        fill=(255, 255, 255),
        font=fonte_nome,
        stroke_width=2,
        stroke_fill=(0, 0, 0),
    )


def _desenhar_rosto(draw: ImageDraw.ImageDraw, centro: int, cy: int, r: int, emocao: str) -> None:
    olho_y = cy - int(r * 0.18)
    olho_dx = int(r * 0.34)
    boca_y = cy + int(r * 0.28)
    preto = (28, 30, 32)

    if emocao in {"feliz", "animado"}:
        draw.arc((centro - olho_dx - 10, olho_y - 5, centro - olho_dx + 10, olho_y + 13), 0, 180, fill=preto, width=4)
        draw.arc((centro + olho_dx - 10, olho_y - 5, centro + olho_dx + 10, olho_y + 13), 0, 180, fill=preto, width=4)
        draw.arc((centro - 28, boca_y - 18, centro + 28, boca_y + 26), 10, 170, fill=preto, width=5)
    elif emocao == "triste":
        draw.ellipse((centro - olho_dx - 6, olho_y - 5, centro - olho_dx + 6, olho_y + 7), fill=preto)
        draw.ellipse((centro + olho_dx - 6, olho_y - 5, centro + olho_dx + 6, olho_y + 7), fill=preto)
        draw.arc((centro - 28, boca_y, centro + 28, boca_y + 38), 200, 340, fill=preto, width=5)
    elif emocao == "raiva":
        draw.line((centro - olho_dx - 16, olho_y - 12, centro - olho_dx + 12, olho_y), fill=preto, width=5)
        draw.line((centro + olho_dx - 12, olho_y, centro + olho_dx + 16, olho_y - 12), fill=preto, width=5)
        draw.ellipse((centro - olho_dx - 5, olho_y, centro - olho_dx + 7, olho_y + 12), fill=preto)
        draw.ellipse((centro + olho_dx - 7, olho_y, centro + olho_dx + 5, olho_y + 12), fill=preto)
        draw.line((centro - 26, boca_y + 12, centro + 26, boca_y + 2), fill=preto, width=5)
    elif emocao in {"surpreso", "medo"}:
        draw.ellipse((centro - olho_dx - 8, olho_y - 7, centro - olho_dx + 8, olho_y + 9), fill=preto)
        draw.ellipse((centro + olho_dx - 8, olho_y - 7, centro + olho_dx + 8, olho_y + 9), fill=preto)
        draw.ellipse((centro - 15, boca_y - 4, centro + 15, boca_y + 32), outline=preto, width=5)
    else:
        draw.ellipse((centro - olho_dx - 6, olho_y - 5, centro - olho_dx + 6, olho_y + 7), fill=preto)
        draw.ellipse((centro + olho_dx - 6, olho_y - 5, centro + olho_dx + 6, olho_y + 7), fill=preto)
        draw.line((centro - 24, boca_y + 8, centro + 24, boca_y + 8), fill=preto, width=4)


def _desenhar_area_mensagens(draw: ImageDraw.ImageDraw, layout: dict[str, Any]) -> None:
    area = layout["areas"]["mensagens"]
    msg_cfg = layout["mensagens"]
    _desenhar_retangulo(draw, area, _cor(msg_cfg["background"]))


def _desenhar_falas(draw: ImageDraw.ImageDraw, layout: dict[str, Any], cena: dict[str, Any]) -> Box | None:
    falas = extrair_falas(cena)
    if not any(valor.strip() for valor in falas.values()):
        return None

    area = layout["areas"]["mensagens"]
    msg_cfg = layout["mensagens"]
    x0, y0, x1, y1 = _box(area)
    padding_x = int(msg_cfg["padding_x"])
    padding_y = int(msg_cfg["padding_y"])
    max_w = x1 - x0 - padding_x * 2
    max_h = y1 - y0 - padding_y * 2

    font_size, blocos, line_height = _ajustar_falas(draw, falas, msg_cfg, max_w, max_h)
    fonte = _carregar_fonte(font_size, bold=True)
    x = x0 + padding_x
    y = y0 + padding_y
    bboxes: list[Box] = []

    for idioma in ("pt", "en", "es"):
        linhas = blocos[idioma]
        for linha in linhas:
            if linha:
                bbox = draw.textbbox((x, y), linha, font=fonte, stroke_width=int(msg_cfg["stroke_width"]))
                bboxes.append(bbox)
                draw.text(
                    (x, y),
                    linha,
                    fill=_cor(msg_cfg["text_color"]),
                    font=fonte,
                    stroke_width=int(msg_cfg["stroke_width"]),
                    stroke_fill=_cor(msg_cfg["stroke_color"]),
                )
            y += line_height
        y += int(msg_cfg["language_gap"])

    if not bboxes:
        return None

    return (
        min(b[0] for b in bboxes),
        min(b[1] for b in bboxes),
        max(b[2] for b in bboxes),
        max(b[3] for b in bboxes),
    )


def _ajustar_falas(
    draw: ImageDraw.ImageDraw,
    falas: dict[str, str],
    msg_cfg: dict[str, Any],
    max_w: int,
    max_h: int,
) -> tuple[int, dict[str, list[str]], int]:
    font_max = int(msg_cfg["font_size_max"])
    font_min = int(msg_cfg["font_size_min"])

    for font_size in range(font_max, font_min - 1, -1):
        fonte = _carregar_fonte(font_size, bold=True)
        blocos = {
            idioma: _quebrar_por_pixel(draw, texto, fonte, max_w)
            for idioma, texto in falas.items()
        }
        line_height = math.ceil(font_size * 1.16) + int(msg_cfg["line_gap"])
        total_linhas = sum(len(blocos[idioma]) for idioma in ("pt", "en", "es"))
        total_h = total_linhas * line_height + int(msg_cfg["language_gap"]) * 2
        if total_h <= max_h:
            return font_size, blocos, line_height

    fonte = _carregar_fonte(font_min, bold=True)
    blocos = {
        idioma: _quebrar_por_pixel(draw, texto, fonte, max_w)
        for idioma, texto in falas.items()
    }
    line_height = math.ceil(font_min * 1.12) + int(msg_cfg["line_gap"])
    return font_min, blocos, line_height


def _quebrar_por_pixel(
    draw: ImageDraw.ImageDraw,
    texto: str,
    fonte: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_w: int,
) -> list[str]:
    texto = str(texto).strip()
    if not texto:
        return []

    linhas: list[str] = []
    for bloco in texto.splitlines():
        palavras = bloco.split()
        atual = ""
        for palavra in palavras:
            tentativa = palavra if not atual else f"{atual} {palavra}"
            if draw.textlength(tentativa, font=fonte) <= max_w:
                atual = tentativa
                continue

            if atual:
                linhas.append(atual)
            atual = palavra

            while draw.textlength(atual, font=fonte) > max_w and len(atual) > 1:
                corte = max(1, int(len(atual) * max_w / draw.textlength(atual, font=fonte)))
                linhas.append(atual[:corte])
                atual = atual[corte:]

        if atual:
            linhas.append(atual)

    return linhas or [""]


def _nome_arquivo(cena: dict[str, Any], indice: int) -> str:
    falante = str(cena.get("personagem") or "grupo").lower()
    falante = falante.replace(" ", "_")
    return f"cena_{indice:03d}_{falante}.png"


def _carregar_fonte(tamanho: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidatos = []
    if config.FONT_PATH:
        candidatos.append(Path(config.FONT_PATH))

    candidatos.extend(
        [
            Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
            Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        ]
    )

    for caminho in candidatos:
        try:
            if caminho.exists():
                return ImageFont.truetype(str(caminho), tamanho)
        except OSError:
            pass

    try:
        return ImageFont.load_default(size=tamanho)
    except TypeError:
        return ImageFont.load_default()


def _carregar_imagem_opcional(caminho: Any) -> Image.Image | None:
    caminho_texto = str(caminho or "").strip()
    if not caminho_texto:
        return None

    caminho_imagem = Path(caminho_texto)
    if not caminho_imagem.is_absolute():
        caminho_imagem = config.BASE_DIR / caminho_imagem
    if not caminho_imagem.exists():
        return None

    return Image.open(caminho_imagem).convert("RGBA")


def _box(area: dict[str, Any]) -> Box:
    x, y, w, h = _xywh(area)
    return (x, y, x + w, y + h)


def _desenhar_retangulo(draw: ImageDraw.ImageDraw, area: dict[str, Any], fill: tuple[int, int, int]) -> None:
    x, y, w, h = _xywh(area)
    draw.rectangle((x, y, x + w - 1, y + h - 1), fill=fill)


def _xywh(area: dict[str, Any]) -> tuple[int, int, int, int]:
    return int(area["x"]), int(area["y"]), int(area["w"]), int(area["h"])


def _cor(valor: str | list[int] | tuple[int, int, int]) -> tuple[int, int, int]:
    if isinstance(valor, str):
        valor = valor.strip()
        if valor.startswith("#") and len(valor) == 7:
            return tuple(int(valor[i : i + 2], 16) for i in (1, 3, 5))
    if isinstance(valor, (list, tuple)) and len(valor) == 3:
        return int(valor[0]), int(valor[1]), int(valor[2])
    raise ValueError(f"Cor invalida: {valor}")


def _misturar(a: tuple[int, int, int], b: tuple[int, int, int], peso_b: float) -> tuple[int, int, int]:
    return tuple(int(ca * (1 - peso_b) + cb * peso_b) for ca, cb in zip(a, b))


def _contem(container: Box, interno: Box) -> bool:
    return (
        interno[0] >= container[0]
        and interno[1] >= container[1]
        and interno[2] <= container[2]
        and interno[3] <= container[3]
    )


def _intersecta(a: Box, b: Box) -> bool:
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]
