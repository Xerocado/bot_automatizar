"""
config.py — Configurações centrais do bot Gacha Club.
Todos os parâmetros ajustáveis ficam aqui.
"""

from pathlib import Path

# ── Diretórios ────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
DATA_DIR    = BASE_DIR / "data"
OUTPUT_DIR  = BASE_DIR / "output"

COORDS_FILE     = DATA_DIR / "coords.json"
EXPRESSOES_FILE = DATA_DIR / "expressoes.json"
PRESETS_FILE    = DATA_DIR / "presets_emocionais.json"
PERSONALIDADES_FILE = DATA_DIR / "personalidades.json"
ROTEIRO_FILE    = DATA_DIR / "roteiro.json"

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
FONT_PATH       = ""     # caminho para .ttf; "" usa fonte padrão do Pillow
FONT_SIZE       = 36
TEXT_COLOR      = (255, 255, 255)   # branco
TEXT_OUTLINE    = (0, 0, 0)         # contorno preto
TEXT_MARGIN_X   = 40    # margem horizontal em pixels
TEXT_MARGIN_Y   = 70    # margem da borda inferior em pixels
TEXT_MAX_CHARS  = 60    # máximo de caracteres por linha (quebra automática)
