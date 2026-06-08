"""
Ponto de entrada do bot Gacha Club React Scene Generator.

Uso:
    python main.py
"""

import sys
import time
from reaction_director import ReactionDirector
import config
import engine
import utils


def main() -> None:
    utils.info("=" * 40)
    utils.info("  Gacha Club - React Scene Bot")
    utils.info("=" * 40)

    engine.inicializar()
    director = ReactionDirector()

    roteiro = utils.carregar_roteiro()
    total = len(roteiro)
    utils.info(f"Roteiro carregado: {total} cena(s) encontrada(s).")

    if total == 0:
        utils.warn("Roteiro vazio. Encerrando.")
        sys.exit(0)

    utils.info("Iniciando em 3 segundos... (mova o mouse ao canto superior-esquerdo para cancelar)")
    time.sleep(3)

    erros: list[str] = []
    concluidas = 0

    for i, cena in enumerate(roteiro, start=1):
        try:
            cena_resolvida = director.processar(cena)
            engine.processar_cena(cena_resolvida, i)
            concluidas += 1
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
