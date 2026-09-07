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
import timeline
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

    cenas_resolvidas: list[dict] = []
    try:
        for cena in roteiro:
            cenas_resolvidas.append(director.processar(cena))

        arquivos_timeline = timeline.salvar_timeline(cenas_resolvidas)
        if arquivos_timeline:
            json_path, csv_path = arquivos_timeline
            utils.info(f"Timeline JSON salva em: {json_path.resolve()}")
            utils.info(f"Timeline CSV salva em:  {csv_path.resolve()}")
    except Exception as exc:
        utils.erro(f"Falha ao preparar roteiro/timeline: {exc}")
        sys.exit(1)

    utils.info("Iniciando em 3 segundos... (mova o mouse ao canto superior-esquerdo para cancelar)")
    time.sleep(3)

    erros: list[str] = []
    concluidas = 0

    for i, cena_resolvida in enumerate(cenas_resolvidas, start=1):
        try:
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
