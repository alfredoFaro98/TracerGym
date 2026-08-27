// Helper per leggere i design token CSS correnti (tema/accent) dentro
// configurazioni Chart.js che non possono usare var() direttamente
// (i grafici sono renderizzati su <canvas>, non lette dalla cascata CSS).
function tracerToken(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}
