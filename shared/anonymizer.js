/**
 * Anonimizador de PII para fluxo IA opt-in (LGPD Art. 12).
 *
 * Roda em DOIS ambientes:
 *  - Browser (carregado via <script> em document.html antes do POST)
 *  - Node.js / server.js (double-check antes de chamar Azure OpenAI)
 *
 * Funciona tanto sem build (CommonJS para Node + global window.Anonymizer
 * para browser via UMD pattern simples).
 *
 * Princípio: a IA recebe apenas TEXTO TÉCNICO (CIDs, datas, estrutura),
 * nunca dados que identifiquem a pessoa.
 *
 * Padrões reconhecidos (Brasil-first):
 *  - CPF (com/sem máscara) ........... [CPF]
 *  - RG (8-10 dígitos + UF opcional) . [RG]
 *  - CNPJ ............................ [CNPJ]
 *  - CEP ............................. [CEP]
 *  - Telefone (fixo/celular) ......... [FONE]
 *  - E-mail .......................... [EMAIL]
 *  - Cartão SUS (15 dígitos) ......... [CNS]
 *  - Data de nascimento ("nasc.:") ... [DATA_NASC]
 *  - Nome após rótulo ("Nome:", etc.) [NOME]
 *  - Endereço após "Endereço:" ....... [ENDERECO]
 *
 * NÃO removidos (necessários para análise médica):
 *  - CID-10/11 (ex: F84.0, Q90)
 *  - Datas genéricas no corpo (laudo precisa de timeline)
 *  - Termos médicos / siglas técnicas
 */

(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory(); // Node.js
  } else {
    root.Anonymizer = factory(); // Browser
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  // Ordem importa: padrões mais específicos ANTES de genéricos
  // (ex: CNPJ antes de CPF para não consumir 11 dígitos do CNPJ como CPF).
  const PATTERNS = [
    // CNPJ: XX.XXX.XXX/XXXX-XX ou 14 dígitos contíguos
    { name: "CNPJ", re: /\b\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2}\b/g, token: "[CNPJ]" },

    // Cartão Nacional de Saúde (CNS / SUS): 15 dígitos
    { name: "CNS", re: /\b\d{3}\s?\d{4}\s?\d{4}\s?\d{4}\b/g, token: "[CNS]" },

    // CPF: XXX.XXX.XXX-XX ou 11 dígitos contíguos
    { name: "CPF", re: /\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b/g, token: "[CPF]" },

    // RG com SSP/UF: "12.345.678-9 SSP/SP" ou "12345678 X"
    {
      name: "RG",
      re: /\b\d{1,2}\.?\d{3}\.?\d{3}-?[\dXx]\b(?:\s*(?:SSP|SESP|DETRAN|IFP|IGP|PC)[\/\s-]?[A-Z]{2})?/g,
      token: "[RG]",
    },

    // CEP: XXXXX-XXX ou 8 dígitos
    { name: "CEP", re: /\b\d{5}-?\d{3}\b/g, token: "[CEP]" },

    // Telefone fixo/celular: (XX) 9XXXX-XXXX, +55 XX XXXX-XXXX, etc.
    { name: "FONE", re: /(?:\+?55\s?)?\(?\d{2}\)?\s?9?\d{4}-?\d{4}\b/g, token: "[FONE]" },

    // E-mail
    { name: "EMAIL", re: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g, token: "[EMAIL]" },

    // Filiação ANTES de NOME — "Nome da mãe" deve casar aqui primeiro
    {
      name: "FILIACAO",
      re: /\b(filia[çc][ãa]o|nome da m[ãa]e|nome do pai|m[ãa]e|pai)\s*:\s*([A-ZÀ-Úa-zà-ÿ][A-Za-zÀ-ÿ\s.'-]{2,79})/gi,
      replace: (m, label) => `${label}: [FILIACAO]`,
    },

    // Nome após rótulo: "Nome:", "Paciente:", "Beneficiário:" — exige `:` literal
    // (sem `:` o "i" flag faria "Paciente diagnosticado com F84.0" virar "Paciente: [NOME]84.0")
    {
      name: "NOME",
      re: /\b(nome(?:\s+(?:do\s+)?paciente)?|paciente|beneficiári[oa]|usuári[oa]|requerente)\s*:\s*([A-ZÀ-Úa-zà-ÿ][A-Za-zÀ-ÿ\s.'-]{2,79})/gi,
      replace: (m, label) => `${label}: [NOME]`,
    },

    // Data de nascimento: "Nasc.:", "Nascido em", "DN:", "Data de nascimento:"
    {
      name: "DATA_NASC",
      re: /\b(nasc(?:imento|ido em)?|dn|data\s+de\s+nascimento)[\s.:]+\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4}/gi,
      replace: (m) => m.split(/[\s.:]+/)[0] + ": [DATA_NASC]",
    },

    // Endereço após rótulo — primeiro char da captura NÃO pode ser `[` (idempotência:
    // evita re-capturar "[ENDERECO]" no segundo passe).
    {
      name: "ENDERECO",
      re: /\b(endereç?o|residente em|domicili?o)\s*:\s+([^\[\s\n\r][^\n\r]{4,149})/gi,
      replace: (m, label) => `${label}: [ENDERECO]`,
    },
  ];

  /**
   * Anonimiza texto removendo PII identificada por padrões regex.
   * Idempotente: rodar 2x produz o mesmo resultado (tokens não viram nada novo).
   *
   * @param {string} text Texto bruto extraído do documento
   * @returns {{text: string, stats: Object<string, number>}}
   *   text: texto anonimizado
   *   stats: contagem de cada padrão aplicado (auditoria/telemetria)
   */
  function anonymize(text) {
    if (typeof text !== "string") {
      return { text: "", stats: {} };
    }

    const stats = {};
    let out = text;

    for (const pat of PATTERNS) {
      let count = 0;
      if (pat.replace) {
        out = out.replace(pat.re, (...args) => {
          count++;
          return pat.replace(...args);
        });
      } else {
        out = out.replace(pat.re, () => {
          count++;
          return pat.token;
        });
      }
      if (count > 0) stats[pat.name] = count;
    }

    return { text: out, stats };
  }

  /**
   * Verifica se um texto AINDA contém PII (após anonimização).
   * Usado pelo server.js como double-check antes de chamar Azure OpenAI.
   *
   * @param {string} text
   * @returns {{clean: boolean, found: string[]}}
   */
  function containsPII(text) {
    if (typeof text !== "string") return { clean: true, found: [] };
    const found = [];
    for (const pat of PATTERNS) {
      // Reset regex (g flag tem state)
      pat.re.lastIndex = 0;
      if (pat.re.test(text)) found.push(pat.name);
    }
    return { clean: found.length === 0, found };
  }

  return { anonymize, containsPII, PATTERNS };
});
