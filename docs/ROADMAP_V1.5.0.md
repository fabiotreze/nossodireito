# ROADMAP v1.5.0 — Expansão de Cobertura de Benefícios

**Versão:** 1.5.0  
**Data de Início:** 11 de fevereiro de 2026  
**Prazo:** 4-6 semanas (até 25 de março de 2026)  
**Responsável:** Fabio Treze  
**Meta:** Atingir **80% de cobertura** (25/31 benefícios)

---

## 📋 Escopo do Projeto

### Objetivos

1. ✅ **Integrar IPVA Estadual** — dropdown com 27 estados em `isencoes_tributarias`
2. ✅ **Implementar 4 benefícios ALTA prioridade:**
   - ProUni/FIES/SISU - Cotas PcD
   - Isenção Imposto de Renda (despesas médicas)
   - Bolsa Família para PcD
   - Defensoria Pública (expandir seção existente)

### Esforço Estimado

| Atividade | Horas | Responsável |
|-----------|-------|-------------|
| **1. IPVA Estadual** | 15h | Fabio |
| - Preparar dados (ipva_pcd_estados.json) | 2h | |
| - Adicionar a direitos.json | 4h | |
| - Implementar dropdown frontend | 6h | |
| - Testes e validação | 3h | |
| **2. ProUni/FIES/SISU** | 12h | Fabio |
| - Pesquisa legal (leis, editais) | 3h | |
| - Estruturar direitos.json | 4h | |
| - Matching_engine + frontend | 3h | |
| - Testes | 2h | |
| **3. Isenção Imposto de Renda** | 10h | Fabio |
| - Pesquisa legal (Lei 7.713/88) | 2h | |
| - Estruturar direitos.json | 3h | |
| - Matching_engine + frontend | 3h | |
| - Testes | 2h | |
| **4. Bolsa Família PcD** | 10h | Fabio |
| - Pesquisa legal (Lei 14.284/2021) | 2h | |
| - Estruturar direitos.json | 3h | |
| - Matching_engine + frontend | 3h | |
| - Testes | 2h | |
| **5. Defensoria Pública (expandir)** | 6h | Fabio |
| - Pesquisa (LC 80/1994, leis estaduais) | 2h | |
| - Expandir atendimento_prioritario | 2h | |
| - Testes | 2h | |
| **6. Documentação e Compliance** | 4h | Fabio |
| - Atualizar CHANGELOG.md | 1h | |
| - Atualizar COMPLIANCE.md §10 | 1h | |
| - Atualizar DEPENDENCY_CONTROL.md | 1h | |
| - Testes finais QA | 1h | |
| **TOTAL** | **57 horas** | |

---

## 🎯 Deliverables

### Arquivos Modificados

1. **data/direitos.json** (+5 categorias ou expansões)
2. **data/matching_engine.json** (+200-300 termos)
3. **js/app.js** (renderização dropdown IPVA)
4. **index.html** (se necessário ajustes CSS/HTML)
5. **sw.js** (atualizar cache v1.5.0)
6. **package.json** (versão 1.4.3 → 1.5.0)
7. **CHANGELOG.md** (nova seção [1.5.0])
8. **docs/COMPLIANCE.md** (atualizar §10)

### Arquivos Deletados

- ❌ `data/ipva_pcd_estados.json` (conteúdo integrado em direitos.json)

---

## 📆 Cronograma (4-6 semanas)

### Semana 1-2 (11-24 fev): IPVA Estadual + ProUni/FIES/SISU

- [ ] **11 fev:** Preparar dados IPVA (estrutura dropdown)
- [ ] **12-13 fev:** Adicionar IPVA estadual a isencoes_tributarias
- [ ] **14-15 fev:** Implementar dropdown frontend (HTML + JS)
- [ ] **16-17 fev:** Testes IPVA + QA
- [ ] **18-19 fev:** Pesquisa ProUni/FIES/SISU (leis, editais, fontes)
- [ ] **20-21 fev:** Estruturar ProUni/FIES/SISU em direitos.json
- [ ] **22-24 fev:** Frontend + matching_engine + testes

### Semana 3-4 (25 fev - 10 mar): Isenção IR + Bolsa Família

- [ ] **25-26 fev:** Pesquisa Isenção IR (Lei 7.713/88, RFB)
- [ ] **27-28 fev:** Estruturar Isenção IR em direitos.json
- [ ] **01-02 mar:** Frontend + matching_engine + testes
- [ ] **03-04 mar:** Pesquisa Bolsa Família PcD (Lei 14.284/2021, Cadastro Único)
- [ ] **05-06 mar:** Estruturar Bolsa Família em direitos.json
- [ ] **07-10 mar:** Frontend + matching_engine + testes

### Semana 5-6 (11-25 mar): Defensoria + Documentação + QA

- [ ] **11-12 mar:** Pesquisa Defensoria Pública (LC 80/1994, sites estaduais)
- [ ] **13-14 mar:** Expandir atendimento_prioritario (Defensoria)
- [ ] **15-16 mar:** Testes Defensoria
- [ ] **17-18 mar:** Atualizar CHANGELOG, COMPLIANCE, DEPENDENCY_CONTROL
- [ ] **19-21 mar:** Testes finais QA (todos os 5 novos benefícios)
- [ ] **22-23 mar:** Correções de bugs
- [ ] **24-25 mar:** Deploy v1.5.0 + anúncio

---

## 🔬 Critérios de Aceitação

### IPVA Estadual

- [ ] Dropdown com 27 estados funcionando
- [ ] Ao selecionar estado, exibir:
  - Lei estadual (nome + artigo)
  - Link SEFAZ do estado
  - Condições resumo
  - Limite de valor (se aplicável)
- [ ] Dados carregados de direitos.json (não mais ipva_pcd_estados.json)
- [ ] Responsivo (mobile-first)

### ProUni/FIES/SISU

- [ ] Informações completas:
  - Base legal (Lei 11.096/2005 ProUni, Lei 10.260/2001 FIES, Portaria SISU)
  - Requisitos (renda, pontuação ENEM, etc.)
  - Documentos necessários
  - Links oficiais (MEC, FNDE, SISU)
  - Como solicitar (passo a passo)
- [ ] Termos de busca: "prouni pcd", "fies deficiência", "sisu cotas", "ensino superior", "faculdade gratuita"

### Isenção Imposto de Renda

- [ ] Informações completas:
  - Base legal (Lei 7.713/88 Art. 6º XIV)
  - Despesas dedutíveis (médicas, terapias, adaptações)
  - Requisitos (laudo médico, comprovantes)
  - Documentos necessários
  - Links oficiais (Receita Federal)
  - Como declarar (passo a passo IRPF)
- [ ] Termos de busca: "imposto renda pcd", "dedução despesas médicas", "irpf deficiência", "declaração ir"

### Bolsa Família PcD

- [ ] Informações completas:
  - Base legal (Lei 14.284/2021, Decreto 11.016/2022)
  - Requisitos (renda, CadÚnico, BPC articulação)
  - Documentos necessários
  - Links oficiais (Ministério do Desenvolvimento Social, CadÚnico)
  - Como solicitar (CRAS passo a passo)
- [ ] Termos de busca: "bolsa família pcd", "cadastro único", "bpc loas bolsa", "auxílio brasil deficiência"

### Defensoria Pública (expandir)

- [ ] Expandir `atendimento_prioritario` com seção específica "Defensoria Pública"
- [ ] Informações completas:
  - Base legal (LC 80/1994, Constituição Art. 134)
  - Serviços gratuitos (orientação jurídica, ações judiciais, recursos)
  - Requisitos (baixa renda - até 3 salários mínimos varia por estado)
  - Links oficiais (Defensoria União + 27 Defensorias Estaduais)
  - Como solicitar (agendamento presencial/online)
- [ ] Termos de busca: "defensoria pública pcd", "advocacia gratuita", "orientação jurídica", "ação judicial deficiência"

---

## 📊 Métricas de Sucesso

| Métrica | Antes (v1.4.3) | Meta (v1.5.0) | Status |
|---------|---------------|---------------|--------|
| Benefícios implementados | 17/31 (54.8%) | 22/31 (71.0%) | ⏳ |
| Benefícios ALTA prioridade | 13/17 (76.5%) | 17/17 (100%) | ⏳ |
| Cobertura total (completa + parcial) | 67.7% | **80%+** | ⏳ |
| Links funcionando | 92.6% (75/81) | 95%+ | ⏳ |
| Termos de busca (matching_engine) | ~2700 | ~3000+ | ⏳ |

---

## 🚨 Riscos e Mitigação

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| **Legislação desatualizada** | MÉDIA | MÉDIO | Validar links oficiais, incluir disclaimers, próxima revisão em 7 dias |
| **Complexidade IPVA dropdown** | BAIXA | MÉDIO | POC primeiro (3 estados), depois escalar para 27 |
| **Escopo creep** | MÉDIA | ALTO | Manter foco nos 5 itens. Não adicionar features não planejadas |
| **Falta de tempo (~57h)** | MÉDIA | ALTO | Priorizar: IPVA → ProUni → IR → Bolsa → Defensoria. Se atraso, remover Defensoria para v1.6.0 |

---

## 📝 Notas de Implementação

### IPVA Estadual - Estrutura Proposta

```json
{
  "id": "isencoes_tributarias",
  "titulo": "Isenções Tributárias — IPI, IOF, ICMS, IPVA e IPTU",
  // ... conteúdo existente ...
  "ipva_estadual": {
    "titulo": "Isenção de IPVA por Estado (Selecione sua UF)",
    "estados": [
      {
        "uf": "AC",
        "nome": "Acre",
        "lei": "Lei Complementar nº 114/2002",
        "artigo": "Art. 7º",
        "condicoes": "Isenção para veículo de propriedade de PcD. Veículo único. Laudo médico e veículo adaptado.",
        "limite_valor": "Segue Convênio CONFAZ",
        "url_sefaz": "https://sefaznet.ac.gov.br/"
      },
      // ... 26 estados restantes ...
    ],
    "aviso": "ATENÇÃO: Legislação tributária muda frequentemente. Sempre confirme na SEFAZ do seu estado antes de requerer isenção."
  }
}
```

### ProUni/FIES/SISU - Estrutura Proposta

```json
{
  "id": "prouni_fies_sisu",
  "categoria": "Educação",
  "titulo": "ProUni, FIES e SISU — Cotas para Pessoas com Deficiência",
  "o_que_e": "Programas federais de acesso ao ensino superior que reservam vagas e oferecem bolsas para pessoas com deficiência.",
  "quem_tem_direito": [
    "Pessoa com deficiência (física, auditiva, visual, intelectual, TEA)",
    "Renda familiar per capita até 1,5 salário mínimo (ProUni integral)",
    "Renda familiar per capita até 3 salários mínimos (ProUni parcial)",
    "ENEM mínimo 450 pontos (média) e nota redação > 0"
  ],
  "base_legal": [
    {
      "lei": "Lei  11.096/2005 (ProUni)",
      "link": "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2005/lei/l11096.htm",
      "artigo": "Art. 2º, III"
    },
    {
      "lei": "Lei 10.260/2001 (FIES)",
      "link": "https://www.planalto.gov.br/ccivil_03/leis/leis_2001/l10260.htm"
    },
    {
      "lei": "Portaria MEC nº 389/2013 (SISU)",
      "link": "http://portal.mec.gov.br/sisu"
    }
  ],
  "como_funciona": {
    "prouni": "Bolsa integral (100%) ou parcial (50%) em universidades privadas",
    "fies": "Financiamento estudantil com juros baixos",
    "sisu": "Sistema de seleção para universidades públicas (vagas via ENEM)"
  },
  "documentos": ["laudo_medico", "comprovante_deficiencia", "comprovante_renda", "cpf", "rg"],
  "links_oficiais": [
    {
      "titulo": "ProUni — Site Oficial",
      "url": "http://prouniportal.mec.gov.br/"
    },
    {
      "titulo": "FIES — Site Oficial",
      "url": "http://fies.mec.gov.br/"
    },
    {
      "titulo": "SISU — Site Oficial",
      "url": "http://sisu.mec.gov.br/"
    }
  ],
  "matching_keywords": ["prouni", "fies", "sisu", "faculdade", "universidade", "ensino superior", "bolsa estudo", "financiamento estudantil", "cotas pcd"]
}
```

---

## 🔄 Processo de Desenvolvimento

1. ✅ **Pesquisa Legal** (leis, decretos, portarias, sites oficiais)
2. ✅ **Estruturar JSON** (direitos.json com base_legal, requisitos, documentos, links)
3. ✅ **Matching Engine** (adicionar termos de busca)
4. ✅ **Frontend** (renderização, dropdown se aplicável)
5. ✅ **Testes** (busca, links, responsivo, acessibilidade)
6. ✅ **Documentação** (CHANGELOG, COMPLIANCE)
7. ✅ **QA Final** (validação JSON, links, selenium tests)

---

## 📚 Referências

### Legislação

- **ProUni:** Lei 11.096/2005, Decreto 5.493/2005
- **FIES:** Lei 10.260/2001, Portaria MEC nº 209/2018
- **SISU:** Portaria Normativa MEC nº 21/2012, Portaria 389/2013
- **IR:** Lei 7.713/88 Art. 6º XIV, Instrução Normativa RFB 2065/2022
- **Bolsa Família:** Lei 14.284/2021, Decreto 11.016/2022
- **Defensoria:** LC 80/1994, Constituição Art. 134

### Sites Oficiais

- MEC: http://portal.mec.gov.br
- Receita Federal: https://www.gov.br/receitafederal
- Ministério do Desenvolvimento Social: https://www.gov.br/cidadania
- DPU (Defensoria União): https://www.dpu.def.br/
- CONFAZ (IPVA/ICMS): https://www.gov.br/pgfn/pt-br/.../confaz

---

**Aprovado por:** Fabio Treze  
**Data de Aprovação:** 11 de fevereiro de 2026  
**Status:** ✅ APROVADO — Iniciar implementação
