# Frontend: correções de mobile e responsividade

## Contexto

Auditoria feita em produção (game.ofertasshow.shop) com viewport de iPhone
(390×844, UA iOS) via portal do navegador do Maestri, cobrindo a landing e os
7 jogos. A landing em si já se comporta bem em mobile (cards, categorias). Os
problemas estão nas telas de jogo — alguns são bugs bloqueantes (não regras
de responsividade "bonita", literalmente impedem jogar), outros são overflow
estrutural.

## Escopo

Todos os itens abaixo entram na mesma spec/branch. Fora de escopo: unificar a
paleta visual dos jogos standalone (Snake/Ant Defense/Tower Defense/Colônia
Hex) com o design system da landing — isso fica para uma rodada futura,
focada em responsividade agora.

## Achados e correções

### 1. [Crítico] Botão de fechar do modal bloqueado pelo overlay do ícone
**Onde:** `static/app.js`, `openModal()`, bloco que insere
`.modal-game-icon-overlay` (adicionado no hotfix anterior para não mostrar
mais o tabuleiro de damas na prévia de outros jogos).
**Problema:** o overlay é `position:absolute; inset:0; z-index:2` sobre
`previewEl.parentElement`. Em telas estreitas isso cobre a área onde o botão
"Fechar modal" (`.modal-close`) fica, e como o overlay tem `z-index:2`, ele
intercepta o clique — confirmado com `elementFromPoint` no ponto exato do
botão retornando o overlay, não o botão. Resultado: impossível fechar o
modal no mobile sem recarregar a página.
**Fix:** dar ao `.modal-close` um `z-index` maior que o do overlay (ex.
`z-index: 10` nele, ou baixar o do overlay para não competir), e/ou escopar
o overlay estritamente ao container da prévia (não a `previewEl.parentElement`
inteiro, que pode ser maior que a prévia em si). Testar clique no × depois.

### 2. [Crítico] Snake, Ant Defense e Tower Defense não têm botão de voltar
**Onde:** `games/snake/index.html`, `games/ant_defense/index.html` (+ sua
duplicata `static/index.html`), `games/tower_defense/static/index.html`.
**Problema:** nenhuma dessas três páginas tem qualquer link/botão de volta
para a landing — confirmado ausência total no DOM. A única saída é o gesto
de voltar do navegador.
**Fix:** adicionar um link de volta no cabeçalho de cada uma, consistente
com o padrão já usado em checkers/wordsearch/crossword/colony_hex
(`.btn-back`, seta ← apontando para `/`).

### 3. [Crítico] Painel lateral da Colônia Hex fica fora da tela no mobile
**Onde:** `games/colony_hex/static/index.html` / `static/styles.css`
(classe `.sidebar` compartilhada).
**Problema:** a página reaproveita a classe `.sidebar`, que no CSS
compartilhado é um painel recolhível fora-da-tela (off-canvas, aberto por um
botão `#sidebar-toggle` que só existe na SPA de damas/palavras). A Colônia
Hex não tem esse botão, então o painel — Seu Painel, Recrutar Operária/
Soldado, Encerrar Turno, Lobby — fica permanentemente en `x: -280px`,
inacessível. Confirmado via `getBoundingClientRect()`. O jogo é injogável no
celular hoje.
**Fix:** não reaproveitar o `.sidebar` off-canvas aqui. Ou (a) dar à Colônia
Hex uma classe própria que empilha o painel abaixo do tabuleiro em telas
estreitas (media query, sem transform/off-canvas), ou (b) adicionar o botão
de abrir/fechar equivalente ao das outras páginas. Opção (a) é mais simples
e evita reintroduzir um padrão de UI que o próprio jogo não precisa.

### 4. [Estrutural] Overflow horizontal em 5 dos 7 jogos
**Onde:** Caça-Palavras, Snake, Ant Defense, Tower Defense, Colônia Hex.
**Problema:** `document.body.scrollWidth > clientWidth` confirmado nos 5 —
página "estoura" para o lado com scroll horizontal indesejado. Causa
recorrente: elementos `<canvas>` com `width`/`height` fixos em atributos
HTML (ex. Colônia Hex: `width="500" height="500"`) sem contenção via CSS.
Danas e Cruzadas não têm esse problema — usar o CSS deles (se houver
`max-width:100%`) como referência.
**Fix:** em cada canvas/grid afetado, aplicar `max-width: 100%; height:
auto` (ou equivalente por `aspect-ratio`) e garantir que o container pai não
force uma largura mínima maior que o viewport. Rodar o sweep de overflow
(abaixo) depois de cada correção pra confirmar que zerou.

### 5. [Menor] Cabeçalho de jogo quebra linha de forma feia em telas estreitas
**Onde:** `.game-status`/`.game-header` (CSS compartilhado, afeta pelo menos
Colônia Hex: "Conectando ao lobby... Turno" quebra no meio, "1/20" cai numa
linha separada).
**Fix:** ajustar o layout do cabeçalho (flex-wrap controlado, `font-size`
menor em telas estreitas via media query, ou abreviar o texto de status) pra
não partir frases no meio.

## Verificação

Para cada item, testar via portal do Maestri em viewport 390×844 (UA iOS):
- Modal: abrir um jogo não-checkers, confirmar que o × fecha o modal.
- Snake/Ant Defense/Tower Defense: confirmar botão de volta presente e
  funcional.
- Colônia Hex: confirmar que o painel lateral aparece e os botões
  (Recrutar Operária/Soldado, Encerrar Turno) são clicáveis.
- Rodar em cada um dos 7 `/play/<jogo>`:
  `document.body.scrollWidth <= document.body.clientWidth` (sem overflow).
- Suíte completa (`./.venv/bin/pytest`) verde antes de considerar pronto.

## Fora de escopo (próxima rodada)

Unificação visual dos jogos standalone com o design system da landing
(`DESIGN.md`/`.impeccable/design.json`) — cada um tem hoje uma paleta
própria, bem diferente da landing e entre si. Fica para depois que a
responsividade estiver resolvida.
