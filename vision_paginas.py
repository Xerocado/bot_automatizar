import json

from PIL import Image, ImageChops
import pyautogui

import config

REFS_DIR = config.BASE_DIR / "refs_paginas"


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

    if config.DEBUG_SCREENSHOTS:
        atual.save("debug_atual.png")

    scores = []

    for arquivo in sorted(
        REFS_DIR.glob(f"{tipo}_*.png")
    ):
        try:
            with Image.open(arquivo) as original:
                ref = original.copy()
            if ref.size != atual.size:
                ref = ref.resize(atual.size, Image.Resampling.LANCZOS)
            score = diferenca(atual, ref)
            pagina = int(arquivo.stem.split("_")[1])
        except (OSError, ValueError) as exc:
            raise PaginaNaoReconhecida(f"Referencia invalida: {arquivo}: {exc}") from exc

        print(
            f"{arquivo.name:<15} "
            f"score={score}"
        )

        scores.append({"pagina": pagina, "score": score})

    scores.sort(key=lambda item: item["score"])
    max_score = atual.width * atual.height * 255
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
            "referencias": str(REFS_DIR), "scores": scores,
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
