// static/games.js
export const GAMES = {
  checkers: {
    id: 'checkers',
    title: 'Damas',
    desc: 'Jogo de damas clássico 8×8. Capture todas as peças do oponente ou bloqueie-as completamente.',
    shortDesc: 'Damas clássicas 8×8. Jogue contra a IA ou com um amigo.',
    players: 2,
    modes: ['Local', 'IA', 'Online'],
    category: ['tabuleiro', 'estrategia', 'classicos'],
    collections: ['2-jogadores', 'classicos-atemporais'],
    duration: '5–15 min',
    difficulty: ['Fácil', 'Médio', 'Difícil'],
    rating: 4.8,
    plays: 125000,
    featured: true,
    badge: 'destaque',
    thumbnail: '',
    rules: [
      'Mova na diagonal para frente, apenas nas casas escuras',
      'Capture pulando sobre uma peça adversária adjacente',
      'Capturas múltiplas são permitidas em um único turno',
      'Chegue à última fileira para virar Dama (move-se também para trás)',
      'Vença capturando todas as peças inimigas ou bloqueando todos os movimentos'
    ]
  },
  wordsearch: {
    id: 'wordsearch',
    title: 'Caça-Palavras',
    desc: 'Encontre palavras escondidas na grade. Múltiplas categorias e níveis de dificuldade.',
    shortDesc: 'Encontre palavras na grade. Várias categorias.',
    players: 1,
    modes: ['Solo', 'Timer', 'Ranking'],
    category: ['palavras', 'classicos'],
    collections: ['treine-sua-mente', 'classicos-atemporais'],
    duration: '5–20 min',
    difficulty: ['Fácil', 'Médio', 'Difícil'],
    rating: 4.5,
    plays: 98000,
    featured: false,
    badge: 'popular',
    thumbnail: '',
    rules: [
      'Palavras podem estar horizontais, verticais ou diagonais',
      'Podem ser lidas da esquerda para direita ou vice-versa',
      'Arraste para selecionar letras da palavra',
      'Palavras encontradas ficam marcadas na lista',
      'Complete todas as palavras para vencer'
    ]
  },
  crossword: {
    id: 'crossword',
    title: 'Palavras Cruzadas',
    desc: 'Resolva palavras cruzadas geradas dinamicamente pelo servidor. Dicas across/down e multijogador.',
    shortDesc: 'Cruza palavras com dicas. Solo ou online.',
    players: '1–2',
    modes: ['Solo', 'Online'],
    category: ['palavras', 'classicos'],
    collections: ['treine-sua-mente'],
    duration: '5–25 min',
    difficulty: ['Fácil', 'Médio', 'Difícil'],
    rating: 4.7,
    plays: 64000,
    featured: false,
    badge: 'novo',
    thumbnail: '',
    rules: [
      'Clique numa dica ou célula para selecionar a palavra',
      'Digite a letra em cada célula; letras corretas ficam verdes',
      'Setas alternam entre horizontal e vertical',
      'Células pretas são blocos (não preenchíveis)',
      'Complete todo o grid para vencer. Dois jogadores podem resolver juntos'
    ]
  },
  snake: {
    id: 'snake',
    title: 'Snake',
    desc: 'Jogo da cobrinha moderno. Coma maçãs para crescer sem colidir com as paredes ou consigo mesmo.',
    shortDesc: 'Coma maçãs, cresça e não colida!',
    players: 1,
    modes: ['Solo', 'High Score'],
    category: ['acao', 'classicos'],
    collections: ['acao-pura', 'classicos-atemporais'],
    duration: '2–10 min',
    difficulty: ['Fácil', 'Médio', 'Difícil'],
    rating: 4.6,
    plays: 150000,
    featured: true,
    badge: 'popular',
    icon: '🐍',
    thumbnail: '',
    rules: [
      'Use setas ou WASD para controlar a cobrinha',
      'Coma maçãs vermelhas para crescer e ganhar pontos',
      'Não colida com as paredes ou com o próprio corpo',
      'A velocidade aumenta progressivamente',
      'Pause/Resume a qualquer momento'
    ]
  },
  tower_defense: {
    id: 'tower_defense',
    title: '🐜 Tower Defense',
    desc: 'Tower Defense estratégico onde formigas defendem o formigueiro contra invasores. 10 ondas, upgrades e 3 tipos de torre!',
    shortDesc: 'Defenda o formigueiro com torres estratégicas!',
    players: 1,
    modes: ['Solo', '10 Ondas'],
    category: ['estrategia', 'acao'],
    collections: ['treine-sua-mente', 'acao-pura'],
    duration: '10–30 min',
    difficulty: ['Fácil', 'Médio', 'Difícil'],
    rating: 4.8,
    plays: 120000,
    featured: true,
    badge: 'destaque',
    thumbnail: '🐜',
    icon: '🐜',
    rules: [
      'Posicione torres nas células do grid ao longo do caminho',
      'Torres: Arqueiro (rápido), Bomba (área), Gelo (desacelera)',
      'Faça upgrade ou venda torres para otimizar sua defesa',
      'Inimigos: Mosca (rápida), Besouro (tanque), Percevejo (voador)',
      'Sobreviva a 10 ondas para vencer!'
    ]
  },
  colony_hex: {
    id: 'colony_hex',
    title: 'Colônia Hex',
    desc: 'Jogo de estratégia 4X por turnos. Expanda seu território em um mapa hexagonal, recrute operárias/soldados e conquiste ninhos inimigos.',
    shortDesc: 'Estratégia hexagonal de formigas. Solo ou multiplayer.',
    players: '2–4',
    modes: ['Solo', 'IA', 'Online'],
    category: ['estrategia', 'tabuleiro'],
    collections: ['treine-sua-mente'],
    duration: '10–20 min',
    difficulty: ['Médio'],
    rating: 4.8,
    plays: 54000,
    featured: true,
    badge: 'novo',
    thumbnail: '🐜',
    icon: '🐜',
    rules: [
      'Controle ninhos de formigas em grade hexagonal (raio 4)',
      'Gere 1 folha por turno para cada célula de território dominado',
      'Ações: expandir território, recrutar unidades (operária/soldado) ou mover/atacar',
      'Soldados atacam e capturam unidades ou territórios oponentes',
      'Capture o ninho adversário para eliminá-lo. Vence quem sobrar ou tiver maior pontuação'
    ]
  }
};

const CATEGORY_LABELS = {
  acao: 'Ação',
  tabuleiro: 'Tabuleiro',
  palavras: 'Palavras',
  estrategia: 'Estratégia',
  classicos: 'Clássicos',
};

export function allGames() {
  return Object.values(GAMES).sort((a, b) => b.rating - a.rating);
}

export function categoryLabel(cat) {
  return CATEGORY_LABELS[cat] || cat;
}

export function categories() {
  return Object.keys(CATEGORY_LABELS).filter(cat =>
    Object.values(GAMES).some(g => g.category && g.category.includes(cat))
  );
}

export function gamesByCategory(category) {
  if (category === 'all') return allGames();
  if (!category) return [];
  return Object.values(GAMES).filter(g => g.category && g.category.includes(category));
}

function formatPlays(plays) {
  if (plays >= 1000000) return (plays / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
  if (plays >= 1000) return (plays / 1000).toFixed(0) + 'K';
  return String(plays);
}

function renderThumbnail(game) {
  if (game.icon) {
    return `<div class="game-icon-real">${game.icon}</div>`;
  }
  if (game.thumbnail) {
    return `<img src="${game.thumbnail}" alt="${game.title}">`;
  }
  return `<svg class="game-preview" viewBox="0 0 80 80" width="80" height="80">${generateGamePreviewSVG(game.id)}</svg>`;
}

function gameHoverOverlay(game) {
  return `
    <div class="game-hover-overlay">
      <h3>${game.title}</h3>
      <p class="game-desc">${game.shortDesc}</p>
      <div class="game-hover-meta">
        <span>★ <span class="val">${game.rating.toFixed(1)}</span></span>
        <span><span class="val">${formatPlays(game.plays)}</span> partidas</span>
      </div>
      <button class="btn-play" data-game="${game.id}">Jogar</button>
    </div>
  `;
}

function playerLabel(players) {
  return players === 1 ? '1 Jogador' : `${players} Jogadores`;
}

export function gameCard(game) {
  return `
    <article class="game-card" data-game="${game.id}">
      <div class="game-thumb">
        ${renderThumbnail(game)}
      </div>
      <div class="game-info">
        <h3>${game.title}</h3>
        <p class="game-desc">${game.shortDesc}</p>
        <div class="game-meta">
          <span class="badge">${playerLabel(game.players)}</span>
          <span class="badge">${game.duration}</span>
        </div>
      </div>
      <button class="btn-card" data-game="${game.id}">Jogar Agora</button>
      ${gameHoverOverlay(game)}
    </article>
  `;
}

function generateGamePreviewSVG(gameId) {
  const square = 10;
  if (gameId === 'crossword') {
    const letters = { '1,1':'A','1,2':'P','1,3':'I','1,4':'O','1,5':'D','3,1':'C','4,1':'O','5,1':'D','5,2':'O','5,3':'M','5,4':'E','5,5':'S','2,3':'T','3,3':'A','4,3':'E' };
    let svg = '';
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const x = c * square, y = r * square;
        const key = `${r},${c}`;
        if (letters[key]) {
          svg += `<rect x="${x}" y="${y}" width="${square}" height="${square}" fill="#fff" stroke="#b58863" stroke-width="0.75"/>`;
          svg += `<text x="${x+5}" y="${y+6.5}" font-size="6" fill="#0f3460" text-anchor="middle" font-family="monospace">${letters[key]}</text>`;
        } else {
          svg += `<rect x="${x}" y="${y}" width="${square}" height="${square}" fill="#0f3460"/>`;
        }
      }
    }
    return svg;
  }
  if (gameId === 'wordsearch') {
    let svg = '';
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const x = c*square, y = r*square;
        svg += `<rect x="${x}" y="${y}" width="${square}" height="${square}" fill="#0f3460" stroke="#2a2a4a" stroke-width="0.5"/>`;
        const letter = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[(r*8+c) % 26];
        svg += `<text x="${x+5}" y="${y+7}" font-size="7" fill="#eaeaea" text-anchor="middle" font-family="monospace">${letter}</text>`;
      }
    }
    return svg;
  }
  let svg = '';
  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      if ((r + c) % 2 === 0) {
        svg += `<rect x="${c*square}" y="${r*square}" width="${square}" height="${square}" fill="#b58863"/>`;
      }
    }
  }
  const pieces = [
    {r:1,c:1,col:'w'},{r:1,c:3,col:'w'},{r:1,c:5,col:'w'},{r:1,c:7,col:'w'},
    {r:6,c:0,col:'b'},{r:6,c:2,col:'b'},{r:6,c:4,col:'b'},{r:6,c:6,col:'b'},
    {r:3,c:3,col:'w'},{r:4,c:4,col:'b'}
  ];
  pieces.forEach(p => {
    const cx = p.c*square + square/2;
    const cy = p.r*square + square/2;
    const col = p.col === 'w' ? '#fff' : '#111';
    svg += `<circle cx="${cx}" cy="${cy}" r="3.5" fill="${col}" stroke="#333" stroke-width="0.5"/>`;
  });
  return svg;
}