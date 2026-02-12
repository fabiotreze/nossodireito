
(function () {
'use strict';
function safeJsonParse(str) {
return JSON.parse(str, (key, value) => {
if (key === '__proto__' || key === 'constructor' || key === 'prototype') {
return undefined;
}
return value;
});
}
function deepFreeze(obj) {
if (obj === null || typeof obj !== 'object') return obj;
Object.freeze(obj);
Object.getOwnPropertyNames(obj).forEach(prop => {
const val = obj[prop];
if (val !== null && typeof val === 'object' && !Object.isFrozen(val)) {
deepFreeze(val);
}
});
return obj;
}
async function resilientFetch(url, retries = 2, delay = 500) {
for (let attempt = 0; attempt <= retries; attempt++) {
try {
const res = await fetch(url);
if (res.ok) return res;
if (res.status >= 400 && res.status < 500) throw new Error(`HTTP ${res.status}`);
} catch (err) {
if (attempt === retries) throw err;
await new Promise(r => setTimeout(r, delay * Math.pow(2, attempt)));
}
}
}
let direitosData = null;
let fontesData = null;
let docsMestreData = null;
let instituicoesData = null;
let orgaosEstaduaisData = null;
let classificacaoData = null;
let jsonMeta = null;
let UPPERCASE_ONLY_TERMS = new Set();
let CID_RANGE_MAP = {};
let KEYWORD_MAP = {};
const STORAGE_PREFIX = 'nossodireito_';
const DB_NAME = 'NossoDireitoDB';
const DB_VERSION = 2;
const STORE_NAME = 'documentos';
const CRYPTO_STORE = 'crypto_keys';
const CRYPTO_KEY_ID = 'master_aes_key';
const MAX_FILES = 5;
const MAX_FILE_SIZE = 5 * 1024 * 1024;
const FILE_TTL_MINUTES = 15;
const ALLOWED_TYPES = [
'application/pdf',
'image/jpeg',
'image/png',
];
const ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png'];
const CRYPTO_AVAILABLE = typeof crypto !== 'undefined' && typeof crypto.subtle !== 'undefined';
const A11Y_FONT_KEY = STORAGE_PREFIX + 'font_size';
const A11Y_CONTRAST_KEY = STORAGE_PREFIX + 'high_contrast';
const FONT_STEPS = [14, 15, 16, 18, 20, 22];
const FONT_DEFAULT = 16;
function setupAccessibilityToolbar() {
const btnDecrease = document.getElementById('a11yFontDecrease');
const btnReset = document.getElementById('a11yFontReset');
const btnIncrease = document.getElementById('a11yFontIncrease');
const btnContrast = document.getElementById('a11yContrast');
const btnLibras = document.getElementById('a11yLibras');
let currentSize = FONT_DEFAULT;
try {
const saved = localStorage.getItem(A11Y_FONT_KEY);
if (saved && FONT_STEPS.includes(Number(saved))) currentSize = Number(saved);
} catch (_) {  }
applyFontSize(currentSize);
if (btnDecrease) btnDecrease.addEventListener('click', () => {
const idx = FONT_STEPS.indexOf(currentSize);
if (idx > 0) { currentSize = FONT_STEPS[idx - 1]; applyFontSize(currentSize); }
});
if (btnReset) btnReset.addEventListener('click', () => {
currentSize = FONT_DEFAULT; applyFontSize(currentSize);
});
if (btnIncrease) btnIncrease.addEventListener('click', () => {
const idx = FONT_STEPS.indexOf(currentSize);
if (idx < FONT_STEPS.length - 1) { currentSize = FONT_STEPS[idx + 1]; applyFontSize(currentSize); }
});
function applyFontSize(size) {
document.documentElement.style.fontSize = size + 'px';
try { localStorage.setItem(A11Y_FONT_KEY, String(size)); } catch (_) { }
}
let contrastOn = false;
try {
contrastOn = localStorage.getItem(A11Y_CONTRAST_KEY) === 'true';
} catch (_) { }
if (contrastOn) toggleContrast(true);
if (btnContrast) btnContrast.addEventListener('click', () => {
contrastOn = !contrastOn;
toggleContrast(contrastOn);
});
function toggleContrast(on) {
document.documentElement.classList.toggle('high-contrast', on);
if (btnContrast) btnContrast.setAttribute('aria-pressed', String(on));
try { localStorage.setItem(A11Y_CONTRAST_KEY, String(on)); } catch (_) { }
}
let vlOK = false, vlP = null;
function initVL() { try { new window.VLibras.Widget('https://vlibras.gov.br/app'); vlOK = true; } catch (_) { } }
function ldVL(u) { return new Promise((y, n) => { const s = document.createElement('script'); s.src = u; s.onload = () => window.VLibras ? (initVL(), y()) : n(); s.onerror = n; document.head.appendChild(s); }); }
const VLC = 'https://cdn.jsdelivr.net/gh/spbgovbr-vlibras/vlibras-portal@dev/app/vlibras-plugin.js';
function ensureVL() { if (vlOK) return Promise.resolve(!0); if (window.VLibras) { initVL(); return Promise.resolve(!0); } if (!vlP) vlP = ldVL('https://vlibras.gov.br/app/vlibras-plugin.js').catch(() => ldVL(VLC)).then(() => !0, () => { vlP = null; return !1; }); return vlP; }
if (window.VLibras) initVL(); else ensureVL();
if (btnLibras) btnLibras.addEventListener('click', async () => {
btnLibras.disabled = true; btnLibras.textContent = '⏳ Carregando...';
try {
if (!await ensureVL()) { showToast('VLibras indisponível. Tente novamente mais tarde.', 'error'); return; }
await new Promise(r => { let c = 0; const iv = setInterval(() => { const b = document.querySelector('[vw-access-button] img[src]'); if (b) { clearInterval(iv); b.closest('[vw-access-button]').click(); r(); } else if (++c > 25) { clearInterval(iv); showToast('VLibras carregou mas o painel não apareceu. Recarregue a página.', 'warning'); r(); } }, 200); });
} finally { btnLibras.disabled = false; btnLibras.textContent = '🤟 Libras'; }
});
const btnReadAloud = document.getElementById('a11yReadAloud');
const TTS_AVAILABLE = typeof speechSynthesis !== 'undefined';
let ttsActive = false;
let currentUtterance = null;
let keepAliveInterval = null;
let currentChunks = [];
let currentChunkIndex = 0;
function preprocessTextForTTS(text) {
return text
.replace(/\s+/g, ' ')
.replace(/\n{3,}/g, '\n\n')
.replace(/\bArt\.?\s*(\d+)/gi, 'Artigo $1')
.replace(/§\s*(\d+)/g, 'parágrafo $1')
.replace(/Inc\.?\s*/gi, 'inciso ')
.replace(/cf\.?\s+/gi, 'conforme ')
.replace(/\bvs\.?\s+/gi, 'versus ')
.replace(/\bDr\.\s+/g, 'Doutor ')
.replace(/\bDra\.\s+/g, 'Doutora ')
.replace(/\bProf\.\s+/g, 'Professor ')
.replace(/\bSr\.\s+/g, 'Senhor ')
.replace(/\bSra\.\s+/g, 'Senhora ')
.replace(/\bINSS\b/g, 'I-N-S-S')
.replace(/\bBPC\b/g, 'B-P-C')
.replace(/\bCID\b/g, 'C-I-D')
.replace(/\bCPF\b/g, 'C-P-F')
.replace(/\bRG\b/g, 'R-G')
.trim();
}
function splitIntoChunks(text) {
const MIN_CHUNK = 1200;
const MAX_CHUNK = 1600;
const paragraphs = text.split(/\n\n+/);
const hasManyParagraphs = paragraphs.length > 3;
if (text.length <= 1800 && !hasManyParagraphs) {
return [text];
}
console.log('[TTS] Texto longo detectado - usando chunking inteligente por frases');
const sentences = text.match(/[^.!?\n]+[.!?\n]+/g) || [text];
const chunks = [];
let currentChunk = '';
for (const sentence of sentences) {
const potentialLength = currentChunk.length + sentence.length;
if (potentialLength > MAX_CHUNK && currentChunk.length >= MIN_CHUNK) {
chunks.push(currentChunk.trim());
currentChunk = sentence;
} else {
currentChunk += sentence;
}
}
if (currentChunk.trim().length > 0) {
chunks.push(currentChunk.trim());
}
return chunks.length > 0 ? chunks : [text];
}
function waitForVoices() {
return new Promise((resolve) => {
const voices = speechSynthesis.getVoices();
if (voices.length) return resolve(voices);
speechSynthesis.onvoiceschanged = () => {
const loadedVoices = speechSynthesis.getVoices();
speechSynthesis.onvoiceschanged = null;
resolve(loadedVoices);
};
});
}
function getTextToRead() {
const selection = window.getSelection();
if (selection && selection.toString().trim().length > 0) {
const selectedText = selection.toString().trim();
const wordCount = selectedText.split(/\s+/).length;
if (wordCount < 3) {
console.log('[TTS] Seleção muito curta (< 3 palavras) - usando seção visível');
} else {
console.log('[TTS] Lendo texto selecionado pelo usuário');
return selectedText;
}
}
const sections = document.querySelectorAll('main section:not([style*="display:none"])');
let bestSection = null;
let bestDistance = Infinity;
for (const section of sections) {
if (section.hidden) continue;
const rect = section.getBoundingClientRect();
const distance = Math.abs(rect.top - 80);
if (distance < bestDistance) {
bestDistance = distance;
bestSection = section;
}
}
if (!bestSection) return '';
const clone = bestSection.cloneNode(true);
clone.querySelectorAll('script, style, input, button, [aria-hidden="true"]').forEach(el => el.remove());
const text = clone.textContent
.replace(/\s+/g, ' ')
.replace(/[📋🔍✅📎📄🔗🏥🏢🤝📜🏛️⚖️💚♿💡⚠️📲📥🗑️🔲🤟🔊⏳]/g, '')
.trim();
return text;
}
function getBestPtBrVoice(voices) {
const savedVoiceName = localStorage.getItem(STORAGE_PREFIX + 'tts_voice');
if (savedVoiceName) {
const savedVoice = voices.find(v => v.name === savedVoiceName);
if (savedVoice) {
currentChunks = [];
currentChunkIndex = 0;
console.log('[TTS] Usando voz salva:', savedVoice.name, savedVoice.lang);
return savedVoice;
}
}
let voice = voices.find(v => v.lang === 'pt-BR');
if (voice) return voice;
voice = voices.find(v => v.lang === 'pt-PT');
if (voice) return voice;
voice = voices.find(v => v.lang.startsWith('pt'));
if (voice) return voice;
if (voices.length === 0) {
console.warn('[TTS] Nenhuma voz disponível no sistema.');
return null;
}
console.warn('[TTS] Nenhuma voz pt encontrada. Usando:', voices[0].name, voices[0].lang);
showToast('\u26a0\ufe0f Seu navegador pode n\u00e3o suportar portugu\u00eas. A leitura pode estar em outro idioma. Instale vozes pt-BR nas configura\u00e7\u00f5es do sistema.', 'warning');
return voices[0];
}
function stopReading() {
ttsActive = false;
if (keepAliveInterval) {
clearInterval(keepAliveInterval);
keepAliveInterval = null;
}
if (speechSynthesis.speaking || speechSynthesis.pending) {
speechSynthesis.cancel();
}
currentUtterance = null;
if (btnReadAloud) {
btnReadAloud.textContent = '🔊 Ouvir';
btnReadAloud.setAttribute('aria-pressed', 'false');
}
}
async function startReading() {
if (!('speechSynthesis' in window)) {
showToast('Seu navegador não suporta leitura em voz.', 'warning');
return;
}
const text = getTextToRead();
if (!text || text.trim().length < 5) {
showToast('Não há conteúdo para ler. Selecione um texto ou navegue até uma seção.', 'info');
return;
}
stopReading();
const voices = await waitForVoices();
if (!voices.length) {
showToast('Nenhuma voz disponível no sistema.', 'warning');
return;
}
const voice = getBestPtBrVoice(voices);
if (voice) {
console.log('[TTS] Usando voz:', voice.name, '|', voice.lang);
try {
localStorage.setItem(STORAGE_PREFIX + 'tts_voice', voice.name);
} catch (_) {  }
} else {
console.warn('[TTS] Nenhuma voz disponível! Tentando voz padrão do sistema.');
}
const processedText = preprocessTextForTTS(text);
currentChunks = splitIntoChunks(processedText);
currentChunkIndex = 0;
console.info('[TTS] Iniciando leitura | voz:', voice ? voice.name : 'padrão', '| chars:', text.length, '| processado:', processedText.length, '| chunks:', currentChunks.length);
ttsActive = true;
speakChunk(voice, processedText.length);
}
function speakChunk(voice, originalTextLength) {
if (!ttsActive || currentChunkIndex >= currentChunks.length) {
stopReading();
return;
}
const chunk = currentChunks[currentChunkIndex];
const utterance = new SpeechSynthesisUtterance(chunk);
utterance.voice = voice;
utterance.lang = voice ? voice.lang : 'pt-BR';
if (originalTextLength < 300) {
utterance.rate = 1.05;
} else if (originalTextLength > 1500 || chunk.includes('Artigo') || chunk.includes('parágrafo')) {
utterance.rate = 0.9;
} else {
utterance.rate = 1.0;
}
utterance.pitch = 1.0;
currentUtterance = utterance;
if (chunk.length > 200 && currentChunks.length === 1) {
keepAliveInterval = setInterval(() => {
if (!ttsActive) return;
if (speechSynthesis.speaking && !speechSynthesis.paused) {
speechSynthesis.pause();
setTimeout(() => speechSynthesis.resume(), 50);
}
}, 12000);
}
const handleEnd = () => {
if (keepAliveInterval) {
clearInterval(keepAliveInterval);
keepAliveInterval = null;
}
currentChunkIndex++;
if (currentChunkIndex < currentChunks.length && ttsActive) {
speakChunk(voice, originalTextLength);
} else {
stopReading();
}
};
const handleError = (e) => {
if (keepAliveInterval) {
clearInterval(keepAliveInterval);
keepAliveInterval = null;
}
stopReading();
if (e.error === 'canceled' || e.error === 'interrupted') {
console.log('[TTS] Leitura interrompida pelo usuário');
return;
}
if (e.error === 'not-allowed') {
showToast('O navegador bloqueou o áudio. Clique novamente para ouvir.', 'warning');
return;
}
if (e.error === 'audio-busy') {
showToast('Outro áudio está em uso no dispositivo.', 'warning');
return;
}
console.error('[TTS] Erro na síntese de voz:', e.error, e);
const errorMsg = voice
? `Erro ao reproduzir voz "${voice.name}": ${e.error}. Tente novamente ou use outro navegador.`
: 'Nenhuma voz instalada no sistema. Instale vozes pt-BR nas configurações do navegador.';
showToast(errorMsg, 'warning');
};
utterance.onend = handleEnd;
utterance.onerror = handleError;
if (speechSynthesis.speaking || speechSynthesis.pending) {
speechSynthesis.cancel();
}
speechSynthesis.speak(utterance);
if (btnReadAloud && currentChunkIndex === 0) {
btnReadAloud.textContent = '⏹️ Parar';
btnReadAloud.setAttribute('aria-pressed', 'true');
}
}
if (btnReadAloud && TTS_AVAILABLE) {
btnReadAloud.addEventListener('click', async () => {
if (ttsActive) {
stopReading();
await new Promise(r => setTimeout(r, 150));
} else {
await startReading();
}
});
waitForVoices().then(voices => {
console.log(`[TTS] ${voices.length} vozes disponíveis:`, voices.map(v => `${v.name} (${v.lang})`).join(', '));
});
} else if (btnReadAloud && !TTS_AVAILABLE) {
btnReadAloud.style.display = 'none';
}
document.addEventListener('visibilitychange', () => {
if (document.hidden && ttsActive) {
console.log('[TTS] Aba oculta - parando leitura automaticamente');
stopReading();
}
});
window.addEventListener('hashchange', () => {
if (ttsActive) stopReading();
});
}
if (document.readyState === 'loading') {
document.addEventListener('DOMContentLoaded', setupAccessibilityToolbar);
} else {
setupAccessibilityToolbar();
}
let _pdfJsReady = typeof pdfjsLib !== 'undefined';
function ensurePdfJs() {
if (_pdfJsReady) return Promise.resolve();
return new Promise((resolve, reject) => {
const s = document.createElement('script');
s.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
s.integrity = 'sha384-/1qUCSGwTur9vjf/z9lmu/eCUYbpOTgSjmpbMQZ1/CtX2v/WcAIKqRv+U1DUCG6e';
s.crossOrigin = 'anonymous';
s.onload = () => {
pdfjsLib.GlobalWorkerOptions.workerSrc =
'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
_pdfJsReady = true;
resolve();
};
s.onerror = () => reject(new Error('Não foi possível carregar o leitor de PDF.'));
document.head.appendChild(s);
});
}
if (_pdfJsReady) {
pdfjsLib.GlobalWorkerOptions.workerSrc =
'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
}
function showToast(message, type = 'info') {
const toast = document.createElement('div');
toast.className = `toast toast-${type}`;
toast.textContent = message;
toast.setAttribute('role', 'alert');
document.body.appendChild(toast);
setTimeout(() => { if (toast.parentNode) toast.remove(); }, 5000);
}
function confirmAction(msg, cb) {
const d = document.createElement('dialog');
d.className = 'confirm-dialog';
d.setAttribute('role', 'alertdialog');
d.setAttribute('aria-label', msg);
d.innerHTML = '<p>' + msg + '</p><div class="confirm-actions"><button>Cancelar</button><button class="btn-confirm">Confirmar</button></div>';
document.body.appendChild(d);
d.showModal();
d.onclick = e => { if (e.target.tagName === 'BUTTON') { const ok = e.target.classList.contains('btn-confirm'); d.close(); d.remove(); if (ok) cb(); } };
}
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);
const dom = {
disclaimerModal: $('#disclaimerModal'),
acceptBtn: $('#acceptDisclaimer'),
menuToggle: $('#menuToggle'),
navLinks: $('#navLinks'),
searchInput: $('#searchInput'),
searchBtn: $('#searchBtn'),
searchResults: $('#searchResults'),
categoryGrid: $('#categoryGrid'),
detalheSection: $('#detalhe'),
detalheContent: $('#detalheContent'),
voltarBtn: $('#voltarBtn'),
categoriasSection: $('#categorias'),
lastUpdate: $('#lastUpdate'),
showDisclaimer: $('#showDisclaimer'),
uploadZone: $('#uploadZone'),
fileInput: $('#fileInput'),
fileList: $('#fileList'),
deleteAllFiles: $('#deleteAllFiles'),
docsChecklist: $('#docsChecklist'),
analysisResults: $('#analysisResults'),
analysisLoading: $('#analysisLoading'),
analysisContent: $('#analysisContent'),
closeAnalysis: $('#closeAnalysis'),
exportPdf: $('#exportPdf'),
fontesLegislacao: $('#fontesLegislacao'),
fontesServicos: $('#fontesServicos'),
fontesNormativas: $('#fontesNormativas'),
instituicoesGrid: $('#instituicoesGrid'),
orgaosEstaduaisGrid: $('#orgaosEstaduaisGrid'),
classificacaoGrid: $('#classificacaoGrid'),
transLastUpdate: $('#transLastUpdate'),
transNextReview: $('#transNextReview'),
transVersion: $('#transVersion'),
footerVersion: $('#footerVersion'),
linksGrid: $('#linksGrid'),
stalenessBanner: $('#stalenessBanner'),
staleDays: $('#staleDays'),
heroCatCount: $('#heroCatCount'),
heroFontesCount: $('#heroFontesCount'),
};
async function init() {
setupDisclaimer();
setupNavigation();
setupSearch();
setupChecklist();
setupFooter();
setupBackToTop();
await loadData();
enrichGovBr();
setupFooterVersion();
renderCategories();
renderTransparency();
renderInstituicoes();
renderOrgaosEstaduais();
renderClassificacao();
renderDocsChecklist();
renderLinksUteis();
renderHeroStats();
checkStaleness();
setupUpload();
setupAnalysis();
await cleanupExpiredFiles();
await renderFileList();
setInterval(async () => {
const removed = await cleanupExpiredFiles();
if (removed > 0) await renderFileList();
}, 60000);
}
function setupDisclaimer() {
function closeModal() {
dom.disclaimerModal.classList.add('hidden');
dom.disclaimerModal.setAttribute('aria-hidden', 'true');
if (dom.showDisclaimer) dom.showDisclaimer.focus();
}
function openModal() {
dom.disclaimerModal.classList.remove('hidden');
dom.disclaimerModal.setAttribute('aria-hidden', 'false');
const firstFocusable = dom.disclaimerModal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
if (firstFocusable) firstFocusable.focus();
}
dom.disclaimerModal.addEventListener('keydown', (e) => {
if (e.key === 'Tab') {
const focusable = dom.disclaimerModal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
if (focusable.length === 0) return;
const first = focusable[0];
const last = focusable[focusable.length - 1];
if (e.shiftKey) {
if (document.activeElement === first) { e.preventDefault(); last.focus(); }
} else {
if (document.activeElement === last) { e.preventDefault(); first.focus(); }
}
}
if (e.key === 'Escape') closeModal();
});
dom.disclaimerModal.addEventListener('click', (e) => {
if (e.target === dom.disclaimerModal) closeModal();
});
dom.acceptBtn.addEventListener('click', closeModal);
dom.showDisclaimer.addEventListener('click', (e) => {
e.preventDefault();
openModal();
});
}
function setupNavigation() {
dom.menuToggle.addEventListener('click', () => {
const open = dom.navLinks.classList.toggle('open');
dom.menuToggle.classList.toggle('open', open);
dom.menuToggle.setAttribute('aria-expanded', String(open));
dom.menuToggle.setAttribute('aria-label', open ? 'Fechar menu' : 'Abrir menu');
});
document.addEventListener('keydown', (e) => {
if (e.key === 'Escape' && dom.navLinks.classList.contains('open')) {
dom.navLinks.classList.remove('open');
dom.menuToggle.classList.remove('open');
dom.menuToggle.setAttribute('aria-expanded', 'false');
dom.menuToggle.setAttribute('aria-label', 'Abrir menu');
dom.menuToggle.focus();
}
});
dom.navLinks.querySelectorAll('a').forEach((link) => {
link.addEventListener('click', () => {
dom.navLinks.classList.remove('open');
dom.menuToggle.classList.remove('open');
dom.menuToggle.setAttribute('aria-expanded', 'false');
dom.menuToggle.setAttribute('aria-label', 'Abrir menu');
});
});
const sections = $$('section[id]');
const navAnchors = dom.navLinks.querySelectorAll('a');
if (!('IntersectionObserver' in window)) return;
const observer = new IntersectionObserver(
(entries) => {
entries.forEach((entry) => {
if (entry.isIntersecting) {
const id = entry.target.id;
navAnchors.forEach((a) => {
a.classList.toggle(
'active',
a.getAttribute('href') === `#${id}`
);
});
}
});
},
{ rootMargin: '-100px 0px -60% 0px' }
);
sections.forEach((s) => observer.observe(s));
dom.voltarBtn.addEventListener('click', () => {
dom.detalheSection.style.display = 'none';
dom.categoriasSection.style.display = '';
history.pushState({ view: 'categorias' }, '', '#categorias');
dom.categoriasSection.scrollIntoView({ behavior: 'smooth' });
const h2 = dom.categoriasSection.querySelector('h2');
if (h2) { h2.setAttribute('tabindex', '-1'); h2.focus({ preventScroll: true }); }
});
window.addEventListener('popstate', (e) => {
if (e.state && e.state.view === 'detalhe' && e.state.id) {
showDetalhe(e.state.id, true);
} else {
dom.detalheSection.style.display = 'none';
dom.categoriasSection.style.display = '';
}
});
}
async function loadData() {
try {
const res = await resilientFetch('data/direitos.json');
const json = await res.json();
direitosData = deepFreeze(json.categorias);
fontesData = deepFreeze(json.fontes || []);
docsMestreData = deepFreeze(json.documentos_mestre || []);
instituicoesData = deepFreeze(json.instituicoes_apoio || []);
orgaosEstaduaisData = deepFreeze(json.orgaos_estaduais || []);
classificacaoData = deepFreeze(json.classificacao_deficiencia || []);
jsonMeta = Object.freeze({
versao: json.versao,
ultima_atualizacao: json.ultima_atualizacao,
proxima_revisao: json.proxima_revisao,
});
if (json.ultima_atualizacao && dom.lastUpdate) {
dom.lastUpdate.textContent = formatDate(json.ultima_atualizacao);
}
} catch (err) {
console.error('Erro ao carregar dados:', err);
dom.categoryGrid.innerHTML = `
<div style="grid-column: 1/-1; text-align:center; padding:32px; color:var(--text-muted);">
<p>⚠️ Não foi possível carregar os dados.</p>
<p style="font-size:0.9rem;">Verifique se o arquivo <code>data/direitos.json</code> está acessível.</p>
</div>`;
}
try {
const meRes = await resilientFetch('data/matching_engine.json');
const me = await meRes.json();
UPPERCASE_ONLY_TERMS = Object.freeze(new Set(me.uppercase_only_terms));
CID_RANGE_MAP = deepFreeze(me.cid_range_map);
KEYWORD_MAP = deepFreeze(me.keyword_map);
} catch (err) {
console.warn('Motor de correspondência não carregou — análise de documentos pode ser limitada:', err.message);
}
}
async function enrichGovBr() {
try {
const r = await fetch('/api/govbr-servico/10783',
{ signal: AbortSignal.timeout(4000) });
if (r.ok) sessionStorage.setItem('govbr_10783', '1');
} catch {  }
}
function renderCategories() {
if (!direitosData) return;
dom.categoryGrid.innerHTML = direitosData
.map(
(cat) => `
<div class="category-card" tabindex="0" role="button"
aria-label="Ver detalhes sobre ${escapeHtml(cat.titulo)}"
data-id="${cat.id}">
<span class="category-icon">${cat.icone}</span>
<h3>${escapeHtml(cat.titulo)}</h3>
<p>${escapeHtml(cat.resumo)}</p>
</div>`
)
.join('');
dom.categoryGrid.querySelectorAll('.category-card').forEach((card) => {
card.addEventListener('click', () => showDetalhe(card.dataset.id));
card.addEventListener('keydown', (e) => {
if (e.key === 'Enter' || e.key === ' ') {
e.preventDefault();
showDetalhe(card.dataset.id);
}
});
});
}
function showDetalhe(id, skipHistory) {
const cat = direitosData.find((c) => c.id === id);
if (!cat) return;
dom.categoriasSection.style.display = 'none';
dom.detalheSection.style.display = '';
if (!skipHistory) {
history.pushState({ view: 'detalhe', id }, '', `#direito/${id}`);
}
let html = `
<h2>${cat.icone} ${escapeHtml(cat.titulo)}</h2>
<p class="detalhe-resumo">${escapeHtml(cat.resumo)}</p>`;
if (cat.valor) {
html += `<div class="detalhe-section">
<h3>💰 Valor</h3>
<span class="valor-destaque">${escapeHtml(cat.valor)}</span>
</div>`;
}
if (cat.base_legal && cat.base_legal.length) {
html += `<div class="detalhe-section">
<h3>📜 Base Legal</h3>
<div>${cat.base_legal
.map(
(l) =>
`<a class="legal-link" href="${escapeHtml(l.link)}" target="_blank" rel="noopener noreferrer">
📄 ${escapeHtml(l.lei)}${l.artigo ? ' — ' + escapeHtml(l.artigo) : ''}
</a>`
)
.join('')}</div>
</div>`;
}
if (cat.requisitos && cat.requisitos.length) {
html += `<div class="detalhe-section">
<h3>📋 Requisitos</h3>
<ul>${cat.requisitos.map((r) => `<li>${escapeHtml(r)}</li>`).join('')}</ul>
</div>`;
}
if (cat.documentos && cat.documentos.length) {
html += `<div class="detalhe-section">
<h3>📄 Documentos Necessários</h3>
<ul>${cat.documentos.map((d) => `<li>${escapeHtml(d)}</li>`).join('')}</ul>
</div>`;
}
if (cat.passo_a_passo && cat.passo_a_passo.length) {
html += `<div class="detalhe-section">
<h3>👣 Passo a Passo</h3>
<ol>${cat.passo_a_passo.map((p) => `<li>${escapeHtml(p)}</li>`).join('')}</ol>
</div>`;
}
if (cat.onde) {
html += `<div class="detalhe-section">
<h3>📍 Onde Solicitar</h3>
<p>${escapeHtml(cat.onde)}</p>
</div>`;
}
if (cat.dicas && cat.dicas.length) {
html += `<div class="detalhe-section">
<h3>💡 Dicas Importantes</h3>
${cat.dicas.map((d) => `<div class="dica-item">${escapeHtml(d)}</div>`).join('')}
</div>`;
}
if (cat.ipva_estados && cat.ipva_estados.length) {
html += `<div class="detalhe-section"><h3>🚗 Isenção de IPVA por Estado</h3>
<details><summary>Ver legislação dos ${cat.ipva_estados.length} estados</summary>
<div class="table-wrapper"><table class="ipva-table">
<thead><tr><th>UF</th><th>Lei</th><th>Art.</th><th>SEFAZ</th></tr></thead>
<tbody>${cat.ipva_estados.map(e => `<tr><td>${escapeHtml(e.uf)}</td><td>${escapeHtml(e.lei)}</td><td>${escapeHtml(e.art)}</td><td><a href="${escapeHtml(e.sefaz)}" target="_blank" rel="noopener noreferrer">Consultar</a></td></tr>`).join('')}</tbody>
</table></div></details></div>`;
}
if (cat.ipva_estados_detalhado && cat.ipva_estados_detalhado.length) {
html += `<div class="detalhe-section">
<h3>🚗 Consulta Detalhada - IPVA por Estado</h3>
<p style="margin-bottom:12px;color:var(--text-muted)">
Selecione seu estado para ver as condições específicas, limites de valor e legislação completa:
</p>
<label for="ipvaEstadoSelect" class="sr-only">Selecione seu estado</label>
<select id="ipvaEstadoSelect" class="ipva-dropdown">
<option value="">Selecione seu estado...</option>
${cat.ipva_estados_detalhado.map(e =>
`<option value="${escapeHtml(e.uf)}">${escapeHtml(e.uf)} - ${escapeHtml(e.nome)}</option>`
).join('')}
</select>
<div id="ipvaEstadoInfo" class="ipva-info-box" role="region" aria-live="polite"></div>
</div>`;
}
if (cat.links && cat.links.length) {
html += `<div class="detalhe-section">
<h3>🔗 Links Úteis</h3>
<div>${cat.links
.filter((l) => isSafeUrl(l.url))
.map(
(l) =>
`<a class="legal-link" href="${escapeHtml(l.url)}" target="_blank" rel="noopener noreferrer">
🌐 ${escapeHtml(l.titulo)}
</a>`
)
.join('')}</div>
</div>`;
}
if (cat.govbr_servico_id) {
const live = sessionStorage.getItem('govbr_' + cat.govbr_servico_id);
html += `<div class="detalhe-section" style="text-align:center">
<a href="https://www.gov.br/pt-br/servicos/obter-isencao-de-impostos-para-comprar-carro" target="_blank" rel="noopener noreferrer" class="tag" style="display:inline-block;background:${live ? '#168821' : '#1351b4'};color:#fff;text-decoration:none;padding:6px 16px;border-radius:20px;font-size:0.95rem">
🇧🇷 ${live ? 'Serviço digital confirmado no gov.br' : 'Acessar serviço no gov.br'}
</a></div>`;
}
if (cat.tags && cat.tags.length) {
html += `<div class="detalhe-tags">
${cat.tags.map((t) => `<span class="tag">${escapeHtml(t)}</span>`).join('')}
</div>`;
}
const shareText = encodeURIComponent(
`${cat.icone} ${cat.titulo}\n${cat.resumo}\n\nVeja mais em: https://nossodireito.fabiotreze.com`
);
html += `<div class="detalhe-section" style="text-align:center;padding-top:8px;">
<a href="https://wa.me/?text=${shareText}" target="_blank" rel="noopener noreferrer"
class="btn btn-whatsapp" aria-label="Compartilhar no WhatsApp">
📲 Compartilhar no WhatsApp
</a>
</div>`;
dom.detalheContent.innerHTML = html;
if (cat.ipva_estados_detalhado && cat.ipva_estados_detalhado.length) {
const ipvaSelect = $('#ipvaEstadoSelect');
const ipvaInfo = $('#ipvaEstadoInfo');
if (ipvaSelect && ipvaInfo) {
ipvaSelect.addEventListener('change', function(e) {
const uf = e.target.value;
if (!uf) {
ipvaInfo.innerHTML = '';
return;
}
const estado = cat.ipva_estados_detalhado.find(e => e.uf === uf);
if (estado) {
ipvaInfo.innerHTML = `
<div class="ipva-detail-card">
<h4>${escapeHtml(estado.nome)} (${escapeHtml(estado.uf)})</h4>
<div class="ipva-detail-row">
<strong>📜 Legislação:</strong>
<span>${escapeHtml(estado.lei)}</span>
</div>
<div class="ipva-detail-row">
<strong>📋 Artigo:</strong>
<span>${escapeHtml(estado.artigo)}</span>
</div>
<div class="ipva-detail-row">
<strong>✅ Condições para Isenção:</strong>
<span>${escapeHtml(estado.condicoes)}</span>
</div>
<div class="ipva-detail-row">
<strong>💰 Limite de Valor:</strong>
<span>${escapeHtml(estado.limite_valor)}</span>
</div>
<a href="${escapeHtml(estado.sefaz)}"
target="_blank"
rel="noopener noreferrer"
class="btn btn-primary"
style="margin-top:16px;display:inline-block">
🔗 Consultar na SEFAZ/${escapeHtml(estado.uf)}
</a>
</div>
`;
}
});
}
}
dom.detalheSection.scrollIntoView({ behavior: 'smooth' });
const h2 = dom.detalheSection.querySelector('h2');
if (h2) { h2.setAttribute('tabindex', '-1'); h2.focus({ preventScroll: true }); }
}
function setupSearch() {
const doSearch = () => {
const query = dom.searchInput.value.trim().toLowerCase();
if (!query || !direitosData) {
dom.searchResults.innerHTML = '';
return;
}
performSearch(query);
};
dom.searchBtn.addEventListener('click', doSearch);
dom.searchInput.addEventListener('keydown', (e) => {
if (e.key === 'Enter') doSearch();
});
let timer;
dom.searchInput.addEventListener('input', () => {
clearTimeout(timer);
timer = setTimeout(doSearch, 300);
});
}
function performSearch(query) {
const terms = query
.normalize('NFD')
.replace(/[\u0300-\u036f]/g, '')
.split(/\s+/)
.filter(Boolean);
const scored = direitosData
.map((cat) => {
const searchable = normalizeText(
[
cat.titulo,
cat.resumo,
...(cat.tags || []),
...(cat.requisitos || []),
...(cat.passo_a_passo || []),
...(cat.dicas || []),
].join(' ')
);
const score = terms.reduce((acc, term) => {
const count = (searchable.match(new RegExp(escapeRegex(term), 'g')) || []).length;
return acc + count;
}, 0);
return { cat, score };
})
.filter((r) => r.score > 0)
.sort((a, b) => b.score - a.score);
if (scored.length === 0) {
dom.searchResults.innerHTML = `
<div class="search-no-results">
<p>Nenhum resultado para "<strong>${escapeHtml(query)}</strong>".</p>
<p>Tente palavras como: BPC, escola, plano de saúde, transporte, TEA...</p>
</div>`;
return;
}
dom.searchResults.innerHTML = scored
.map(
({ cat }) => `
<div class="search-result-item" data-id="${cat.id}" tabindex="0" role="button">
<span class="search-result-icon">${cat.icone}</span>
<div class="search-result-info">
<h4>${escapeHtml(cat.titulo)}</h4>
<p>${escapeHtml(cat.resumo)}</p>
</div>
</div>`
)
.join('');
dom.searchResults.querySelectorAll('.search-result-item').forEach((item) => {
item.addEventListener('click', () => showDetalhe(item.dataset.id));
item.addEventListener('keydown', (e) => {
if (e.key === 'Enter' || e.key === ' ') {
e.preventDefault();
showDetalhe(item.dataset.id);
}
});
});
}
function setupChecklist() {
const checkboxes = $$('.checklist-item input[type="checkbox"]');
const saved = localGet('checklist') || {};
const total = checkboxes.length;
const progressText = $('#checklistProgress');
const progressBar = $('#checklistProgressBar');
function updateProgress() {
const done = $$('.checklist-item input[type="checkbox"]:checked').length;
if (progressText) progressText.textContent = `${done} de ${total} concluídos`;
if (progressBar) {
progressBar.style.width = `${Math.round(done / total * 100)}%`;
progressBar.closest('.progress-bar')?.setAttribute('aria-valuenow', done);
}
}
function checkDependencies(checkbox) {
const step = parseInt(checkbox.dataset.step);
if (step === 7 && checkbox.checked) {
const step4 = document.querySelector('[data-step="4"]');
if (step4 && !step4.checked) {
showToast('⚠️ Atenção: O BPC/LOAS (passo 7) exige inscrição no CadÚnico (passo 4). O INSS não agenda sem o NIS. Complete o passo 4 primeiro.', 'warning');
checkbox.checked = false;
return false;
}
}
if ([4,6,7,8].includes(step) && checkbox.checked) {
const step3 = document.querySelector('[data-step="3"]');
if (step3 && !step3.checked) {
const names = {4: 'CadÚnico', 6: 'CIPTEA', 7: 'BPC', 8: 'UBS/CER/CAPS'};
showToast(`⚠️ Atenção: ${names[step]} precisa de laudo médico válido (passo 3). Valide seu laudo primeiro: CID, data, assinatura, CRM.`, 'warning');
checkbox.checked = false;
return false;
}
}
return true;
}
checkboxes.forEach((cb) => {
const step = cb.dataset.step;
if (saved[step]) cb.checked = true;
cb.addEventListener('change', () => {
if (!checkDependencies(cb)) {
updateProgress();
return;
}
const state = localGet('checklist') || {};
if (cb.checked) {
state[step] = true;
} else {
delete state[step];
}
localSet('checklist', state);
updateProgress();
});
});
updateProgress();
}
function renderTransparency() {
if (!fontesData || !jsonMeta) return;
if (dom.transLastUpdate) {
dom.transLastUpdate.textContent = formatDate(jsonMeta.ultima_atualizacao);
}
if (dom.transNextReview) {
dom.transNextReview.textContent = formatDate(jsonMeta.proxima_revisao);
}
if (dom.transVersion) {
dom.transVersion.textContent = `v${jsonMeta.versao}`;
}
const transLastUpdateInline = document.getElementById('transLastUpdateInline');
if (transLastUpdateInline) {
transLastUpdateInline.textContent = formatDate(jsonMeta.ultima_atualizacao);
}
const transLastUpdateText = document.getElementById('transLastUpdateText');
if (transLastUpdateText) {
transLastUpdateText.textContent = formatDate(jsonMeta.ultima_atualizacao);
}
const transNextReviewText = document.getElementById('transNextReviewText');
if (transNextReviewText) {
transNextReviewText.textContent = formatDate(jsonMeta.proxima_revisao);
}
const legislacao = fontesData.filter((f) => f.tipo === 'legislacao');
const servicos = fontesData.filter((f) => f.tipo === 'servico');
const normativas = fontesData.filter((f) => f.tipo === 'normativa');
const renderFonte = (f) => {
const tipoIcon = f.tipo === 'legislacao' ? '📜' : f.tipo === 'servico' ? '🌐' : '📋';
const artigos = f.artigos_referenciados
? `<div class="fonte-artigos">Artigos: ${f.artigos_referenciados.join(', ')}</div>`
: '';
return `
<div class="fonte-item">
<span class="fonte-icon">${tipoIcon}</span>
<div class="fonte-info">
<div class="fonte-nome">${escapeHtml(f.nome)}</div>
<div class="fonte-orgao">${escapeHtml(f.orgao)}</div>
${artigos}
</div>
<div class="fonte-data">Consultado<br>${formatDate(f.consultado_em)}</div>
<div class="fonte-link">
${isSafeUrl(f.url) ? `<a href="${escapeHtml(f.url)}" target="_blank" rel="noopener noreferrer">Abrir ↗</a>` : ''}
</div>
</div>`;
};
if (dom.fontesLegislacao) {
dom.fontesLegislacao.innerHTML = legislacao.map(renderFonte).join('');
}
if (dom.fontesServicos) {
dom.fontesServicos.innerHTML = servicos.map(renderFonte).join('');
}
if (dom.fontesNormativas) {
dom.fontesNormativas.innerHTML = normativas.length
? normativas.map(renderFonte).join('')
: '<p style="color:var(--text-light);font-size:0.9rem;">Nenhuma normativa adicional no momento.</p>';
}
}
function renderDocsChecklist() {
if (!docsMestreData || !direitosData) return;
const saved = localGet('docs_checklist') || {};
const catNameMap = {};
direitosData.forEach((c) => {
catNameMap[c.id] = c.titulo.split('—')[0].trim();
});
dom.docsChecklist.innerHTML = docsMestreData
.map((doc) => {
const checked = saved[doc.id] ? 'checked' : '';
const catTags = (doc.categorias || [])
.map((cid) => `<span class="doc-cat-tag">${escapeHtml(catNameMap[cid] || cid)}</span>`)
.join('');
return `
<div class="doc-master-item">
<label class="doc-master-header">
<input type="checkbox" data-doc-id="${doc.id}" ${checked}>
<div class="doc-master-info">
<div class="doc-master-name">${escapeHtml(doc.nome)}</div>
<div class="doc-master-desc">${escapeHtml(doc.descricao)}</div>
<div class="doc-master-categories">${catTags}</div>
</div>
</label>
${doc.dica ? `<div class="doc-master-dica">💡 ${escapeHtml(doc.dica)}</div>` : ''}
</div>`;
})
.join('');
dom.docsChecklist.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
cb.addEventListener('change', () => {
const state = localGet('docs_checklist') || {};
if (cb.checked) {
state[cb.dataset.docId] = true;
} else {
delete state[cb.dataset.docId];
}
localSet('docs_checklist', state);
});
});
}
function renderInstituicoes() {
if (!instituicoesData || !direitosData) return;
const catNameMap = {};
direitosData.forEach((c) => {
catNameMap[c.id] = c.titulo.split('—')[0].trim();
});
function renderInstitutions(filter) {
const filtered = filter === 'todos'
? instituicoesData
: instituicoesData.filter((i) => i.tipo === filter);
if (filtered.length === 0) {
dom.instituicoesGrid.innerHTML = '<p style="text-align:center;color:var(--text-muted);">Nenhuma instituição nesta categoria.</p>';
return;
}
dom.instituicoesGrid.innerHTML = filtered
.map((inst) => {
const tipoIcon = inst.tipo === 'governamental' ? '🏛️' : inst.tipo === 'ong' ? '💚' : '⚖️';
const tipoLabel = inst.tipo === 'governamental' ? 'Governamental' : inst.tipo === 'ong' ? 'ONG' : 'Profissional';
const catTags = (inst.categorias || [])
.map((cid) => `<span class="inst-cat-tag">${escapeHtml(catNameMap[cid] || cid)}</span>`)
.join('');
const servicos = (inst.servicos || [])
.slice(0, 3)
.map((s) => `<li>${escapeHtml(s)}</li>`)
.join('');
return `
<div class="inst-card" data-tipo="${inst.tipo}">
<div class="inst-header">
<span class="inst-tipo-badge ${inst.tipo}">${tipoIcon} ${tipoLabel}</span>
</div>
<h4 class="inst-nome">${escapeHtml(inst.nome)}</h4>
<p class="inst-desc">${escapeHtml(inst.descricao)}</p>
${servicos ? `<ul class="inst-servicos">${servicos}</ul>` : ''}
<div class="inst-como">${escapeHtml(inst.como_acessar)}</div>
<div class="inst-categories">${catTags}</div>
${isSafeUrl(inst.url) ? `<a href="${escapeHtml(inst.url)}" class="btn btn-sm btn-outline inst-link" target="_blank" rel="noopener noreferrer">
Acessar site ↗
</a>` : ''}
</div>`;
})
.join('');
}
renderInstitutions('todos');
document.querySelectorAll('.inst-filter-btn').forEach((btn) => {
btn.addEventListener('click', () => {
document.querySelectorAll('.inst-filter-btn').forEach((b) => {
b.classList.remove('active');
b.setAttribute('aria-pressed', 'false');
});
btn.classList.add('active');
btn.setAttribute('aria-pressed', 'true');
renderInstitutions(btn.dataset.filter);
});
});
}
function renderLinksUteis() {
if (!fontesData || !direitosData || !dom.linksGrid) return;
const seen = new Set();
const links = [];
fontesData
.filter((f) => f.tipo === 'servico')
.forEach((f) => {
if (!seen.has(f.url)) {
seen.add(f.url);
links.push({ titulo: f.nome, url: f.url, orgao: f.orgao });
}
});
direitosData.forEach((cat) => {
(cat.links || []).forEach((lk) => {
if (!seen.has(lk.url)) {
seen.add(lk.url);
links.push({ titulo: lk.titulo, url: lk.url, orgao: '' });
}
});
});
dom.linksGrid.innerHTML = links
.filter((lk) => isSafeUrl(lk.url))
.map((lk) => {
const isTel = lk.url.trim().toLowerCase().startsWith('tel:');
const domain = (() => {
if (isTel) return lk.url.replace('tel:', '');
try { return new URL(lk.url).hostname.replace('www.', ''); }
catch { return ''; }
})();
const icon = isTel ? '📞'
: domain.includes('cfm.org') ? '👨‍⚕️'
: domain.includes('cfp.org') ? '🧠'
: domain.includes('who.int') ? '🌐'
: domain.includes('gov.br') ? '🏛️'
: domain.includes('inss') ? '📋'
: domain.includes('mds.gov') ? '🏠'
: '🔗';
return `
<a href="${escapeHtml(lk.url)}" class="link-card" target="_blank" rel="noopener noreferrer">
<span class="link-icon">${icon}</span>
<span class="link-title">${escapeHtml(lk.titulo)}</span>
<span class="link-domain">${escapeHtml(domain)}</span>
</a>`;
})
.join('');
}
function renderHeroStats() {
if (!direitosData || !fontesData) return;
if (dom.heroCatCount) {
dom.heroCatCount.textContent = `${direitosData.length}`;
}
if (dom.heroFontesCount) {
dom.heroFontesCount.textContent = `${fontesData.length}`;
}
}
function renderOrgaosEstaduais() {
if (!orgaosEstaduaisData || !dom.orgaosEstaduaisGrid) return;
const regioes = {
'Norte': ['AC', 'AM', 'AP', 'PA', 'RO', 'RR', 'TO'],
'Nordeste': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
'Centro-Oeste': ['DF', 'GO', 'MS', 'MT'],
'Sudeste': ['ES', 'MG', 'RJ', 'SP'],
'Sul': ['PR', 'RS', 'SC'],
};
let activeFilter = 'todos';
function renderGrid(filter) {
const filtered = filter === 'todos'
? orgaosEstaduaisData
: orgaosEstaduaisData.filter((o) => {
const states = regioes[filter] || [];
return states.includes(o.uf);
});
if (filtered.length === 0) {
dom.orgaosEstaduaisGrid.innerHTML = '<p style="text-align:center;color:var(--text-muted);">Nenhum órgão nesta região.</p>';
return;
}
dom.orgaosEstaduaisGrid.innerHTML = filtered
.map((org) => {
const urlSafe = isSafeUrl(org.url);
return `
<div class="orgao-card">
<span class="orgao-uf-badge">${escapeHtml(org.uf)}</span>
<span class="orgao-nome">${escapeHtml(org.nome)}</span>
${urlSafe ? `<a href="${escapeHtml(org.url)}" class="btn btn-sm btn-outline orgao-link" target="_blank" rel="noopener noreferrer">
Acessar ↗
</a>` : ''}
</div>`;
})
.join('');
}
renderGrid('todos');
document.querySelectorAll('.orgao-filter-btn').forEach((btn) => {
btn.addEventListener('click', () => {
document.querySelectorAll('.orgao-filter-btn').forEach((b) => {
b.classList.remove('active');
b.setAttribute('aria-pressed', 'false');
});
btn.classList.add('active');
btn.setAttribute('aria-pressed', 'true');
activeFilter = btn.dataset.filter;
renderGrid(activeFilter);
});
});
}
function renderClassificacao() {
if (!classificacaoData || !dom.classificacaoGrid) return;
dom.classificacaoGrid.innerHTML = `
<div class="classif-table-wrapper">
<table class="classif-table">
<thead>
<tr>
<th>Tipo de Deficiência</th>
<th>CID-10</th>
<th>CID-11</th>
<th>Critério Técnico</th>
</tr>
</thead>
<tbody>
${classificacaoData.map((c) => `
<tr>
<td class="classif-tipo"><strong>${escapeHtml(c.tipo)}</strong></td>
<td class="classif-cid"><code>${escapeHtml(c.cid10)}</code></td>
<td class="classif-cid"><code>${escapeHtml(c.cid11)}</code></td>
<td class="classif-criterio">${escapeHtml(c.criterio)}</td>
</tr>`).join('')}
</tbody>
</table>
</div>
<p class="classif-note">
💡 <strong>Dica:</strong> A CID-11 (OMS 2022) está sendo adotada gradualmente.
No Brasil, a maioria dos laudos ainda usa CID-10. O sistema aceita ambas as codificações.
</p>`;
}
function checkStaleness() {
if (!jsonMeta || !dom.stalenessBanner) return;
const updated = new Date(jsonMeta.ultima_atualizacao);
const now = new Date();
const diffDays = Math.floor((now - updated) / (1000 * 60 * 60 * 24));
const STALE_THRESHOLD = 30;
if (diffDays > STALE_THRESHOLD) {
if (dom.staleDays) {
dom.staleDays.textContent = `há ${diffDays} dias`;
}
dom.stalenessBanner.hidden = false;
} else {
dom.stalenessBanner.hidden = true;
}
}
function revealDocsUpload() {
const area = document.getElementById('docsUploadArea');
if (area) area.style.display = '';
}
(function setupDocsReveal() {
const heroBtn = document.getElementById('heroDocsBtn');
if (heroBtn) {
heroBtn.addEventListener('click', revealDocsUpload);
}
document.querySelectorAll('a[href="#documentos"]').forEach(link => {
link.addEventListener('click', revealDocsUpload);
});
})();
function setupUpload() {
dom.uploadZone.addEventListener('click', () => dom.fileInput.click());
dom.uploadZone.addEventListener('keydown', (e) => {
if (e.key === 'Enter' || e.key === ' ') {
e.preventDefault();
dom.fileInput.click();
}
});
dom.fileInput.addEventListener('change', async (e) => {
await handleFiles(e.target.files);
e.target.value = '';
});
dom.uploadZone.addEventListener('dragover', (e) => {
e.preventDefault();
dom.uploadZone.classList.add('drag-over');
});
dom.uploadZone.addEventListener('dragleave', () => {
dom.uploadZone.classList.remove('drag-over');
});
dom.uploadZone.addEventListener('drop', async (e) => {
e.preventDefault();
dom.uploadZone.classList.remove('drag-over');
await handleFiles(e.dataTransfer.files);
});
dom.deleteAllFiles.addEventListener('click', () => {
confirmAction('Tem certeza? Todos os arquivos serão removidos permanentemente do seu navegador.', async () => {
await clearAllFiles();
await renderFileList();
});
});
}
async function handleFiles(fileList) {
const currentCount = await getFileCount();
const filesToAdd = Array.from(fileList);
if (currentCount + filesToAdd.length > MAX_FILES) {
showToast(`Limite de ${MAX_FILES} arquivos. Pode adicionar mais ${MAX_FILES - currentCount}.`, 'warning');
return;
}
for (const file of filesToAdd) {
if (!ALLOWED_TYPES.includes(file.type)) {
const parts = file.name.split('.');
const ext = parts.length > 1 ? parts.pop().toLowerCase() : '';
if (!ALLOWED_EXTENSIONS.includes('.' + ext)) {
showToast(`Formato não aceito: ${file.name}. Use PDF, JPG ou PNG.`, 'error');
continue;
}
}
if (file.size > MAX_FILE_SIZE) {
showToast(`Arquivo muito grande: ${file.name} (${formatBytes(file.size)}). Máx: 5MB.`, 'error');
continue;
}
try {
const buffer = await file.arrayBuffer();
const encrypted = await encryptBuffer(buffer);
const now = new Date();
const expires = new Date(now.getTime() + FILE_TTL_MINUTES * 60000);
await storeFile({
id: Date.now() + '_' + Math.random().toString(36).slice(2, 8),
name: file.name,
type: file.type,
size: file.size,
data: encrypted.ciphertext,
iv: encrypted.iv,
encrypted: true,
addedAt: now.toISOString(),
expiresAt: expires.toISOString(),
});
} catch (err) {
console.error('Erro ao salvar arquivo:', err);
showToast(`Erro ao salvar: ${file.name}`, 'error');
}
}
await renderFileList();
}
async function renderFileList() {
try {
const files = await getAllFiles();
if (files.length === 0) {
dom.fileList.innerHTML = '';
dom.deleteAllFiles.style.display = 'none';
return;
}
dom.deleteAllFiles.style.display = '';
dom.fileList.innerHTML = files
.map((f) => {
const icon = f.type === 'application/pdf' ? '📄' : '🖼️';
const date = new Date(f.addedAt).toLocaleDateString('pt-BR');
const cryptoBadge = f.encrypted ? '<span class="crypto-badge" title="Criptografia AES-256-GCM">🔐</span>' : '';
const expiresStr = f.expiresAt
? `· ⏱️ ${formatTimeRemaining(f.expiresAt)}`
: '';
return `
<div class="file-item" data-file-id="${f.id}">
<label class="file-item-checkbox" title="Selecionar para análise">
<input type="checkbox" class="file-select-cb" data-id="${f.id}" checked>
</label>
<span class="file-item-icon">${icon}</span>
<div class="file-item-info">
<div class="file-item-name" title="${escapeHtml(f.name)}">${cryptoBadge}${escapeHtml(f.name)}</div>
<div class="file-item-meta">${formatBytes(f.size)} · Adicionado em ${date} ${expiresStr}</div>
</div>
<div class="file-item-actions">
<button class="btn-view" title="Visualizar" data-id="${f.id}">👁️ Ver</button>
<button class="btn-delete" title="Excluir" data-id="${f.id}">🗑️</button>
</div>
</div>`;
})
.join('');
updateAnalyzeButton();
dom.fileList.querySelectorAll('.file-select-cb').forEach((cb) => {
cb.addEventListener('change', updateAnalyzeButton);
});
dom.fileList.querySelectorAll('.btn-view').forEach((btn) => {
btn.addEventListener('click', async () => {
const file = await getFile(btn.dataset.id);
if (file) {
const plainData = await decryptFileData(file);
const blob = new Blob([plainData], { type: file.type });
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.target = '_blank';
a.rel = 'noopener';
document.body.appendChild(a);
a.click();
document.body.removeChild(a);
setTimeout(() => URL.revokeObjectURL(url), 15000);
}
});
});
dom.fileList.querySelectorAll('.btn-delete').forEach((btn) => {
btn.addEventListener('click', () => {
confirmAction('Excluir este arquivo?', async () => {
await deleteFile(btn.dataset.id);
await renderFileList();
});
});
});
} catch (err) {
console.error('Erro ao listar arquivos:', err);
}
}
function updateAnalyzeButton() {
const btn = document.getElementById('analyzeSelected');
if (!btn) return;
const checked = dom.fileList.querySelectorAll('.file-select-cb:checked');
const count = checked.length;
btn.disabled = count === 0;
btn.textContent = count === 0
? '🔍 Enviar para análise local'
: count === 1
? '🔍 Analisar 1 arquivo'
: `🔍 Analisar ${count} arquivos`;
}
function setupAnalysis() {
dom.closeAnalysis.addEventListener('click', () => {
dom.analysisResults.style.display = 'none';
});
dom.exportPdf.addEventListener('click', () => {
dom.analysisResults.setAttribute('data-print-date', new Date().toLocaleDateString('pt-BR'));
document.body.classList.add('printing-analysis');
window.print();
const cleanup = () => {
document.body.classList.remove('printing-analysis');
window.removeEventListener('afterprint', cleanup);
};
window.addEventListener('afterprint', cleanup);
setTimeout(cleanup, 5000);
});
const analyzeBtn = document.getElementById('analyzeSelected');
if (analyzeBtn) {
analyzeBtn.addEventListener('click', analyzeSelectedDocuments);
}
}
async function analyzeSelectedDocuments() {
const analyzeBtn = document.getElementById('analyzeSelected');
const checkboxes = dom.fileList.querySelectorAll('.file-select-cb:checked');
const fileIds = Array.from(checkboxes).map((cb) => cb.dataset.id);
if (fileIds.length === 0) {
showToast('Selecione pelo menos um arquivo para analisar.', 'warning');
return;
}
if (analyzeBtn) {
analyzeBtn.disabled = true;
analyzeBtn.textContent = '⏳ Analisando...';
}
dom.analysisResults.style.display = '';
dom.analysisLoading.style.display = '';
dom.analysisContent.innerHTML = '';
dom.analysisResults.scrollIntoView({ behavior: 'smooth' });
const allText = [];
const fileNames = [];
const hasPdf = [];
const errors = [];
const successIds = [];
try {
const filesToProcess = [];
for (const fileId of fileIds) {
try {
const file = await getFile(fileId);
if (!file) {
errors.push({ name: `ID ${fileId}`, reason: 'Arquivo não encontrado' });
} else {
filesToProcess.push({ fileId, file });
}
} catch (dbErr) {
console.error(`Erro ao recuperar arquivo ${fileId}:`, dbErr);
errors.push({ name: `ID ${fileId}`, reason: 'Erro ao acessar arquivo' });
}
}
for (let i = 0; i < filesToProcess.length; i++) {
const { fileId, file } = filesToProcess[i];
if (filesToProcess.length > 1) {
const loadingText = dom.analysisLoading.querySelector('p');
if (loadingText) {
loadingText.textContent = `Analisando ${i + 1} de ${filesToProcess.length}: ${file.name}`;
}
}
try {
const plainData = await decryptFileData(file);
let text = '';
if (file.type === 'application/pdf') {
text = await extractPdfText(plainData);
hasPdf.push(true);
} else {
text = file.name;
hasPdf.push(false);
}
allText.push(text);
fileNames.push(file.name);
successIds.push(fileId);
} catch (err) {
console.error(`Erro ao processar ${file.name}:`, err);
errors.push({
name: file.name,
reason: file.type === 'application/pdf'
? 'PDF protegido, escaneado ou formato incompatível'
: 'Erro ao processar imagem',
});
}
}
if (allText.length === 0) {
dom.analysisContent.innerHTML = `
<div class="analysis-error">
<p>⚠️ Não foi possível analisar nenhum dos arquivos selecionados.</p>
${errors.map((e) => `<p style=\"font-size:0.85rem;color:var(--text-muted);\">· ${escapeHtml(e.name)}: ${escapeHtml(e.reason)}</p>`).join('')}
<p style="font-size:0.85rem;margin-top:8px;">
💡 <strong>Dica:</strong> Navegue pelas <a href=\"#categorias\">categorias</a>
para encontrar seus direitos manualmente.
</p>
</div>`;
return;
}
const medicalTerms = [
'laudo', 'atestado', 'receita médica', 'receita medica', 'diagnóstico', 'diagnostico',
'cid', 'crm', 'médico', 'medico', 'exame', 'prescrição', 'prescricao',
'relatório médico', 'relatorio medico', 'doença', 'doenca', 'deficiência', 'deficiencia',
'autismo', 'tea', 'psiquiatra', 'neurologista', 'fisioterapeuta', 'terapeuta',
'psicólogo', 'psicologo', 'fonoaudiólogo', 'fonoaudiologo', 'terapia ocupacional',
'transtorno', 'síndrome', 'sindrome', 'especialista', 'consulta médica', 'consulta medica',
'encaminhamento', 'habilitação', 'habilitacao', 'reabilitação', 'reabilitacao',
'paciente', 'prontuário', 'prontuario', 'anamnese', 'prognóstico', 'prognostico',
'comorbidade', 'terapêutico', 'terapeutico', 'clínico', 'clinico', 'neuropediatra'
];
const originalText = allText.join('\n');
const combinedTextLower = originalText.toLowerCase();
const foundMedical = medicalTerms.some(term => combinedTextLower.includes(term));
if (!foundMedical) {
dom.analysisContent.innerHTML = `
<div class="analysis-error">
<p>⚠️ O documento enviado não parece ser um laudo, atestado ou documento médico.</p>
<p>Por favor, envie um documento relacionado à saúde (laudo, atestado, receita, diagnóstico, etc.) para análise dos direitos.</p>
<p style="font-size:0.85rem;margin-top:8px;">
💡 <strong>Dica:</strong> Navegue pelas <a href=\"#categorias\">categorias</a> para encontrar seus direitos manualmente.
</p>
</div>`;
for (const id of successIds) {
try { await deleteFile(id); } catch (delErr) { console.warn('Erro ao descartar arquivo após análise:', delErr); }
}
await renderFileList();
if (analyzeBtn) updateAnalyzeButton();
dom.analysisLoading.style.display = 'none';
return;
}
const combinedNames = fileNames.join(' ');
const results = matchRights(originalText, combinedNames);
const anyPdf = hasPdf.some(Boolean);
renderAnalysisResults(results, fileNames, anyPdf, errors);
for (const id of successIds) {
try {
await deleteFile(id);
} catch (delErr) {
console.warn('Erro ao descartar arquivo após análise:', delErr);
}
}
console.info(`[Security] ${successIds.length} arquivo(s) descartado(s) automaticamente após análise.`);
await renderFileList();
} catch (err) {
console.error('Erro na análise unificada:', err);
dom.analysisContent.innerHTML = `
<div class="analysis-error">
<p>⚠️ Ocorreu um erro durante a análise.</p>
<p style="font-size:0.85rem;margin-top:8px;">
💡 <strong>Dica:</strong> Navegue pelas <a href=\"#categorias\">categorias</a>
para encontrar seus direitos manualmente.
</p>
</div>`;
} finally {
dom.analysisLoading.style.display = 'none';
const loadingText = dom.analysisLoading.querySelector('p');
if (loadingText) {
loadingText.textContent = 'Analisando documentos... (100% local, nada é enviado)';
}
if (analyzeBtn) {
updateAnalyzeButton();
}
}
}
async function extractPdfText(arrayBuffer) {
await ensurePdfJs();
if (typeof pdfjsLib === 'undefined') {
throw new Error('pdf.js não disponível');
}
const pdf = await pdfjsLib.getDocument({ data: new Uint8Array(arrayBuffer) }).promise;
const textParts = [];
for (let i = 1; i <= Math.min(pdf.numPages, 20); i++) {
const page = await pdf.getPage(i);
const content = await page.getTextContent();
const pageText = content.items.map((item) => item.str).join(' ');
textParts.push(pageText);
}
return textParts.join('\n');
}
function cidGenericRegex() { return /\b([A-Z]\d{2}(?:\.\d{1,2})?)\b/g; }
function cid11GenericRegex() { return /\b(\d[A-Z]\d{2}(?:\.\d{1,2})?)\b/g; }
function cid11TwoLetterRegex() { return /\b([A-Z]{2}\d{2}(?:\.\d{1,2})?)\b/g; }
function crmRegex() { return /\bCRM[\s/\-]*([A-Z]{2})?[\s/\-]*(\d{4,7})[\s/\-]*([A-Z]{2})?\b/gi; }
function matchRights(text, fileName) {
if (!direitosData) return [];
const rawText = text + ' ' + fileName;
const normalizedText = normalizeText(rawText);
const scores = {};
direitosData.forEach((cat) => {
scores[cat.id] = { score: 0, matches: new Set() };
});
const cidMatched = new Set();
for (const cidRegex of [cidGenericRegex(), cid11GenericRegex(), cid11TwoLetterRegex()]) {
let m;
while ((m = cidRegex.exec(rawText)) !== null) {
const code = m[1];
const prefix = code.substring(0, 3).toLowerCase();
if (KEYWORD_MAP[prefix] || KEYWORD_MAP[code.toLowerCase()]) continue;
if (cidMatched.has(code)) continue;
cidMatched.add(code);
const letter = code.charAt(0);
const cats = CID_RANGE_MAP[letter] || ['bpc', 'sus_terapias'];
cats.forEach((catId) => {
if (scores[catId]) {
scores[catId].score += 3;
scores[catId].matches.add(`CID ${code}`);
}
});
}
}
const crmMatch = crmRegex().exec(rawText);
if (crmMatch) {
const uf = crmMatch[1] || crmMatch[3] || '';
const num = crmMatch[2];
const crmLabel = uf ? `CRM/${uf} ${num}` : `CRM ${num}`;
['bpc', 'ciptea', 'plano_saude', 'sus_terapias', 'transporte', 'trabalho', 'fgts'].forEach((catId) => {
if (scores[catId]) {
scores[catId].score += 2;
scores[catId].matches.add(crmLabel);
}
});
}
const seenNormalized = new Set();
for (const [keyword, { cats, weight }] of Object.entries(KEYWORD_MAP)) {
const normalizedKey = normalizeText(keyword);
if (seenNormalized.has(normalizedKey)) continue;
seenNormalized.add(normalizedKey);
let matchCount;
if (UPPERCASE_ONLY_TERMS.has(normalizedKey)) {
const upperKey = keyword.toUpperCase();
const safeB = '(?:^|[\\s,.;:()\\[\\]/\\-])';
const safeA = '(?=$|[\\s,.;:()\\[\\]/\\-])';
const regex = new RegExp(safeB + escapeRegex(upperKey) + safeA, 'g');
matchCount = (rawText.match(regex) || []).length;
} else {
const regex = new RegExp('\\b' + escapeRegex(normalizedKey) + '\\b', 'g');
matchCount = (normalizedText.match(regex) || []).length;
}
if (matchCount > 0) {
cats.forEach((catId) => {
if (scores[catId]) {
scores[catId].score += weight * Math.min(matchCount, 3);
scores[catId].matches.add(keyword);
}
});
}
}
direitosData.forEach((cat) => {
(cat.tags || []).forEach((tag) => {
const normalizedTag = normalizeText(tag);
if (UPPERCASE_ONLY_TERMS.has(normalizedTag)) {
const upperTag = tag.toUpperCase();
const safeB = '(?:^|[\\s,.;:()\\[\\]/\\-])';
const safeA = '(?=$|[\\s,.;:()\\[\\]/\\-])';
const regex = new RegExp(safeB + escapeRegex(upperTag) + safeA);
if (regex.test(rawText)) {
scores[cat.id].score += 2;
scores[cat.id].matches.add(tag);
}
return;
}
if (normalizedTag.length <= 5) {
const tagRegex = new RegExp('\\b' + escapeRegex(normalizedTag) + '\\b');
if (tagRegex.test(normalizedText)) {
scores[cat.id].score += 2;
scores[cat.id].matches.add(tag);
}
} else if (normalizedText.includes(normalizedTag)) {
scores[cat.id].score += 2;
scores[cat.id].matches.add(tag);
}
});
});
direitosData.forEach((cat) => {
(cat.requisitos || []).forEach((req) => {
const words = normalizeText(req).split(/\s+/).filter((w) => w.length > 4);
const matchedWords = words.filter((w) => {
const wRegex = new RegExp('\\b' + escapeRegex(w) + '\\b');
return wRegex.test(normalizedText);
});
if (matchedWords.length >= 2) {
scores[cat.id].score += 1;
}
});
});
return direitosData
.map((cat) => ({
category: cat,
score: scores[cat.id].score,
matches: Array.from(scores[cat.id].matches),
}))
.filter((r) => r.score > 0)
.sort((a, b) => b.score - a.score);
}
function renderAnalysisResults(results, fileNames, hasPdf, errors = []) {
const names = Array.isArray(fileNames) ? fileNames : [fileNames];
const fileCount = names.length;
const filesLabel = fileCount === 1
? `📄 Arquivo analisado: <strong>${escapeHtml(names[0])}</strong>`
: `📄 ${fileCount} arquivos analisados: ${names.map((n) => `<strong>${escapeHtml(n)}</strong>`).join(', ')}`;
if (results.length === 0) {
dom.analysisContent.innerHTML = `
<div class="analysis-empty">
<p>${filesLabel}</p>
<p>Não foram encontradas correspondências claras com as categorias de direitos.</p>
${!hasPdf ? `<p class="analysis-hint">💡 Para imagens, a análise é limitada ao nome do arquivo.
Faça upload do <strong>PDF do laudo</strong> para uma análise mais completa.</p>` : ''}
${errors.length ? `<div class="analysis-errors-summary">
<p>⚠️ Alguns arquivos não puderam ser processados:</p>
${errors.map((e) => `<p class="analysis-hint">· ${escapeHtml(e.name)}: ${escapeHtml(e.reason)}</p>`).join('')}
</div>` : ''}
<p class="analysis-hint">💡 Navegue pelas <a href="#categorias">categorias</a> para encontrar
seus direitos manualmente, ou use a <a href="#busca">busca</a>.</p>
</div>`;
return;
}
const maxScore = results[0].score;
let html = `
<div class="analysis-file-info">
<p>${filesLabel}</p>
<p class="analysis-privacy">🔒 Análise 100% local — nenhum dado foi enviado para servidores.</p>
${errors.length ? `<p class="analysis-errors-inline">⚠️ ${errors.length} arquivo(s) com erro: ${errors.map((e) => escapeHtml(e.name)).join(', ')}</p>` : ''}
</div>
<div class="analysis-legend" aria-label="Legenda da precisão">
<span class="legend-badge high">Alta relevância</span>
<span class="legend-badge medium">Média relevância</span>
<span class="legend-badge low">Possível relação</span>
<span class="legend-bar"><span class="legend-bar-sample high" aria-hidden="true"></span><span class="legend-bar-sample medium" aria-hidden="true"></span><span class="legend-bar-sample low" aria-hidden="true"></span> Barra indica grau de correspondência</span>
</div>
<div class="analysis-match-list">`;
results.forEach(({ category, score, matches }) => {
const pct = Math.round((score / maxScore) * 100);
const level = pct >= 80 ? 'high' : pct >= 40 ? 'medium' : 'low';
const levelLabel = pct >= 80 ? 'Alta relevância' : pct >= 40 ? 'Média relevância' : 'Possível relação';
const barPct = level === 'high' ? Math.max(85, pct) : level === 'medium' ? Math.round(45 + (pct - 40) * 0.625) : Math.round(15 + pct * 0.5);
html += `
<div class="analysis-match ${level}" data-cat-id="${category.id}" aria-label="${levelLabel}">
<div class="analysis-match-header">
<span class="analysis-match-icon">${category.icone}</span>
<div class="analysis-match-title">
<h4>${escapeHtml(category.titulo)}</h4>
<span class="analysis-badge ${level}" aria-label="${levelLabel}">${levelLabel}</span>
</div>
<div class="analysis-bar-group">
<span class="analysis-bar-label ${level}">${level === 'high' ? 'Alta' : level === 'medium' ? 'Média' : 'Baixa'}</span>
<div class="analysis-match-bar" role="img" aria-label="${levelLabel}: ${barPct}%">
<div class="analysis-match-fill ${level}" style="width:${barPct}%"></div>
</div>
</div>
</div>
<p class="analysis-match-resumo">${escapeHtml(category.resumo)}</p>
${matches.length ? `
<div class="analysis-match-keywords">
<span class="kw-label"><strong>Termos encontrados:</strong></span>
${matches.slice(0, 8).map((m) => {
if (m.startsWith('CID')) {
const cidNum = m.match(/CID\s+([A-Z0-9.]+)/);
return cidNum ? `<span class="kw-tag ${level}">${escapeHtml(m)}</span>` : `<span class="kw-tag low">CID não identificado</span>`;
}
if (m.startsWith('CRM')) {
const crmNum = m.match(/CRM\/?[A-Z]{0,2}\s*\d{4,7}/);
return crmNum ? `<span class="kw-tag ${level}">${escapeHtml(m)}</span>` : `<span class="kw-tag low">CRM não identificado</span>`;
}
return `<span class="kw-tag ${level}">${escapeHtml(m)}</span>`;
}).join('')}
</div>` : ''}
<div class="analysis-match-actions">
<button class="btn btn-sm btn-primary analysis-see-more" data-id="${category.id}">
Ver detalhes e passo a passo →
</button>
</div>
</div>`;
});
html += `</div>
<div class="analysis-footer">
<p>⚠️ <strong>Atenção:</strong> Esta análise é uma <strong>orientação preliminar</strong>
baseada em correspondência de palavras-chave. <strong>Não substitui</strong> orientação
profissional. Para confirmação, procure a <strong>Defensoria Pública</strong>,
um advogado ou o <strong>CRAS</strong> da sua cidade.</p>
</div>`;
dom.analysisContent.innerHTML = html;
dom.analysisContent.querySelectorAll('.analysis-see-more').forEach((btn) => {
btn.addEventListener('click', () => {
showDetalhe(btn.dataset.id);
dom.analysisResults.style.display = 'none';
});
});
}
async function getCryptoKey() {
if (!CRYPTO_AVAILABLE) return null;
const db = await openDB();
try {
const existing = await new Promise((resolve, reject) => {
const tx = db.transaction(CRYPTO_STORE, 'readonly');
const req = tx.objectStore(CRYPTO_STORE).get(CRYPTO_KEY_ID);
req.onsuccess = () => resolve(req.result);
req.onerror = () => reject(req.error);
});
if (existing && existing.key) {
return existing.key;
}
if (existing && existing.jwk) {
return await crypto.subtle.importKey(
'jwk', existing.jwk,
{ name: 'AES-GCM', length: 256 },
false, ['encrypt', 'decrypt']
);
}
} finally {
db.close();
}
let exportable = false;
let key;
try {
key = await crypto.subtle.generateKey(
{ name: 'AES-GCM', length: 256 },
false,
['encrypt', 'decrypt']
);
const testDb = await openDB();
try {
await new Promise((resolve, reject) => {
const tx = testDb.transaction(CRYPTO_STORE, 'readwrite');
tx.objectStore(CRYPTO_STORE).put({ id: CRYPTO_KEY_ID, key: key });
tx.oncomplete = () => resolve();
tx.onerror = () => reject(tx.error);
});
} finally {
testDb.close();
}
return key;
} catch (cloneErr) {
console.warn('[Crypto] CryptoKey structured clone failed, using JWK fallback:', cloneErr.message);
exportable = true;
key = await crypto.subtle.generateKey(
{ name: 'AES-GCM', length: 256 },
true,
['encrypt', 'decrypt']
);
}
const jwk = await crypto.subtle.exportKey('jwk', key);
const db2 = await openDB();
try {
await new Promise((resolve, reject) => {
const tx = db2.transaction(CRYPTO_STORE, 'readwrite');
tx.objectStore(CRYPTO_STORE).put({ id: CRYPTO_KEY_ID, jwk: jwk });
tx.oncomplete = () => resolve();
tx.onerror = () => reject(tx.error);
});
} finally {
db2.close();
}
return key;
}
async function encryptBuffer(plainBuffer) {
const key = await getCryptoKey();
if (!key) {
return { ciphertext: plainBuffer, iv: null };
}
const iv = crypto.getRandomValues(new Uint8Array(12));
const ciphertext = await crypto.subtle.encrypt(
{ name: 'AES-GCM', iv: iv, tagLength: 128 },
key,
plainBuffer
);
return { ciphertext, iv: Array.from(iv) };
}
async function decryptFileData(fileObj) {
if (!fileObj.encrypted || !fileObj.iv) {
return fileObj.data;
}
const key = await getCryptoKey();
if (!key) {
console.warn('Crypto unavailable — returning raw data');
return fileObj.data;
}
try {
const iv = new Uint8Array(fileObj.iv);
return await crypto.subtle.decrypt(
{ name: 'AES-GCM', iv: iv, tagLength: 128 },
key,
fileObj.data
);
} catch (err) {
console.error('Decryption failed:', err);
return fileObj.data;
}
}
async function cleanupExpiredFiles() {
try {
const files = await getAllFiles();
const now = Date.now();
let removed = 0;
for (const file of files) {
if (file.expiresAt && new Date(file.expiresAt).getTime() < now) {
await deleteFile(file.id);
removed++;
}
}
if (removed > 0) {
console.info(`[Security] ${removed} arquivo(s) expirado(s) removido(s) automaticamente.`);
}
return removed;
} catch (err) {
console.error('Erro na limpeza de arquivos expirados:', err);
return 0;
}
}
function openDB() {
return new Promise((resolve, reject) => {
const req = indexedDB.open(DB_NAME, DB_VERSION);
req.onupgradeneeded = (e) => {
const db = e.target.result;
if (!db.objectStoreNames.contains(STORE_NAME)) {
db.createObjectStore(STORE_NAME, { keyPath: 'id' });
}
if (!db.objectStoreNames.contains(CRYPTO_STORE)) {
db.createObjectStore(CRYPTO_STORE, { keyPath: 'id' });
}
};
req.onsuccess = () => resolve(req.result);
req.onerror = () => reject(req.error);
});
}
async function dbOp(mode, fn) {
const db = await openDB();
return new Promise((ok, no) => {
const tx = db.transaction(STORE_NAME, mode);
const r = fn(tx.objectStore(STORE_NAME));
tx.oncomplete = () => { db.close(); ok(r.result); };
tx.onerror = () => { db.close(); no(tx.error); };
});
}
function storeFile(f) { return dbOp('readwrite', s => s.put(f)); }
function getAllFiles() { return dbOp('readonly', s => s.getAll()); }
function getFile(id) { return dbOp('readonly', s => s.get(id)); }
function deleteFile(id) { return dbOp('readwrite', s => s.delete(id)); }
function clearAllFiles() { return dbOp('readwrite', s => s.clear()); }
function getFileCount() { return dbOp('readonly', s => s.count()); }
function setupFooter() {
if (dom.lastUpdate && !dom.lastUpdate.textContent) {
dom.lastUpdate.textContent = new Date().toLocaleDateString('pt-BR');
}
}
function setupFooterVersion() {
if (dom.footerVersion && jsonMeta && jsonMeta.versao) {
dom.footerVersion.textContent = `v${jsonMeta.versao}`;
dom.footerVersion.title = `Versão dos dados: ${jsonMeta.versao}`;
}
}
function localGet(key) {
try {
const val = localStorage.getItem(STORAGE_PREFIX + key);
return val ? safeJsonParse(val) : null;
} catch {
return null;
}
}
function localSet(key, value) {
try {
localStorage.setItem(STORAGE_PREFIX + key, JSON.stringify(value));
} catch {
}
}
function isSafeUrl(url) {
if (!url || typeof url !== 'string') return false;
const trimmed = url.trim().toLowerCase();
if (trimmed.startsWith('javascript:') || trimmed.startsWith('vbscript:')) return false;
if (trimmed.startsWith('#') || trimmed.startsWith('/') || trimmed.startsWith('./')) return true;
if (trimmed.startsWith('blob:') || trimmed.startsWith('tel:') || trimmed.startsWith('mailto:')) return true;
try {
const parsed = new URL(url, window.location.origin);
if (parsed.origin === window.location.origin) return true;
const host = parsed.hostname;
const TRUSTED = [
'.gov.br', '.planalto.gov.br', '.inss.gov.br', '.mds.gov.br',
'.apaebrasil.org.br', '.ama.org.br', 'cdnjs.cloudflare.com',
'.oab.org.br', '.cnmp.mp.br', '.anadep.org.br', '.mp.br',
'.ijc.org.br', '.procon.sp.gov.br', '.autismbrasil.org',
'.abntcatalogo.com.br', '.caixa.gov.br',
'.cfm.org.br', '.cfp.org.br', '.who.int',
];
return TRUSTED.some(t => host === t.slice(1) || host.endsWith(t));
} catch {
return false;
}
}
const _escapeDiv = document.createElement('div');
function escapeHtml(str) {
if (!str) return '';
_escapeDiv.textContent = str;
return _escapeDiv.innerHTML;
}
function escapeRegex(str) {
return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
function normalizeText(text) {
return text
.toLowerCase()
.normalize('NFD')
.replace(/[\u0300-\u036f]/g, '');
}
function formatDate(dateStr) {
try {
const d = new Date(dateStr + 'T00:00:00');
return d.toLocaleDateString('pt-BR', {
day: '2-digit',
month: 'long',
year: 'numeric',
});
} catch {
return dateStr;
}
}
function formatBytes(bytes) {
if (bytes < 1024) return bytes + ' B';
if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}
function formatTimeRemaining(expiresAt) {
const diff = new Date(expiresAt).getTime() - Date.now();
if (diff <= 0) return 'Expirado';
const mins = Math.ceil(diff / 60000);
if (mins < 60) return `Expira em ${mins} min`;
const hours = Math.floor(mins / 60);
const remMins = mins % 60;
return `Expira em ${hours}h${remMins > 0 ? remMins + 'min' : ''}`;
}
function setupBackToTop() {
const btn = document.getElementById('backToTop');
if (!btn) return;
window.addEventListener('scroll', () => {
if (window.scrollY > 300) {
btn.classList.add('visible');
} else {
btn.classList.remove('visible');
}
});
btn.addEventListener('click', () => {
window.scrollTo({
top: 0,
behavior: 'smooth'
});
});
}
if (document.readyState === 'loading') {
document.addEventListener('DOMContentLoaded', init);
} else {
init();
}
})();
