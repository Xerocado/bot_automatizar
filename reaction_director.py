from emotion_preset_system import EmotionPresetSystem
from character_personality import carregar_todos


class ReactionDirector:
    def __init__(self):
        self.presets = EmotionPresetSystem()
        self.personalidades = carregar_todos("data/personalidades.json")

    def processar(self, cena: dict) -> dict:
        if "personagens" in cena:
            return self._processar_cena_completa(cena)

        personagem = cena["personagem"]
        emocao = cena["emocao"]
        intensidade = cena["intensidade"]

        personalidade = self.personalidades[personagem.upper()]

        emocao_final, intensidade_final = personalidade.filtrar_emocao(
            emocao,
            intensidade
        )

        preset = self.presets.resolver(
            emocao_final,
            intensidade_final
        )

        return {
            "personagem": personagem,
            "olhos": preset["olhos"],
            "boca": preset["boca"],
            "texto": cena["texto"]
        }

    def _processar_cena_completa(self, cena: dict) -> dict:
        personagens = self._normalizar_personagens(cena["personagens"])
        esperados = set(self.personalidades)
        recebidos = set(personagens)

        faltando = sorted(esperados - recebidos)
        extras = sorted(recebidos - esperados)
        if faltando:
            raise ValueError(
                "Cena completa sem estado para: " + ", ".join(faltando)
            )
        if extras:
            raise ValueError(
                "Cena completa com personagem desconhecido: " + ", ".join(extras)
            )

        texto_cena = self._texto_da_cena(cena)
        falante_declarado = self._falante_declarado(cena)

        cena_resolvida = {
            "personagens": {},
            "personagem": None,
            "texto": texto_cena,
        }

        falantes = []
        intensidade_3 = []

        for personagem, estado in personagens.items():
            texto = self._texto_do_estado(estado)
            if not texto and personagem == falante_declarado:
                texto = texto_cena

            falando = (
                bool(estado.get("falando", False))
                or bool(texto.strip())
                or personagem == falante_declarado
            )
            if falando:
                falantes.append(personagem)

            estado_resolvido = self._resolver_estado_personagem(
                personagem,
                estado,
                texto,
                falando,
            )

            if estado_resolvido.get("intensidade") == 3:
                intensidade_3.append(personagem)

            cena_resolvida["personagens"][personagem] = estado_resolvido

        if len(falantes) > 1:
            raise ValueError(
                "Apenas um personagem pode falar por cena: "
                + ", ".join(falantes)
            )

        if len(intensidade_3) > 1:
            raise ValueError(
                "Apenas um personagem pode usar intensidade 3 por cena: "
                + ", ".join(intensidade_3)
            )

        if falantes:
            falante = falantes[0]
            cena_resolvida["personagem"] = falante
            if not cena_resolvida["texto"]:
                cena_resolvida["texto"] = (
                    cena_resolvida["personagens"][falante]["texto"]
                )

        return cena_resolvida

    def _resolver_estado_personagem(
        self,
        personagem: str,
        estado: dict,
        texto: str,
        falando: bool,
    ) -> dict:
        if "olhos" in estado and "boca" in estado:
            resolvido = {
                "olhos": estado["olhos"],
                "boca": estado["boca"],
                "texto": texto,
                "falando": falando,
            }
            if "emocao" in estado:
                resolvido["emocao"] = estado["emocao"]
            if "intensidade" in estado:
                resolvido["intensidade"] = int(estado["intensidade"])
            return resolvido

        emocao = estado["emocao"]
        intensidade = int(estado["intensidade"])

        personalidade = self.personalidades[personagem]
        emocao_final, intensidade_final = personalidade.filtrar_emocao(
            emocao,
            intensidade,
        )

        preset = self.presets.resolver(
            emocao_final,
            intensidade_final,
        )

        return {
            "emocao": emocao_final,
            "intensidade": intensidade_final,
            "olhos": preset["olhos"],
            "boca": preset["boca"],
            "texto": texto,
            "falando": falando,
        }

    def _normalizar_personagens(self, personagens: dict | list) -> dict:
        if isinstance(personagens, dict):
            return {
                self._normalizar_nome(nome): estado
                for nome, estado in personagens.items()
            }

        if isinstance(personagens, list):
            normalizados = {}
            for estado in personagens:
                personagem = self._normalizar_nome(estado["personagem"])
                normalizados[personagem] = {
                    chave: valor
                    for chave, valor in estado.items()
                    if chave != "personagem"
                }
            return normalizados

        raise TypeError("'personagens' deve ser um objeto ou uma lista")

    def _normalizar_nome(self, nome: str) -> str:
        return str(nome).upper()

    def _falante_declarado(self, cena: dict) -> str | None:
        for chave in ("personagem", "falante"):
            if chave in cena and cena[chave]:
                return self._normalizar_nome(cena[chave])
        return None

    def _texto_da_cena(self, cena: dict) -> str:
        for chave in ("texto", "comentario", "coment\u00e1rio"):
            if chave in cena:
                return str(cena[chave])
        return ""

    def _texto_do_estado(self, estado: dict) -> str:
        for chave in ("texto", "comentario", "coment\u00e1rio"):
            if chave in estado:
                return str(estado[chave])
        return ""
