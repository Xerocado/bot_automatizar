"""
Ferramenta simples para conferir e remapear olhos/bocas.

Exemplos:
    python remapear.py listar olhos
    python remapear.py listar bocas
    python remapear.py set olhos feliz_1 1 1 1
    python remapear.py set boca gritando_raiva_1 13 1 1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import utils


BASE_DIR = Path(__file__).parent
EXPRESSOES_FILE = BASE_DIR / "data" / "expressoes.json"
COORDS_FILE = BASE_DIR / "data" / "coords.json"

CATEGORIAS = {
    "olho": "olhos",
    "olhos": "olhos",
    "eye": "olhos",
    "eyes": "olhos",
    "boca": "bocas",
    "bocas": "bocas",
    "mouth": "bocas",
    "mouths": "bocas",
}

GRID_POR_CATEGORIA = {
    "olhos": "GRID_OLHOS",
    "bocas": "GRID_BOCAS",
}


def carregar_json(caminho: Path) -> dict:
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def salvar_json(caminho: Path, dados: dict) -> None:
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)
        arquivo.write("\n")


def normalizar_categoria(valor: str) -> str:
    chave = valor.strip().lower()
    if chave not in CATEGORIAS:
        opcoes = ", ".join(sorted(CATEGORIAS))
        raise SystemExit(f"Categoria invalida: {valor}. Use uma destas: {opcoes}")
    return CATEGORIAS[chave]


def validar_posicao(pagina: int, linha: int, coluna: int) -> None:
    if pagina < 1 or linha < 1 or coluna < 1:
        raise SystemExit("Pagina, linha e coluna precisam ser numeros maiores ou iguais a 1.")


def calcular_xy(grid: dict, linha: int, coluna: int) -> tuple[int, int]:
    x = grid["primeiro_x"] + (coluna - 1) * grid["dx"]
    y = grid["primeiro_y"] + (linha - 1) * grid["dy"]
    return x, y


def listar(categoria: str | None) -> None:
    expressoes = carregar_json(EXPRESSOES_FILE)
    coords = utils.carregar_coords()
    categorias = [normalizar_categoria(categoria)] if categoria else ["olhos", "bocas"]

    for nome_categoria in categorias:
        grid = coords[GRID_POR_CATEGORIA[nome_categoria]]
        print(f"\n[{nome_categoria}]")
        for nome, posicao in sorted(expressoes.get(nome_categoria, {}).items()):
            pagina, linha, coluna = posicao
            x, y = calcular_xy(grid, linha, coluna)
            print(f"{nome}: pagina={pagina} linha={linha} coluna={coluna} clique=({x}, {y})")


def setar(categoria: str, nome: str, pagina: int, linha: int, coluna: int) -> None:
    nome_categoria = normalizar_categoria(categoria)
    validar_posicao(pagina, linha, coluna)

    expressoes = carregar_json(EXPRESSOES_FILE)
    coords = utils.carregar_coords()
    expressoes.setdefault(nome_categoria, {})

    anterior = expressoes[nome_categoria].get(nome)
    expressoes[nome_categoria][nome] = [pagina, linha, coluna]
    salvar_json(EXPRESSOES_FILE, expressoes)

    grid = coords[GRID_POR_CATEGORIA[nome_categoria]]
    x, y = calcular_xy(grid, linha, coluna)

    if anterior:
        print(f"{nome_categoria}/{nome} remapeado: {anterior} -> {[pagina, linha, coluna]}")
    else:
        print(f"{nome_categoria}/{nome} criado: {[pagina, linha, coluna]}")
    print(f"Coordenada de clique calculada: ({x}, {y})")


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Conferir ou remapear expressoes do bot.")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    listar_parser = subparsers.add_parser("listar", help="Lista o mapa atual.")
    listar_parser.add_argument("categoria", nargs="?", help="olhos ou bocas")

    set_parser = subparsers.add_parser("set", help="Cria ou atualiza uma expressao.")
    set_parser.add_argument("categoria", help="olhos ou bocas")
    set_parser.add_argument("nome", help="Nome usado no roteiro, exemplo: feliz_1")
    set_parser.add_argument("pagina", type=int)
    set_parser.add_argument("linha", type=int)
    set_parser.add_argument("coluna", type=int)

    return parser


def main() -> None:
    parser = criar_parser()
    args = parser.parse_args()

    if args.comando == "listar":
        listar(args.categoria)
    elif args.comando == "set":
        setar(args.categoria, args.nome, args.pagina, args.linha, args.coluna)


if __name__ == "__main__":
    main()
