// sw-register.js
// Registra o Service Worker para suporte offline
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(function () { });
}
