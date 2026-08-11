export const PLAYABLE_GAMES = [
  'checkers',
  'wordsearch',
  'crossword',
  'snake',
  'ant_defense',
  'tower_defense',
];

const DIFFICULTIES = ['easy', 'medium', 'hard'];
const CATEGORIES = ['random', 'animals', 'countries', 'tech', 'food', 'sports'];

const DEFAULTS = { difficulty: 'easy', category: 'random' };

function pick(value, allowed, fallback) {
  return allowed.includes(value) ? value : fallback;
}

// Devolve `null` quando `game` não está em PLAYABLE_GAMES. Um jogo desconhecido
// só produziria um link para um 404, então a validação falha alto no ponto de
// construção em vez de silenciosamente: quem chama decide o que fazer (a
// landing simplesmente não publica o href).
export function buildPlayUrl(game, options = {}) {
  if (!PLAYABLE_GAMES.includes(game)) return null;
  const params = new URLSearchParams();
  const difficulty = pick(options.difficulty, DIFFICULTIES, DEFAULTS.difficulty);
  const category = pick(options.category, CATEGORIES, DEFAULTS.category);
  // Only values that differ from the default earn a place in the URL, so a
  // shared link stays readable.
  if (difficulty !== DEFAULTS.difficulty) params.set('difficulty', difficulty);
  if (category !== DEFAULTS.category) params.set('category', category);
  const query = params.toString();
  return query ? `/play/${game}?${query}` : `/play/${game}`;
}

export function parsePlayUrl(pathname, search = '') {
  const match = /^\/play\/([^/?#]+)\/?$/.exec(pathname || '');
  if (!match) return null;
  let game;
  try {
    game = decodeURIComponent(match[1]);
  } catch {
    return null;
  }
  if (!PLAYABLE_GAMES.includes(game)) return null;
  const params = new URLSearchParams(search);
  return {
    game,
    difficulty: pick(params.get('difficulty'), DIFFICULTIES, DEFAULTS.difficulty),
    category: pick(params.get('category'), CATEGORIES, DEFAULTS.category),
  };
}
