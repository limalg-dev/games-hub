export const CATEGORIES = {
  animals: { name: 'Animais', words: ['CACHORRO', 'GATO', 'ELEFANTE', 'GIRAFA', 'LEAO', 'MACACO', 'PAPAGAIO', 'TARTARUGA', 'ZEBRA', 'COBRA', 'TIGRE', 'URSO', 'LOBO', 'RAPOSA', 'COELHO'] },
  countries: { name: 'Países', words: ['BRASIL', 'ARGENTINA', 'CANADA', 'FRANCA', 'ALEMANHA', 'ITALIA', 'JAPAO', 'MEXICO', 'PORTUGAL', 'ESPANHA', 'CHINA', 'INDIA', 'AUSTRALIA', 'EGITO', 'NORUEGA'] },
  tech: { name: 'Tecnologia', words: ['COMPUTADOR', 'INTERNET', 'SOFTWARE', 'HARDWARE', 'PYTHON', 'JAVASCRIPT', 'DATABASE', 'ALGORITMO', 'SERVIDOR', 'ROTEADOR', 'FIREWALL', 'CLOUD', 'SOCKET', 'API', 'FRAMEWORK'] },
  food: { name: 'Comida', words: ['PIZZA', 'HAMBURGUER', 'SUSHI', 'CHURRASCO', 'LASANHA', 'SALADA', 'SOBREMESA', 'CHOCOLATE', 'FRUTAS', 'VEGETAIS', 'PASTEL', 'TORTA', 'BOLO', 'SORVETE', 'CAFE'] },
  sports: { name: 'Esportes', words: ['FUTEBOL', 'BASQUETE', 'VOLEI', 'NATACAO', 'TENIS', 'CORRIDA', 'CICLISMO', 'BOXE', 'GOLFE', 'SURFE', 'SKATE', 'HIPISMO', 'REMO', 'VELA', 'ESGRIMA'] }
};

export function getRandomCategory() {
  const cats = Object.keys(CATEGORIES).filter(k => k !== 'random');
  return cats[Math.floor(Math.random() * cats.length)];
}

export function getWordsForCategory(category, count) {
  if (category === 'random') {
    const cat = getRandomCategory();
    return getWordsForCategory(cat, count);
  }
  const words = [...CATEGORIES[category].words];
  for (let i = words.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [words[i], words[j]] = [words[j], words[i]];
  }
  return words.slice(0, count);
}

export const DIFFICULTIES = {
  easy:   { gridSize: 10, wordCount: 6,  directions: 4,  name: 'Fácil',   timeBonus: 300 },
  medium: { gridSize: 12, wordCount: 10, directions: 8,  name: 'Médio',   timeBonus: 180 },
  hard:   { gridSize: 15, wordCount: 15, directions: 8,  name: 'Difícil', timeBonus: 120 }
};

export const DIRS_4 = [[0,1], [1,0], [0,-1], [-1,0]];
export const DIRS_8 = [[0,1], [1,0], [0,-1], [-1,0], [1,1], [1,-1], [-1,1], [-1,-1]];