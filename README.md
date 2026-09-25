# bot_automatizar

Bot em Python para automatizar cenas de reação no Gacha Club. Ele lê um roteiro em JSON, aplica expressões de olhos e boca nos personagens e gera imagens finais para edição.

O modo padrão é `RENDER_MODE = "gacha"`: controla o Gacha Club, aplica as expressões e salva as capturas em `output/`. O modo opcional `layout` gera PNG limpo em `cenas/`, com canvas 1920x1080, área verde para o vídeo, espaço de QR Live Pix e faixa inferior de falas. Esse modo não controla o jogo nem captura seus personagens; usa as imagens configuradas no preset ou avatares de exemplo.

O projeto trabalha principalmente com coordenadas fixas, grid matemático e comparação simples de imagens para identificar a página atual dos seletores de olhos/bocas.

## Estrutura

```text
bot_automatizar/
├── data/
│   ├── coords.json                    # Coordenadas de botões, grids e contador de página
│   ├── expressoes.json                # Mapa de olhos/bocas: [pagina, linha, coluna]
│   ├── layouts/
│   │   └── react_room_livepix_v1.json # Preset do canvas limpo para react
│   ├── personagens.json               # Slots genéricos e aliases aceitos
│   ├── personalidades.json            # Regras por personagem
│   ├── presets_emocionais.json        # Emoção + intensidade -> olhos/boca
│   ├── roteiro.json                   # Roteiro executado pelo bot
│   ├── roteiro_completo.exemplo.json  # Exemplo de roteiro com vários personagens
│   └── roteiro_layout.exemplo.json    # Exemplo do layout react_room_livepix_v1
├── cenas/                             # PNGs limpos gerados pelo modo layout
├── refs_paginas/                      # Referências do contador de página
├── output/                            # Capturas do modo gacha e arquivos de apoio
├── character_personality.py           # Ajustes de emoção por personagem
├── config.py                          # Configurações centrais
├── emotion_preset_system.py           # Resolve presets emocionais
├── engine.py                          # Motor de automação
├── layout_renderer.py                 # Render limpo 1920x1080 por preset
├── main.py                            # Ponto de entrada
├── PROMPT_ROTEIRO_LAYOUT.md            # Instruções para gerar roteiros com layout
├── reaction_director.py               # Converte roteiro em expressões finais
├── remapear.py                        # Ferramenta para listar/editar expressões
├── screenshot.py                      # Captura e overlay de texto
├── utils.py                           # JSON, logs, grid e quebra de texto
├── validar_layout.py                  # Validação do layout fixo
└── vision_paginas.py                  # Detecção da página atual por comparação de imagem
```

## Instalação

Use Python 3.11 ou superior.

```bash
pip install -r requirements.txt
```

Dependências principais:

- `pyautogui`: controle de mouse e teclado.
- `Pillow`: manipulação de imagens e texto.
- `mss`: captura rápida da tela final.

## Como Rodar

1. Edite `data/roteiro.json`.
2. Mantenha `RENDER_MODE = "gacha"` em `config.py` e abra o Gacha Club na resolução mapeada, na tela esperada pelo bot.
3. Execute:

```bash
python main.py
```

As capturas do jogo são salvas em `output/`.

### Resolução do jogo

Em `config.py`, escolha a resolução do monitor principal:

```python
SCREEN_RESOLUTION = (1920, 1080)  # ou (1366, 768)
```

O arquivo `data/coords.json` continua mapeado em 1920x1080. Para 1366x768, o bot calcula `x * 1366 / 1920` e `y * 768 / 1080` para os botões, o grid e a região do contador de páginas. Por exemplo, `(1761, 71)` vira aproximadamente `(1253, 50)`. As imagens de referência do contador também são redimensionadas para a região capturada. O arquivo de coordenadas original não é alterado.

Configure o Windows e o jogo para que o Gacha Club ocupe a tela inteira na resolução escolhida, sem bordas, deslocamento ou escala de interface diferente. O bot confere o tamanho do monitor capturado e das coordenadas do mouse antes de clicar; se houver divergência, interrompe a execução. Em notebook com escala do Windows acima de 100%, confira se os dois tamanhos reportados pelo bot coincidem. O modo `layout` mantém seu canvas próprio de 1920x1080.

Para gerar apenas as composições do layout, troque para `RENDER_MODE = "layout"` em `config.py`. Nesse modo, as imagens são salvas em `cenas/` e o bot não interage com o Gacha Club. O campo `layout` do roteiro escolhe o preset visual, mas não muda o modo de execução.

Para cancelar em emergência, mova o mouse para o canto superior esquerdo da tela. Isso usa o failsafe do `pyautogui`.


## Personagens Genéricos

O bot não depende mais de `KOKUJIN`, `KAEDE`, `NAO`, `KANOKO` e `YUMI` como nomes oficiais. O roteiro deve usar slots genéricos:

| Slot | Posição no Gacha Club | Apelidos antigos aceitos |
| --- | --- | --- |
| `personagem_1` | Primeiro personagem de cima | `KAEDE`, `P1` |
| `personagem_2` | Segundo personagem de cima | `NAO`, `P2` |
| `personagem_3` | Terceiro personagem de cima | `KANOKO`, `P3` |
| `personagem_4` | Quarto personagem de cima | `YUMI`, `P4` |
| `personagem_5` | Quinto personagem de cima | `KOKUJIN`, `P5` |

A IA pode escrever `personagem_1`, `personagem 1` ou `P1`; o bot normaliza tudo para `PERSONAGEM_1` internamente.

Para mudar de universo, não precisa alterar o código. Basta explicar para a IA quem ocupa cada slot, por exemplo:

```text
personagem_1 = Naruto
personagem_2 = Sasuke
personagem_3 = Sakura
personagem_4 = Kakashi
personagem_5 = Hinata
```

O arquivo `data/personagens.json` guarda os apelidos aceitos. As coordenadas continuam em `data/coords.json`.

## Formato Principal do Roteiro

O formato atual usa apenas `cena`, `layout` e `personagens`. As falas ficam no `texto` de quem fala; cenas mudas deixam todos os textos vazios. O bot gera os PNGs na ordem do roteiro, e o editor escolhe a posição de cada imagem no vídeo.

```json
[
  {
    "cena": 1,
    "layout": "react_room_livepix_v1",
    "personagens": {
      "personagem_1": {
        "emocao": "animado",
        "intensidade": 3,
        "texto": "Personagem 1: Olha isso!\nPersonagem 1: Look at that!\nPersonagem 1: Mira eso!"
      },
      "personagem_2": {
        "emocao": "neutro",
        "intensidade": 1,
        "texto": ""
      },
      "personagem_3": {
        "emocao": "surpreso",
        "intensidade": 2,
        "texto": ""
      },
      "personagem_4": {
        "emocao": "feliz",
        "intensidade": 2,
        "texto": ""
      },
      "personagem_5": {
        "emocao": "raiva",
        "intensidade": 1,
        "texto": ""
      }
    }
  }
]
```

Campos importantes:

| Campo | Descrição |
| --- | --- |
| `cena` | Número da cena. |
| `layout` | Preset visual; use `react_room_livepix_v1`. |
| `personagens` | Objeto com o estado de cada personagem da cena. |
| `emocao` | Chave em `data/presets_emocionais.json`. |
| `intensidade` | Nível usado no preset emocional, normalmente de 1 a 3. |
| `texto` | Texto exibido na imagem final. Se estiver vazio, o personagem não fala. |

### Falas em tres idiomas

Use uma string em `personagens.personagem_X.texto` com as três falas separadas por `\n`:

```json
{
  "emocao": "feliz",
  "intensidade": 3,
  "texto": "PERSONAGEM 1: fala em portugues\nPERSONAGEM 1: fala em ingles\nPERSONAGEM 1: fala em espanhol"
}
```

O bot interpreta as linhas nesta ordem:

```text
linha 1 = portugues
linha 2 = ingles
linha 3 = espanhol
```

O layout quebra automaticamente cada fala e ajusta a fonte para a faixa inferior. Roteiros antigos sem `layout` usam o preset padrão de `config.py`.

Veja `data/roteiro_layout.exemplo.json` para cenas com fala e mudas, e `PROMPT_ROTEIRO_LAYOUT.md` para as instruções de geração do roteiro.

Regras aplicadas pelo `ReactionDirector`:

- Os nomes dos personagens são normalizados para maiúsculo.
- Cada emoção/intensidade vira um par `olhos` + `boca` usando `presets_emocionais.json`.
- `personalidades.json` pode limitar intensidade ou substituir emoções por personagem.
- Apenas um personagem deve falar por cena.
- Apenas um personagem deve usar intensidade `3` por cena.

## Layout React Room Live Pix

O preset fixo se chama `react_room_livepix_v1` e fica em:

```text
data/layouts/react_room_livepix_v1.json
```

Ele define todas as regioes do canvas:

| Area | Posicao |
| --- | --- |
| Personagens + cenario | `x=0, y=0, w=1120, h=780` |
| QR Live Pix | `x=1120, y=20, w=760, h=90` |
| Video react | `x=1120, y=120, w=760, h=560` |
| Mensagens | `x=0, y=780, w=1920, h=300` |

O video react e preenchido com verde puro `#00FF00`. Essa area deve ser substituida manualmente no CapCut.

Para configurar QR Live Pix, edite o campo `qr_livepix.imagem` no preset. Se o caminho estiver vazio, a area fica limpa.

Cada slot em `personagens.slots` tambem aceita `imagem`. Se esse campo apontar para um PNG transparente, o bot usa esse arquivo no lugar do avatar desenhado. Se ficar vazio, usa o fallback visual do proprio render.

Valide o layout com:

```bash
python validar_layout.py
```

Esse teste gera:

```text
cenas/cena_001_exemplo_layout.png
cenas/cena_002_fala_longa.png
cenas/cena_003_muda_layout.png
```

## Formato Manual Compatível

O motor ainda aceita cena simples com olhos e boca explícitos:

```json
[
  {
    "personagem": "personagem_5",
    "olhos": "raiva",
    "boca": "gritando_raiva_2",
    "texto": "Personagem 5: Eu não aceito isso."
  }
]
```

Use esse formato quando quiser controlar diretamente as expressões sem passar pelo sistema de emoções.

## Emoções e Presets

`data/presets_emocionais.json` define a relação:

```text
emocao + intensidade -> olhos + boca
```

Exemplo:

```json
{
  "feliz": {
    "intensidade_1": { "olhos": "feliz", "boca": "sorrindo" },
    "intensidade_2": { "olhos": "olho_feliz", "boca": "sorrindo_feliz" },
    "intensidade_3": { "olhos": "neutro", "boca": "boca_falando_feliz" }
  }
}
```

As expressões citadas nos presets precisam existir em `data/expressoes.json`.

## Expressões

`data/expressoes.json` mapeia cada expressão para uma posição no seletor do Gacha Club:

```json
{
  "olhos": {
    "raiva": [1, 4, 4]
  },
  "bocas": {
    "gritando_raiva_2": [13, 1, 3]
  }
}
```

O formato é:

```text
[pagina, linha, coluna]
```

Os índices começam em 1.

## Remapear Expressões

Para listar o mapa atual:

```bash
python remapear.py listar
python remapear.py listar olhos
python remapear.py listar bocas
```

Para criar ou alterar uma expressão:

```bash
python remapear.py set olhos feliz_1 1 1 1
python remapear.py set boca gritando_raiva_1 13 1 1
```

O comando atualiza `data/expressoes.json` e mostra a coordenada de clique calculada.

## Coordenadas e Grid

`data/coords.json` guarda:

- Botões de personagens e navegação em `BOTOES`.
- Grade de olhos em `GRID_OLHOS`.
- Grade de bocas em `GRID_BOCAS`.
- Área do contador de página em `PAGINA_CONTADOR`.

O clique dentro do grid é calculado assim:

```text
x = primeiro_x + (coluna - 1) * dx
y = primeiro_y + (linha  - 1) * dy
```

Se a resolução, escala do Windows ou posição da janela mudar, essas coordenadas podem precisar ser refeitas.

## Detecção de Página

O bot usa `vision_paginas.py` para comparar o contador atual com imagens de referência em `refs_paginas/`.

Arquivos esperados:

- `refs_paginas/olhos_1.png`, `olhos_2.png`, etc.
- `refs_paginas/bocas_1.png`, `bocas_2.png`, etc.

Quando `DEBUG_SCREENSHOTS=True`, a captura atual do contador é salva em `debug_atual.png`.

## Saída

No modo `layout`, as imagens finais são salvas em `cenas/`:

```text
cena_001_personagem_1.png
cena_002_personagem_4.png
cena_003_grupo.png
```

Quando não há falante detectado, o rótulo usado no arquivo é `grupo`.

No modo `gacha`, imagens capturadas do jogo continuam usando `output/`. Se `DEBUG_SCREENSHOTS=True` em `config.py`, capturas de diagnóstico também são salvas em `output/debug/`.

### Legenda no modo gacha

Após a captura com MSS, a fala é desenhada no canto inferior esquerdo, em branco com contorno preto e uma caixa retangular preta atrás. A caixa acompanha o tamanho real do bloco, incluindo as quebras manuais `\n`. Cada idioma começa em sua própria linha; falas longas ganham linhas adicionais conforme a largura em pixels.

Valores recomendados em `config.py` (já configurados):

```python
FONT_SIZE = 36
TEXT_MIN_FONT_SIZE = 16
TEXT_ALIGN = "left"
TEXT_MARGIN_X = 15
TEXT_MARGIN_Y = 50
TEXT_LINE_SPACING = 8
TEXT_MAX_WIDTH_RATIO = 0.95
TEXT_COLOR = (255, 255, 255)
TEXT_OUTLINE = (0, 0, 0)
TEXT_STROKE_WIDTH = 2
TEXT_BOX_ENABLED = True
TEXT_BOX_PADDING_X = 20
TEXT_BOX_PADDING_Y = 12
TEXT_BOX_COLOR = (0, 0, 0)
TEXT_BOX_OPACITY = 220
TEXT_BOX_BORDER_COLOR = (80, 80, 80)
TEXT_BOX_BORDER_WIDTH = 0
```

As margens são medidas da borda externa da caixa até as bordas esquerda e inferior da captura. O padding fica dentro da caixa, além da borda opcional. A margem horizontal também reserva espaço à direita. Mantenha `TEXT_ALIGN = "left"` para alinhar todas as linhas à esquerda.

Use opacidade `255` para preto sólido ou um valor entre `0` e `254` para transparência. Para uma borda fina, use `TEXT_BOX_BORDER_WIDTH = 1`. Sem fala, nenhuma caixa é desenhada. Com `TEXT_BOX_ENABLED = False`, somente o texto e seu contorno são desenhados, usando as margens diretamente.

Com `FONT_PATH` vazio, o bot tenta Arial/Segoe UI do Windows antes da fonte padrão do Pillow, para exibir acentos e pontuação dos três idiomas. A fonte diminui apenas se o bloco não couber, até `TEXT_MIN_FONT_SIZE`. Se ainda não houver espaço, o bot informa um erro em vez de salvar texto cortado. A resolução original da captura e o destino `output/` são preservados. Essas opções não alteram o preset do modo `layout`.

Para validar as legendas sem controlar o jogo nem capturar a tela real:

```bash
py -X utf8 -B -m unittest test_screenshot -v
```

## Configurações

Os ajustes principais ficam em `config.py`:

| Configuração | Uso |
| --- | --- |
| `CLICK_DURATION` | Duração do movimento do mouse até o alvo. |
| `DELAY_CURTO`, `DELAY_MEDIO`, `DELAY_LONGO` | Pausas entre ações do jogo. |
| `DELAY_SUBMENU` | Pausa específica para submenus. |
| `CLICK_JITTER` | Pequena variação aleatória nos cliques. |
| `DEBUG_MOUSE` | Move o mouse e pausa antes de clicar. |
| `DEBUG_SCREENSHOTS` | Salva capturas antes de aplicar olhos/boca. |
| `FAILSAFE` | Permite cancelar levando o mouse ao canto superior esquerdo. |
| `RENDER_MODE` | `"layout"` gera PNG limpo; `"gacha"` usa o fluxo antigo do Gacha Club. |
| `LAYOUT_PRESET` | Nome do preset usado pelo render limpo. |
| `CENAS_DIR` | Pasta onde o modo `layout` salva os PNGs finais. |
| `MONITOR_INDEX` | Monitor capturado pelo MSS. |
| `SCREEN_RESOLUTION` | Resolução do monitor usada no modo `gacha`: `(1920, 1080)` ou `(1366, 768)`. |
| `COORDS_BASE_RESOLUTION` | Resolução em que `data/coords.json` foi medido; mantenha `(1920, 1080)`. |
| `FONT_PATH`, `FONT_SIZE` | Fonte usada no texto final. |
| `TEXT_ALIGN`, `TEXT_LINE_SPACING` | Alinhamento e espaçamento entre linhas da legenda no modo `gacha`. |
| `TEXT_MARGIN_X`, `TEXT_MARGIN_Y` | Margens externas da caixa de fala. |
| `TEXT_BOX_*` | Fundo, opacidade, padding e borda da caixa de fala. |
| `TEXT_MAX_WIDTH_RATIO`, `TEXT_MIN_FONT_SIZE` | Largura máxima da caixa e limite de redução da fonte. |
| `TEXT_MAX_CHARS` | Compatibilidade com `utils.quebrar_texto()`; a legenda agora usa largura em pixels. |

## Fluxo de Cada Cena

1. O roteiro é carregado de `data/roteiro.json`.
2. `ReactionDirector` resolve emoções em expressões finais.
3. Se `RENDER_MODE = "layout"`, o `layout_renderer.py`:
   - cria um canvas 1920x1080;
   - desenha cenário, sofá e personagens;
   - reserva a área verde `#00FF00` para o vídeo react;
   - reserva a área de QR Live Pix;
   - desenha as falas na faixa inferior;
   - valida tamanho, área verde, texto e limites dos personagens;
   - salva o PNG em `cenas/`.
4. Se `RENDER_MODE = "gacha"`, o bot usa o fluxo antigo. Para cada personagem da cena, ele:
   - seleciona o personagem;
   - abre o editor;
   - entra em Eyes e aplica olhos;
   - entra em Face e aplica boca;
   - fecha o editor.
5. No modo `gacha`, o bot entra no Estúdio, oculta a interface, captura a tela, restaura a interface, desenha o texto e salva em `output/`.

## Cuidados

- Não use o mouse enquanto o bot estiver rodando.
- Confirme se o jogo está na mesma resolução usada no mapeamento.
- Se o bot clicar no lugar errado, revise `data/coords.json`.
- Se ele errar páginas de olhos/bocas, revise `refs_paginas/` e `PAGINA_CONTADOR`.
- Antes de rodar um roteiro grande, teste com uma cena curta.

