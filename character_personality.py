import json
from pathlib import Path


class CharacterPersonality:
    def __init__(self, nome: str, dados: dict):
        self.nome = nome
        self._intensidade_maxima = dados.get("intensidade_maxima", 3)
        self._modificadores = dados.get("modificadores", {})

    def filtrar_emocao(self, emocao: str, intensidade: int) -> tuple[str, int]:
        mod = self._modificadores.get(emocao, {})

        # 1. Substituir emoção
        emocao_final = mod.get("substitui_por", emocao)

        # 2. Intensidade fixa do modificador
        if "intensidade" in mod:
            intensidade_final = mod["intensidade"]
        else:
            intensidade_final = intensidade

        # 3. Delta de intensidade
        if "delta_intensidade" in mod:
            intensidade_final += mod["delta_intensidade"]

        # 4. intensidade_maxima específica do modificador (ex: feliz tem max 2)
        mod_max = mod.get("intensidade_maxima", self._intensidade_maxima)

        # 5. Respeitar o menor entre o max do modificador e o max do personagem
        teto = min(mod_max, self._intensidade_maxima)
        intensidade_final = max(1, min(intensidade_final, teto))

        return emocao_final, intensidade_final

    @classmethod
    def carregar(cls, nome: str, caminho_json: str = "personalidades.json") -> "CharacterPersonality":
        with open(caminho_json, encoding="utf-8") as f:
            dados = json.load(f)
        nome_upper = nome.upper()
        if nome_upper not in dados:
            raise ValueError(f"Personagem '{nome_upper}' não encontrado em {caminho_json}")
        return cls(nome_upper, dados[nome_upper])


def carregar_todos(caminho_json: str = "personalidades.json") -> dict[str, CharacterPersonality]:
    with open(caminho_json, encoding="utf-8") as f:
        dados = json.load(f)
    return {nome: CharacterPersonality(nome, info) for nome, info in dados.items()}


# --- testes rápidos ---
if __name__ == "__main__":
    base = Path(__file__).parent
    personagens = carregar_todos(base / "personalidades.json")

    casos = [
        ("PERSONAGEM_1", "triste", 2),
        ("PERSONAGEM_2", "medo", 3),
        ("PERSONAGEM_3", "feliz", 3),
        ("PERSONAGEM_4", "animado", 3),
        ("PERSONAGEM_5", "raiva", 3),
    ]

    print(f"{'Personagem':<10} {'Entrada':<12} {'Int':>3}  →  {'Saída':<15} {'Int':>3}")
    print("-" * 55)
    for nome, emocao, intensidade in casos:
        p = personagens[nome]
        emocao_out, intensidade_out = p.filtrar_emocao(emocao, intensidade)
        mudou = "★" if (emocao_out != emocao or intensidade_out != intensidade) else ""
        print(f"{nome:<10} {emocao:<12} {intensidade:>3}  →  {emocao_out:<15} {intensidade_out:>3}  {mudou}")