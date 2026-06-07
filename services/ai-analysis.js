/**
 * services/ai-analysis.js
 *
 * Cliente Azure OpenAI (gpt-4o-mini) para análise IA de laudos PcD.
 *
 * Histórico: era services/doc-intelligence.js (Azure AI Document Intelligence
 * via prebuilt-read) até v1.17.0. Em v1.18.0 a implementação foi trocada para
 * Azure OpenAI Chat Completions porque prebuilt-read é OCR e rejeitava
 * text/plain. Renomeado para services/ai-analysis.js em v1.19.0 (cleanup).
 *
 * Autenticação: DefaultAzureCredential → Managed Identity em produção
 * (zero secrets), az login em dev. Token AAD com escopo
 * https://cognitiveservices.azure.com/.default.
 *
 * Modelo: gpt-4o-mini (Azure OpenAI, brazilsouth, GlobalStandard).
 *
 * Privacidade (LGPD):
 *  - Texto chega aqui já anonimizado pelo client (Anonymizer)
 *  - server.js roda containsPII() como double-check antes de chamar
 *  - Microsoft DPA: zero retention de prompts/completions (abuse opt-out)
 *  - Logs apenas: hash SHA-256 + duração + status (nunca texto)
 *  - Residência: brazilsouth (LGPD Art. 33)
 */

"use strict";

const crypto = require("node:crypto");

// Lazy require — só carrega SDK se endpoint estiver configurado.
let _client = null;
let _initError = null;
let _credential = null;

const AI_TIMEOUT_MS = Number(process.env.AI_TIMEOUT_MS || 12000);
const AI_MAX_RETRIES = Number(process.env.AI_MAX_RETRIES || 2);
const AI_RETRY_BASE_MS = Number(process.env.AI_RETRY_BASE_MS || 600);
const AI_CB_FAILURE_THRESHOLD = Number(process.env.AI_CB_FAILURE_THRESHOLD || 3);
const AI_CB_COOLDOWN_MS = Number(process.env.AI_CB_COOLDOWN_MS || 60000);

const aiCircuit = {
  failures: 0,
  openUntil: 0,
  lastError: "",
};

/** Schema esperado do JSON estruturado retornado pelo modelo. */
const ANALYSIS_JSON_SCHEMA = {
  name: "analise_laudo_pcd",
  strict: true,
  schema: {
    type: "object",
    additionalProperties: false,
    required: ["cids", "datas", "diagnosticos", "direitos_sugeridos", "resumo", "confianca"],
    properties: {
      cids: {
        type: "array",
        description: "CIDs encontrados no texto (formato CID-10/11)",
        items: {
          type: "object",
          additionalProperties: false,
          required: ["codigo", "descricao", "confianca"],
          properties: {
            codigo: { type: "string", description: "Código CID (ex: F84.0)" },
            descricao: { type: "string", description: "Doença/condição em pt-BR" },
            confianca: { type: "string", enum: ["alta", "media", "baixa"] },
          },
        },
      },
      datas: {
        type: "array",
        description: "Datas relevantes no documento",
        items: {
          type: "object",
          additionalProperties: false,
          required: ["data", "contexto"],
          properties: {
            data: { type: "string", description: "Data em ISO (YYYY-MM-DD)" },
            contexto: { type: "string", description: "O que representa" },
          },
        },
      },
      diagnosticos: {
        type: "array",
        description: "Condições clínicas identificadas (texto livre, pt-BR)",
        items: { type: "string" },
      },
      direitos_sugeridos: {
        type: "array",
        description: "Categorias do catálogo NossoDireito cuja base legal cobre os CIDs identificados. NÃO é recomendação, nÃO é parecer — apenas mapeamento CID→catálogo.",
        items: {
          type: "object",
          additionalProperties: false,
          required: ["categoria_id", "justificativa", "confianca"],
          properties: {
            categoria_id: {
              type: "string",
              description: "ID da categoria (ex: bpc_loas, ciptea, educacao)",
            },
            justificativa: { type: "string", description: "Trecho LITERAL do texto (máx 80 caracteres) que motivou a menção desta categoria. Não opinar, não interpretar." },
            confianca: { type: "string", enum: ["alta", "media", "baixa"] },
          },
        },
      },
      resumo: {
        type: "string",
        description: "Resumo FACTUAL, NEUTRO e CURTO em pt-BR (máx 60 palavras, 2-3 frases) descrevendo apenas o que o texto contém: CIDs identificados, datas, condições. Use linguagem simples (nível ensino fundamental), frases curtas, sem jargão médico ou jurídico. PROIBIDO: recomendar, orientar, sugerir ação, prometer resultado, opinar sobre direito ou tratamento.",
      },
      confianca: {
        type: "string",
        enum: ["alta", "media", "baixa"],
        description: "Confiança geral da análise",
      },
    },
  },
};

const SYSTEM_PROMPT = [
  "Você é um EXTRATOR de informação textual sobre direitos de pessoas com deficiência (PcD) no Brasil.",
  "Você NÃO é advogado(a), médico(a), assistente social, perito ou consultor. Você NÃO dá parecer, NÃO recomenda, NÃO orienta, NÃO encaminha.",
  "Recebe trechos de laudos médicos JÁ ANONIMIZADOS (nome, CPF, RG, endereço, telefone foram substituídos por tokens).",
  "Única tarefa: extrair CIDs e datas LITERAIS do texto e mapear quais categorias do catálogo NossoDireito possuem base legal cobrindo esses CIDs.",
  "",
  "PÚBLICO-ALVO: pessoa leiga, sem formação jurídica ou médica. Escreva como se explicasse para alguém com ensino fundamental. Frases curtas (no máx 20 palavras). Evite jargão técnico; quando precisar usar um termo técnico, explique entre parênteses (ex.: 'CID F84 (espectro autista)').",
  "",
  "REGRAS ABSOLUTAS:",
  "1. NUNCA invente CIDs, datas, números, prazos, valores, processos ou serviços. Só reproduza o que aparece LITERALMENTE no texto.",
  "2. NUNCA faça diagnóstico médico, NUNCA recomende tratamento, NUNCA opine sobre dosagens, terapias ou prognóstico.",
  "3. NUNCA oriente ação do usuário: PROIBIDO usar verbos como 'procure', 'agende', 'solicite', 'recorra', 'peça', 'faça', 'denuncie', 'você pode', 'você tem direito', 'você deve'.",
  "4. NUNCA prometa resultado: PROIBIDO 'você terá', 'você conseguirá', 'você receberá', 'isso garante'.",
  "5. Para cada CID identificado, liste apenas categorias do catálogo cuja base legal cobre aquele CID. Em 'justificativa', cole o TRECHO LITERAL do texto (máx 80 caracteres) que motivou a menção. Não resuma, não interprete — copie.",
  "6. Confiança 'alta' apenas quando CID aparece textualmente + contexto inequívoco. Caso contrário, 'media' ou 'baixa'.",
  "7. Resumo deve ser CURTO (máx 60 palavras, 2 a 3 frases), FACTUAL, NEUTRO e em LINGUAGEM SIMPLES. Descreva apenas o que o documento contém. Ex: 'O documento cita o CID F84.0 (espectro autista) e a data 12/03/2025.' (correto) vs 'Você pode solicitar BPC' (proibido).",
  "8. Se o texto for irrelevante (não médico/jurídico), retorne arrays vazios, resumo='Texto não contém informações médicas ou jurídicas identificáveis.' e confianca='baixa'.",
  "9. NUNCA cite URLs no resumo. Se referenciar legislação, escreva apenas o nome (ex.: 'Lei 8.742/1993'); o site renderiza os links a partir do catálogo oficial.",
  "10. NUNCA cite fontes fora de .gov.br, .jus.br, .def.br, .leg.br, .mp.br, .mil.br ou icd.who.int. Em dúvida, não cite.",
  "11. NUNCA mencione, recomende ou encaminhe a profissionais, órgãos, escritórios, ONGs ou serviços no resumo. O site é catálogo de referências, não agente de encaminhamento.",
  "",
  "CATEGORIAS DISPONÍVEIS (use exatamente estes IDs):",
  "bpc_loas, ciptea, educacao, terapias_plano, terapias_sus, transporte, trabalho,",
  "fgts, habitacao, ipva, ir, prioridade_filas, tecnologia_assistiva, aposentadoria,",
  "auxilio_inclusao, meia_entrada, cotas_pcd, isencao_ipi, passe_livre",
].join("\n");

/**
 * G3 — Pós-validador da resposta da IA.
 * Verifica que nenhum URL fora da allowlist apareceu no campo `resumo`.
 * Não confia no LLM: regex agressivo sobre a string final.
 *
 * Allowlist (sincronizada com data/fontes_oficiais.json):
 *  - *.gov.br, *.planalto.gov.br, *.jus.br, *.def.br, *.leg.br, *.mp.br, *.mil.br
 *  - www.in.gov.br
 *  - icd.who.int, www.who.int
 *
 * @param {object} parsed resposta JSON já parseada
 * @returns {{ok: boolean, sanitized: object, violations: string[]}}
 */
function postValidateAIResponse(parsed) {
  const URL_RE = /https?:\/\/[^\s)>\]"'`]+/gi;
  const ALLOW_HOST_RE =
    /^(?:[a-z0-9-]+\.)*(?:gov\.br|jus\.br|def\.br|leg\.br|mp\.br|mil\.br|who\.int)$|^www\.in\.gov\.br$/i;

  const violations = [];
  const resumo = typeof parsed.resumo === "string" ? parsed.resumo : "";
  const found = resumo.match(URL_RE) || [];

  for (const url of found) {
    let host = "";
    try {
      host = new URL(url).hostname.toLowerCase();
    } catch {
      violations.push(url);
      continue;
    }
    if (!ALLOW_HOST_RE.test(host)) {
      violations.push(url);
    }
  }

  if (violations.length === 0) {
    return { ok: true, sanitized: parsed, violations: [] };
  }

  // Estratégia: remover o resumo inteiro e devolver mensagem segura.
  // Não vale a pena tentar "limpar" URLs porque o texto adjacente pode estar
  // contaminado por uma alucinação maior.
  const sanitized = {
    ...parsed,
    resumo:
      "A resposta automática foi descartada porque citou fontes fora da allowlist oficial. Consulte os direitos sugeridos abaixo, cuja Base Legal aponta para fontes verificadas.",
    confianca: "baixa",
  };
  return { ok: false, sanitized, violations };
}

function getCredential() {
  if (_credential) return _credential;
  // Em App Service usamos Managed Identity direto: pular EnvironmentCredential
  // evita ruído de "CredentialUnavailableError" em telemetria (issue #250).
  if (process.env.WEBSITE_SITE_NAME) {
    const { ManagedIdentityCredential } = require("@azure/identity");
    _credential = new ManagedIdentityCredential();
  } else {
    const { DefaultAzureCredential } = require("@azure/identity");
    _credential = new DefaultAzureCredential();
  }
  return _credential;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isTransientError(err) {
  const status = Number(err?.status || err?.statusCode || 0);
  const code = String(err?.code || "").toUpperCase();
  if ([408, 409, 425, 429, 500, 502, 503, 504].includes(status)) return true;
  return ["ETIMEDOUT", "ECONNRESET", "ECONNREFUSED", "EAI_AGAIN", "ABORT_ERR"].includes(code);
}

function markFailure(err) {
  aiCircuit.failures += 1;
  aiCircuit.lastError = String(err?.message || err || "").slice(0, 500);
  if (aiCircuit.failures >= AI_CB_FAILURE_THRESHOLD) {
    aiCircuit.openUntil = Date.now() + AI_CB_COOLDOWN_MS;
  }
}

function markSuccess() {
  aiCircuit.failures = 0;
  aiCircuit.openUntil = 0;
  aiCircuit.lastError = "";
}

function assertCircuitClosed() {
  if (Date.now() < aiCircuit.openUntil) {
    const retryAfter = Math.ceil((aiCircuit.openUntil - Date.now()) / 1000);
    const err = new Error(`AI circuit breaker open for ${retryAfter}s`);
    err.code = "CIRCUIT_OPEN";
    err.retryAfter = retryAfter;
    throw err;
  }
}

async function runWithTimeout(promiseFactory, timeoutMs) {
  let timer;
  try {
    return await Promise.race([
      promiseFactory(),
      new Promise((_, reject) => {
        timer = setTimeout(() => {
          const err = new Error(`AI timeout after ${timeoutMs}ms`);
          err.code = "ETIMEDOUT";
          reject(err);
        }, timeoutMs);
      }),
    ]);
  } finally {
    if (timer) clearTimeout(timer);
  }
}

async function createCompletionWithResilience(client, payload) {
  let attempt = 0;
  while (true) {
    attempt += 1;
    try {
      const completion = await runWithTimeout(
        () => client.chat.completions.create(payload),
        AI_TIMEOUT_MS,
      );
      markSuccess();
      return completion;
    } catch (err) {
      markFailure(err);
      if (attempt > AI_MAX_RETRIES || !isTransientError(err)) {
        throw err;
      }
      const backoff = AI_RETRY_BASE_MS * Math.pow(2, attempt - 1);
      await sleep(backoff);
    }
  }
}

function getClient() {
  if (_client) return _client;
  if (_initError) throw _initError;

  const endpoint = process.env.AZURE_OPENAI_ENDPOINT || "";
  const deployment = process.env.AZURE_OPENAI_DEPLOYMENT_NAME || "";
  const apiVersion = process.env.AZURE_OPENAI_API_VERSION || "2024-10-21";

  if (!endpoint) {
    _initError = new Error("AZURE_OPENAI_ENDPOINT not configured");
    throw _initError;
  }
  if (!deployment) {
    _initError = new Error("AZURE_OPENAI_DEPLOYMENT_NAME not configured");
    throw _initError;
  }

  try {
    const { AzureOpenAI } = require("openai");
    const { getBearerTokenProvider } = require("@azure/identity");

    const azureADTokenProvider = getBearerTokenProvider(
      getCredential(),
      "https://cognitiveservices.azure.com/.default",
    );

    _client = new AzureOpenAI({
      endpoint,
      apiVersion,
      deployment,
      azureADTokenProvider,
    });
    return _client;
  } catch (err) {
    _initError = new Error(`Failed to init Azure OpenAI client: ${err.message}`);
    throw _initError;
  }
}

/**
 * Analisa texto via Azure OpenAI (gpt-4o-mini) com Structured Outputs.
 *
 * @param {string} anonymizedText Texto JÁ ANONIMIZADO
 */
async function analyzeText(anonymizedText) {
  assertCircuitClosed();
  const t0 = Date.now();
  const contentHash = crypto.createHash("sha256").update(anonymizedText).digest("hex").slice(0, 16);

  // Truncar texto para proteger budget (gpt-4o-mini context 128K mas
  // input grande = custo). 8K chars ~= 2K tokens cobre laudos comuns.
  const MAX_CHARS = 8000;
  const text = anonymizedText.length > MAX_CHARS
    ? anonymizedText.slice(0, MAX_CHARS) + "\n[...truncado]"
    : anonymizedText;

  const client = getClient();
  const deployment = process.env.AZURE_OPENAI_DEPLOYMENT_NAME;

  const completion = await createCompletionWithResilience(client, {
    model: deployment,
    messages: [
      { role: "system", content: SYSTEM_PROMPT },
      { role: "user", content: `LAUDO ANONIMIZADO:\n\n${text}` },
    ],
    temperature: 0.1,
    max_tokens: 1500,
    response_format: {
      type: "json_schema",
      json_schema: ANALYSIS_JSON_SCHEMA,
    },
  });

  const raw = completion.choices?.[0]?.message?.content || "{}";
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch {
    parsed = {
      cids: [],
      datas: [],
      diagnosticos: [],
      direitos_sugeridos: [],
      resumo: "Não foi possível interpretar a resposta do modelo.",
      confianca: "baixa",
    };
  }

  // G3: descartar resumo se conter URLs fora da allowlist (sanitização defensiva).
  const validation = postValidateAIResponse(parsed);
  parsed = validation.sanitized;
  const allowlistViolations = validation.violations;

  return {
    contentHash,
    durationMs: Date.now() - t0,
    model: deployment,
    cids: parsed.cids || [],
    datas: parsed.datas || [],
    diagnosticos: parsed.diagnosticos || [],
    direitos_sugeridos: parsed.direitos_sugeridos || [],
    resumo: parsed.resumo || "",
    confianca: parsed.confianca || "baixa",
    allowlistViolations,
    tokens: {
      input: completion.usage?.prompt_tokens || 0,
      output: completion.usage?.completion_tokens || 0,
    },
  };
}

function getAIHealth() {
  const configured = Boolean(
    process.env.AZURE_OPENAI_ENDPOINT && process.env.AZURE_OPENAI_DEPLOYMENT_NAME,
  );
  const circuitOpen = Date.now() < aiCircuit.openUntil;
  return {
    enabled: process.env.AI_ANALYSIS_ENABLED === "true",
    configured,
    circuitOpen,
    retryAfterSeconds: circuitOpen ? Math.ceil((aiCircuit.openUntil - Date.now()) / 1000) : 0,
    timeoutMs: AI_TIMEOUT_MS,
    maxRetries: AI_MAX_RETRIES,
    lastError: aiCircuit.lastError,
  };
}

module.exports = { analyzeText, getAIHealth, postValidateAIResponse };
