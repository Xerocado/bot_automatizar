import pyautogui
import utils

coords = utils.carregar_coords()

cfg = coords["PAGINA_CONTADOR"]

img = pyautogui.screenshot(
    region=(
        cfg["x"],
        cfg["y"],
        cfg["largura"],
        cfg["altura"],
    )
)

img.save("captura_atual.png")

print("salvo")