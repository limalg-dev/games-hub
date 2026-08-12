---
target: GameHub shared SPA shell (landing/modal/game view)
total_score: 21
max_score: 36
na_heuristics: 7
p0_count: 1
p1_count: 2
p2_count: 2
timestamp: 2026-08-12T11-11-23Z
slug: static-index-html
---
Method: dual-agent (A: ses_00a56b4beffeNUHm6VArQY4OQR · B: ses_00a56a650ffeQvzaoAXsDcNL0H)

# Design Critique — GameHub shared SPA shell (static/index.html)

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 2 | WS connect/close only logs to console (app.js:522,531); board shows static "Brancas jogam" even while status is waiting; resign gives zero feedback |
| 2 | Match System / Real World | 2 | Shell is pt-BR but checkers content is fully EN (games.js:5-25); preview canvas aria is hardcoded "Checkers board preview" for crossword/wordsearch too |
| 3 | User Control and Freedom | 2 | Esc/backdrop/back work, but "Desistir" is a no-op (app.js:380) — a visible exit control that cannot exit an online match |
| 4 | Consistency and Standards | 2 | Two same-action "Jogar" buttons per card (games.js:204,227); focus-visible list omits .sidebar-toggle, clue rows, history rows; inline style override for wordsearch menu |
| 5 | Error Prevention | 3 | Guarded play-gate, buildPlayUrl nulls href instead of 404, strict /play whitelist parser — genuine hardening |
| 6 | Recognition Rather Than Recall | 3 | Badges, modal rules, gate titles; few memory demands |
| 7 | Flexibility and Efficiency | n/a | No-account casual hub; accelerators (arrows, Esc, target=_blank) already present, no personalization surface to earn more |
| 8 | Aesthetic and Minimalist Design | 3 | Disciplined flat-by-default + mono + gold rules; penalized by 6 redundant full-width red CTAs and animated emoji thumbs |
| 9 | Error Recovery | 2 | Only game-prepare path recovers well ("Não foi possível carregar o jogo" + "Recarregar"); WS/fetch/resign fail silently |
| 10 | Help and Documentation | 2 | Inline modal rules are contextual; zero elsewhere |
| **Total** | | **21/36** | **Acceptable (58%)** |

## Design Specificity Verdict

**Token-anchored, composition-interchangeable — coherent in parts, generic in the middle.**

**LLM assessment:** The theater rules from DESIGN.md are plausibly executed — one-gradient hero H1, wood confined to real board surfaces, mono only for read-outs, hairline-not-shadow at rest, the play-gate scrim, gold reserved for earned states. Those tokens would not sit on an unrelated product. But the composition is the default game-store rectangle: a repeat(auto-fit, minmax(280px,1fr)) catalog where every card ships an identical full-width red "Jogar Agora" button plus a generic dark-blur hover overlay. Six simultaneous equal-weight red CTAs contradict "red is rare; its rarity is its power." The emoji-thumb with 3s float is a category cliché. The genuinely authored moments: the modal's board preview rendered from the real game, and the wordsearch gate that builds the live grid behind the scrim. Verdict: partially anchored.

**Deterministic scan:** The bundled detector returned zero findings (exit 0, empty output). The manual contrast arithmetic caught what the detector can't and the LLM review missed: action-surface contrast failures (below).

**Visual overlays:** No browser automation tool exists in this environment, so no [Human] overlay injection was possible. This must be flagged as a limitation — several findings were approximated from source and arithmetic, not rendered proof. Fallback signal: CLI only.

## Overall Impression

The shell executes its own design system with discipline, but the moment the visitor reaches for an action, the theater breaks: a dead "Desistir", a modal that opens a second tab demanding a second decision, EN copy inside a PT shell, and action buttons that fail their own contrast test. The single biggest opportunity: trust the in-place SPA flow the code already has, so choosing a game stays one click and the neon-red spotlight actually means something.

## What's Working

1. **The palette/elevation contract is executed**, not improvised — flat-by-default, lift-on-state, wood only on boards, mono for read-outs, one-gradient hero (styles.css:36,58-61,84-86,329).
2. **The /play deep-link machinery is product-grade** — nulls href instead of 404ing (play-url.js:23-34), whitelist parser fails high, double-click guarded, prepare-failure recovers with "Recarregar" (app.js:471-474,496-502). This is the differentiator treated as a product.
3. **The modal decision anatomy is right, and one touch is genuinely delightful** — title → specs → rules → config → one CTA, three close affordances, aria-modal; and for wordsearch the gate shows the already-built grid behind the scrim before "Jogar" (app.js:484-489).

## Priority Issues

1. **[P0] "Desistir" is a corpse.** `// TODO: resign logic` at app.js:380 — renders enabled, never disables, does nothing. In a multiplayer checkers match it's the user's only exit; the opponent waits forever. **Fix:** implement a resign WebSocket message, or remove the button until then. *(suggested: $impeccable adapt)*
2. **[P1] Modal "Jogar Agora" double-gates and double-tabs.** index.html:36 is target="_blank" → /play/… → gate → second click. The SPA knows how to start every game in place (startGame/startCrossword/beginWordSearch). Contradicts PRODUCT's "play gated behind one click"; worst on mobile. **Fix:** start in this SPA from the modal; reserve the gate for cold /play shared links. *(suggested: $impeccable polish / adapt)*
3. **[P1] Action surfaces fail WCAG AA contrast.** White on neon-red = 3.83:1 (fails 4.5:1 for normal text) on .btn-play, .category-tab.active, .history li.current; white on accent-hover #ff6b6b = 2.78:1 (fails even 3:1) on hover states; neon-red text on night-card = 3.26:1 for links/danger. **Fix:** darken the red for text-on-red contexts, or use dark text on red buttons; bump accent-hover for hover-contrast. *(suggested: $impeccable audit / colorize)*
4. **[P2] Checkers still speaks English inside a pt-BR shell** — desc, shortDesc, modes, difficulty and all rules are EN (games.js:5-25); plus hardcoded "Checkers board preview" aria mislabels the crossword/wordsearch preview (index.html:29). **Fix:** translate the checkers entry and dynamic aria re-labeling. *(suggested: $impeccable polish)*
5. **[P2] The One-Spotlight rule is defeated.** Six full-width red CTAs at once (games.js:227) plus the red active pill. "Rare, so it means press me" cannot survive six. **Fix:** demote card CTAs to secondary/hairline; let red live on hovered/focused card, active tab, and the modal's single primary. *(suggested: $impeccable quieter / bolder on the right target)*

## Persona Red Flags

**Casey (Distracted Mobile)** — the primary audience:
- Taps "Jogar Agora" and lands in a fresh tab facing a second "Jogar" gate — the game moved to a tab she didn't ask for.
- Refresh/tab-switch mid-game loses the whole puzzle (module-memory only; backToLanding re-zeroes at app.js:353); no resume.
- On ≤480px crossword/checkers lose Novo Jogo/Desistir entirely (styles.css:174); crossword cells shrink to 26px — far below 44px, and the dead resign is hidden exactly where it'd be needed.

**Jordan (First-Timer):**
- Opens Checkers and reads "Classic 8×8 English draughts… Capture all opponent pieces" inside an otherwise-Portuguese modal (games.js:5-25); hesitates and assumes the game will be in English too.
- Hover-overlay Jogar button can't be reached on touch, but the visible one works — minor, yet the card offers two CTAs for one action, which is confusing when it can't be tapped.

**Sam (Accessibility):**
- Tabs to .sidebar-toggle and sees no focus ring (styles.css:307-317 omits it); crossword inputs drop the native outline entirely (styles.css:271), relying on a JS class that can miss.
- White-on-red action text fails 4.5:1; hovered buttons drop to 2.78:1 — below even the 3:1 UI minimum.
- .category-toggle aria-label never flips to "Fechar" when expanded; #modal-board-canvas aria is wrong for non-checkers games.

## Minor Observations

- index.html:36 default href="/" on #modal-play-btn — a click before refreshPlayLink runs navigates to landing root.
- "Brancas jogam" hardcoded in the shared #turn-indicator flashes for wordsearch/crossword until JS rewrites it.
- Wordsearch victory uses native alert() — the anti-theater reward (app.js:233); crossword victory has no Play Again off-ramp.
- The 6-tab category row exceeds the ≤5 nav guideline (app.js:416-421); mild.
- Wordsearch bypasses the ≤480px menu-hide rule via inline style (app.js:305) while board games don't — inconsistency.

## Questions to Consider

- What if the modal played the game in this same tab, so "Jogar Agora" was the only gate ever shown?
- Does the emoji-float thumbnail earn its place, or is it the one category default holding the world back?
- What would a confident version of the in-game state look like once Desistir actually works?

## Run Notes

- Target slug: static-index-html (confirmed via critique-storage slug).
- Ignore list: none (no .impeccable/critique/ignore.md).
- Assessment independence: preserved — A and B ran as two isolated parallel sub-agents with self-contained prompts; B's detector output entered synthesis only after A finished.
- CLI detector: ran, exit 0, zero findings.
- Browser visibility: unavailable — no browser automation tool in this environment; fallback signal "CLI only".
- Overlay injection: not attempted (no browser); no user-visible overlay exists.
- Live server: none started.
- Contrast values computed arithmetically from CIELAB/luminance; rendered gradient states approximated and flagged as unconfirmed.
- Known limitation: several findings are source-derived, not rendered proof, because this environment has no browser to inspect computed styles.
