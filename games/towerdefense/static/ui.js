export function createHUD(container) {
    const hud = document.createElement("div");
    hud.className = "td-hud";
    hud.innerHTML = `
        <div class="td-stats">
            <span class="td-gold">Gold: 200</span>
            <span class="td-lives">Lives: 20</span>
            <span class="td-wave">Wave: 0</span>
        </div>
        <div class="td-shop">
            <button data-tower="rifle" class="td-tower-btn">Rifle (50g)</button>
            <button data-tower="sniper" class="td-tower-btn">Sniper (120g)</button>
            <button data-tower="missile" class="td-tower-btn">Missile (150g)</button>
            <button data-tower="tesla" class="td-tower-btn">Tesla (100g)</button>
            <button data-tower="slow" class="td-tower-btn">Slow (80g)</button>
        </div>
        <button class="td-start-wave">Start Wave</button>
    `;
    container.appendChild(hud);
    return hud;
}

export function updateHUD(hud, gold, lives, wave) {
    hud.querySelector(".td-gold").textContent = `Gold: ${gold}`;
    hud.querySelector(".td-lives").textContent = `Lives: ${lives}`;
    hud.querySelector(".td-wave").textContent = `Wave: ${wave}`;
}
