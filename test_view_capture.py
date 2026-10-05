import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

import engine


def _telas(tamanho):
    limpa = Image.new("RGB", tamanho, (220, 220, 220))
    hud = limpa.copy()
    desenho = ImageDraw.Draw(hud)
    for x1, y1, x2, y2 in (
        (0.040, 0.801, 0.124, 0.931),
        (0.816, 0.176, 0.875, 0.267),
    ):
        desenho.rectangle(
            (round(x1 * tamanho[0]), round(y1 * tamanho[1]),
             round(x2 * tamanho[0]), round(y2 * tamanho[1])),
            fill=(35, 38, 53),
        )
    return hud, limpa


class ViewCaptureTests(unittest.TestCase):
    def test_detecta_hud_oculto_nas_duas_resolucoes(self):
        for tamanho in ((1366, 768), (1920, 1080)):
            with self.subTest(tamanho=tamanho):
                hud, limpa = _telas(tamanho)
                self.assertTrue(engine._hud_oculto(hud, limpa))
                self.assertFalse(engine._hud_oculto(hud, hud))

    def test_aguarda_view_antes_de_salvar(self):
        hud, limpa = _telas((1366, 768))
        with patch("engine.screenshot.capturar_tela", side_effect=[hud, hud, limpa]), \
             patch("engine.clicar") as clicar, patch("engine.time.sleep"):
            self.assertIs(engine._capturar_sem_hud(), limpa)
        self.assertEqual(clicar.call_count, 2)  # View e restauracao

    def test_falha_sem_salvar_se_view_nao_responder(self):
        hud, _ = _telas((1366, 768))
        with patch("engine.screenshot.capturar_tela", return_value=hud), \
             patch("engine.clicar") as clicar, \
             patch("engine.time.sleep"), \
             patch("engine.screenshot.salvar_imagem") as salvar:
            with self.assertRaisesRegex(RuntimeError, "screenshot nao foi salva"):
                engine._capturar_sem_hud()
        self.assertEqual(clicar.call_count, 2)
        salvar.assert_not_called()


if __name__ == "__main__":
    unittest.main()
