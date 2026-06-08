/* Status check — feito 100% client-side, sem coleta. */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var t0 = performance.now();
  fetch("/health", { cache: "no-store", credentials: "omit", referrerPolicy: "no-referrer" })
    .then(function (r) {
      var dt = Math.round(performance.now() - t0);
      if (!r.ok) { throw new Error("HTTP " + r.status); }
      return r.json().then(function (j) { return { dt: dt, body: j, code: r.status }; });
    })
    .then(function (res) {
      $("appStatus").textContent = "operacional";
      $("appStatus").className = "badge ok";
      $("appLatency").textContent = "Latência: " + res.dt + " ms · HTTP " + res.code;
      if (res.body) {
        if (res.body.version) { $("appVersion").textContent = "v" + res.body.version; }
        if (res.body.uptime != null) {
          var s = Math.round(res.body.uptime);
          var d = Math.floor(s / 86400), h = Math.floor((s % 86400) / 3600), m = Math.floor((s % 3600) / 60);
          $("appUptime").textContent = "Uptime: " + d + "d " + h + "h " + m + "min";
        }
      }
      $("lastCheck").textContent = new Date().toLocaleString("pt-BR");
    })
    .catch(function (err) {
      $("appStatus").textContent = "indisponível";
      $("appStatus").className = "badge err";
      $("appLatency").textContent = String(err && err.message || err);
      $("lastCheck").textContent = new Date().toLocaleString("pt-BR");
    });
})();
