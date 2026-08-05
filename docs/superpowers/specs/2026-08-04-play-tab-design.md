# Abrir o jogo numa aba própria com portão de Play

**Data:** 2026-08-04
**Status:** aprovado, aguardando plano de implementação

## Problema

Hoje o jogo começa na mesma aba: o card abre um modal, e "Jogar Agora" troca a
landing pela `#game-view` imediatamente. Isso tem dois efeitos ruins. A partida
não tem endereço próprio — não dá para compartilhar, favoritar nem recarregar
sem perder o jogo. E o wordsearch dispara o cronômetro no mesmo instante em que
o tabuleiro aparece, antes do jogador estar pronto.

## Solução

Cada jogo ganha uma URL própria, aberta numa aba nova. A aba mostra o jogo em
estado de espera com um botão Play; a partida só começa no clique.

### Rotas

`GET /play/{game}` devolve `static/index.html` — o mesmo arquivo servido em `/`.
Um `game` fora da lista conhecida responde 404.

A configuração viaja na query string, com os nomes que o código já usa
(`difficulty`, `category`), evitando uma camada de tradução:

| Jogo | URL |
|---|---|
| Damas | `/play/checkers` |
| Wordsearch | `/play/wordsearch?difficulty=hard&category=animals` |
| Crossword | `/play/crossword?difficulty=medium` |

Parâmetros ausentes ou inválidos caem no mesmo padrão que o modal já aplica
hoje: `difficulty=easy`, `category=random`.

### Landing

O modal continua sendo o único lugar onde se escolhe dificuldade e categoria.
O que muda é o destino do botão.

`#modal-play-btn` deixa de chamar `startGame` e vira um `<a target="_blank">`
cujo `href` é remontado sempre que o modal abre ou que uma opção muda. Um
âncora, e não `window.open`, para que ctrl+clique e clique do meio funcionem e
nenhum bloqueador de pop-up interfira.

### Boot na aba

No carregamento, `app.js` lê `location.pathname`. Se casar `/play/{game}`:

1. pula a landing e chama `showView('game')`
2. monta a tela em estado "pronto"
3. exibe um overlay com o nome do jogo e o botão Play

O clique no Play chama as funções de início que já existem — `startGame`,
`startWordSearch(config)`, `startCrossword()` — e remove o overlay. Nenhuma
delas é reescrita.

### O que "pronto" significa

| Jogo | Antes do Play | No Play |
|---|---|---|
| Damas | tabuleiro inicial desenhado localmente, sem `POST /games` e sem WebSocket | cria a partida e conecta |
| Wordsearch | grid montado com a config da URL, cronômetro parado | inicia o cronômetro |
| Crossword | tabuleiro vazio sob o overlay | cria a partida e conecta |

O crossword aparece vazio porque o puzzle é gerado no servidor e só chega
depois do `POST /games`. Criar a partida ao abrir a aba deixaria partidas órfãs
no banco a cada aba aberta e abandonada.

O portão vale igual para os três jogos, inclusive damas, que não tem nenhuma
opção para configurar. Um caminho único é mais simples de manter do que uma
exceção.

### Mudança necessária no wordsearch

`WordSearchGame.init()` hoje chama `this.start()` no fim, disparando o
cronômetro junto com a montagem do grid. Os dois passos precisam ser separados
para o portão significar alguma coisa: `init()` monta, `start()` começa a
contar.

### Navegação dentro da aba

O botão voltar passa a navegar para `/`. A aba não é fechada por script — o
navegador só permite fechar abas que ele mesmo abriu, e esta pode ter vindo de
um link colado.

O New Game continua reiniciando direto, sem voltar ao overlay.

## Verificação

- pytest: `/play/{jogo}` devolve 200 e o mesmo HTML de `/`; jogo inválido
  devolve 404
- Chrome headless: escolher dificuldade e categoria no modal e conferir que o
  `href` do botão reflete a escolha
- Chrome headless: abrir `/play/wordsearch?difficulty=hard&category=animals`,
  confirmar overlay presente e cronômetro zerado; após o Play, grid 15×15 e
  cronômetro correndo
- Chrome headless: abrir `/play/checkers` e confirmar que nenhum WebSocket é
  aberto antes do Play

## Fora de escopo

- O fluxo do New Game, corrigido em #5
- Roteamento client-side além da leitura única no boot
- Qualquer mudança na landing além do destino do botão
