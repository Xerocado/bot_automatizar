"""
utils.py — Funções utilitárias do bot Gacha Club.

Responsabilidades:
  - Carregamento dos arquivos JSON de dados.
  - Sistema de log padronizado (INFO, WARN, ERRO, DEBUG).
  - Cálculo matemático de posições no grid.
  - Quebra automática de texto para overlay.
"""

import json
import re
import textwrap
from pathlib import Path
from typing import Any

import config


# ── Logging ───────────────────────────────────────────────────────────────────

def log(nivel: str, mensagem: str) -> None:
    """Exibe uma mensagem de log formatada no terminal."""
    print(f"[{nivel.upper()}] {mensagem}")


def info(msg: str)  -> None: log("INFO",  msg)
def warn(msg: str)  -> None: log("WARN",  msg)
def erro(msg: str)  -> None: log("ERRO",  msg)

def debug(msg: str) -> None:
    """
    Exibe log de nível DEBUG.
    Sempre visível no terminal — útil para rastrear fluxo de submenus.
    Para silenciar, filtre por '[DEBUG]' no output.
    """
    log("DEBUG", msg)


# ── Carregamento de dados ─────────────────────────────────────────────────────

def carregar_json(caminho: Path) -> Any:
    """Lê e retorna o conteúdo de um arquivo JSON."""
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def carregar_coords() -> dict:
    return carregar_json(config.COORDS_FILE)


def carregar_expressoes() -> dict:
    return carregar_json(config.EXPRESSOES_FILE)


def carregar_roteiro() -> list[dict]:
    roteiro = carregar_json(config.ROTEIRO_FILE)
    if isinstance(roteiro, dict) and "cenas" in roteiro:
        return roteiro["cenas"]
    return roteiro

def carregar_presets() -> dict:
    return carregar_json(config.PRESETS_FILE)


def carregar_personalidades() -> dict:
    return carregar_json(config.PERSONALIDADES_FILE)


def carregar_personagens_config() -> dict:
    if not config.PERSONAGENS_FILE.exists():
        return {}
    return carregar_json(config.PERSONAGENS_FILE)


def normalizar_chave_personagem(nome: str) -> str:
    chave = str(nome).strip().upper()
    chave = re.sub(r"[\s-]+", "_", chave)
    chave = re.sub(r"_+", "_", chave).strip("_")

    match = re.fullmatch(r"(?:PERSONAGEM|PERSONA|CHARACTER|CHAR|P)_?(\d+)", chave)
    if match:
        return f"PERSONAGEM_{int(match.group(1))}"

    return chave


def carregar_aliases_personagens() -> dict[str, str]:
    aliases: dict[str, str] = {}
    for nome, dados in carregar_personagens_config().items():
        canonico = normalizar_chave_personagem(nome)
        aliases[canonico] = canonico

        if isinstance(dados, dict):
            for campo in ("botao", "nome"):
                if dados.get(campo):
                    aliases[normalizar_chave_personagem(dados[campo])] = canonico
            for apelido in dados.get("apelidos", []):
                aliases[normalizar_chave_personagem(apelido)] = canonico

    return aliases


def resolver_personagem(nome: str, aliases: dict[str, str] | None = None) -> str:
    chave = normalizar_chave_personagem(nome)
    if aliases and chave in aliases:
        return aliases[chave]
    return chave
# ── Grid matemático ───────────────────────────────────────────────────────────

def calcular_posicao_grid(
    grid: dict,
    pagina: int,
    linha: int,
    coluna: int,
) -> tuple[int, int]:
    """
    Calcula as coordenadas (x, y) de um item no grid de seleção.

    Índices começam em 1.
    Fórmula:
        x = primeiro_x + (coluna - 1) * dx
        y = primeiro_y + (linha  - 1) * dy

    Args:
        grid:   dicionário com primeiro_x, primeiro_y, dx, dy.
        pagina: página alvo (apenas para log; navegação feita antes).
        linha:  linha no grid (1-based).
        coluna: coluna no grid (1-based).

    Returns:
        Tupla (x, y) em pixels.
    """
    x = grid["primeiro_x"] + (coluna - 1) * grid["dx"]
    y = grid["primeiro_y"] + (linha  - 1) * grid["dy"]
    debug(f"Grid calculado → página={pagina} linha={linha} col={coluna} → ({x}, {y})")
    return x, y


# ── Quebra de texto ───────────────────────────────────────────────────────────

def quebrar_texto(texto: str, max_chars: int = config.TEXT_MAX_CHARS) -> list[str]:
    """
    Divide o comentário em linhas respeitando o limite de caracteres.

    Respeita quebras de linha manuais (\n) inseridas no roteiro — por exemplo,
    para separar blocos de idiomas diferentes (PT-BR / EN / ES). Cada bloco
    separado por \n é então quebrado individualmente pelo limite de largura.
    Linhas vazias (\n\n) são preservadas como espaçamento entre blocos.
    """
    linhas: list[str] = []
    for bloco in texto.split("\n"):
        bloco = bloco.rstrip()
        if not bloco:
            # Linha em branco intencional (espaçamento entre idiomas)
            linhas.append("")
            continue
        linhas.extend(textwrap.wrap(bloco, width=max_chars) or [""])
    return linhas