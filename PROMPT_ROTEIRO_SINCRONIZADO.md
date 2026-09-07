# Prompt para roteiro sincronizado React Gacha

Voc? vai gerar um roteiro JSON para o bot React Gacha.

Entrada dispon?vel:
- dura??o total do v?deo
- letra completa
- acontecimentos do v?deo
- emo??es por trecho
- ordem dos acontecimentos

Tarefa:
0. Use a timeline decupada por Gemini como fonte de verdade. A IA diretora n?o deve alterar os tempos vindos da decupagem.
1. Divida o v?deo em cenas naturais de aproximadamente 3 segundos.
2. Cada cena pode durar 2.5, 3.0 ou 3.5 segundos.
3. Nunca corte uma frase no meio.
4. Corte apenas em mudan?a de verso, emo??o, cantor, punchline, revela??o importante, in?cio/fim de refr?o ou mudan?a de assunto.
5. Insira cenas mudas quando houver revela??o importante ou rea??o visual sem fala.
6. Gere somente JSON v?lido, sem coment?rios fora do JSON.

Cada cena precisa conter:
- cena
- inicio
- fim
- duracao
- trecho_da_letra
- resumo_do_trecho
- personagem_cantando
- fala
- personagens

Personagens obrigatórios em todas as cenas:
- personagem_1
- personagem_2
- personagem_3
- personagem_4
- personagem_5

Antes de gerar o JSON, use a explicação do usuário para entender quem ocupa cada slot. Exemplo: `personagem_1 = Naruto`, `personagem_2 = Sasuke`. Nunca troque os nomes dos slots no JSON final.

Emo??es permitidas:
- neutro
- feliz
- triste
- raiva
- surpreso
- medo
- tedio
- animado

Regras obrigat?rias:
- Intensidade permitida: 1, 2 ou 3.
- Apenas um personagem pode usar intensidade 3 por cena.
- Apenas um personagem pode falar por cena.
- Se fala for false, todos os textos devem ser vazios.
- O JSON final deve ser uma lista direta, come?ando com `[`.
- N?o use o formato `{ "cenas": [...] }`.
- Preserve exatamente `inicio`, `fim`, `duracao`, `trecho_da_letra`, `resumo_do_trecho` e `personagem_cantando`. Esses campos s?o metadados de sincroniza??o e n?o controlam emo??es.

Modelo de cena:

```json
{
  "cena": 1,
  "inicio": "00:00.0",
  "fim": "00:03.0",
  "duracao": 3,
  "trecho_da_letra": "trecho exato da m?sica",
  "resumo_do_trecho": "contexto dram?tico do trecho",
  "personagem_cantando": "nome de quem canta nesse trecho",
  "fala": false,
  "personagens": {
    "personagem_1": { "emocao": "neutro", "intensidade": 1, "texto": "" },
    "personagem_2": { "emocao": "neutro", "intensidade": 1, "texto": "" },
    "personagem_3": { "emocao": "neutro", "intensidade": 1, "texto": "" },
    "personagem_4": { "emocao": "neutro", "intensidade": 1, "texto": "" },
    "personagem_5": { "emocao": "neutro", "intensidade": 1, "texto": "" }
  }
}
```
