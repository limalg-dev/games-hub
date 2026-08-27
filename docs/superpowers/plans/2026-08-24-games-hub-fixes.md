# Games Hub — Correções Pós-Análise (Implementation Plan)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restaurar 100% da suíte de testes, padronizar o Damas em PT-BR, persistir estado WS no SQLite e alinhar dependências.

**Architecture:** FastAPI + SQLModel/SQLite; jogos em `games/<nome>/` com routers próprios; WS compartilhado em `app/websocket.py` com `ConnectionManager` em memória; frontend estático por jogo em `games/<nome>/static/`.

**Tech Stack:** Python 3.14, FastAPI 0.115, SQLModel 0.0.21, pytest 9 + pytest-asyncio 1.4, uvicorn[standard].

## Global Constraints

- NÃO fazer `git commit` — commits centrais serão feitos pelo OpenCode após verificação integrada.
- Cada tarefa só pode modificar arquivos do SEU escopo (listado abaixo). Qualquer mudança fora do escopo = parar e reportar.
- Seguir TDD: teste primeiro, ver falhar, implementar, ver passar.
- Rodar testes com `.venv/bin/python -m pytest` a partir da raiz do projeto.
- Estado geral atual: 250 passed / 7 failed / 1 skipped (`tests/test_tower_defense_integration.py`).

---

### Task 1: Corrigir os 7 testes de Tower Defense (ALTA)

**Owner:** agent1 · **Status:** pendente

**Files:**
- Modify (se necessário): `tests/test_tower_defense_integration.py`
- Modify (se for bug real): `games/tower_defense/logic.py`
- Read-only: `games/tower_defense/routes.py`, `games/tower_defense/tests.py`

**Contexto recon:**
- As 7 falhas: `TestTowerUpgrade::test_upgrade_increases_damage`, `test_upgrade_increases_range`, `test_upgrade_deducts_crystals`, `test_upgrade_insufficient_leaves`, `TestTowerSell::test_sell_returns_correct_value`, `test_sell_adds_leaves`, `test_sell_removes_tower`.
- Falha observada: `game.place_tower(1, 1, TowerType.ARCHER)` retorna `success=False`.
- Suspeita: refatoração de terreno/moeda — obstáculos agora em posições fixas (`logic.py:590-596`: pebble/leaf/twig/water/moss) e moeda renomeada `leaves`→`crystals` (alias property em `logic.py:449-454`).
- Os testes unitários em `games/tower_defense/tests.py` PASSAM (usam posições/valores diferentes).

**Passos:**
- [ ] **Step 1:** Rodar os 7 testes e capturar falhas exatas: `.venv/bin/python -m pytest tests/test_tower_defense_integration.py -v --tb=short`
- [ ] **Step 2:** Investigar causa raiz (systematic-debugging): ler `logic.py` (grid/obstáculos/place_tower/upgrade_tower/sell_tower) e comparar posições usadas pelos testes vs obstáculos definidos. Determinar: teste desatualizado ou bug funcional?
- [ ] **Step 3:** Decidir correção por evidência:
  - Se terreno mudou (posições viraram obstáculo): atualizar posições nos TESTES para células válidas/vazias, mantendo as assertions semânticas (upgrade aumenta dano/range, deduz custo, sell devolve 50%, remove torre).
  - Se for bug real na lógica (ex.: upgrade não aplica, sell calcula errado): corrigir `logic.py` e adicionar caso de teste que reproduz o bug antes do fix.
- [ ] **Step 4:** Verificar suíte completa verde: `.venv/bin/python -m pytest tests/test_tower_defense_integration.py games/tower_defense/tests.py -v` → 100% pass
- [ ] **Step 5:** Reportar via `maestri ask "OpenCode" "<resumo: causa raiz, arquivos alterados, resultado dos testes>"`

---

### Task 2: Checkers/Damas PT-BR completo (MÉDIA)

**Owner:** agent2 (após Task 4) · **Status:** pendente

**Files:**
- Modify: `games/checkers/static/board.js`, `games/checkers/static/index.html` (se existir), outros assets de `games/checkers/static/`
- Modify (se houver textos): `static/index.html` (hub) — somente strings relacionadas ao checkers
- Read-only: `games/checkers/routes.py`, `games/checkers/ai.py`

**Contexto recon (da análise do agent1):**
- Textos visuais já majoritariamente PT-BR; restam aria-labels, índices/coordenadas (a–h/1–8 são padrão internacional — MANTER), e textos residuais em inglês (ex.: "Easy", "White", mensagens de status).
- Regras de xadrez/damas em PT-BR: Brancas/Negras, Fácil/Médio/Difícil, "Sua vez", "Vitória!", "Empate".

**Passos:**
- [ ] **Step 1:** Inventariar strings em inglês: `grep -rnE '"[A-Z][a-z]+( [a-z]+)*"' games/checkers/static/ | grep -vE '^\s*//'` e revisar aria-labels, alt, title, toasts, botões.
- [ ] **Step 2:** Traduzir para PT-BR mantendo chaves de i18n/classes CSS intactas. Não traduzir: nomes de variáveis, IDs DOM, coordenadas do tabuleiro, termos consagrados ("checkers" no código).
- [ ] **Step 3:** Verificar se há teste de UI/rota do checkers: `.venv/bin/python -m pytest tests/ -k checkers -v` → deve continuar passando.
- [ ] **Step 4:** Reportar via `maestri ask "OpenCode" "<lista de strings traduzidas + resultado dos testes>"`

---

### Task 3: Persistência incremental do estado WS no SQLite (BAIXA→MÉDIA)

**Owner:** agente livre após Task 1 ou 2 · **Status:** pendente

**Files:**
- Modify: `app/websocket.py` (handler `websocket_endpoint`, `_cleanup_game`)
- Possibly modify: `app/models.py` (campo de estado serializado já existe? verificar `Game.state`)
- Test: criar `tests/test_ws_persistence.py`

**Contexto recon:**
- Hoje: estado das partidas (Damas, Palavras Cruzadas) vive só no `ConnectionManager` (RAM); DB é consultado apenas em connect/game over (`app/websocket.py:32,297,348`).
- Objetivo: snapshot do estado a cada jogada relevante, permitindo recuperação após restart do servidor.

**Interfaces:**
- Produces: função `persist_state(game_id: str, state: dict) -> None` (ou equivalente inline) chamada após cada mutação de jogo broadcastada; reconnect lê estado do DB antes do RAM.

**Passos:**
- [ ] **Step 1:** Escrever teste falhando em `tests/test_ws_persistence.py`: conectar WS, enviar jogada, desconectar, reiniciar manager (novo ConnectionManager), reconectar e assertar que o estado veio do SQLite (não vazio). Usar DB de teste isolado (fixture tmp_path), nunca `games.db` de produção.
- [ ] **Step 2:** Rodar e confirmar FAIL: `.venv/bin/python -m pytest tests/test_ws_persistence.py -v`
- [ ] **Step 3:** Implementação mínima: salvar `state` serializado (JSON) na coluna existente do `Game` após cada jogada processada; no connect, hidratar `manager.game_states[game_id]` do DB quando ausente em RAM.
- [ ] **Step 4:** Verde: `.venv/bin/python -m pytest tests/test_ws_persistence.py -v` PASS + suíte WS existente: `.venv/bin/python -m pytest tests/ -k "ws or websocket or connection" -v` PASS.
- [ ] **Step 5:** Reportar via `maestri ask "OpenCode" "<resumo técnico + testes>"`

---

### Task 4: Alinhar dependências pyproject/requirements (BAIXA)

**Owner:** agent2 (primeiro, rápido) · **Status:** pendente

**Files:**
- Modify: `pyproject.toml`
- Read-only: `requirements.txt`, `requirements-prod.txt`

**Diff atual (recon):**

| Pacote | pyproject.toml | requirements.txt | requirements-prod.txt |
|---|---|---|---|
| fastapi | ==0.115 ✓ | ==0.115 | ==0.115 |
| uvicorn | ==0.30 ✗ (sem [standard]) | ==0.30 [standard] | ==0.30 [standard] |
| sqlmodel | ==0.21 ✓ | ==0.21 | ==0.21 |
| reportlab | AUSENTE ✗ | ==5.0.1 | ==5.0.1 |

**Passos:**
- [ ] **Step 1:** Em `pyproject.toml [project.dependencies]`: trocar `"uvicorn==0.30"` → `"uvicorn[standard]==0.30"`; adicionar `"reportlab==5.0.1"`.
- [ ] **Step 2:** Adicionar grupo dev com deps de teste (espelhando requirements.txt): `[dependency-groups] dev = ["pytest==8.2", "pytest-asyncio==1.4.0", "httpx==0.27"]`. Nota: ambiente local tem versões mais novas instaladas — alinhar ARQUIVOS apenas, não reinstalar nada.
- [ ] **Step 3:** Validar parse: `.venv/bin/python -c "import tomllib; tomllib.load(open('pyproject.toml','rb')); print('ok')"` e smoke import: `.venv/bin/python -c "from app.main import app; print('import ok')"`.
- [ ] **Step 4:** Reportar via `maestri ask "OpenCode" "<diff aplicado>"`.

---

## Sequenciamento (evitar conflito de pytest simultâneo em DB compartilhado)

```
Rodada 1 (paralelo):
  agent1 → Task 1 (TD tests, pesada)
  agent2 → Task 4 (deps, rápida) → depois Task 2 (checkers, frontend)
Rodada 2:
  primeiro agente livre → Task 3 (WS persistence)
Verificação final: OpenCode roda suíte completa + revisa diffs + commits sequenciais
```

## Self-review do plano

- Cobertura: 4 itens da nota Projeto + bug TD detectado pelo agent2 → Tasks 1-4 ✓
- Sem placeholders: todos os steps têm comandos/critérios ✓
- Tipos/interfaces: `persist_state(game_id, state)` definida na Task 3, consumida internamente ✓
- Riscos: prompt de permissão do Antigravity (agent1) → orquestrador aprova via raw input se travar ✓
