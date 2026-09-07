from pathlib import Path
from PIL import Image, ImageChops
import pyautogui

import config

REFS_DIR = Path("refs_paginas")


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

    return sum(diff.getdata())


def detectar_pagina(tipo, coords):
    atual = capturar_contador(coords)

    if config.DEBUG_SCREENSHOTS:
        atual.save("debug_atual.png")

    melhor_pagina = None
    melhor_score = float("inf")

    for arquivo in sorted(
        REFS_DIR.glob(f"{tipo}_*.png")
    ):
        ref = Image.open(arquivo)

        try:
            score = diferenca(atual, ref)
        except Exception as e:
            print(
                f"{arquivo.name:<15} "
                f"ERRO: {e}"
            )
            continue

        print(
            f"{arquivo.name:<15} "
            f"score={score}"
        )

        if score < melhor_score:
            melhor_score = score

            melhor_pagina = int(
                arquivo.stem.split("_")[1]
            )

    print()
    print("Melhor score:", melhor_score)

    return melhor_pagina
