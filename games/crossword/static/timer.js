export class Timer {
    constructor() {
        this.seconds = 0;
        this.interval = null;
        this.element = null;
    }

    start(elementId) {
        this.element = document.getElementById(elementId);
        this.seconds = 0;
        this.interval = setInterval(() => {
            this.seconds++;
            if (this.element) {
                const m = Math.floor(this.seconds / 60);
                const s = this.seconds % 60;
                this.element.textContent = `${m}:${s.toString().padStart(2, "0")}`;
            }
        }, 1000);
    }

    stop() {
        clearInterval(this.interval);
        return this.seconds;
    }

    reset() {
        this.stop();
        this.seconds = 0;
    }
}

export function saveScore(time, difficulty) {
    const scores = JSON.parse(localStorage.getItem("crossword_scores") || "[]");
    scores.push({ time, difficulty, date: new Date().toISOString() });
    scores.sort((a, b) => a.time - b.time);
    localStorage.setItem("crossword_scores", JSON.stringify(scores.slice(0, 10)));
}

export function getLeaderboard() {
    return JSON.parse(localStorage.getItem("crossword_scores") || "[]");
}
