import utils


class EmotionPresetSystem:
    def __init__(self):
        self.presets = utils.carregar_presets()

    def resolver(self, emocao: str, intensidade: int) -> dict:
        if emocao not in self.presets:
            raise ValueError(f"Emoção desconhecida: {emocao}")

        chave = f"intensidade_{intensidade}"

        if chave not in self.presets[emocao]:
            raise ValueError(
                f"Intensidade inválida para {emocao}: {intensidade}"
            )

        return self.presets[emocao][chave]