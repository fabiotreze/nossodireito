/**
 * historico-aceite.js — render/export/revoke do aceite local (LGPD Art. 9º + 18).
 * Extraído do <script> inline de historico-aceite.html para conformar com CSP estrita
 * (script-src 'self' sem 'unsafe-inline'). Sem inline, o IIFE nunca rodava e a página
 * ficava eternamente em "Carregando…".
 * Estado 100% local (localStorage). Zero PII, zero rede.
 */
(function () {
  'use strict';
  const KEYS = ['tos_version_accepted', 'tos_accepted_at', 'tos_hash'];
  const statusEl = document.getElementById('statusContent');
  const toastEl = document.getElementById('toast');
  let toastTimer = null;

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function showToast(msg, isError) {
    toastEl.textContent = msg;
    toastEl.classList.toggle('error', !!isError);
    toastEl.classList.add('show');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove('show'), 3000);
  }

  function readState() {
    const state = {};
    let hasAny = false;
    try {
      for (const k of KEYS) {
        const v = localStorage.getItem(k);
        state[k] = v;
        if (v !== null) hasAny = true;
      }
    } catch (e) {
      return { error: 'localStorage indisponível: ' + e.message };
    }
    return { state, hasAny };
  }

  function formatDate(iso) {
    if (!iso) return '—';
    try {
      const d = new Date(iso);
      if (isNaN(d.getTime())) return iso;
      return d.toLocaleString('pt-BR', { dateStyle: 'long', timeStyle: 'short' });
    } catch (e) {
      return iso;
    }
  }

  function render() {
    const result = readState();
    if (result.error) {
      statusEl.innerHTML = '<p class="empty">⚠️ ' + escapeHtml(result.error) + '</p>';
      return;
    }
    if (!result.hasAny) {
      statusEl.innerHTML = '<p class="empty">📭 Nenhum aceite registrado neste navegador. <br><br>Acesse a <a href="/">página inicial</a> e use o banner de aceite que aparecerá no rodapé.</p>';
      return;
    }
    const s = result.state;
    const html = [
      '<dl class="status-line"><dt>Status</dt><dd><span class="status-badge status-ok">✓ Aceito</span></dd></dl>',
      '<dl class="status-line"><dt>Versão aceita</dt><dd><code>' + escapeHtml(s.tos_version_accepted || '—') + '</code></dd></dl>',
      '<dl class="status-line"><dt>Data/hora</dt><dd>' + escapeHtml(formatDate(s.tos_accepted_at)) + '</dd></dl>',
      '<dl class="status-line"><dt>Hash do texto (SHA-256)</dt><dd><code>' + escapeHtml(s.tos_hash || '—') + '</code></dd></dl>'
    ].join('');
    statusEl.innerHTML = html;
  }

  function exportJson() {
    const result = readState();
    if (result.error || !result.hasAny) {
      showToast('Nada para exportar', true);
      return;
    }
    const payload = {
      generated_at: new Date().toISOString(),
      domain: window.location.hostname,
      source: 'NossoDireito — /historico-aceite.html',
      state: result.state
    };
    try {
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'nossodireito-aceite-' + new Date().toISOString().slice(0, 10) + '.json';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast('Arquivo exportado');
    } catch (e) {
      showToast('Erro ao exportar: ' + e.message, true);
    }
  }

  function revoke() {
    const confirmed = window.confirm(
      'Confirma a revogação do aceite?\n\n' +
      '• Os registros locais serão apagados.\n' +
      '• No próximo acesso à página inicial, o banner de aceite reaparecerá.\n' +
      '• Esta ação não envia notificação a servidor (não há servidor — tudo é local).'
    );
    if (!confirmed) return;
    try {
      for (const k of KEYS) localStorage.removeItem(k);
      showToast('Aceite revogado');
      render();
    } catch (e) {
      showToast('Erro ao revogar: ' + e.message, true);
    }
  }

  document.getElementById('btnExport').addEventListener('click', exportJson);
  document.getElementById('btnRevoke').addEventListener('click', revoke);
  document.getElementById('btnReload').addEventListener('click', () => { render(); showToast('Status atualizado'); });

  render();
})();
