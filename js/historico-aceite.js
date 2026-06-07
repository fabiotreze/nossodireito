/**
 * historico-aceite.js — render/export/revoke do aceite local (LGPD Art. 9º + 18).
 * Extraído do <script> inline de historico-aceite.html para conformar com CSP estrita
 * (script-src 'self' sem 'unsafe-inline'). Sem inline, o IIFE nunca rodava e a página
 * ficava eternamente em "Carregando…".
 * v1.43.41: botões de revogação movidos para dentro dos cards correspondentes (UX).
 *           Card "Ações gerais" agora só exporta + recarrega (frase de ação clara).
 * Estado 100% local (localStorage). Zero PII, zero rede.
 */
(function () {
  'use strict';
  const KEYS = ['tos_version_accepted', 'tos_accepted_at', 'tos_hash'];
  const AI_KEY = 'nd_ai_consent_v2';
  const statusEl = document.getElementById('statusContent');
  const aiStatusEl = document.getElementById('aiStatusContent');
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

  /**
   * Lê o consentimento de IA (chave nd_ai_consent_v2, schema {granted, sensitive, exp}).
   * exp é timestamp ms (Date.now() + 30 * 24h). Calcula remainingDays para UI.
   * Espelha getStoredAIConsentMeta() em js/app.js, mas standalone (esta página não importa o app).
   */
  function readAIConsent() {
    try {
      const raw = localStorage.getItem(AI_KEY);
      if (!raw) return { present: false };
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== 'object') return { present: false };
      const now = Date.now();
      const exp = typeof parsed.exp === 'number' ? parsed.exp : null;
      const expired = exp !== null && exp < now;
      const remainingDays = exp !== null && !expired
        ? Math.max(0, Math.ceil((exp - now) / (24 * 60 * 60 * 1000)))
        : 0;
      return {
        present: true,
        granted: !!parsed.granted,
        sensitive: !!parsed.sensitive,
        exp: exp,
        expired: expired,
        remainingDays: remainingDays,
        raw: raw
      };
    } catch (e) {
      return { present: false, error: e.message };
    }
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
    } else if (!result.hasAny) {
      statusEl.innerHTML = '<p class="empty">📭 Nenhum aceite registrado neste navegador. <br><br>Acesse a <a href="/">página inicial</a> e use o banner de aceite que aparecerá no rodapé.</p>';
    } else {
      const s = result.state;
      const html = [
        '<dl class="status-line"><dt>Status</dt><dd><span class="status-badge status-ok">✓ Aceito</span></dd></dl>',
        '<dl class="status-line"><dt>Versão aceita</dt><dd><code>' + escapeHtml(s.tos_version_accepted || '—') + '</code></dd></dl>',
        '<dl class="status-line"><dt>Data/hora</dt><dd>' + escapeHtml(formatDate(s.tos_accepted_at)) + '</dd></dl>',
        '<dl class="status-line"><dt>Hash do texto (SHA-256)</dt><dd><code>' + escapeHtml(s.tos_hash || '—') + '</code></dd></dl>'
      ].join('');
      statusEl.innerHTML = html;
    }
    renderAI();
  }

  function renderAI() {
    const ai = readAIConsent();
    if (ai.error) {
      aiStatusEl.innerHTML = '<p class="empty">⚠️ Erro ao ler consentimento IA: ' + escapeHtml(ai.error) + '</p>';
      return;
    }
    if (!ai.present) {
      aiStatusEl.innerHTML = '<p class="empty">📭 Nenhum consentimento de IA registrado. <br><br>O modal aparecerá ao clicar em "Analisar com IA" na <a href="/">página inicial</a>.</p>';
      return;
    }
    const badge = ai.expired
      ? '<span class="status-badge status-revoked">⌛ Expirado</span>'
      : (ai.granted
          ? '<span class="status-badge status-ok">✓ Concedido</span>'
          : '<span class="status-badge status-pending">↻ Recusado</span>');
    const sensitiveBadge = ai.sensitive
      ? '<span class="status-badge status-ok">✓ Sim (Art. 11 II "a")</span>'
      : '<span class="status-badge status-pending">— Não autorizado</span>';
    const expText = ai.exp ? formatDate(new Date(ai.exp).toISOString()) : '—';
    const remainText = ai.expired
      ? 'Expirado'
      : (ai.exp ? ai.remainingDays + ' dia(s) restantes' : 'Sem validade definida');
    const html = [
      '<dl class="status-line"><dt>Status</dt><dd>' + badge + '</dd></dl>',
      '<dl class="status-line"><dt>Dados sensíveis</dt><dd>' + sensitiveBadge + '</dd></dl>',
      '<dl class="status-line"><dt>Expira em</dt><dd>' + escapeHtml(expText) + ' (' + escapeHtml(remainText) + ')</dd></dl>',
      '<dl class="status-line"><dt>Chave</dt><dd><code>' + escapeHtml(AI_KEY) + '</code></dd></dl>'
    ].join('');
    aiStatusEl.innerHTML = html;
  }

  function exportJson() {
    const result = readState();
    const ai = readAIConsent();
    if ((result.error || !result.hasAny) && !ai.present) {
      showToast('Nada para exportar', true);
      return;
    }
    const payload = {
      generated_at: new Date().toISOString(),
      domain: window.location.hostname,
      source: 'NossoDireito — /historico-aceite.html',
      tos_state: result.error ? { error: result.error } : result.state,
      ai_consent: ai.present
        ? { granted: ai.granted, sensitive: ai.sensitive, exp_iso: ai.exp ? new Date(ai.exp).toISOString() : null, expired: ai.expired, remaining_days: ai.remainingDays }
        : null
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
      'Confirma a revogação do aceite dos Termos?\n\n' +
      '• Os registros locais serão apagados (tos_version_accepted, tos_accepted_at, tos_hash).\n' +
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

  function revokeAI() {
    const ai = readAIConsent();
    if (!ai.present) {
      showToast('Nada para revogar (consentimento IA não registrado)', true);
      return;
    }
    const confirmed = window.confirm(
      'Confirma a revogação do consentimento de análise por IA?\n\n' +
      '• A chave ' + AI_KEY + ' será apagada do localStorage.\n' +
      '• No próximo clique em "Analisar com IA", o modal de consentimento reaparecerá.\n' +
      '• LGPD Art. 8º §5 (revogação a qualquer momento, sem ônus).'
    );
    if (!confirmed) return;
    try {
      localStorage.removeItem(AI_KEY);
      showToast('Consentimento IA revogado');
      renderAI();
    } catch (e) {
      showToast('Erro ao revogar IA: ' + e.message, true);
    }
  }

  document.getElementById('btnExport').addEventListener('click', exportJson);
  document.getElementById('btnRevoke').addEventListener('click', revoke);
  document.getElementById('btnRevokeAI').addEventListener('click', revokeAI);
  document.getElementById('btnReload').addEventListener('click', () => { render(); showToast('Status atualizado'); });

  render();
})();
