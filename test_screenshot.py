import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image, ImageChops, ImageDraw

import config
import screenshot
import utils


FALA = (
    "PERSONAGEM 1: Olha isso!\n"
    "PERSONAGEM 1: Look at that!\n"
    "PERSONAGEM 1: Mira eso!"
)


class LegendaTests(unittest.TestCase):
    def setUp(self):
        ajustes = patch.multiple(
            config, FONT_SIZE=36, FONT_PATH="", TEXT_MIN_FONT_SIZE=16,
            TEXT_ALIGN="left", TEXT_MARGIN_X=15, TEXT_MARGIN_Y=50,
            TEXT_LINE_SPACING=8, TEXT_STROKE_WIDTH=2,
            TEXT_COLOR=(255, 255, 255), TEXT_OUTLINE=(0, 0, 0),
            TEXT_MAX_WIDTH_RATIO=0.95, TEXT_BOX_ENABLED=True,
            TEXT_BOX_PADDING_X=20, TEXT_BOX_PADDING_Y=12,
            TEXT_BOX_COLOR=(0, 0, 0), TEXT_BOX_OPACITY=255,
            TEXT_BOX_BORDER_COLOR=(80, 80, 80), TEXT_BOX_BORDER_WIDTH=0,
        )
        ajustes.start()
        self.addCleanup(ajustes.stop)
        self.base = Image.new("RGB", (1280, 720), (180, 180, 180))

    def test_caixa_margens_alinhamento_e_idiomas(self):
        resultado = screenshot.adicionar_comentario(self.base, FALA)
        caixa = ImageChops.difference(self.base, resultado).getbbox()
        self.assertEqual(caixa[0], config.TEXT_MARGIN_X)
        self.assertEqual(caixa[3], self.base.height - config.TEXT_MARGIN_Y)
        self.assertLessEqual(caixa[2], self.base.width - config.TEXT_MARGIN_X)
        self.assertEqual(resultado.getpixel((caixa[0], caixa[1])), (0, 0, 0))

        mascara = resultado.convert("L").point(lambda valor: 255 if valor > 220 else 0)
        blocos = []
        for y in range(resultado.height):
            linha = mascara.crop((0, y, resultado.width, y + 1)).getbbox()
            if linha:
                if not blocos or y > blocos[-1][1] + 1:
                    blocos.append([y, y, linha[0]])
                else:
                    blocos[-1][1] = y
                    blocos[-1][2] = min(blocos[-1][2], linha[0])
        self.assertEqual(len(blocos), 3)
        self.assertLessEqual(max(b[2] for b in blocos) - min(b[2] for b in blocos), 2)
        self.assertLess(blocos[0][2], 60)
        self.assertEqual(resultado.size, self.base.size)
        self.assertEqual(self.base.getextrema(), ((180, 180),) * 3)

    def test_caixa_largura_fixa_opacidade_e_borda(self):
        curta = screenshot.adicionar_comentario(self.base, "Oi!")
        longa = screenshot.adicionar_comentario(self.base, "Uma frase maior para a caixa.")
        bbox_curta = ImageChops.difference(self.base, curta).getbbox()
        bbox_longa = ImageChops.difference(self.base, longa).getbbox()
        self.assertEqual(bbox_longa[2], bbox_curta[2])
        with patch.multiple(config, TEXT_BOX_OPACITY=128, TEXT_BOX_BORDER_WIDTH=1):
            resultado = screenshot.adicionar_comentario(self.base, "Oi!")
        caixa = ImageChops.difference(self.base, resultado).getbbox()
        self.assertEqual(resultado.getpixel(caixa[:2]), config.TEXT_BOX_BORDER_COLOR)
        self.assertEqual(resultado.getpixel((caixa[0] + 2, caixa[1] + 2)), (90, 90, 90))

    def test_quebra_em_pixels_preserva_linhas_e_palavras(self):
        draw = ImageDraw.Draw(self.base)
        fonte = screenshot._carregar_fonte(36)
        linhas = screenshot._quebrar_texto_por_pixels(
            "Portugues\r\n\r\nEnglish\nEspanol\n", draw, fonte, 800, 2,
        )
        self.assertEqual(linhas, ["Portugues", "", "English", "Espanol", ""])
        texto = "Uma frase com varias palavras e " + "W" * 120
        linhas = screenshot._quebrar_texto_por_pixels(texto, draw, fonte, 200, 2)
        self.assertEqual("".join(linhas).replace(" ", ""), texto.replace(" ", ""))
        for linha in linhas:
            bbox = draw.textbbox((0, 0), linha, font=fonte, stroke_width=2)
            self.assertLessEqual(bbox[2] - bbox[0], 200)
        estreita = screenshot._quebrar_texto_por_pixels("iiiiiiiiii", draw, fonte, 120, 2)
        larga = screenshot._quebrar_texto_por_pixels("WWWWWWWWWW", draw, fonte, 120, 2)
        self.assertGreater(len(larga), len(estreita))

    def test_fala_longa_em_resolucoes_diferentes(self):
        texto = FALA.replace("Olha isso!", "Olha isso! " * 16)
        for tamanho in ((1920, 1080), (1280, 720), (640, 360)):
            with self.subTest(tamanho=tamanho):
                base = Image.new("RGB", tamanho, (180, 180, 180))
                resultado = screenshot.adicionar_comentario(base, texto)
                caixa = ImageChops.difference(base, resultado).getbbox()
                self.assertGreaterEqual(caixa[1], 0)
                self.assertEqual(caixa[0], config.TEXT_MARGIN_X)
                self.assertEqual(caixa[3], tamanho[1] - config.TEXT_MARGIN_Y)
                self.assertLessEqual(caixa[2] - caixa[0], int(tamanho[0] * 0.95))

    def test_cena_muda_e_caixa_desativada(self):
        for texto in ("", " \n\n"):
            resultado = screenshot.adicionar_comentario(self.base, texto)
            self.assertIsNot(resultado, self.base)
            self.assertIsNone(ImageChops.difference(self.base, resultado).getbbox())
        with patch.object(config, "TEXT_BOX_ENABLED", False):
            resultado = screenshot.adicionar_comentario(self.base, FALA)
        self.assertEqual(resultado.getpixel((15, self.base.height - 51)), (180, 180, 180))
        self.assertIsNotNone(ImageChops.difference(self.base, resultado).getbbox())

    def test_rgba_nao_altera_original(self):
        base = self.base.convert("RGBA")
        original = base.tobytes()
        resultado = screenshot.adicionar_comentario(base, "A\u00e7\u00e3o! \u00bfQu\u00e9 pas\u00f3?")
        self.assertEqual(resultado.mode, "RGBA")
        self.assertEqual(base.tobytes(), original)
        self.assertNotEqual(resultado.tobytes(), original)

    def test_configuracao_sem_espaco_falha_sem_cortar_texto(self):
        with patch.object(config, "TEXT_MARGIN_X", 1000):
            with self.assertRaisesRegex(ValueError, "espaco"):
                screenshot.adicionar_comentario(self.base, FALA)
        with self.assertRaisesRegex(ValueError, "nao cabe"):
            screenshot.adicionar_comentario(Image.new("RGB", (200, 150)), FALA * 10)

    def test_captura_mss_e_salvamento_png(self):
        raw = SimpleNamespace(size=self.base.size, bgra=self.base.tobytes("raw", "BGRX"))
        with tempfile.TemporaryDirectory() as pasta, \
                patch.object(config, "OUTPUT_DIR", Path(pasta)), \
                patch("screenshot.mss.mss") as mss_mock:
            captura = mss_mock.return_value.__enter__.return_value
            captura.monitors = [None, {"monitor": "teste"}]
            captura.grab.return_value = raw
            with patch.object(config, "MONITOR_INDEX", 1):
                caminho = screenshot.capturar_e_salvar(FALA, "cena_teste.png")
            captura.grab.assert_called_once_with(captura.monitors[1])
            self.assertEqual(caminho.parent, config.OUTPUT_DIR)
            with Image.open(caminho) as salva:
                self.assertEqual(salva.format, "PNG")
                self.assertEqual(salva.size, self.base.size)
                self.assertEqual(salva.mode, "RGB")
                self.assertIsNotNone(ImageChops.difference(self.base, salva).getbbox())

    def test_quebra_antiga_continua_disponivel(self):
        self.assertEqual(utils.quebrar_texto("Oi mundo\n\nHello", 5), ["Oi", "mundo", "", "Hello"])


if __name__ == "__main__":
    unittest.main()
