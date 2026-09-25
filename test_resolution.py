import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image

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
        self.assertEqual(scaled["PAGINA_CONTADOR"]["largura"], round(29 * 1366 / 1920))
        self.assertEqual(scaled["PAGINA_CONTADOR"]["altura"], round(44 * 768 / 1080))
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


if __name__ == "__main__":
    unittest.main()
