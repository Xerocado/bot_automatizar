"""
engine.py — Motor de automação do bot Gacha Club.

Arquitetura:
  ┌─────────────────────────────────────────────────────────┐
  │  Camada 1 — Clique primitivo                            │
  │    clicar()  /  clicar_coordenada()                     │
  ├─────────────────────────────────────────────────────────┤
  │  Camada 2 — Navegação de UI (funções explícitas)        │
  │    abrir_face()                                         │
  │    abrir_submenu_olhos()                                │
  │    abrir_submenu_boca()                                 │
  ├─────────────────────────────────────────────────────────┤
  │  Camada 3 — Reset e avanço de páginas                   │
  │    _resetar_pagina_olhos()  /  _avancar_pagina_olhos()  │
  │    _resetar_pagina_bocas()  /  _avancar_pagina_bocas()  │
  ├─────────────────────────────────────────────────────────┤
  │  Camada 4 — Seleção de expressão via grid               │
  │    _aplicar_grid_olhos()                                │
  │    _aplicar_grid_boca()                                 │
  ├─────────────────────────────────────────────────────────┤
  │  Camada 5 — Fluxo completo de cena                      │
  │    processar_cena()                                     │
  └─────────────────────────────────────────────────────────┘

Fluxo correto de UI dentro do editor:
  Editor aberto
    └─ abrir_face()
         ├─ abrir_submenu_olhos() → reset páginas → avançar → grid
         └─ abrir_submenu_boca()  → reset páginas → avançar → grid
    └─ fechar editor

NÃO usa: visão computacional, OCR, locateOnScreen, OpenCV.
Tudo via coordenadas fixas + grid matemático.
"""

from __future__ import annotations

import random
import time

import pyautogui
import mss

import config
import screenshot
import utils
from vision_paginas import PaginaNaoReconhecida, detectar_pagina

# ── Estado interno ─────────────────────────────────────────────────────────────

_estado: dict = {
    "screen": "HOME",
    "category": None,
    "section": None,
    "grid": None,
    "personagem_atual": None,
    "pagina_olhos": 1,
    "pagina_bocas": 1,
}

_coords:     dict = {}
_expressoes: dict = {}
_aliases_personagens: dict = {}

def _pagina_real_olhos() -> int:
    return detectar_pagina(
        "olhos",
        _coords["PAGINA_CONTADOR"]
    )


def _pagina_real_bocas() -> int:
    return detectar_pagina(
        "bocas",
        _coords["PAGINA_CONTADOR"]
    )

def _estado_texto() -> str:
    return (
        f"screen={_estado['screen']} "
        f"category={_estado['category']} "
        f"section={_estado['section']} "
        f"grid={_estado['grid']} "
        f"pagina_olhos={_estado['pagina_olhos']} "
        f"pagina_bocas={_estado['pagina_bocas']}"
    )


def _log_estado(contexto: str) -> None:
    utils.debug(f"[STATE] {contexto}: {_estado_texto()}")


def _texto_da_cena(cena: dict) -> str:
    """
    Aceita roteiros antigos com 'comentario' e roteiros novos com 'texto'.
    """
    for chave in ("comentario", "comentário", "texto"):
        if chave in cena:
            return str(cena[chave])
    utils.warn("Cena sem campo de texto/comentario; usando comentario vazio.")
    return ""


def _personagem_da_cena(cena: dict) -> str:
    """
    Normaliza o nome do personagem para a chave usada em coords.json.
    """
    personagem = utils.resolver_personagem(cena["personagem"], _aliases_personagens)
    botoes = _coords.get("BOTOES", {})
    if personagem in botoes:
        return personagem

    personagem_upper = personagem.upper()
    if personagem_upper in botoes:
        return personagem_upper

    return personagem


def _pagina_conhecida(chave_estado: str) -> bool:
    pagina = _estado.get(chave_estado)
    return isinstance(pagina, int) and pagina >= 1


def _resetar_pagina_dinamica(chave_estado: str, botao_retroceder: str, rotulo: str) -> None:
    """
    Retorna para a pagina 1 usando o estado interno quando ele e confiavel.
    Se o estado estiver desconhecido, preserva o fallback antigo PAGE_RESET_CLICKS.
    """
    pagina_atual = _estado.get(chave_estado)

    if _pagina_conhecida(chave_estado):
        cliques = max(pagina_atual - 1, 0)
        utils.info(f"Resetando paginas de {rotulo}: pagina atual={pagina_atual} -> 1 ({cliques}x retroceder).")
    else:
        cliques = config.PAGE_RESET_CLICKS
        utils.warn(
            f"Pagina atual de {rotulo} desconhecida; usando fallback seguro "
            f"de {config.PAGE_RESET_CLICKS}x retroceder."
        )

    for _ in range(cliques):
        clicar(botao_retroceder, delay=config.DELAY_CURTO)

    _estado[chave_estado] = 1
    utils.info(f"Paginas de {rotulo}: pagina 1 garantida.")
    _log_estado(f"depois resetar pagina {rotulo}")


def _ir_para_pagina_dinamica(
    chave_estado: str,
    botao_retroceder: str,
    botao_avancar: str,
    pagina_alvo: int,
    rotulo: str,
) -> None:
    """
    Move diretamente da pagina conhecida para a pagina alvo.
    Ex.: se esta na pagina 3 e precisa ir para 1, clica apenas 2x retroceder.
    """
    if pagina_alvo < 1:
        raise ValueError(f"Pagina alvo invalida para {rotulo}: {pagina_alvo}")

    pagina_atual = _estado.get(chave_estado)
    if not _pagina_conhecida(chave_estado):
        utils.warn(f"Pagina atual de {rotulo} desconhecida; reset dinamico usara fallback seguro.")
        _resetar_pagina_dinamica(chave_estado, botao_retroceder, rotulo)
        pagina_atual = _estado[chave_estado]

    delta = pagina_alvo - pagina_atual
    if delta == 0:
        utils.info(f"{rotulo.capitalize()}: ja esta na pagina {pagina_alvo}, sem troca de pagina.")
    elif delta > 0:
        utils.info(f"Avancando {rotulo}: pagina {pagina_atual} -> {pagina_alvo} ({delta}x avancar).")
        for _ in range(delta):
            clicar(botao_avancar, delay=config.DELAY_CURTO)
    else:
        cliques = abs(delta)
        utils.info(f"Retrocedendo {rotulo}: pagina {pagina_atual} -> {pagina_alvo} ({cliques}x retroceder).")
        for _ in range(cliques):
            clicar(botao_retroceder, delay=config.DELAY_CURTO)

    _estado[chave_estado] = pagina_alvo
    _log_estado(f"depois ir para pagina {rotulo}")


# ══════════════════════════════════════════════════════════════════════════════
# CAMADA 1 — Clique primitivo
# ══════════════════════════════════════════════════════════════════════════════

def _mover_e_clicar(x: int, y: int, delay: float) -> None:
    """
    Núcleo do sistema de clique.

    Se DEBUG_MOUSE=True: move o mouse e pausa 1s antes de clicar,
    permitindo inspecionar visualmente o alvo antes da ação.
    """
    jitter = config.CLICK_JITTER
    xr = x + random.randint(-jitter, jitter)
    yr = y + random.randint(-jitter, jitter)

    pyautogui.moveTo(xr, yr, duration=config.CLICK_DURATION)

    if config.DEBUG_MOUSE:
        utils.debug(f"[DEBUG_MOUSE] Mouse em ({xr}, {yr}) — aguardando 1s antes de clicar...")
        time.sleep(1.0)

    pyautogui.click()
    time.sleep(delay)


def clicar(nome_botao: str, delay: float = config.DELAY_CURTO) -> None:
    """
    Clica em um botão nomeado do coords.json.

    Args:
        nome_botao: Chave em BOTOES do coords.json.
        delay:      Pausa após o clique.
    """
    botoes = _coords["BOTOES"]
    if nome_botao not in botoes:
        utils.erro(f"Botão desconhecido: '{nome_botao}'")
        raise KeyError(f"Botão '{nome_botao}' não encontrado em coords.json")

    coordenada = botoes[nome_botao]
    if coordenada is None:
        msg = f"Coordenada pendente para '{nome_botao}' em coords.json"
        utils.erro(msg)
        raise ValueError(msg)

    x, y = coordenada
    utils.debug(f"[CLICK_STATE] {_estado_texto()}")
    utils.info(f"Clicando em '{nome_botao}' → base ({x}, {y})")
    _mover_e_clicar(x, y, delay)


def clicar_coordenada(x: int, y: int, delay: float = config.DELAY_CURTO) -> None:
    """
    Clica em uma coordenada absoluta — usado exclusivamente pelo grid matemático.

    Args:
        x, y:  Coordenadas calculadas pelo grid.
        delay: Pausa após o clique.
    """
    utils.info(f"Clicando em coordenada grid ({x}, {y})")
    _mover_e_clicar(x, y, delay)


# ══════════════════════════════════════════════════════════════════════════════
# CAMADA 2 — Navegação de UI (funções explícitas de menu)
# ══════════════════════════════════════════════════════════════════════════════

def abrir_face() -> None:
    """
    Abre o menu Face dentro do editor do personagem.

    Pré-condição:  Editor está aberto.
    Pós-condição:  Menu Face está visível com os submenus disponíveis.
    """
    utils.debug("Abrindo menu Face...")
    clicar("quickjump_face", delay=config.DELAY_MEDIO)
    utils.debug("Menu Face aberto.")


def abrir_submenu_olhos() -> None:
    """
    Fluxo correto:
    Face -> Eyes -> submenu olhos.
    """

    utils.debug("Abrindo menu Eyes...")
    clicar("quickjump_eyes", delay=config.DELAY_SUBMENU)

    utils.debug("Abrindo submenu de olhos...")

    clicar("selector_olhos", delay=config.DELAY_SUBMENU)

    utils.debug("Submenu de olhos aberto.")


def abrir_submenu_boca() -> None:
    """
    Abre o submenu de boca dentro do menu Face.

    Pré-condição:  Menu Face está visível (abrir_face() foi chamado).
                   NÃO precisa fechar o submenu de olhos antes — o jogo
                   faz a troca automaticamente ao clicar em 'boca'.
    Pós-condição:  Grade de opções de boca está visível.
    """
    utils.debug("Abrindo submenu de boca...")
    clicar("selector_boca", delay=config.DELAY_SUBMENU)
    utils.debug("Submenu de boca aberto. Grade de bocas visível.")


# ══════════════════════════════════════════════════════════════════════════════
# CAMADA 3 — Reset e avanço de páginas
# ══════════════════════════════════════════════════════════════════════════════

def ir_para_secao_eyes() -> None:
    """
    Fluxo correto observado no video:
    Quick Jump -> Eyes -> painel Head/Eyes.
    """
    _log_estado("antes ir_para_secao_eyes")
    if _estado["screen"] == "EDITOR" and _estado["section"] == "EYES" and _estado["grid"] is None:
        utils.debug("Secao Eyes ja esta ativa; clique ignorado.")
        return

    utils.debug("Abrindo secao Eyes pelo Quick Jump...")
    clicar("quickjump_eyes", delay=config.DELAY_SUBMENU)
    _estado.update({"screen": "EDITOR", "category": "HEAD", "section": "EYES", "grid": None})
    _log_estado("depois ir_para_secao_eyes")


def abrir_grid_olhos() -> None:
    """
    Abre o grid Face - Both Eyes a partir do painel Head/Eyes.
    """
    _log_estado("antes abrir_grid_olhos")

    if _estado["grid"] == "BOTH_EYES":
        utils.debug("Grid de olhos ja esta aberto; clique ignorado.")
        return

    if _estado["section"] != "EYES":
        utils.warn(
            f"Esperado section=EYES antes do grid de olhos; "
            f"estado atual: {_estado_texto()}"
        )

    utils.debug(
        f"[DEBUG PAGINA OLHOS] Antes de abrir grid -> "
        f"pagina_olhos={_estado.get('pagina_olhos')}"
    )

    utils.debug("Abrindo grid Face - Both Eyes...")
    clicar("selector_olhos", delay=config.DELAY_SUBMENU)

    _estado.update({
        "screen": "EDITOR",
        "category": "HEAD",
        "section": "EYES",
        "grid": "BOTH_EYES",
        # NÃO mexer em pagina_olhos aqui
    })

    utils.debug(
        f"[DEBUG PAGINA OLHOS] Depois de abrir grid -> "
        f"pagina_olhos={_estado.get('pagina_olhos')}"
    )

    _log_estado("depois abrir_grid_olhos")

def ir_para_secao_face() -> None:
    """
    Troca do painel Head/Eyes para Head/Face dentro do editor.
    """
    _log_estado("antes ir_para_secao_face")
    if _estado["screen"] == "EDITOR" and _estado["section"] == "FACE" and _estado["grid"] is None:
        utils.debug("Secao Face ja esta ativa; clique ignorado.")
        return

    if _estado["section"] == "EYES":
        utils.debug("Fechando painel/submenu de olhos antes de trocar para Face...")
        clicar("fechar_x", delay=config.DELAY_MEDIO)

    utils.debug("Abrindo aba Face dentro do editor...")
    clicar("tab_face", delay=config.DELAY_SUBMENU)
    _estado.update({"screen": "EDITOR", "category": "HEAD", "section": "FACE", "grid": None})
    _log_estado("depois ir_para_secao_face")


def abrir_grid_boca() -> None:
    """
    Abre o grid Face - Mouth a partir do painel Head/Face.
    """
    _log_estado("antes abrir_grid_boca")

    if _estado["grid"] == "MOUTH":
        utils.debug("Grid de boca ja esta aberto; clique ignorado.")
        return

    if _estado["section"] != "FACE":
        utils.warn(
            f"Esperado section=FACE antes do grid de boca; "
            f"estado atual: {_estado_texto()}"
        )

    utils.debug(
        f"[DEBUG PAGINA BOCAS] Antes de abrir grid -> "
        f"pagina_bocas={_estado.get('pagina_bocas')}"
    )

    utils.debug("Abrindo grid Face - Mouth...")
    clicar("selector_boca", delay=config.DELAY_SUBMENU)

    _estado.update({
        "screen": "EDITOR",
        "category": "HEAD",
        "section": "FACE",
        "grid": "MOUTH",
        # NÃO mexer em pagina_bocas aqui
    })

    utils.debug(
        f"[DEBUG PAGINA BOCAS] Depois de abrir grid -> "
        f"pagina_bocas={_estado.get('pagina_bocas')}"
    )

    _log_estado("depois abrir_grid_boca")


def _resetar_pagina_olhos() -> None:
    """
    Garante retorno à página 1 do submenu de olhos.
    Usa o estado interno para clicar apenas o necessário em 'retroceder'.

    Pré-condição: submenu de olhos está aberto.
    """
    _resetar_pagina_dinamica("pagina_olhos", "retroceder_pagina_olhos", "olhos")


def _avancar_pagina_olhos(pagina_alvo: int) -> None:
    """
    Avança da página atual conhecida até pagina_alvo no submenu de olhos.

    Pré-condição: submenu de olhos está aberto.
    """
    pagina_atual = _estado["pagina_olhos"] if _pagina_conhecida("pagina_olhos") else 1
    passos = pagina_alvo - pagina_atual
    if passos <= 0:
        utils.info(f"Olhos: página alvo {pagina_alvo} não exige avanço.")
        return
    utils.info(f"Avançando olhos: página {pagina_atual} -> {pagina_alvo} ({passos}x avançar)")
    for _ in range(passos):
        clicar("avancar_pagina_olhos", delay=config.DELAY_CURTO)
    _estado["pagina_olhos"] = pagina_alvo


def _ir_para_pagina_olhos(pagina_alvo: int):
    pagina_atual = _pagina_real_olhos()

    utils.info(
        f"[VISION OLHOS] atual={pagina_atual} "
        f"alvo={pagina_alvo}"
    )

    tentativas = 0

    while pagina_atual != pagina_alvo:
        tentativas += 1

        if tentativas > 20:
            raise RuntimeError(
                f"Não consegui chegar na página {pagina_alvo}"
            )

        if pagina_atual < pagina_alvo:
            clicar(
                "avancar_pagina_olhos",
                delay=config.DELAY_CURTO
            )
        else:
            clicar(
                "retroceder_pagina_olhos",
                delay=config.DELAY_CURTO
            )

        time.sleep(0.15)

        pagina_atual = _pagina_real_olhos()

    utils.info(
        f"[VISION OLHOS] página confirmada={pagina_atual}"
    )

    _estado["pagina_olhos"] = pagina_atual


def _resetar_pagina_bocas() -> None:
    """
    Garante retorno à página 1 do submenu de bocas.
    Usa o estado interno para clicar apenas o necessário em 'retroceder'.

    Pré-condição: submenu de boca está aberto.
    """
    _resetar_pagina_dinamica("pagina_bocas", "retroceder_pagina_bocas", "bocas")


def _avancar_pagina_bocas(pagina_alvo: int) -> None:
    """
    Avança da página atual conhecida até pagina_alvo no submenu de bocas.

    Pré-condição: submenu de boca está aberto.
    """
    pagina_atual = _estado["pagina_bocas"] if _pagina_conhecida("pagina_bocas") else 1
    passos = pagina_alvo - pagina_atual
    if passos <= 0:
        utils.info(f"Boca: página alvo {pagina_alvo} não exige avanço.")
        return
    utils.info(f"Avançando bocas: página {pagina_atual} -> {pagina_alvo} ({passos}x avançar)")
    for _ in range(passos):
        clicar("avancar_pagina_bocas", delay=config.DELAY_CURTO)
    _estado["pagina_bocas"] = pagina_alvo


def _ir_para_pagina_bocas(pagina_alvo: int):
    pagina_atual = _pagina_real_bocas()

    utils.info(
        f"[VISION BOCAS] atual={pagina_atual} "
        f"alvo={pagina_alvo}"
    )

    tentativas = 0

    while pagina_atual != pagina_alvo:
        tentativas += 1

        if tentativas > 30:
            raise RuntimeError(
                f"Não consegui chegar na página {pagina_alvo}"
            )

        if pagina_atual < pagina_alvo:
            clicar(
                "avancar_pagina_bocas",
                delay=config.DELAY_CURTO
            )
        else:
            clicar(
                "retroceder_pagina_bocas",
                delay=config.DELAY_CURTO
            )

        time.sleep(0.15)

        pagina_atual = _pagina_real_bocas()

    utils.info(
        f"[VISION BOCAS] página confirmada={pagina_atual}"
    )

    _estado["pagina_bocas"] = pagina_atual
    utils.debug(
        f"[DEBUG PAGINA BOCAS] atual={_estado.get('pagina_bocas')} "
        f"alvo={pagina_alvo}"
    )

    _ir_para_pagina_dinamica(
        "pagina_bocas",
        "retroceder_pagina_bocas",
        "avancar_pagina_bocas",
        pagina_alvo,
        "bocas",
    )

    utils.debug(
        f"[DEBUG PAGINA BOCAS] final={_estado.get('pagina_bocas')}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# CAMADA 4 — Seleção de expressão via grid matemático
# ══════════════════════════════════════════════════════════════════════════════

def _aplicar_grid_olhos(nome_expressao: str) -> None:
    """
    Navega até a expressão de olho correta e clica via grid matemático.

    Pré-condição: submenu de olhos está aberto (abrir_submenu_olhos() chamado).

    Sequência interna:
      reset páginas → avançar até página → calcular coordenada → clicar
    """
    olhos_map = _expressoes.get("olhos", {})
    if nome_expressao not in olhos_map:
        raise ValueError(f"Expressão de olhos '{nome_expressao}' não mapeada em expressoes.json")

    pagina, linha, coluna = olhos_map[nome_expressao]
    grid = _coords["GRID_OLHOS"]

    utils.debug(
        f"Aplicando grid olhos: expressao='{nome_expressao}' "
        f"pagina_alvo={pagina} linha={linha} coluna={coluna}"
    )

    # Captura de debug antes do clique no grid
    if config.DEBUG_SCREENSHOTS:
        _salvar_debug_screenshot("antes_olhos")


    utils.warn(
    f"[SYNC OLHOS] estado={_estado.get('pagina_olhos')} "
    f"alvo={pagina} "
    f"expressao={nome_expressao}"
    )
    _ir_para_pagina_olhos(pagina)

    x, y = utils.calcular_posicao_grid(grid, pagina, linha, coluna)
    utils.debug(f"Aplicando grid olhos → clique em ({x}, {y})")
    clicar_coordenada(x, y, delay=config.DELAY_MEDIO)
    _estado.update({"screen": "EDITOR", "category": "HEAD", "section": "EYES", "grid": None})
    _log_estado("depois aplicar olhos")


def _aplicar_grid_boca(nome_expressao: str) -> None:
    """
    Navega até a expressão de boca correta e clica via grid matemático.

    Pré-condição: submenu de boca está aberto (abrir_submenu_boca() chamado).
    """
    bocas_map = _expressoes.get("bocas", {})
    if nome_expressao not in bocas_map:
        raise ValueError(f"Expressão de boca '{nome_expressao}' não mapeada em expressoes.json")

    pagina, linha, coluna = bocas_map[nome_expressao]
    grid = _coords["GRID_BOCAS"]

    utils.debug(
        f"Aplicando grid boca: expressao='{nome_expressao}' "
        f"pagina_alvo={pagina} linha={linha} coluna={coluna}"
    )

    # Captura de debug antes do clique no grid
    if config.DEBUG_SCREENSHOTS:
        _salvar_debug_screenshot("antes_boca")

    _ir_para_pagina_bocas(pagina)

    x, y = utils.calcular_posicao_grid(grid, pagina, linha, coluna)
    utils.debug(f"Aplicando grid boca → clique em ({x}, {y})")
    clicar_coordenada(x, y, delay=config.DELAY_MEDIO)
    _estado.update({"screen": "EDITOR", "category": "HEAD", "section": "FACE", "grid": None})
    _log_estado("depois aplicar boca")


# ══════════════════════════════════════════════════════════════════════════════
# UTILITÁRIO DE DEBUG
# ══════════════════════════════════════════════════════════════════════════════

def _salvar_debug_screenshot(nome: str) -> None:
    """
    Salva uma screenshot de diagnóstico na pasta output/debug/.
    Chamado automaticamente quando DEBUG_SCREENSHOTS=True.
    """
    try:
        debug_dir = config.OUTPUT_DIR / "debug"
        debug_dir.mkdir(parents=True, exist_ok=True)

        img = screenshot.capturar_tela()
        caminho = debug_dir / f"{nome}.png"
        img.save(str(caminho))
        utils.debug(f"Debug screenshot salva → {caminho}")
    except Exception as e:
        utils.warn(f"Falha ao salvar debug screenshot '{nome}': {e}")


# ══════════════════════════════════════════════════════════════════════════════
# INICIALIZAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

def inicializar() -> None:
    """
    Configura pyautogui e carrega todos os dados JSON.
    Deve ser chamado uma única vez no início da execução.
    """
    global _coords, _expressoes, _aliases_personagens

    esperado = tuple(config.SCREEN_RESOLUTION)
    with mss.mss() as sct:
        if not 0 < config.MONITOR_INDEX < len(sct.monitors):
            raise ValueError(f"MONITOR_INDEX invalido: {config.MONITOR_INDEX}")
        monitor = sct.monitors[config.MONITOR_INDEX]
    tamanho_mss = (monitor["width"], monitor["height"])
    tamanho_mouse = tuple(pyautogui.size())
    if tamanho_mss != esperado or tamanho_mouse != esperado or (monitor["left"], monitor["top"]) != (0, 0):
        raise RuntimeError(
            f"Resolucao configurada: {esperado}; monitor MSS: {tamanho_mss} "
            f"na posicao ({monitor['left']}, {monitor['top']}); mouse: {tamanho_mouse}. "
            "Use o monitor principal na resolucao configurada e confira a escala do Windows."
        )

    pyautogui.FAILSAFE = config.FAILSAFE
    utils.info(f"FAILSAFE {'ativado' if config.FAILSAFE else 'desativado'}.")

    if config.DEBUG_MOUSE:
        utils.debug("DEBUG_MOUSE ativado: mouse pausará 1s antes de cada clique.")
    if config.DEBUG_SCREENSHOTS:
        utils.debug("DEBUG_SCREENSHOTS ativado: capturas antes_olhos.png e antes_boca.png serão salvas.")

    _coords     = utils.carregar_coords()
    _expressoes = utils.carregar_expressoes()
    _aliases_personagens = utils.carregar_aliases_personagens()

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    utils.info("Engine inicializado. Dados carregados.")


def recuperar_para_home(motivo: str = "") -> None:
    """
    Tenta devolver a UI para HOME depois de uma falha no editor ou no estudio.
    Nao usa OCR: aplica uma sequencia curta e previsivel de close/escape/home.
    """
    if motivo:
        utils.warn(f"Recovery para HOME iniciado: {motivo}")
    else:
        utils.warn("Recovery para HOME iniciado.")
    _log_estado("antes recuperar_para_home")

    try:
        if _estado["screen"] in {"EDITOR", "QUICK_JUMP"} or _estado["grid"] is not None:
            utils.warn("Recovery: tentando fechar editor com fechar_x.")
            clicar("fechar_x", delay=config.DELAY_LONGO)
        elif _estado["screen"] == "STUDIO":
            utils.warn("Recovery: estado STUDIO detectado; usando apenas Esc porque voltar_home foi removido.")
    except pyautogui.FailSafeException:
        raise
    except Exception as exc:
        utils.warn(f"Recovery: falha ao clicar no botao de retorno conhecido: {exc}")

    for tentativa in range(config.RECOVERY_ESCAPE_PRESSES):
        try:
            utils.debug(f"Recovery: pressionando Esc ({tentativa + 1}/{config.RECOVERY_ESCAPE_PRESSES}).")
            pyautogui.press("esc")
            time.sleep(config.DELAY_RECOVERY)
        except pyautogui.FailSafeException:
            raise
        except Exception as exc:
            utils.warn(f"Recovery: falha ao pressionar Esc: {exc}")
            break

    _estado.update({
        "screen": "HOME",
        "category": None,
        "section": None,
        "grid": None,
        "pagina_olhos": None,
        "pagina_bocas": None,
    })
    _log_estado("depois recuperar_para_home")


# ══════════════════════════════════════════════════════════════════════════════
# CAMADA 5 — Fluxo completo de cena
# ══════════════════════════════════════════════════════════════════════════════

def processar_cena(cena: dict, indice: int) -> None:
    """
    Executa uma cena com recovery basico em caso de falha de UI.
    """
    if _estado["screen"] not in {"HOME", "STUDIO"}:
        recuperar_para_home(f"estado inicial inesperado antes da cena {indice:03d}")

    try:
        _processar_cena_impl(cena, indice)
    except pyautogui.FailSafeException:
        raise
    except PaginaNaoReconhecida:
        _estado.update({"pagina_olhos": None, "pagina_bocas": None})
        raise
    except Exception as exc:
        recuperar_para_home(f"Cena {indice:03d} falhou: {exc}")
        raise


def _processar_cena_impl(cena: dict, indice: int) -> None:
    """
    Executa uma cena.

    Roteiro antigo: aplica um personagem e captura.
    Roteiro novo: aplica o estado de todos os personagens e captura uma
    unica imagem final da cena.
    """
    personagens = _personagens_da_cena(cena)
    comentario = _texto_da_cena(cena)
    falante = _falante_da_cena(cena, personagens)
    rotulo = falante or "GRUPO"

    utils.info(f"=== CENA {indice:03d} | {rotulo} ===")
    utils.info(f"  personagens: {len(personagens)}")
    utils.info(f"  texto: {comentario}")

    for posicao, (personagem, estado_personagem) in enumerate(personagens, start=1):
        _aplicar_estado_personagem(
            personagem,
            estado_personagem["olhos"],
            estado_personagem["boca"],
            posicao,
            len(personagens),
        )

    _capturar_cena(indice, rotulo, comentario)
    utils.info(f"Cena {indice:03d} concluida.\n")


def _personagens_da_cena(cena: dict) -> list[tuple[str, dict]]:
    if "personagens" not in cena:
        comentario = _texto_da_cena(cena)
        personagem = _personagem_da_cena(cena)
        return [
            (
                personagem,
                {
                    "olhos": cena["olhos"],
                    "boca": cena["boca"],
                    "texto": comentario,
                    "falando": bool(comentario.strip()),
                },
            )
        ]

    personagens = cena["personagens"]
    if isinstance(personagens, dict):
        return [
            (_normalizar_personagem(nome), estado)
            for nome, estado in personagens.items()
        ]

    if isinstance(personagens, list):
        return [
            (
                _normalizar_personagem(estado["personagem"]),
                {chave: valor for chave, valor in estado.items() if chave != "personagem"},
            )
            for estado in personagens
        ]

    raise TypeError("'personagens' deve ser um objeto ou uma lista")


def _normalizar_personagem(nome: str) -> str:
    personagem = utils.resolver_personagem(nome, _aliases_personagens)
    botoes = _coords.get("BOTOES", {})
    if personagem in botoes:
        return personagem

    personagem_upper = personagem.upper()
    if personagem_upper in botoes:
        return personagem_upper

    return personagem


def _falante_da_cena(cena: dict, personagens: list[tuple[str, dict]]) -> str | None:
    if cena.get("personagem"):
        return _normalizar_personagem(cena["personagem"])

    falantes = [
        personagem
        for personagem, estado in personagens
        if estado.get("falando") or str(estado.get("texto", "")).strip()
    ]
    if falantes:
        return falantes[0]
    return None


def _aplicar_estado_personagem(
    personagem: str,
    nome_olhos: str,
    nome_boca: str,
    posicao: int,
    total: int,
) -> None:
    utils.info(f"[{posicao}/{total}] Atualizando {personagem}")
    utils.info(f"  olhos: {nome_olhos}")
    utils.info(f"  boca:  {nome_boca}")

    clicar(personagem, delay=config.DELAY_MEDIO)
    _estado["personagem_atual"] = personagem

    utils.info("Abrindo editor...")
    clicar("editar", delay=config.DELAY_LONGO)
    _estado.update({"screen": "QUICK_JUMP", "category": None, "section": None, "grid": None})
    _log_estado("depois abrir editor")

    utils.info("Indo para secao Eyes pelo Quick Jump...")
    ir_para_secao_eyes()

    utils.info(f"Selecionando olhos: '{nome_olhos}'")
    abrir_grid_olhos()
    _aplicar_grid_olhos(nome_olhos)

    utils.info(f"Selecionando boca: '{nome_boca}'")
    ir_para_secao_face()
    abrir_grid_boca()
    _aplicar_grid_boca(nome_boca)

    utils.info("Fechando editor...")
    time.sleep(config.DELAY_MEDIO)
    clicar("fechar_x", delay=config.DELAY_LONGO)
    _estado.update({"screen": "HOME", "category": None, "section": None, "grid": None})
    _log_estado("depois fechar editor")

    _retornar_para_tela_de_personagens()


def _retornar_para_tela_de_personagens() -> None:
    utils.info("Retornando para tela de personagens...")
    clicar("estudio", delay=config.DELAY_LONGO)
    _estado.update({"screen": "STUDIO", "category": None, "section": None, "grid": None})
    _log_estado("depois retornar para tela de personagens")


def _capturar_cena(indice: int, rotulo: str, comentario: str) -> None:
    if _estado["screen"] != "STUDIO":
        utils.info("Navegando para Estudio...")
        clicar("estudio", delay=config.DELAY_LONGO)
        _estado.update({"screen": "STUDIO", "category": None, "section": None, "grid": None})
        _log_estado("depois abrir estudio")
    else:
        utils.debug("Estudio ja esta aberto; seguindo para captura.")

    utils.info("Ocultando HUD e capturando screenshot...")
    clicar("ocultar_interface", delay=config.DELAY_LONGO)
    img = screenshot.capturar_tela()

    utils.info("Restaurando HUD...")
    clicar("ocultar_interface", delay=config.DELAY_MEDIO)

    utils.info("Adicionando comentario e salvando...")
    img_final = screenshot.adicionar_comentario(img, comentario)
    nome_arquivo = f"cena_{indice:03d}_{rotulo.lower()}.png"
    screenshot.salvar_imagem(img_final, nome_arquivo)


def _processar_cena_impl_antigo(cena: dict, indice: int) -> None:
    """
    Executa o pipeline completo para uma cena do roteiro.

    Fluxo de UI (tudo acontece dentro do mesmo menu Face — sem sair):

        [Selecionar personagem]
        [Editar]
        abrir_face()
          abrir_submenu_olhos()
            _aplicar_grid_olhos()     ← reset páginas → avançar → clique
          abrir_submenu_boca()        ← ainda dentro de Face, sem fechar
            _aplicar_grid_boca()      ← reset páginas → avançar → clique
        [Fechar editor]
        [Estúdio → ocultar HUD → screenshot → restaurar HUD]

    Args:
        cena:   Dict com personagem, olhos, boca, comentario/texto.
        indice: Número da cena (usado no nome do arquivo de saída).
    """
    personagem = _personagem_da_cena(cena)
    nome_olhos = cena["olhos"]
    nome_boca  = cena["boca"]
    comentario = _texto_da_cena(cena)

    utils.info(f"═══ CENA {indice:03d} | {personagem} ═══")
    utils.info(f"  olhos: {nome_olhos}")
    utils.info(f"  boca:  {nome_boca}")
    utils.info(f"  texto: {comentario}")

    # ── 1. Selecionar personagem ──────────────────────────────────────────────
    utils.info(f"[1/9] Selecionando personagem {personagem}")
    clicar(personagem, delay=config.DELAY_MEDIO)
    _estado["personagem_atual"] = personagem

    # ── 2. Abrir editor ───────────────────────────────────────────────────────
    utils.info("[2/9] Abrindo editor...")
    clicar("editar", delay=config.DELAY_LONGO)
    _estado.update({"screen": "QUICK_JUMP", "category": None, "section": None, "grid": None})
    _log_estado("depois abrir editor")

    # ── 3. Abrir menu Face ────────────────────────────────────────────────────
    utils.info("[3/9] Indo para secao Eyes pelo Quick Jump...")
    ir_para_secao_eyes()

    # ── 4. Submenu olhos → grid ───────────────────────────────────────────────
    # Permanece dentro do menu Face.
    utils.info(f"[4/9] Selecionando olhos: '{nome_olhos}'")
    abrir_grid_olhos()
    _aplicar_grid_olhos(nome_olhos)

    # ── 5. Submenu boca → grid ────────────────────────────────────────────────
    # NÃO fecha Face. NÃO volta ao home.
    # Fluxo original preservado para referencia:
    #   abrir_submenu_boca()  # clicava direto em selector_boca apos Eyes.
    # Fluxo seguro atual: Eyes -> fechar_x -> tab_face -> selector_boca.
    # fechar_x aqui fecha o painel/submenu ativo de olhos antes de trocar para Face.
    utils.info(f"[5/9] Selecionando boca: '{nome_boca}'")
    ir_para_secao_face()
    abrir_grid_boca()
    _aplicar_grid_boca(nome_boca)

    # ── 6. Fechar editor ──────────────────────────────────────────────────────
    utils.info("[6/9] Fechando editor...")
    time.sleep(config.DELAY_MEDIO)   # aguarda jogo registrar última seleção
    clicar("fechar_x", delay=config.DELAY_LONGO)
    _estado.update({"screen": "HOME", "category": None, "section": None, "grid": None})
    _log_estado("depois fechar editor")

    # ── 7. Navegar para Estúdio ───────────────────────────────────────────────
    utils.info("[7/9] Navegando para Estúdio...")
    clicar("estudio", delay=config.DELAY_LONGO)
    _estado.update({"screen": "STUDIO", "category": None, "section": None, "grid": None})
    _log_estado("depois abrir estudio")

    # ── 8. Screenshot limpa ───────────────────────────────────────────────────
    utils.info("[8/9] Ocultando HUD e capturando screenshot...")
    clicar("ocultar_interface", delay=config.DELAY_LONGO)

    img = screenshot.capturar_tela()

    utils.info("[8/9] Restaurando HUD...")
    clicar("ocultar_interface", delay=config.DELAY_MEDIO)

    # ── 9. Salvar imagem com comentário ──────────────────────────────────────
    utils.info("[9/9] Adicionando comentário e salvando...")
    img_final    = screenshot.adicionar_comentario(img, comentario)
    nome_arquivo = f"cena_{indice:03d}_{personagem.lower()}.png"
    screenshot.salvar_imagem(img_final, nome_arquivo)

    utils.info(f"✓ Cena {indice:03d} concluída.\n")
