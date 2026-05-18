/**
 * services/doc-intelligence.js
 *
 * Cliente Azure OpenAI (gpt-4o-mini) para análise IA de laudos PcD.
 *
 * @deprecated Nome legado (era Doc Intelligence até v1.17.0). Em v1.18.0
 * a implementação interna foi trocada para Azure OpenAI Chat Completions
 * porque `prebuilt-read` é OCR e rejeitava text/plain. O arquivo mantém
 * o nome para minimizar diff de import no server.js — será renomeado
 * para services/ai-analysis.js em uma futura release de cleanup.
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
        description: "Categorias de direitos sugeridos com base no diagnóstico",
        items: {
          type: "object",
          additionalProperties: false,
          required: ["categoria_id", "justificativa", "confianca"],
          properties: {
            categoria_id: {
              type: "string",
              description: "ID da categoria (ex: bpc_loas, ciptea, educacao)",
            },
            justificativa: { type: "string", description: "Por que se aplica, em 1 frase" },
            confianca: { type: "string", enum: ["alta", "media", "baixa"] },
          },
        },
      },
      resumo: {
        type: "string",
        description: "Resumo orientativo em pt-BR (max 200 palavras)",
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
  "Você é assistente de orientação em direitos de pessoas com deficiência (PcD) no Brasil.",
  "Recebe trechos de laudos médicos JÁ ANONIMIZADOS (nome, CPF, RG, endereço, telefone foram substituídos por tokens).",
  "Tarefa: extrair CIDs, datas e sugerir categorias de direitos aplicáveis.",
  "",
  "REGRAS:",
  "1. NÃO invente CIDs. Só liste códigos que aparecem literalmente no texto.",
  "2. NÃO faça diagnóstico médico. NÃO recomende tratamento. NÃO opine sobre dosagens.",
  "3. Para cada CID válido, sugira categorias de direitos do catálogo PcD brasileiro.",
  "4. Use confiança 'alta' apenas quando CID + contexto explicitam a condição.",
  "5. Resumo deve ser informativo, neutro, em pt-BR — lembre que NÃO substitui orientação profissional.",
  "6. Se o texto for irrelevante (não médico/jurídico), retorne arrays vazios e confianca='baixa'.",
  "",
  "CATEGORIAS DISPONÍVEIS (use exatamente estes IDs):",
  "bpc_loas, ciptea, educacao, terapias_plano, terapias_sus, transporte, trabalho,",
  "fgts, habitacao, ipva, ir, prioridade_filas, tecnologia_assistiva, aposentadoria,",
  "auxilio_inclusao, meia_entrada, cotas_pcd, isencao_ipi, passe_livre",
].join("\n");

function getCredential() {
  if (_credential) return _credential;
  const { DefaultAzureCredential } = require("@azure/identity");
  _credential = new DefaultAzureCredential();
  return _credential;
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

  const completion = await client.chat.completions.create({
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
    tokens: {
      input: completion.usage?.prompt_tokens || 0,
      output: completion.usage?.completion_tokens || 0,
    },
  };
}

module.exports = { analyzeText };
