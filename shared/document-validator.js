/**
 * document-validator.js — heurística multidimensional para validar se o texto
 * extraído de um PDF/imagem é realmente um documento clínico/médico antes de
 * alimentá-lo ao motor de sugestão de direitos (matchRights).
 *
 * Motivação: antes deste módulo, o gate era um `medicalTerms.some(t => txt.includes(t))`
 * sobre ~40 palavras. Bastava UMA ocorrência ("paciente", "médico", "deficiência")
 * para passar — então boletos de plano de saúde, manuais de remédio, cardápios de
 * hospital e até boletins escolares com a palavra "deficiência" entravam e geravam
 * sugestões erradas. Erro semântico inaceitável para conteúdo PcD.
 *
 * Estratégia: scorar 4 dimensões e exigir score mínimo + presença de pelo menos
 * UM sinal "forte" (CRM/conselho profissional OU código CID válido). Isso evita
 * tanto falsos positivos (qualquer texto com 1 palavra clínica) quanto falsos
 * negativos (laudo legítimo sem CRM mas com CID).
 *
 *   A. Identificação profissional .... CRM/CRP/COFFITO/CRF[A]?/CREFITO/CRO/CRN  → +3
 *   B. Código diagnóstico válido ..... CID-10 (A99.9) ou CID-11 (8A00 / 6A02.0) → +3
 *   C. Tipo de documento clínico ..... "laudo médico", "atestado médico", etc.   → +2 cada (cap 4)
 *   D. Vocabulário clínico ........... paciente, diagnóstico, prognóstico, …    → +1 cada (cap 3)
 *
 * Aprovação: score total >= 5 E (A presente OU B presente).
 *
 * Roda em DOIS ambientes (UMD): browser (via window.DocumentValidator) e Node
 * (via require). Sem dependências externas.
 */

(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory(); // Node.js
  } else {
    root.DocumentValidator = factory(); // Browser
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  // ── A. Identificação profissional (peso 3) ──
  // CRM/CRP/COFFITO/CRF/CRFA/CREFITO/CRO/CRN/CREFONO. Após o conselho aceita:
  //   - UF opcional (2 letras maiúsculas: CRM/SP 123456)
  //   - OU número regional opcional (1-3 dígitos: CRP 06/12345, COFFITO 12345)
  // Tudo separado por espaço, barra ou hífen. Termina em 4-7 dígitos.
  const PROFESSIONAL_REGISTRY_RE =
    /\b(CRM|CRP|COFFITO|CRF[A]?|CREFITO|CRO|CRN|CREFONO)[\s\/\-]*(?:[A-Z]{2}|\d{1,3})?[\s\/\-]*\d{4,7}\b/i;

  // ── B. Código diagnóstico válido (peso 3) ──
  // CID-10: letra + 2 dígitos + opcional .D ou .DD (ex.: F84, F84.0, Q90.9)
  // CID-11: dígito + letra + 2 alfanuméricos + opcional .D (ex.: 6A02, 6A02.0, 8A00)
  // Token boundary com espaços/pontuação para evitar casar "abcF84.0" em URLs.
  const CID10_RE = /(?:^|[\s,.;:()\[\]\/\-])([A-Z]\d{2}(?:\.\d{1,2})?)(?=$|[\s,.;:()\[\]\/\-])/g;
  const CID11_RE = /(?:^|[\s,.;:()\[\]\/\-])(\d[A-Z][0-9A-Z]{2}(?:\.\d{1,2})?)(?=$|[\s,.;:()\[\]\/\-])/g;

  // ── C. Tipo de documento clínico (peso 2 cada, cap 4) ──
  // Frases nominais que tipificam o documento. Exigem o substantivo + qualificador
  // clínico/médico/técnico — evita matchar "atestado de comparecimento", "laudo pericial
  // ambiental", "relatório financeiro", etc.
  const CLINICAL_DOC_TYPES = [
    /\blaudo\s+m[eé]dico\b/i,
    /\blaudo\s+cl[ií]nico\b/i,
    /\blaudo\s+(?:neuro|psiqui|psicol[oó]g|fisio|fonoaudiol[oó]g|terap[eê]ut)/i,
    /\blaudo\s+pericial\s+m[eé]dico\b/i,
    /\batestado\s+m[eé]dico\b/i,
    /\bdeclara[cç][aã]o\s+m[eé]dica\b/i,
    /\brelat[oó]rio\s+m[eé]dico\b/i,
    /\brelat[oó]rio\s+(?:neuro|psiqui|psicol[oó]g|fisio|fonoaudiol[oó]g|terap[eê]ut)/i,
    /\bparecer\s+(?:m[eé]dico|t[eé]cnico\s+m[eé]dico|cl[ií]nico)\b/i,
    /\bprontu[aá]rio\s+m[eé]dico\b/i,
    /\banamnese\b/i,
    /\bevolu[cç][aã]o\s+cl[ií]nica\b/i,
    /\breceitu[aá]rio\s+m[eé]dico\b/i,
  ];

  // ── D. Vocabulário clínico (peso 1 cada, cap 3, sem repetição) ──
  // Palavras isoladas que, em conjunto, indicam contexto clínico. NUNCA decisivas
  // sozinhas — exigem corroboração por A ou B.
  const CLINICAL_VOCABULARY = [
    /\bdiagn[oó]stico\b/i,
    /\bprogn[oó]stico\b/i,
    /\bprescri[cç][aã]o\b/i,
    /\banamnese\b/i,
    /\bsinais?\s+cl[ií]nicos?\b/i,
    /\bsintomas?\b/i,
    /\bencaminhamento\s+(?:para|ao|à|aos|às)?\s*(?:especialista|terapia|m[eé]dico)/i,
    /\bhip[oó]tese\s+diagn[oó]stica\b/i,
    /\bevolu[cç][aã]o\s+(?:cl[ií]nica|do\s+paciente)\b/i,
    /\bquadro\s+(?:cl[ií]nico|psiqui[aá]trico|neurol[oó]gico)\b/i,
    /\bavalia[cç][aã]o\s+(?:cl[ií]nica|m[eé]dica|neuro|psicol[oó]gica)/i,
    /\bcomorbidades?\b/i,
    /\bterapia\s+(?:ocupacional|cognitivo|comportamental|fonoaudiol[oó]gica)/i,
    /\bcondu[tç][aã]o\s+terap[eê]utica\b/i,
  ];

  // Cap por dimensão (evita inflar score com repetição da mesma evidência).
  const CAP_C = 4;
  const CAP_D = 3;
  const MIN_SCORE = 5;

  /**
   * @param {string} text — texto bruto extraído do(s) arquivo(s).
   * @returns {{
   *   accepted: boolean,
   *   score: number,
   *   signals: {
   *     professional: boolean,
   *     cid: boolean,
   *     docTypes: string[],
   *     vocabulary: string[]
   *   },
   *   reasons: string[]    — lista de razões legíveis para rejeição (vazio se accepted)
   * }}
   */
  function validate(text) {
    const signals = {
      professional: false,
      cid: false,
      docTypes: [],
      vocabulary: [],
    };

    if (typeof text !== "string" || text.length === 0) {
      return {
        accepted: false,
        score: 0,
        signals,
        reasons: ["Texto vazio ou não extraído do arquivo."],
      };
    }

    let score = 0;

    // A. Conselho profissional
    if (PROFESSIONAL_REGISTRY_RE.test(text)) {
      signals.professional = true;
      score += 3;
    }

    // B. CID válido (CID-10 OU CID-11). Reset regex (g flag tem state).
    CID10_RE.lastIndex = 0;
    CID11_RE.lastIndex = 0;
    if (CID10_RE.test(text) || CID11_RE.test(text)) {
      signals.cid = true;
      score += 3;
    }

    // C. Tipo de documento (com cap)
    let cScore = 0;
    for (const re of CLINICAL_DOC_TYPES) {
      const m = text.match(re);
      if (m) {
        signals.docTypes.push(m[0].trim().toLowerCase());
        cScore += 2;
        if (cScore >= CAP_C) break;
      }
    }
    score += Math.min(cScore, CAP_C);

    // D. Vocabulário (com cap, sem repetição da mesma regex)
    let dScore = 0;
    for (const re of CLINICAL_VOCABULARY) {
      const m = text.match(re);
      if (m) {
        signals.vocabulary.push(m[0].trim().toLowerCase());
        dScore += 1;
        if (dScore >= CAP_D) break;
      }
    }
    score += Math.min(dScore, CAP_D);

    // Regra de aprovação: score mínimo E sinal forte presente.
    const hasStrongSignal = signals.professional || signals.cid;
    const accepted = score >= MIN_SCORE && hasStrongSignal;

    const reasons = [];
    if (!accepted) {
      if (!hasStrongSignal) {
        reasons.push(
          "Falta identificação profissional (CRM/CRP/COFFITO/CRF) ou código CID válido (ex.: F84.0, Q90)."
        );
      }
      if (score < MIN_SCORE) {
        reasons.push(
          `Texto não tem evidência suficiente de documento clínico (pontuação ${score}/${MIN_SCORE}).`
        );
      }
    }

    return { accepted, score, signals, reasons };
  }

  return {
    validate,
    // Exposto para testes e auditoria.
    _internals: {
      PROFESSIONAL_REGISTRY_RE,
      CID10_RE,
      CID11_RE,
      CLINICAL_DOC_TYPES,
      CLINICAL_VOCABULARY,
      MIN_SCORE,
      CAP_C,
      CAP_D,
    },
  };
});
