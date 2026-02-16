// sw-register.js
// Registra o Service Worker e garante atualização automática após deploy.
if ('serviceWorker' in navigator) {
    // Flag para evitar reload infinito
    var _swReloading = false;

    navigator.serviceWorker.register('/sw.js').then(function (reg) {
        // Verifica atualizações a cada 60 s (além do check automático na navegação)
        setInterval(function () { reg.update(); }, 60000);
    }).catch(function () { });

    // Quando um novo SW assume o controle, recarrega a página para aplicar assets frescos.
    // Isso só dispara quando o controller muda (novo deploy), não no primeiro load.
    navigator.serviceWorker.addEventListener('controllerchange', function () {
        if (!_swReloading) {
            _swReloading = true;
            location.reload();
        }
    });
}
