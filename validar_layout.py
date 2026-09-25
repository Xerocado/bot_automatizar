from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

sys.dont_write_bytecode = True

from PIL import Image

from reaction_director import ReactionDirector
import layout_renderer


def main() -> None:
    director = ReactionDirector()

    caminho_exemplo = Path(__file__).parent / "data" / "roteiro_layout.exemplo.json"
    with open(caminho_exemplo, encoding="utf-8") as arquivo:
        exemplos = json.load(arquivo)
    for cena in exemplos:
        assert set(cena) == {"cena", "layout", "personagens"}
        director.processar(cena)
    cena_nova = exemplos[0]

    fala_longa = (
        "PERSONAGEM 3: Esta e uma fala longa em portugues para testar a quebra automatica "
        "sem cortar palavras, sem sair da faixa inferior e mantendo espaco para os tres idiomas.\n"
        "PERSONAGEM 3: This is a long English line to test automatic wrapping without cutting "
        "the text or letting it escape from the bottom message area.\n"
        "PERSONAGEM 3: Esta es una frase larga en espanol para probar el ajuste automatico "
        "sin invadir el area verde del video ni tapar a los personajes."
    )
    cena_longa = {
        "cena": 2,
        "layout": "react_room_livepix_v1",
        "personagens": {
            "personagem_1": {"emocao": "triste", "intensidade": 2, "texto": ""},
            "personagem_2": {"emocao": "neutro", "intensidade": 1, "texto": ""},
            "personagem_3": {"emocao": "animado", "intensidade": 3, "texto": fala_longa},
            "personagem_4": {"emocao": "surpreso", "intensidade": 2, "texto": ""},
            "personagem_5": {"emocao": "tedio", "intensidade": 1, "texto": ""},
        },
    }

    cenas = [director.processar(cena_nova), director.processar(cena_longa)]
    falas_esperadas = dict(zip(
        ("pt", "en", "es"),
        cena_nova["personagens"]["personagem_1"]["texto"].splitlines(),
    ))
    assert layout_renderer.extrair_falas(cenas[0]) == falas_esperadas
    assert cenas[0]["personagem"] == "PERSONAGEM_1"
    assert layout_renderer.extrair_falas(cenas[1]) == dict(zip(
        ("pt", "en", "es"), fala_longa.splitlines(),
    ))

    cena_antiga = deepcopy(cena_nova)
    cena_antiga.pop("layout")
    assert layout_renderer.extrair_falas(director.processar(cena_antiga)) == falas_esperadas
    assert layout_renderer.carregar_layout()["nome"] == cena_nova["layout"]

    cena_com_fala = deepcopy(cena_nova)
    cena_com_fala["personagens"]["personagem_1"]["texto"] = ""
    cena_com_fala["fala"] = falas_esperadas
    resolvida_com_fala = director.processar(cena_com_fala)
    assert resolvida_com_fala["personagem"] == "PERSONAGEM_1"
    assert layout_renderer.extrair_falas(resolvida_com_fala) == falas_esperadas

    campos_removidos = {
        "video": 1, "inicio": "invalido", "fim": -1, "duracao": 99,
        "trecho": "antigo", "trecho_da_letra": "antigo", "contexto": "antigo",
        "resumo_do_trecho": "antigo", "personagem_cantando": "antigo",
    }
    assert director.processar({**cena_nova, **campos_removidos}) == cenas[0]

    cena_muda = director.processar(exemplos[2])
    assert cena_muda["personagem"] is None
    assert not any(layout_renderer.extrair_falas(cena_muda).values())
    assert not any(estado["falando"] for estado in cena_muda["personagens"].values())

    resultados = [
        layout_renderer.renderizar_cena(
            cenas[0],
            1,
            nome_arquivo="cena_001_exemplo_layout.png",
        ),
        layout_renderer.renderizar_cena(
            cenas[1],
            2,
            nome_arquivo="cena_002_fala_longa.png",
        ),
        layout_renderer.renderizar_cena(
            cena_muda,
            3,
            nome_arquivo="cena_003_muda_layout.png",
        ),
    ]

    for resultado in resultados:
        with Image.open(resultado.caminho) as img:
            assert img.format == "PNG"
            assert img.size == (1920, 1080)
            assert img.crop((1120, 120, 1880, 680)).getextrema() == (
                (0, 0), (255, 255), (0, 0),
            )
    assert all(resultado.text_box is not None for resultado in resultados[:2])
    assert resultados[2].text_box is None

    resumo = {
        "validacoes": {
            "png_1920x1080": True,
            "area_react_verde_puro": True,
            "texto_dentro_da_area_de_mensagens": True,
            "roteiro_apenas_cena_layout_personagens": True,
            "roteiro_antigo_funciona": True,
            "compatibilidade_fala_pt_en_es": True,
            "campos_temporais_ignorados": True,
            "cena_muda_funciona": True,
            "personagens_fora_da_area_react": True,
        },
        "arquivos": [str(resultado.caminho) for resultado in resultados],
    }

    print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
