# Simplificar a navegação da landing para um grid único

Data: 2026-08-11

## Objetivo

Exibir todos os jogos uma única vez, sem repetição e sem destaques (badges
"Novo"/"Popular"/"Em Destaque" e seção "Em destaque"/coleções). Manter os
filtros por tipo/categoria, mostrando apenas os jogos que fazem sentido para
a categoria clicada, sem badges e sem repetir jogos.

## Contexto atual

A landing possui três áreas que duplicam jogos:

- `featured-spotlight` + `featured-secondary` (seção "Em destaque") — um jogo
  pode aparecer tanto aqui quanto no grid.
- `renderCollections()` — sliders por coleção (`treine-sua-mente`,
  `acao-pura`, `2-jogadores`, `classicos-atemporais`); jogos com múltiplas
  coleções aparecem em vários sliders.
- `game-grid` — lista principal filtrada pelos tabs de categoria.

Todos os cards renderizam badges via `renderBadge`/`getBadgeLabel`/
`getBadgeClass`.

## Decisões

- Remover a seção `featured` (spotlight + secondary) e a seção `collections`
  da landing.
- Manter apenas hero + navegação por categoria + grid único.
- Grid sem badges: remover `renderBadge(game)` dos cards do grid.
- Abas de categoria derivadas dinamicamente das categorias presentes nos
  jogos (sem abas vazias), preservando o comportamento atual de filtro por
  `game.category`.
- Extrair a lógica pura (lista de jogos, categorias, filtro e cards) para
  `static/games.js`, consumida por `app.js`, para permitir teste via Node
  usando o mesmo harness de `tests/test_play_url.py`.
- `GAMES` continua definido em `static/games.js`, eliminando o duplicado
  atual em `app.js`.

## Arquitetura

### `static/games.js` (novo)

- `GAMES` — objeto com os 6 jogos (checkers, wordsearch, crossword, snake,
  ant_defense, tower_defense), movido do `app.js`.
- `allGames()` → `Game[]` (valores de `GAMES`, ordenados por `rating`
  descendente para uma vitrine estável).
- `categories()` → `string[]` — categorias distintas presentes em `GAMES`,
  na ordem de definição dos tabs existentes.
- `gamesByCategory(category)` → `Game[]` — todos os jogos quando
  `category === 'all'`; caso contrário os que incluem a categoria.
- `gameCard(game)` → `string` — HTML do card do grid **sem badge**.

### `static/app.js`

- Importar `GAMES`, `allGames`, `categories`, `gamesByCategory`, `gameCard`
  de `/static/games.js`; remover a definição local de `GAMES` e de
  `COLLECTIONS`.
- Remover `renderFeaturedSpotlight`, `renderFeaturedSecondary`,
  `renderCollections`, `gamesForCollection`, `renderBadge` e os listeners de
  `featuredSection` e `collectionsContainer`; remover
  `activeCollectionFilteredGames`.
- `renderGameGrid(category)` → usa `gamesByCategory` + `gameCard`.
- Adicionar `renderCategoryTabs()` que popula `.category-list` a partir de
  `categories()` (todas + uma aba por categoria), mantendo o listener de
  clique existente (via delegação).
- `init()` passa a chamar `renderCategoryTabs()` + `renderGameGrid()`.

### `static/index.html`

- Remover o bloco `<section class="featured">` e sua moldura; remover as abas
  de categoria estáticas (passam a ser renderizadas por JS) e a seção
  `<section class="collections">`.
- Manter hero, `.category-nav` (vazio, populado por JS) e `<main id="game-grid">`.

### Estilos

- Limpar/remover regras órfãs `.featured*` e `.collections*` em
  `static/styles.css` somente se ficarem sem uso; regras sobreviventes do
  grid são mantidas. (Avaliar por cobertura após a mudança de markup.)

## Fluxo de dados

`init()` → `renderCategoryTabs()` (popula tabs) → `renderGameGrid('all')`
(renderiza os 6 cards, um por jogo). Click numa aba → `activeCategory` muda →
`renderGameGrid(category)` → `gamesByCategory(category)` → cards sem badge.

## Tratamento de erros

- `gamesByCategory` nunca lança: retorna `[]` para categoria inexistente.
- Tabs: abas sem jogos não são renderizadas.
- Sem alterações no fluxo de `/play/{game}` nem no backend.

## Testes

Novo `tests/test_games_list.py` (harness Node, espelhando `test_play_url.py`):

- `allGames()` contém exatamente os 6 ids, sem duplicados.
- `categories()` inclui todas as categorias usadas por `GAMES` e não exige o
  'all' (inserido no front).
- `gamesByCategory(cat)` retorna só jogos daquela categoria e `[]` para
  categoria inexistente.
- `gameCard(g)` não contém `badge`, `featured`, `collection` nem o jogo
  repetido.
- Requisito "sem repetição" é coberto por: para cada categoria real, cada id
  aparece no máximo uma vez em `gamesByCategory(cat)` e exatamente uma vez em
  `allGames()`.
- Ajustes em `tests/test_static_js_imports.py` continuam válidos (imports
  batem com novos exports).

## Fora de escopo

- Mudanças em backend, em `/play/{game}`, no modal ou no fluxo de jogo.
- Alteração de conteúdo/coleções dos jogos em si.