from __future__ import annotations

import csv
import json
import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

import config


CAMPOS_TIMELINE = (
    "inicio",
    "fim",
    "duracao",
    "trecho",
    "trecho_da_letra",
    "contexto",
    "resumo_do_trecho",
    "personagem_cantando",
    "cantor",
    "personagem_cantor",
    "fala",
)

TIME_RE = re.compile(
    r"^(?:(\d{1,2}):(\d{1,2}):(\d{2})(?:[.,](\d+))?|(\d{1,2}):(\d{2})(?:[.,](\d+))?)$"
)


def salvar_timeline(cenas: list[dict[str, Any]]) -> tuple[Path, Path] | None:
    if not any(_tem_timeline(cena) for cena in cenas):
        return None

    linhas = [_normalizar_linha(cena, indice) for indice, cena in enumerate(cenas, start=1)]

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(config.TIMELINE_JSON_FILE, "w", encoding="utf-8") as arquivo:
        json.dump(linhas, arquivo, ensure_ascii=False, indent=2)
        arquivo.write("\n")

    with open(config.TIMELINE_CSV_FILE, "w", encoding="utf-8-sig", newline="") as arquivo:
        campos = [
            "cena",
            "inicio",
            "fim",
            "duracao",
            "trecho_da_letra",
            "resumo_do_trecho",
            "personagem_cantando",
            "fala",
            "falante",
        ]
        writer = csv.DictWriter(arquivo, fieldnames=campos)
        writer.writeheader()
        writer.writerows(linhas)

    return config.TIMELINE_JSON_FILE, config.TIMELINE_CSV_FILE


def _tem_timeline(cena: dict[str, Any]) -> bool:
    return any(campo in cena for campo in CAMPOS_TIMELINE)


def _normalizar_linha(cena: dict[str, Any], indice: int) -> dict[str, Any]:
    numero_cena = cena.get("cena", indice)
    faltando = [
        campo
        for campo in ("inicio", "fim")
        if campo not in cena or str(cena[campo]).strip() == ""
    ]
    trecho = _primeiro_texto(cena, "trecho_da_letra", "trecho")
    contexto = _primeiro_texto(cena, "resumo_do_trecho", "contexto")
    cantando = _primeiro_texto(cena, "personagem_cantando", "cantor", "personagem_cantor")
    if not trecho:
        faltando.append("trecho_da_letra/trecho")
    if not contexto:
        faltando.append("resumo_do_trecho/contexto")
    if not cantando:
        faltando.append("personagem_cantando")
    if faltando:
        raise ValueError(
            f"Cena {numero_cena} sem campo(s) de timeline: "
            + ", ".join(faltando)
        )

    inicio_seg = _parse_tempo(cena["inicio"], numero_cena, "inicio")
    fim_seg = _parse_tempo(cena["fim"], numero_cena, "fim")
    if fim_seg <= inicio_seg:
        raise ValueError(f"Cena {numero_cena} tem fim menor ou igual ao inicio.")

    duracao = _duracao(cena, inicio_seg, fim_seg, numero_cena)
    if duracao < Decimal("2.5") or duracao > Decimal("3.5"):
        raise ValueError(
            f"Cena {numero_cena} tem duracao {duracao}s. "
            "Use entre 2.5 e 3.5 segundos."
        )

    return {
        "cena": int(numero_cena),
        "inicio": str(cena["inicio"]),
        "fim": str(cena["fim"]),
        "duracao": _numero(duracao),
        "trecho_da_letra": trecho,
        "resumo_do_trecho": contexto,
        "personagem_cantando": cantando,
        "fala": _fala(cena),
        "falante": cena.get("personagem") or "",
    }


def _primeiro_texto(cena: dict[str, Any], *chaves: str) -> str:
    for chave in chaves:
        if chave in cena and str(cena[chave]).strip():
            return str(cena[chave])
    return ""


def _duracao(cena: dict[str, Any], inicio: Decimal, fim: Decimal, numero_cena: Any) -> Decimal:
    calculada = (fim - inicio).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    if "duracao" not in cena or str(cena["duracao"]).strip() == "":
        return calculada

    informada = Decimal(str(cena["duracao"]).replace(",", "."))
    if abs(informada - calculada) > Decimal("0.2"):
        raise ValueError(
            f"Cena {numero_cena} tem duracao {informada}s, "
            f"mas inicio/fim indicam {calculada}s."
        )
    return informada.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def _parse_tempo(valor: Any, numero_cena: Any, campo: str) -> Decimal:
    texto = str(valor).strip().replace(",", ".")
    match = TIME_RE.match(texto)
    if not match:
        raise ValueError(
            f"Cena {numero_cena} tem {campo} invalido: {valor}. "
            "Use MM:SS.d ou HH:MM:SS.d."
        )

    if match.group(5) is not None:
        horas = Decimal(0)
        minutos = Decimal(match.group(5))
        segundos = Decimal(match.group(6))
        frac = match.group(7) or "0"
    else:
        horas = Decimal(match.group(1) or 0)
        minutos = Decimal(match.group(2))
        segundos = Decimal(match.group(3))
        frac = match.group(4) or "0"

    return horas * 3600 + minutos * 60 + segundos + Decimal(f"0.{frac}")


def _numero(valor: Decimal) -> int | float:
    if valor == valor.to_integral():
        return int(valor)
    return float(valor)


def _fala(cena: dict[str, Any]) -> bool:
    if "fala" in cena:
        valor = cena["fala"]
        if isinstance(valor, str):
            return valor.strip().lower() not in {"false", "falso", "0", "nao", "n?o", ""}
        return bool(valor)
    return bool(str(cena.get("texto", "")).strip() or cena.get("personagem"))


def main() -> None:
    import utils
    from reaction_director import ReactionDirector

    roteiro = utils.carregar_roteiro()
    director = ReactionDirector()
    cenas = [director.processar(cena) for cena in roteiro]
    arquivos = salvar_timeline(cenas)
    if not arquivos:
        print("Roteiro sem campos de timeline. Nada foi gerado.")
        return

    json_path, csv_path = arquivos
    print(f"Timeline JSON salva em: {json_path.resolve()}")
    print(f"Timeline CSV salva em:  {csv_path.resolve()}")


if __name__ == "__main__":
    main()
