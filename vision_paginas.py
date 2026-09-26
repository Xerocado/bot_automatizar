import json

from PIL import Image, ImageChops
import pyautogui

import config

REFS_DIR = config.BASE_DIR / "refs_paginas"
TOTAL_PAGINAS = {"olhos": 7, "bocas": 13}


def recortar_numero(img):
    """Isola os digitos antes da barra, preservando paginas de dois digitos."""
    mascara = preparar(img)
    bbox = mascara.getbbox()
    if bbox is None:
        raise ValueError("Contador vazio.")
    mascara = mascara.crop(bbox)
    grupos = []
    inicio = None
    for x in range(mascara.width + 1):
        ocupado = x < mascara.width and mascara.crop((x, 0, x + 1, mascara.height)).getbbox() is not None
        if ocupado and inicio is None:
            inicio = x
        if not ocupado and inicio is not None:
            grupos.append((inicio, x))
            inicio = None
    altura = mascara.height
    fim = 0
    for esquerda, direita in grupos:
        componente = mascara.crop((esquerda, 0, direita, altura))
        limites = componente.getbbox()
        componente = componente.crop(limites)
        # Fragmentos curtos no fim sao sobras da barra de capturas manuais.
        if componente.height < altura * 0.6:
            break
        linhas = [componente.crop((0, y, componente.width, y + 1)).getbbox()
                  for y in range(componente.height)]
        linhas = [linha for linha in linhas if linha]
        quarto = max(1, len(linhas) // 4)
        topo = sum((l[0] + l[2]) / 2 for l in linhas[:quarto]) / quarto
        base = sum((l[0] + l[2]) / 2 for l in linhas[-quarto:]) / quarto
        barra = (topo - base > componente.height * 0.18
                 and max(l[2] - l[0] for l in linhas) <= componente.height * 0.25)
        if barra:
            break
        fim = direita
    if fim == 0:
        raise ValueError("Nenhum digito antes da barra do contador.")
    numero = mascara.crop((0, 0, fim, altura))
    return numero.crop(numero.getbbox())


def normalizar_numero(img):
    numero = recortar_numero(img)
    escala = min(40 / numero.width, 32 / numero.height)
    numero = numero.resize((max(1, round(numero.width * escala)),
                            max(1, round(numero.height * escala))), Image.Resampling.NEAREST)
    canvas = Image.new("L", (44, 36))
    canvas.paste(numero, ((44 - numero.width) // 2, (36 - numero.height) // 2))
    return canvas


def selecionar_referencias(tipo):
    largura, altura = config.SCREEN_RESOLUTION
    pasta = REFS_DIR / f"{largura}x{altura}"
    if pasta.is_dir():
        faltando = [n for n in range(1, TOTAL_PAGINAS[tipo] + 1)
                    if not (pasta / f"{tipo}_{n}.png").is_file()]
        if faltando:
            raise PaginaNaoReconhecida(f"Referencias incompletas em {pasta}: {tipo} {faltando}")
        return pasta, True
    if tuple(config.SCREEN_RESOLUTION) != tuple(config.COORDS_BASE_RESOLUTION):
        raise PaginaNaoReconhecida(f"Faltam referencias proprias para esta resolucao: {pasta}")
    return REFS_DIR, False


class PaginaNaoReconhecida(RuntimeError):
    """Interrompe a automacao quando o contador nao permite confirmar a pagina."""


def capturar_contador(coords):
    img = pyautogui.screenshot(
        region=(
            coords["x"],
            coords["y"],
            coords["largura"],
            coords["altura"],
        )
    )

    return img


def preparar(img):
    """
    Converte para preto/branco puro.
    Remove quase toda influência de brilho,
    transparência e anti-aliasing.
    """

    img = img.convert("L")

    img = img.point(
        lambda p: 255 if p > 120 else 0
    )

    return img


def diferenca(img1, img2):
    img1 = preparar(img1)
    img2 = preparar(img2)

    if img1.size != img2.size:
        raise ValueError(
            f"Tamanhos diferentes: "
            f"{img1.size} vs {img2.size}"
        )

    diff = ImageChops.difference(img1, img2)

    return sum(valor * quantidade for valor, quantidade in enumerate(diff.histogram()))


def detectar_pagina(tipo, coords, *, salvar_diagnostico=False):
    if tipo not in {"olhos", "bocas"}:
        raise ValueError(f"Tipo de seletor invalido: {tipo}")
    if not 0 <= config.PAGE_MAX_DIFFERENCE <= 1 or not 0 <= config.PAGE_MIN_SCORE_GAP <= 1:
        raise ValueError("PAGE_MAX_DIFFERENCE e PAGE_MIN_SCORE_GAP devem estar entre 0 e 1.")
    atual = capturar_contador(coords)
    pasta_refs, normalizar = selecionar_referencias(tipo)
    try:
        comparacao = normalizar_numero(atual) if normalizar else atual
    except ValueError:
        comparacao = None

    if config.DEBUG_SCREENSHOTS:
        atual.save("debug_atual.png")

    scores = []

    for arquivo in sorted(
        pasta_refs.glob(f"{tipo}_*.png")
    ):
        try:
            with Image.open(arquivo) as original:
                ref = original.copy()
            if normalizar:
                ref = normalizar_numero(ref)
            elif ref.size != atual.size:
                ref = ref.resize(atual.size, Image.Resampling.LANCZOS)
            score = diferenca(comparacao, ref) if comparacao is not None else ref.width * ref.height * 255
            pagina = int(arquivo.stem.split("_")[1])
        except (OSError, ValueError) as exc:
            raise PaginaNaoReconhecida(f"Referencia invalida: {arquivo}: {exc}") from exc

        print(
            f"{arquivo.name:<15} "
            f"score={score}"
        )

        scores.append({"pagina": pagina, "score": score})

    scores.sort(key=lambda item: item["score"])
    max_score = (44 * 36 if normalizar else atual.width * atual.height) * 255
    diferenca_relativa = scores[0]["score"] / max_score if scores else 1.0
    separacao = (scores[1]["score"] - scores[0]["score"]) / max_score if len(scores) > 1 else 0.0
    confiavel = (
        len(scores) > 1
        and diferenca_relativa <= config.PAGE_MAX_DIFFERENCE
        and separacao > 0
        and separacao >= config.PAGE_MIN_SCORE_GAP
    )
    print(f"Contador {tipo}: diferenca={diferenca_relativa:.1%}; separacao={separacao:.1%}")

    if not confiavel or salvar_diagnostico:
        pasta = config.OUTPUT_DIR / "debug"
        pasta.mkdir(parents=True, exist_ok=True)
        imagem = pasta / f"contador_{tipo}.png"
        atual.save(imagem)
        dados = {
            "resolucao_configurada": config.SCREEN_RESOLUTION,
            "regiao": coords, "tamanho_captura": atual.size,
            "referencias": str(pasta_refs), "scores": scores,
            "numeros_normalizados": normalizar,
            "diferenca": diferenca_relativa, "separacao": separacao,
            "confiavel": confiavel,
        }
        imagem.with_suffix(".json").write_text(
            json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8",
        )
        print(f"Diagnostico do contador salvo em: {imagem}")
    if not confiavel:
        raise PaginaNaoReconhecida(
            f"Contador de {tipo} sem correspondencia confiavel "
            f"(diferenca {diferenca_relativa:.1%}, separacao {separacao:.1%}). "
            f"Confira o recorte em {imagem} e a posicao/escala da janela do jogo."
        )
    return scores[0]["pagina"]


if __name__ == "__main__":
    import argparse
    import time
    import utils

    parser = argparse.ArgumentParser(description="Diagnosticar o contador sem mover o mouse.")
    parser.add_argument("tipo", choices=("olhos", "bocas"))
    args = parser.parse_args()
    if tuple(pyautogui.size()) != tuple(config.SCREEN_RESOLUTION):
        parser.error("SCREEN_RESOLUTION nao corresponde ao tamanho da tela.")
    print("Em 5 segundos, capturando o contador. Deixe o seletor do jogo aberto.")
    time.sleep(5)
    try:
        pagina = detectar_pagina(args.tipo, utils.carregar_coords()["PAGINA_CONTADOR"], salvar_diagnostico=True)
        print(f"Pagina reconhecida: {pagina}")
    except PaginaNaoReconhecida as exc:
        parser.exit(1, f"{exc}\n")
