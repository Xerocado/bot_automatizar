# Prompt para roteiro React Gacha com layout

Gere um roteiro JSON para o bot React Gacha usando o layout `react_room_livepix_v1`.
O bot gera imagens PNG 1920x1080 com personagens a esquerda, area verde para o
video a direita, espaco para QR Live Pix e falas na faixa inferior.

## Informacoes para criar as reacoes

Use o conteudo fornecido pelo usuario, a ordem dos acontecimentos e a personalidade
dos personagens. O usuario explica quem ocupa cada slot de `personagem_1` a
`personagem_5`. Mantenha esses slots como chaves, mesmo ao mudar de universo.

## Formato obrigatorio

- Retorne somente JSON valido, em uma lista direta `[...]`.
- Cada cena deve conter apenas `cena`, `layout` e `personagens`.
- Numere as cenas em sequencia a partir de 1.
- Use `layout: "react_room_livepix_v1"` em todas as cenas.
- Inclua todos os cinco slots em cada cena.
- Cada personagem deve ter `emocao`, `intensidade` e `texto`.
- Emocoes aceitas: `neutro`, `feliz`, `triste`, `raiva`, `surpreso`, `medo`, `tedio`, `animado`.
- Intensidades aceitas: 1, 2 ou 3; no maximo um personagem com intensidade 3 por cena.
- No maximo um personagem fala por cena.

## Falas

Coloque a fala em `personagens.personagem_X.texto`, no slot de quem fala.
Use uma string com tres linhas separadas por `\n`, nesta ordem: portugues,
ingles e espanhol. O nome exibido pode ser o nome real do personagem do universo.
Os demais personagens ficam com `texto: ""`.

Em cenas mudas, deixe `texto: ""` nos cinco personagens. As emocoes continuam
definindo as reacoes visuais. O editor escolhe quando colocar cada PNG no video.

## Exemplo

```json
[
  {
    "cena": 1,
    "layout": "react_room_livepix_v1",
    "personagens": {
      "personagem_1": {
        "emocao": "surpreso",
        "intensidade": 3,
        "texto": "PERSONAGEM 1: Eu nao esperava por isso!\nPERSONAGEM 1: I was not expecting that!\nPERSONAGEM 1: No esperaba eso!"
      },
      "personagem_2": { "emocao": "neutro", "intensidade": 1, "texto": "" },
      "personagem_3": { "emocao": "feliz", "intensidade": 2, "texto": "" },
      "personagem_4": { "emocao": "neutro", "intensidade": 1, "texto": "" },
      "personagem_5": { "emocao": "triste", "intensidade": 1, "texto": "" }
    }
  }
]
```
