import unittest
import base64
import tempfile
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

import engine
import utils
import vision_paginas


class ResolutionTests(unittest.TestCase):
    def test_both_resolution_profiles(self):
        with patch("config.SCREEN_RESOLUTION", (1920, 1080)):
            base = utils.carregar_coords()
        with patch("config.SCREEN_RESOLUTION", (1366, 768)):
            scaled = utils.carregar_coords()

        self.assertEqual(base["BOTOES"]["PERSONAGEM_1"], [1761, 71])
        self.assertEqual(scaled["BOTOES"]["PERSONAGEM_1"], [1253, 50])
        self.assertEqual(scaled["GRID_OLHOS"]["primeiro_x"], round(842 * 1366 / 1920))
        self.assertEqual(scaled["GRID_BOCAS"]["dy"], round(165 * 768 / 1080))
        self.assertEqual(scaled["PAGINA_CONTADOR"], {"x": 875, "y": 640, "largura": 78, "altura": 42})
        self.assertEqual(utils.carregar_json(engine.config.COORDS_FILE), base)

    def test_wrong_screen_stops_before_clicking(self):
        with patch("config.SCREEN_RESOLUTION", (1366, 768)), \
             patch("engine.mss.mss") as mss_mock, \
             patch("engine.pyautogui.size", return_value=(1920, 1080)), \
             patch("engine.pyautogui.moveTo") as move_mock:
            mss_mock.return_value.__enter__.return_value.monitors = [
                {}, {"width": 1366, "height": 768, "left": 0, "top": 0}
            ]
            with self.assertRaisesRegex(RuntimeError, "Resolucao configurada"):
                engine.inicializar()
            move_mock.assert_not_called()

    def test_page_reference_is_resized_for_notebook(self):
        with tempfile.TemporaryDirectory() as temp:
            refs = Path(temp)
            ref = Image.new("RGB", (29, 44), "black")
            ref.save(refs / "olhos_1.png")
            Image.new("RGB", (29, 44), "white").save(refs / "olhos_2.png")
            atual = ref.resize((21, 31), Image.Resampling.LANCZOS)
            with patch.object(vision_paginas, "REFS_DIR", refs), \
                 patch.object(vision_paginas, "capturar_contador", return_value=atual):
                self.assertEqual(vision_paginas.detectar_pagina("olhos", {}), 1)

    def test_real_references_in_both_sizes(self):
        # Simula a reducao; a calibracao real ainda depende da janela do notebook.
        for size in ((29, 44), (21, 31)):
            for path in vision_paginas.REFS_DIR.glob("*.png"):
                tipo, numero = path.stem.split("_")
                with self.subTest(size=size, reference=path.name):
                    with Image.open(path) as ref:
                        atual = ref.resize(size, Image.Resampling.LANCZOS)
                    with patch.object(vision_paginas, "capturar_contador", return_value=atual), \
                         redirect_stdout(io.StringIO()):
                        self.assertEqual(vision_paginas.detectar_pagina(tipo, {}), int(numero))

    def test_notebook_page_one_from_reported_capture(self):
        # Mascara real do contador no print 1366x768, regiao (887, 643, 913, 679).
        pixels = base64.b64decode(
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAHABAAH4AwAH+AMAB/gDAAJ4BwAAeAcAAHgHAAB4B"
            "wAAeA8AAHgOAAB4DgAAeB4AAHgcAAB4HAAAeBwAAHg8AAB4OAAAeDgAAHh4AAB4c"
            "AAAeHAAAHjwAAB48AAAeOAAAHjgAAAw4AAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        )
        tela = Image.new("RGB", (1366, 768))
        tela.paste(Image.frombytes("1", (26, 36), pixels), (887, 643))

        def captura(region):
            x, y, w, h = region
            return tela.crop((x, y, x + w, y + h))

        with patch("config.SCREEN_RESOLUTION", (1366, 768)), \
             patch.object(vision_paginas.pyautogui, "screenshot", side_effect=captura), \
             redirect_stdout(io.StringIO()):
            coords = utils.carregar_coords()["PAGINA_CONTADOR"]
            self.assertEqual(coords, {"x": 875, "y": 640, "largura": 78, "altura": 42})
            self.assertEqual(vision_paginas.detectar_pagina("olhos", coords), 1)

    def test_notebook_all_pages_with_margins_and_denominator(self):
        pasta = vision_paginas.REFS_DIR / "1366x768"
        for tipo, total in vision_paginas.TOTAL_PAGINAS.items():
            with Image.open(pasta / f"{tipo}_{total}.png") as ref_total:
                denominador = ref_total.copy()
            for pagina in range(1, total + 1):
                with self.subTest(tipo=tipo, pagina=pagina):
                    with Image.open(pasta / f"{tipo}_{pagina}.png") as ref:
                        numero = ref.copy()
                    for deslocamento in (2, 5):
                        captura = Image.new("L", (78, 42))
                        captura.paste(numero, (deslocamento, 5))
                        barra_x = deslocamento + numero.width + 3
                        ImageDraw.Draw(captura).line((barra_x + 8, 5, barra_x, 30), fill=255, width=3)
                        captura.paste(denominador, (barra_x + 12, 5))
                        with patch("config.SCREEN_RESOLUTION", (1366, 768)), \
                             patch.object(vision_paginas, "capturar_contador", return_value=captura), \
                             redirect_stdout(io.StringIO()):
                            self.assertEqual(vision_paginas.detectar_pagina(tipo, {}), pagina)

    def test_missing_native_profile_is_not_replaced_by_resized_desktop_refs(self):
        with tempfile.TemporaryDirectory() as temp, \
             patch.object(vision_paginas, "REFS_DIR", Path(temp)), \
             patch("config.SCREEN_RESOLUTION", (1366, 768)):
            with self.assertRaisesRegex(vision_paginas.PaginaNaoReconhecida, "Faltam referencias"):
                vision_paginas.selecionar_referencias("olhos")
            (Path(temp) / "1366x768").mkdir()
            with self.assertRaisesRegex(vision_paginas.PaginaNaoReconhecida, "incompletas"):
                vision_paginas.selecionar_referencias("olhos")

    def test_bad_or_ambiguous_capture_saves_diagnostic(self):
        for ambiguous in (False, True):
            with self.subTest(ambiguous=ambiguous), tempfile.TemporaryDirectory() as temp:
                refs = Path(temp) / "refs"
                refs.mkdir()
                Image.new("RGB", (20, 20), "black").save(refs / "olhos_1.png")
                Image.new("RGB", (20, 20), "black" if ambiguous else "white").save(refs / "olhos_2.png")
                atual = Image.new("RGB", (20, 20), "black")
                if not ambiguous:
                    atual.paste("white", (0, 0, 10, 20))
                output = Path(temp) / "output"
                with patch.object(vision_paginas, "REFS_DIR", refs), \
                     patch.object(vision_paginas, "capturar_contador", return_value=atual), \
                     patch("config.OUTPUT_DIR", output), redirect_stdout(io.StringIO()):
                    with self.assertRaises(vision_paginas.PaginaNaoReconhecida):
                        vision_paginas.detectar_pagina("olhos", {"x": 892, "y": 648})
                self.assertTrue((output / "debug" / "contador_olhos.png").is_file())
                dados = json.loads((output / "debug" / "contador_olhos.json").read_text(encoding="utf-8"))
                self.assertFalse(dados["confiavel"])

    def test_unrecognized_page_does_not_trigger_recovery_clicks(self):
        with patch.dict(engine._estado, {"screen": "HOME"}), \
             patch.object(engine, "_processar_cena_impl", side_effect=vision_paginas.PaginaNaoReconhecida("contador")), \
             patch.object(engine, "recuperar_para_home") as recovery:
            with self.assertRaises(vision_paginas.PaginaNaoReconhecida):
                engine.processar_cena({}, 1)
            recovery.assert_not_called()

    def test_main_stops_before_next_scene(self):
        import main
        with patch("config.RENDER_MODE", "gacha"), \
             patch.object(main, "ReactionDirector"), \
             patch.object(utils, "carregar_roteiro", return_value=[{}, {}]), \
             patch.object(engine, "inicializar"), \
             patch.object(main.time, "sleep"), \
             patch.object(engine, "processar_cena", side_effect=vision_paginas.PaginaNaoReconhecida("contador")) as process, \
             redirect_stdout(io.StringIO()):
            main.main()
            self.assertEqual(process.call_count, 1)


if __name__ == "__main__":
    unittest.main()
