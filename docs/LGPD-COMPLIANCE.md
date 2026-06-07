# LGPD Compliance — Checklist Auditável

Documento único e auditável de conformidade do portal NossoDireito com a Lei
Geral de Proteção de Dados (Lei 13.709/2018) e com a postura editorial pública
de avisos legais, disclaimers e termos de uso informativos.

Este documento é a fonte única de verdade da revisão pedida no
[#189](https://github.com/fabiotreze/nossodireito/issues/189). Quaisquer textos
no produto (UI, README, docs operacionais) devem ser coerentes com o que está
aqui.

## 1. Escopo e premissas

- Portal informativo, conteúdo educacional sobre direitos de pessoas com
  deficiência no Brasil.
- Hospedagem em Azure App Service na região `brazilsouth` (LGPD Art. 33 — dados
  permanecem em território nacional).
- Operação por pessoa natural com finalidade não econômica
  (LGPD Art. 4º, I), sem comercialização de dados.
- Sem coleta de dados pessoais por padrão. Análise por IA é estritamente opt-in.

## 2. Bases legais utilizadas

| Tratamento | Base legal | Referência |
|------------|------------|------------|
| Navegação geral, leitura de conteúdo | Não há tratamento de dado pessoal | LGPD Art. 5º I (não aplicável) |
| Análise opcional de documento por IA | Consentimento livre, informado e específico | LGPD Art. 7º, I e Art. 8º |
| Anonimização técnica antes do envio à IA | Anonimização (não é dado pessoal) | LGPD Art. 12 |

## 3. Direitos do titular (Art. 18)

A UI permanente do site informa e operacionaliza:

- Confirmação da existência de tratamento (Art. 18, I).
- Acesso aos dados tratados (Art. 18, II).
- Correção (Art. 18, III).
- Anonimização, bloqueio ou eliminação (Art. 18, IV).
- Eliminação dos dados tratados com consentimento (Art. 18, VI).
- Informação sobre compartilhamento (Art. 18, VII).
- Informação sobre a possibilidade de não fornecer consentimento e suas
  consequências (Art. 18, VIII).
- Revogação do consentimento (Art. 18, IX e Art. 8º, §5).

Operacionalmente:

- Botão permanente de revogação de consentimento de IA está sempre visível.
- A revogação é imediata, local (limpa armazenamento do navegador) e não exige
  contato com o operador.
- Para os demais direitos, o canal único é o e-mail do Encarregado.

## 4. Encarregado (DPO)

- E-mail: `dpo@fabiotreze.com`
- SLA de resposta: até 15 dias corridos.
- Procedimento: registro da solicitação, confirmação de identidade e escopo,
  verificação do mapa de dados, resposta com resumo das ações.

## 5. Mapa de dados

| Fluxo | Dado | Coleta | Armazenamento | Retenção | Compartilhamento |
|-------|------|--------|---------------|----------|------------------|
| Navegação | Nenhum dado pessoal | Não | Não | Não | Não |
| Análise IA opcional | Texto anonimizado pelo navegador | Servidor recebe e repassa à IA | Azure OpenAI (Brasil) | Sem retenção de prompt/conteúdo | Azure OpenAI no tenant do operador |
| Rate limit | Bucket global sem identificador por cliente | Cache Redis privado | Azure (Brasil) | TTL curto operacional | Não |

Notas:

- O servidor rejeita explicitamente payloads com indicadores evidentes de PII
  (HTTP 422), conforme `services/ai-analysis.js` e `lib/ai-analyze.js`.
- A análise default é executada localmente no navegador, sem envio.

## 6. Cookies, identificadores e tracking

- Sem cookies de marketing.
- Sem ferramentas de tracking de terceiros.
- Sem fingerprinting.
- Armazenamento local (Web Storage) usado apenas para preferências do próprio
  usuário e para registrar a decisão de consentimento de IA, com chave
  versionada e revogável.

## 7. Disclaimer e termos informativos

O produto deve manter, de forma destacada e acessível:

1. Aviso no topo de cada página informando que o conteúdo é educacional e
   não substitui orientação profissional (advocacia, defensoria, CRAS,
   medicina, assistência social).
2. Bloco completo de aviso legal acessível pelo menu e pelo rodapé.
3. Rodapé com link direto para esta página
   (`docs/LGPD-COMPLIANCE.md`) e para o aviso completo.
4. Linguagem conservadora ao citar leis: preferir remissão ao texto vigente e
   à regulamentação aplicável, evitando interpretações categóricas.
5. **Conteúdo gerado por IA marcado explicitamente** no resultado da análise
   opcional, no PDF exportado e em qualquer compartilhamento — conforme
   [Princípios de uso de IA](AI-PRINCIPLES.md) (alinhados ao Microsoft Learn:
   [Principles for AI-generated content](https://learn.microsoft.com/en-gb/principles-for-ai-generated-content)).

## 8. Segurança técnica relacionada (resumo)

- HTTPS obrigatório com HSTS.
- CSP estrita com allowlist explícita.
- Ingresso restrito à edge da Cloudflare no App Service público.
- Azure OpenAI, Key Vault e Redis com `publicNetworkAccess=Disabled` e
  Private Endpoint + Private DNS.
- TLS 1.2 mínimo em Redis e demais serviços PaaS quando aplicável.
- Identidades por Managed Identity. Sem credenciais embutidas.
- Segredos em Key Vault. CI/CD usa OIDC com Workload Identity Federation.

Detalhes técnicos completos: [SECURITY-LGPD.md](SECURITY-LGPD.md) e
[ARCHITECTURE.md](ARCHITECTURE.md).

## 9. Checklist auditável

Marque cada item ao final de cada revisão recorrente da postura LGPD.

### 9.1 Conteúdo e UX

- [x] Aviso de "não substitui orientação profissional" visível no topo, na home
      e no rodapé.
- [x] Bloco completo de aviso legal acessível pelo menu.
- [x] Modal de consentimento de IA informa base legal, finalidade, destino,
      retenção e direitos do titular.
- [x] Botão permanente de revogação de consentimento de IA disponível.
- [x] Linguagem das citações legais é conservadora e remete à legislação
      vigente.

### 9.2 Tratamento de dados

- [x] Sem cookies de tracking.
- [x] Sem coleta de dado pessoal por padrão.
- [x] Sem telemetria de aplicação (nenhum SDK de APM/observabilidade emite envelopes a partir do servidor).
- [x] Rejeição automática de payloads com PII evidente na análise por IA.
- [x] Anonimização do texto antes do envio à IA.

### 9.3 Segurança

- [x] HTTPS-only com HSTS.
- [x] CSP estrita.
- [x] Ingresso restrito à edge da Cloudflare no App Service.
- [x] Azure OpenAI, Key Vault e Redis com Private Endpoint e DNS privado.
- [x] Identidade gerenciada para acesso a Key Vault e demais serviços.
- [x] Segredos em Key Vault.
- [x] OIDC do GitHub Actions para Azure (sem client secret no repositório).

### 9.4 Governança

- [x] DPO definido e canal `dpo@fabiotreze.com` documentado.
- [x] Mapa de dados documentado nesta página.
- [x] Bases legais documentadas nesta página.
- [x] Procedimento de exercício de direitos descrito.
- [x] Workflow de freshness de fontes legais ativo no CI.

### 9.5 Revisões recorrentes

- [ ] Revisar este documento a cada release relevante de conteúdo.
- [ ] Confirmar que `docs/SECURITY-LGPD.md` e este documento permanecem
      consistentes.
- [ ] Confirmar que [README.md](../README.md) aponta para este checklist na
      seção de privacidade.

## 10. Relação com o issue #189

Este documento atende ao item explícito do issue
[#189](https://github.com/fabiotreze/nossodireito/issues/189):

> 6. LGPD checklist formal ausente — existe `validate_legal_compliance.py` mas
>    não há doc `docs/LGPD-COMPLIANCE.md` com checklist auditável (cookies,
>    consentimento, retenção, DPO contact).

A partir desta revisão, esta página é o ponto único de auditoria recorrente
para textos legais, disclaimers, termos informativos e postura LGPD do
NossoDireito.

## 11. Referências normativas ANPD

| Resolução | Assunto | Documento relacionado |
|-----------|---------|----------------------|
| Res. CD/ANPD nº 2/2022 | Agentes de pequeno porte | N/A — portal não se enquadra |
| Res. CD/ANPD nº 4/2023 | RIPD | [docs/RIPD.md](RIPD.md) |
| Res. CD/ANPD nº 15/2024 | Comunicação de incidentes | [RUNBOOK-INCIDENTE-LGPD.md](RUNBOOK-INCIDENTE-LGPD.md) |
| Res. CD/ANPD nº 18/2024 | Encarregado (DPO) | [docs/ENCARREGADO.md](ENCARREGADO.md) |

### Dados sensíveis (Art. 11, II, a)

O titular pode inserir dados de saúde (CIDs, laudos, diagnósticos) no
formulário de análise por IA. O tratamento é autorizado com base em
**consentimento específico e destacado** (Art. 11, II, a) coletado via
modal dedicado antes do envio. O RIPD documenta os riscos e mitigações.

### Marco Civil da Internet (Lei 12.965/2014)

- **Art. 15** (provedor de aplicações com fins econômicos): o serviço é educacional e sem fins econômicos, portanto **não se enquadra** na obrigação de guarda de 6 meses do Art. 15.
- **Art. 13** (provedor de conexão / acesso): por boa prática e para fins de segurança, auditoria e resposta a incidentes, mantemos registros de acesso à aplicação no Azure Monitor / Log Analytics Workspace `log-nossodireito-br` com **retenção de 180 dias** (categoria `AppServiceHTTPLogs`).
- O servidor de aplicação vê apenas o **IP da edge Cloudflare** (proxy reverso), não o IP de origem do usuário final. Demais campos coletados: User-Agent, URL, status, bytes, tempo de resposta.
- **Base legal LGPD:** Art. 7º, II (cumprimento de obrigação legal pelo operador) c/c Art. 7º, IX (legítimo interesse para segurança), considerando que o dado tratado (IP de edge Cloudflare + metadata HTTP) tem baixíssimo potencial de identificação direta do titular.
- **Art. 7º, VII Marco Civil:** registros não são fornecidos a terceiros sem consentimento livre, expresso e informado ou determinação judicial.
