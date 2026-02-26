// sw-register.js
// Registra o Service Worker APÓS o page load para não competir com recursos
// críticos (elimina ~389 ms de TBT e warnings de preload no Chrome).
if ('serviceWorker' in navigator) {
    var _swReloading = false;

    function _registerSW() {
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

    // Defer registration to after page load so SW install (pre-cache) doesn't
    // compete with the page's own resource fetches.
    if (document.readyState === 'complete') {
        _registerSW();
    } else {
        window.addEventListener('load', _registerSW);
    }
}
