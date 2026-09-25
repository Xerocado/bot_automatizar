"""
config.py — Configurações centrais do bot Gacha Club.
Todos os parâmetros ajustáveis ficam aqui.
"""

from pathlib import Path

# ── Diretórios ────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
DATA_DIR    = BASE_DIR / "data"
OUTPUT_DIR  = BASE_DIR / "output"
CENAS_DIR   = BASE_DIR / "cenas"
LAYOUTS_DIR = DATA_DIR / "layouts"

COORDS_FILE     = DATA_DIR / "coords.json"
# As coordenadas de coords.json foram medidas nesta resolucao.
COORDS_BASE_RESOLUTION = (1920, 1080)
# Resolucao do monitor onde o Gacha Club ocupa a tela inteira.
SCREEN_RESOLUTION = (1920, 1080)  # ou (1366, 768)
EXPRESSOES_FILE = DATA_DIR / "expressoes.json"
PRESETS_FILE    = DATA_DIR / "presets_emocionais.json"
PERSONALIDADES_FILE = DATA_DIR / "personalidades.json"
PERSONAGENS_FILE = DATA_DIR / "personagens.json"
ROTEIRO_FILE    = DATA_DIR / "roteiro.json"

# Renderizacao
RENDER_MODE = "gacha"  # "gacha" controla o jogo; "layout" gera PNG sem controlar o jogo.
LAYOUT_PRESET = "react_room_livepix_v1"
LAYOUT_FILE = LAYOUTS_DIR / f"{LAYOUT_PRESET}.json"

# ── Delays (segundos) ─────────────────────────────────────────────────────────
CLICK_DURATION  = 0.5   # duração do movimento do mouse até o alvo
DELAY_CURTO     = 0.05   # entre cliques rápidos (ex: virar páginas)
DELAY_MEDIO     = 0.10   # após abrir menus / mudar estado de UI
DELAY_LONGO     = 0.30   # aguardar animações maiores (editor, estúdio)
DELAY_SUBMENU   = 0.05  # especificamente após abrir submenus de face

# ── Randomização de clique ────────────────────────────────────────────────────
# Reduzido para ±1 pixel — botões do Gacha Club são pequenos
CLICK_JITTER = 1

# ── Modo debug ────────────────────────────────────────────────────────────────
# Quando True: mouse move → pausa 1s → clica (permite visualizar o alvo)
DEBUG_MOUSE = False

# ── Debug screenshots ─────────────────────────────────────────────────────────
# Salva capturas antes de cada submenu para diagnóstico
DEBUG_SCREENSHOTS = False

# ── Segurança ─────────────────────────────────────────────────────────────────
FAILSAFE = True          # mover mouse ao canto superior-esquerdo encerra o bot

# ── Repetições para reset de página ──────────────────────────────────────────
PAGE_RESET_CLICKS = 15   # fallback quando o estado interno nao sabe a pagina atual

# Recovery de UI
RECOVERY_ESCAPE_PRESSES = 3
DELAY_RECOVERY = 0.35

# ── Screenshot ────────────────────────────────────────────────────────────────
MONITOR_INDEX = 1        # índice do monitor principal no MSS (1 = primário)

# ── Overlay de texto (Pillow) ─────────────────────────────────────────────────
FONT_PATH       = ""     # .ttf; vazio tenta Arial/Segoe UI, depois padrao do Pillow
FONT_SIZE       = 36
TEXT_COLOR      = (255, 255, 255)   # branco
TEXT_OUTLINE    = (0, 0, 0)         # contorno preto
TEXT_STROKE_WIDTH = 2
TEXT_ALIGN      = "left"
TEXT_MARGIN_X   = 60    # distancia da caixa as bordas laterais, em pixels
TEXT_MARGIN_Y   = 60    # distancia da caixa a borda inferior, em pixels
TEXT_LINE_SPACING = 8
TEXT_MAX_WIDTH_RATIO = 1.0  # largura maxima da caixa / largura da captura
TEXT_MIN_FONT_SIZE = 16     # reduzir fonte apenas se o bloco nao couber
TEXT_BOX_ENABLED = True
TEXT_BOX_PADDING_X = 20
TEXT_BOX_PADDING_Y = 12
TEXT_BOX_COLOR = (0, 0, 0)
TEXT_BOX_OPACITY = 220      # 0 = transparente; 255 = fundo solido
TEXT_BOX_BORDER_COLOR = (80, 80, 80)
TEXT_BOX_BORDER_WIDTH = 0   # 0 = sem borda; 1 = borda fina
TEXT_MAX_CHARS  = 90    # compatibilidade com utils.quebrar_texto()
