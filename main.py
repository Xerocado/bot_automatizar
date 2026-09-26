"""
Ponto de entrada do bot Gacha Club React Scene Generator.

Uso:
    python main.py
"""

import sys
import time
from reaction_director import ReactionDirector
import config
import layout_renderer
import utils


def main() -> None:
    utils.info("=" * 40)
    utils.info("  Gacha Club - React Scene Bot")
    utils.info("=" * 40)

    director = ReactionDirector()

    roteiro = utils.carregar_roteiro()
    total = len(roteiro)
    utils.info(f"Roteiro carregado: {total} cena(s) encontrada(s).")

    if total == 0:
        utils.warn("Roteiro vazio. Encerrando.")
        sys.exit(0)

    cenas_resolvidas: list[dict] = []
    try:
        for cena in roteiro:
            cenas_resolvidas.append(director.processar(cena))

    except Exception as exc:
        utils.erro(f"Falha ao preparar roteiro: {exc}")
        sys.exit(1)

    erros: list[str] = []
    concluidas = 0

    if config.RENDER_MODE == "layout":
        utils.info("Modo layout: gera PNGs sem controlar o Gacha Club.")
        for i, cena_resolvida in enumerate(cenas_resolvidas, start=1):
            try:
                layout_renderer.renderizar_cena(cena_resolvida, i)
                concluidas += 1
            except Exception as exc:
                msg = f"Cena {i:03d} falhou: {exc}"
                utils.erro(msg)
                erros.append(msg)

        utils.info("=" * 40)
        utils.info(f"Concluido: {concluidas}/{total} cena(s) gerada(s).")
        if erros:
            utils.warn(f"{len(erros)} erro(s) registrado(s):")
            for erro in erros:
                utils.erro(f"  - {erro}")
        utils.info(f"Imagens salvas em: {config.CENAS_DIR.resolve()}")
        utils.info("=" * 40)
        return

    if config.RENDER_MODE != "gacha":
        utils.erro(f"RENDER_MODE invalido: {config.RENDER_MODE}")
        sys.exit(1)

    import engine
    from vision_paginas import PaginaNaoReconhecida

    utils.info("Modo gacha: controla o Gacha Club e captura as cenas do jogo.")
    engine.inicializar()
    utils.info("Iniciando em 3 segundos... (mova o mouse ao canto superior-esquerdo para cancelar)")
    time.sleep(3)

    for i, cena_resolvida in enumerate(cenas_resolvidas, start=1):
        try:
            engine.processar_cena(cena_resolvida, i)
            concluidas += 1
        except PaginaNaoReconhecida as exc:
            msg = f"Cena {i:03d}: {exc}"
            utils.erro(msg)
            erros.append(msg)
            utils.warn("Execucao interrompida. O seletor foi mantido aberto para conferir o contador.")
            break
        except KeyboardInterrupt:
            utils.warn("Interrompido pelo usuario.")
            break
        except Exception as exc:
            msg = f"Cena {i:03d} falhou: {exc}"
            utils.erro(msg)
            erros.append(msg)

    utils.info("=" * 40)
    utils.info(f"Concluido: {concluidas}/{total} cena(s) gerada(s).")
    if erros:
        utils.warn(f"{len(erros)} erro(s) registrado(s):")
        for erro in erros:
            utils.erro(f"  - {erro}")
    utils.info(f"Imagens salvas em: {config.OUTPUT_DIR.resolve()}")
    utils.info("=" * 40)


if __name__ == "__main__":
    main()
