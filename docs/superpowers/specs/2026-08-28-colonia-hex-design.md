# Colônia Hex — Game Design Specification

> **Game:** Colônia Hex (Hex Colony)
> **Category:** Estratégia em Turnos / Conquista Territorial (Turn-Based Strategy / 4X Minimalist)
> **Benchmark:** *Antiyoy* / *Slay* (Sean O'Connor)
> **Platform:** GameHub Web (FastAPI + HTML5 Canvas 2D + Web Audio API)
> **Status:** Approved

---

## 1. Visão Geral do Jogo

**Colônia Hex** é um jogo de estratégia pura e minimalista jogado em uma grade hexagonal. O objetivo é expandir o território da sua colônia, administrar a economia (renda vs. salários das tropas) e conquistar as colônias rivais através do controle de fronteiras e fusão tática de unidades.

### Características Principais
- **Zero Sorte / 100% Estratégia:** Sem dados ou probabilidades. O combate é determinístico baseado em hierarquia de força e defesa de zona.
- **Fusão de Unidades:** Junte 2 Operárias para criar 1 Soldado; junte Operária + Soldado para criar 1 Guardião; junte unidades para criar um Guerreiro de Elite.
- **Economia Territorial:** Cada hexágono controlado gera folhas/ouro (+1/turno). Unidades consomem salário de manutenção (upkeep). Se a economia quebrar, as tropas morrem de fome!
- **Corte de Território (Províncias):** Ao cortar a linha de conexão do território inimigo, você divide a colônia rival em duas províncias menores com economias isoladas.
- **Partidas Rápidas:** 5 a 10 minutos contra IA inteligente (Fácil, Médio, Difícil) ou 2 jogadores locais.

---

## 2. Arquitetura & Estrutura de Arquivos

Seguindo o padrão de módulos autocontidos do GameHub:

```
games/colonia_hex/
├── __init__.py
├── logic.py              # Lógica pura: Hex grid, províncias (BFS), fusão, combate, economia, gerador de mapa, IA bots
├── routes.py             # FastAPI APIRouter: /colonia-hex/* (criar partida, mover, passar turno, highscores, /play)
├── test_colonia_hex_logic.py # Suíte de testes unitários
└── static/
    └── index.html        # Canvas 2D interativo com renderização hexagonal, WebAudio SFX, HUD e animações

app/main.py               # Registro do router e mount dos estáticos
static/games.js           # Card do jogo no catálogo principal
tests/test_colonia_hex_integration.py # Testes de integração de API
```

---

## 3. Mecânicas Detalhadas

### 3.1 Sistema de Coordenadas Hexagonais
- **Grade Axial:** Coordenadas $(q, r)$.
- **Vizinhos (6 Direções):**
  $$(+1, 0), (+1, -1), (0, -1), (-1, 0), (-1, +1), (0, +1)$$
- **Conversão para Pixels (Pointy-Topped):**
  $$x = \text{size} \times \sqrt{3} \times (q + r / 2) + \text{offsetX}$$
  $$y = \text{size} \times \frac{3}{2} \times r + \text{offsetY}$$
  Raio do hexágono: $R = 24\text{px}$.

---

### 3.2 Hierarquia de Unidades e Fusão

| Nível | Unidade | Custo Recrutamento | Salário (Upkeep/turno) | Força de Ataque | Regra de Fusão |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **1** | 🐜 **Operária (Worker)** | 10 🍃 | 2 🍃 | **1** | Recrutada na Capital/Hexágono |
| **2** | 🛡️ **Soldado (Spearman)** | 20 🍃 | 6 🍃 | **2** | $1 + 1$ (2 Operárias) |
| **3** | ⚔️ **Guardião (Guardian)** | 30 🍃 | 18 🍃 | **3** | $1 + 2$ (Operária + Soldado) |
| **4** | 👑 **Elite (Knight)** | 40 🍃 | 54 🍃 | **4** | $2 + 2$ ou $1 + 3$ |

- **Regra de Movimento:** Cada unidade pode mover-se até 4 hexágonos dentro do próprio território ou dar 1 passo para conquistar um hexágono adjacente neutro/inimigo por turno.
- **Fusão em Campo:** Mover uma unidade sobre outra unidade aliada no mesmo hexágono combina seus níveis (ex: Nível 1 + Nível 2 = Nível 3), desde que o nível final não ultrapasse 4.

---

### 3.3 Construções & Defesas

| Estrutura | Custo | Upkeep | Defesa Fornecida | Efeito Especial |
| :--- | :---: | :---: | :---: | :--- |
| 🏰 **Castelo (Capital)** | Inicial / 20 🍃 | 0 🍃 | **Defesa 1** | Centro de comando da Província. |
| 🌾 **Fazenda (Farm)** | 12 🍃 | 0 🍃 | **Defesa 0** | Gera **+4 🍃** extras de renda por turno. |
| 🗼 **Torre de Vigia (Tower)** | 15 🍃 | 1 🍃 | **Defesa 2** | Protege o próprio hexágono e todos os 6 hexágonos vizinhos. |
| 🏰 **Torre Forte (Strong Tower)** | 35 🍃 | 6 🍃 | **Defesa 3** | Protege o próprio hexágono e vizinhos com Força 3 (precisa de Elite para invadir). |
| 🌲 **Árvore / Floresta** | — | — | — | Obstáculo natural. Operárias podem cortar (+3 🍃 instantâneo). |

---

### 3.4 Regras de Combate e Conquista
1. **Defesa do Hexágono:**
   $$\text{Defesa} = \max(\text{Nível da Unidade no Hex}, \text{Estrutura no Hex}, \text{Torres Aliadas Vizinhas})$$
2. **Condição de Conquista:**
   Uma unidade só pode capturar um hexágono inimigo se:
   $$\text{Força da Unidade Atacante} > \text{Defesa do Hexágono Alvo}$$
3. **Eliminação de Defensores:**
   Ao invadir um hexágono com unidade inimiga inferior, a unidade defensora é destruída.

---

### 3.5 Economia, Províncias e Falência
- **Formação de Província:** Todos os hexágonos conectados do mesmo jogador formam uma Província com tesouro compartilhado.
- **Cálculo de Fim de Turno:**
  $$\text{Renda Líquida} = \text{Qtd Hexágonos} + (4 \times \text{Fazendas}) - \text{Total Upkeep}$$
  $$\text{Novo Tesouro} = \text{Tesouro Atual} + \text{Renda Líquida}$$
- **Falência (Fome):**
  Se $\text{Novo Tesouro} < 0$, a província entra em colapso: todas as unidades morrem imediatamente e viram lápides/árvores. O tesouro é resetado para 0.

---

### 3.6 Inteligência Artificial dos Bots (Single Player)
- **Fácil:** Expande para hexágonos neutros e corta árvores; raramente recruta acima do Nível 1.
- **Médio:** Mantém economia positiva (+5 de margem), recruta Soldados e Guardiões, protege fronteiras com Torres.
- **Difícil:** Identifica chokepoints, corta linhas inimigas para causar falência por isolamento, prioriza destruir Fazendas e cercar capitais.

---

## 4. Frontend & Game Feel (`index.html`)

- **Renderização Hexagonal:** Desenho de malha vetorial no Canvas com cores distintas por facção (Verde, Vermelho, Azul, Dourado).
- **Contornos de Província:** Traçado escuro conectando as bordas externas do território unificado.
- **Áudio Procedural WebAudio:**
  - `sfx_click`: clique sutil de seleção de hexágono.
  - `sfx_move`: som de marcha/passo de formiga.
  - `sfx_merge`: fanfarra de promoção de unidade.
  - `sfx_build`: som de construção de madeira/pedra.
  - `sfx_conquer`: impacto de conquista territorial.
  - `sfx_starve`: som dramático de quebra econômica.
  - `sfx_turn`: sino de passagem de turno.
  - `sfx_victory` / `sfx_defeat`.
- **HUD Interativo:**
  - Painel superior: Província selecionada, Tesouro (🍃), Renda Líquida (+/- por turno), Indicador de Turno.
  - Painel inferior: Ações rápidas (Recrutar Operária [10🍃], Construir Fazenda [12🍃], Construir Torre [15🍃], Passar Turno).

---

## 5. Endpoints REST & Contrato de API

- `POST /colonia-hex/api/new`: cria partida `{ difficulty: "easy"|"medium"|"hard", map_size: "small"|"medium"|"large", players: 2|3|4 }`.
- `GET /colonia-hex/api/state/{game_id}`: retorna estado da grade, províncias, unidades, histórico e turno atual.
- `POST /colonia-hex/api/action`: executa ação `{ game_id, action_type: "recruit"|"move"|"build"|"end_turn", ... }`.
- `GET /colonia-hex/api/highscores` e `POST /colonia-hex/api/highscores`: ranking de vitórias e pontuações.
- `GET /play/colonia_hex`: serve a interface HTML5 do jogo.
