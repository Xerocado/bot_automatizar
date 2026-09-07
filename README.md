# bot_automatizar

Bot em Python para automatizar cenas de reação no Gacha Club. Ele lê um roteiro em JSON, aplica expressões de olhos e boca nos personagens, abre o Estúdio, oculta a interface, captura a tela e salva uma imagem final com texto sobreposto.

O projeto trabalha principalmente com coordenadas fixas, grid matemático e comparação simples de imagens para identificar a página atual dos seletores de olhos/bocas.

## Estrutura

```text
bot_automatizar/
├── data/
│   ├── coords.json                    # Coordenadas de botões, grids e contador de página
│   ├── expressoes.json                # Mapa de olhos/bocas: [pagina, linha, coluna]
│   ├── personalidades.json            # Regras por personagem
│   ├── presets_emocionais.json        # Emoção + intensidade -> olhos/boca
│   ├── roteiro.json                   # Roteiro executado pelo bot
│   └── roteiro_completo.exemplo.json  # Exemplo de roteiro com vários personagens
├── refs_paginas/                      # Referências do contador de página
├── output/                            # Imagens geradas
├── character_personality.py           # Ajustes de emoção por personagem
├── config.py                          # Configurações centrais
├── emotion_preset_system.py           # Resolve presets emocionais
├── engine.py                          # Motor de automação
├── main.py                            # Ponto de entrada
├── reaction_director.py               # Converte roteiro em expressões finais
├── remapear.py                        # Ferramenta para listar/editar expressões
├── screenshot.py                      # Captura e overlay de texto
├── utils.py                           # JSON, logs, grid e quebra de texto
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

1. Abra o Gacha Club na tela e resolução usadas para mapear as coordenadas.
2. Deixe o jogo na tela inicial/personagens esperada pelo bot.
3. Edite `data/roteiro.json`.
4. Execute:

```bash
python main.py
```

O bot espera 3 segundos antes de começar, para dar tempo de focar a janela do jogo.

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

O formato atual descreve o estado de todos os personagens em cada cena:

```json
[
  {
    "video": 1,
    "cena": 1,
    "personagens": {
      "personagem_1": {
        "emocao": "animado",
        "intensidade": 3,
        "texto": "Personagem 1: Olha isso!"
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
| `personagens` | Objeto com o estado de cada personagem da cena. |
| `emocao` | Chave em `data/presets_emocionais.json`. |
| `intensidade` | Nível usado no preset emocional, normalmente de 1 a 3. |
| `texto` | Texto exibido na imagem final. Se estiver vazio, o personagem não fala. |

Regras aplicadas pelo `ReactionDirector`:

- Os nomes dos personagens são normalizados para maiúsculo.
- Cada emoção/intensidade vira um par `olhos` + `boca` usando `presets_emocionais.json`.
- `personalidades.json` pode limitar intensidade ou substituir emoções por personagem.
- Apenas um personagem deve falar por cena.
- Apenas um personagem deve usar intensidade `3` por cena.

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

As imagens finais são salvas em `output/`:

```text
cena_001_personagem_1.png
cena_002_personagem_4.png
cena_003_grupo.png
```

Quando não há falante detectado, o rótulo usado no arquivo é `grupo`.

Se `DEBUG_SCREENSHOTS=True` em `config.py`, capturas de diagnóstico são salvas em `output/debug/`.

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
| `MONITOR_INDEX` | Monitor capturado pelo MSS. |
| `FONT_PATH`, `FONT_SIZE` | Fonte usada no texto final. |
| `TEXT_MAX_CHARS` | Limite de caracteres por linha no overlay. |

## Fluxo de Cada Cena

1. O roteiro é carregado de `data/roteiro.json`.
2. `ReactionDirector` resolve emoções em expressões finais.
3. Para cada personagem da cena, o bot:
   - seleciona o personagem;
   - abre o editor;
   - entra em Eyes e aplica olhos;
   - entra em Face e aplica boca;
   - fecha o editor.
4. O bot entra no Estúdio.
5. A interface é ocultada.
6. A tela é capturada.
7. A interface é restaurada.
8. O texto é desenhado na imagem.
9. O PNG final é salvo em `output/`.

## Cuidados

- Não use o mouse enquanto o bot estiver rodando.
- Confirme se o jogo está na mesma resolução usada no mapeamento.
- Se o bot clicar no lugar errado, revise `data/coords.json`.
- Se ele errar páginas de olhos/bocas, revise `refs_paginas/` e `PAGINA_CONTADOR`.
- Antes de rodar um roteiro grande, teste com uma cena curta.

## Roteiro Sincronizado para CapCut

O roteiro tamb?m pode trazer a marca??o temporal de cada cena. O bot n?o edita o v?deo, mas valida esses tempos, preserva os metadados e gera dois arquivos de apoio em `output/`:

- `timeline_capcut.json`: timeline limpa para consulta.
- `timeline_capcut.csv`: planilha simples para abrir ao lado do CapCut.

Para gerar somente a timeline, sem controlar o Gacha Club:

```bash
python timeline.py
```

Ao rodar `python main.py`, a timeline tamb?m ? gerada antes da automa??o come?ar.

Formato recomendado:

```json
[
  {
    "cena": 18,
    "inicio": "00:52.0",
    "fim": "00:55.0",
    "duracao": 3,
    "trecho_da_letra": "?s vezes eu s? queria ser normal",
    "resumo_do_trecho": "Hiroki demonstra cansa?o e desejo por uma vida comum.",
    "personagem_cantando": "Hiroki",
    "fala": false,
    "personagens": {
      "personagem_1": { "emocao": "triste", "intensidade": 2, "texto": "" },
      "personagem_2": { "emocao": "triste", "intensidade": 1, "texto": "" },
      "personagem_3": { "emocao": "neutro", "intensidade": 1, "texto": "" },
      "personagem_4": { "emocao": "triste", "intensidade": 2, "texto": "" },
      "personagem_5": { "emocao": "tedio", "intensidade": 1, "texto": "" }
    }
  }
]
```

Aliases aceitos no roteiro:

| Campo preferido | Alias aceito |
| --- | --- |
| `trecho_da_letra` | `trecho` |
| `resumo_do_trecho` | `contexto` |
| `personagem_cantando` | `cantor`, `personagem_cantor` |

Regras validadas pelo bot:

- Se uma cena tiver timeline, todas as cenas precisam ter `inicio`, `fim`, trecho, contexto e `personagem_cantando`.
- `duracao` deve bater com `inicio` e `fim`, com toler?ncia de 0.2 segundo.
- Cada cena deve durar entre 2.5 e 3.5 segundos.
- O tempo final precisa ser maior que o tempo inicial.
- O formato aceito ? `MM:SS.d` ou `HH:MM:SS.d`.
- Cenas mudas devem usar `fala: false` e deixar `texto` vazio nos personagens.
- O bot preserva `inicio`, `fim`, `duracao`, `trecho_da_letra`, `resumo_do_trecho` e `personagem_cantando`; esses campos servem s? para sincroniza??o da edi??o.

Veja tamb?m `data/roteiro_sincronizado.exemplo.json` e `PROMPT_ROTEIRO_SINCRONIZADO.md`.

