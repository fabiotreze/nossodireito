/**
 * Cliente Azure Document Intelligence (Form Recognizer).
 *
 * Autenticação: DefaultAzureCredential → Managed Identity em produção,
 * az login em dev local. Zero secrets em código.
 *
 * Modelo: prebuilt-read (OCR + estrutura).
 * Roadmap: prebuilt-document para extração key-value automática
 *          ou modelo custom treinado em laudos médicos PcD.
 *
 * Privacidade:
 *  - Documentos SÓ chegam aqui já anonimizados (verificado em server.js)
 *  - Logs apenas: hash do conteúdo + duração + status (zero texto)
 *  - Retenção: Azure não persiste após análise (per Doc Intelligence ToS)
 *  - Região: brazilsouth (LGPD residência)
 */

"use strict";

const crypto = require("node:crypto");

// Lazy require — só carrega SDK se endpoint estiver configurado.
// Evita falha em dev local sem credenciais Azure.
let _client = null;
let _initError = null;

function getClient() {
  if (_client) return _client;
  if (_initError) throw _initError;

  const endpoint = process.env.AZURE_DOC_INTELLIGENCE_ENDPOINT || "";
  if (!endpoint) {
    _initError = new Error("AZURE_DOC_INTELLIGENCE_ENDPOINT not configured");
    throw _initError;
  }

  try {
    const { DocumentAnalysisClient } = require("@azure/ai-form-recognizer");
    const { DefaultAzureCredential } = require("@azure/identity");
    _client = new DocumentAnalysisClient(endpoint, new DefaultAzureCredential());
    return _client;
  } catch (err) {
    _initError = new Error(`Failed to init Doc Intelligence client: ${err.message}`);
    throw _initError;
  }
}

/**
 * Analisa texto via prebuilt-read e retorna estrutura JSON.
 *
 * @param {string} anonymizedText Texto JÁ ANONIMIZADO (validado em server.js)
 * @returns {Promise<{
 *   contentHash: string,
 *   durationMs: number,
 *   pages: number,
 *   paragraphs: Array<{role?: string, content: string}>,
 *   cids: string[],
 *   dates: string[]
 * }>}
 */
async function analyzeText(anonymizedText) {
  const t0 = Date.now();
  const contentHash = crypto.createHash("sha256").update(anonymizedText).digest("hex").slice(0, 16);

  const client = getClient();

  // Doc Intelligence aceita PDF/imagem ou texto cru via Buffer.
  // Para texto puro, passamos como text/plain.
  const buffer = Buffer.from(anonymizedText, "utf8");

  const poller = await client.beginAnalyzeDocument("prebuilt-read", buffer, {
    contentType: "text/plain",
  });
  const result = await poller.pollUntilDone();

  // Extrai CIDs (regex padrão: letra + 2 dígitos + opcional .N)
  const cidRegex = /\b[A-Z]\d{2}(?:\.\d{1,2})?\b/g;
  const dateRegex = /\b\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4}\b/g;

  const cidsSet = new Set();
  const datesSet = new Set();
  const paragraphs = [];

  if (result.paragraphs) {
    for (const p of result.paragraphs) {
      paragraphs.push({
        role: p.role || undefined,
        content: p.content,
      });
      const cidMatches = p.content.match(cidRegex);
      if (cidMatches) cidMatches.forEach((c) => cidsSet.add(c));
      const dateMatches = p.content.match(dateRegex);
      if (dateMatches) dateMatches.forEach((d) => datesSet.add(d));
    }
  }

  return {
    contentHash,
    durationMs: Date.now() - t0,
    pages: result.pages ? result.pages.length : 0,
    paragraphs,
    cids: [...cidsSet],
    dates: [...datesSet],
  };
}

module.exports = { analyzeText };
