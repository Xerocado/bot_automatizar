# 🎮 Gacha Club — React Scene Bot

Bot de automação determinística para gerar screenshots de cenas de react no **Gacha Club**, sem visão computacional, OCR ou OpenCV. Tudo via coordenadas fixas e grid matemático.

---

## 📁 Estrutura

```
bot/
├── data/
│   ├── coords.json       # Coordenadas de todos os botões e grids
│   ├── expressoes.json   # Mapeamento [pagina, linha, coluna] de cada expressão
│   └── roteiro.json      # Lista de cenas a gerar
│
├── output/               # Screenshots geradas (criada automaticamente)
│
├── config.py             # Todos os parâmetros ajustáveis
├── engine.py             # Motor de automação e fluxo de cada cena
├── main.py               # Ponto de entrada
├── screenshot.py         # Captura MSS + overlay Pillow
└── utils.py              # Logs, JSON, cálculo de grid
```

---

## ⚙️ Instalação

```bash
pip install -r requirements.txt
```

**Dependências:**
- `pyautogui` — controle de mouse/teclado
- `Pillow` — overlay de texto nas imagens
- `mss` — captura de tela rápida

---

## 🚀 Uso

1. **Configure o jogo:** Abra o Gacha Club maximizado na resolução esperada.
2. **Edite o roteiro** em `data/roteiro.json` com as cenas desejadas.
3. **Execute o bot:**

```bash
python main.py
```

O bot inicia após **3 segundos** — tempo para você focar a janela do jogo.

> **🛑 FAILSAFE:** Mova o mouse rapidamente para o **canto superior-esquerdo** da tela para encerrar o bot imediatamente.

---

## 📝 Roteiro (`data/roteiro.json`)

Cada cena é um objeto JSON:

```json
[
  {
    "personagem": "KOKUJIN",
    "olhos": "assustado_1",
    "boca": "gritando_raiva_1",
    "comentario": "Ele realmente perdeu o controle."
  }
]
```

| Campo        | Descrição                                    |
|--------------|----------------------------------------------|
| `personagem` | Chave em `BOTOES` do `coords.json`           |
| `olhos`      | Chave em `olhos` do `expressoes.json`        |
| `boca`       | Chave em `bocas` do `expressoes.json`        |
| `comentario` | Texto exibido na parte inferior do screenshot|

---

## 🗺️ Expressões (`data/expressoes.json`)

Formato: `[pagina, linha, coluna]` — índices **começam em 1**.

```json
{
  "olhos": {
    "assustado_1": [1, 3, 4]
  },
  "bocas": {
    "gritando_raiva_1": [13, 1, 1]
  }
}
```

Para adicionar novas expressões, identifique manualmente a página, linha e coluna no jogo e adicione a entrada.

---

## 📐 Grid Matemático

Cálculo da posição de clique em um item do grid:

```
x = primeiro_x + (coluna - 1) × dx
y = primeiro_y + (linha  - 1) × dy
```

Os valores de `primeiro_x/y`, `dx` e `dy` ficam em `data/coords.json` sob `GRID_OLHOS` e `GRID_BOCAS`.

---

## ⚡ Fluxo por cena

```
Selecionar personagem
→ Abrir editor
→ Abrir Face → Olhos
  → Resetar página (15× retroceder)
  → Avançar até página alvo
  → Clicar item via grid matemático
→ Abrir Boca
  → Resetar página
  → Avançar
  → Clicar item
→ Fechar editor
→ Ir ao Estúdio
→ Ocultar HUD
→ Capturar (MSS)
→ Restaurar HUD
→ Adicionar comentário (Pillow)
→ Salvar PNG em output/
→ Voltar home
```

---

## 🔧 Configurações (`config.py`)

| Parâmetro          | Padrão | Descrição                             |
|--------------------|--------|---------------------------------------|
| `CLICK_DURATION`   | 0.10   | Velocidade do movimento do mouse (s)  |
| `DELAY_CURTO`      | 0.20   | Pausa entre cliques rápidos           |
| `DELAY_MEDIO`      | 0.50   | Pausa ao abrir menus                  |
| `DELAY_LONGO`      | 1.00   | Pausa para animações                  |
| `CLICK_JITTER`     | 3      | Randomização ±pixels no clique        |
| `PAGE_RESET_CLICKS`| 15     | Cliques no retroceder para reset      |
| `FONT_PATH`        | `""`   | Caminho para fonte .ttf (vazio=padrão)|
| `FONT_SIZE`        | 36     | Tamanho do texto de comentário        |

---

## 🖼️ Output

As imagens são salvas em `output/` com o formato:

```
cena_001_kokujin.png
cena_002_kaede.png
...
```
