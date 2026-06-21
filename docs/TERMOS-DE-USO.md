# Termos de Uso — NossoDireito

**Última atualização:** 2026-06-06
**Versão:** 2026-06-06 (alinhada com `TOS_VERSION` em [js/tos-banner.js](../js/tos-banner.js))

## 1. Natureza do serviço

O **NossoDireito** é um **catálogo público** — não governamental, sem fins lucrativos, mantido em ambiente de desenvolvimento (POC) — que **reúne referências** a informações já publicadas em **fontes oficiais brasileiras** sobre direitos de pessoas com deficiência (PcD). Cada conteúdo cita explicitamente a base legal e o canal oficial de origem.

O site **não é** órgão público, **não substitui** profissional habilitado (advogado, médico, assistente social, psicólogo) e **não tem competência legal ou administrativa** para conceder, negar, peticionar ou interpretar direitos. Pedidos, recursos, perícias e benefícios são tratados **exclusivamente pelos órgãos oficiais** listados em cada direito.

## 2. Fontes utilizadas

Todo conteúdo cita fontes oficiais conforme allowlist registrada em [`data/fontes_oficiais.json`](../data/fontes_oficiais.json):

- Domínios oficiais brasileiros: `*.gov.br`, `*.planalto.gov.br`, `*.jus.br`, `*.def.br`, `*.leg.br`, `*.mp.br`, `*.mil.br`, `www.in.gov.br`.
- Organização Mundial da Saúde (`icd.who.int`, `www.who.int`) — adotada pelo Ministério da Saúde via Portaria GM/MS nº 1.405/2022 (CID).
- APIs públicas integradas: `servicos.gov.br/api/v1` (servidor proxy SSRF-hardened em [`lib/govbr-proxy.js`](../lib/govbr-proxy.js)).

Qualquer alteração nessa allowlist exige PR público com justificativa.

## 3. Limitações conhecidas

- **Não há verificação em tempo real** das fontes. A frequência de atualização manual está descrita em `data[i].data_ultima_verificacao` para cada direito; após 180 dias o site exibe banner de "conteúdo possivelmente desatualizado".
- **Não há aconselhamento personalizado.** O conteúdo é genérico — sua situação concreta pode ter peculiaridades que mudam o resultado.
- **Diagnóstico não é direito automático.** Condições como TEA, TDAH, fibromialgia, lúpus, doenças raras ou dor crônica podem exigir análise de funcionalidade, barreiras e documentação clínica. O enquadramento como PcD depende da avaliação aplicável ao caso concreto, não apenas do nome da doença ou do CID.
- **A legislação muda.** Confirme sempre na fonte oficial citada antes de tomar qualquer decisão.
- **O recurso de IA (quando habilitado)** é uma sugestão informativa baseada apenas nas fontes já indexadas pelo catálogo e nas regras descritas em [`services/ai-analysis.js`](../services/ai-analysis.js); não dá parecer jurídico.

## 4. Privacidade

- **Não há cadastro, cookies de rastreamento, fingerprinting ou perfilamento individual.** Logs técnicos de acesso, contadores agregados, armazenamento local e análise por IA opcional seguem a Política de Privacidade.
- Documentos PDF eventualmente analisados pelo usuário **são processados localmente no navegador**; se a análise por IA for acionada, somente o texto anonimizado é enviado após consentimento específico.
- Preferências, Meus Documentos, checklists e cache temporário de resultados ficam em `localStorage`/`IndexedDB` no dispositivo do usuário e podem ser apagados a qualquer momento via interface ou "Limpar dados do navegador".
- Detalhes em [`docs/SECURITY-LGPD.md`](SECURITY-LGPD.md).

## 5. Aceite (browse-wrap)

Ao continuar a navegar no `https://nossodireito.fabiotreze.com` (ou em qualquer instância derivada do projeto), o usuário declara estar ciente destes termos e do aviso legal exibido em `#disclaimerInline`. Não há clique de aceite — modelo *browse-wrap* já reconhecido pelo Superior Tribunal de Justiça (REsp 1.819.075/RS, 3ª Turma, Min. Ricardo Villas Bôas Cueva, j. 25/08/2020) desde que o aviso seja claro e visível, como é o caso aqui.

## 6. Limitação de responsabilidade

Na **máxima extensão permitida pela legislação aplicável**, o autor, mantenedores
e contribuidores limitam responsabilidade por:

- Decisões tomadas com base no conteúdo do site sem validação em fonte oficial.
- Desatualizações, erros, omissões e mudanças regulatórias supervenientes.
- Indisponibilidade temporária do serviço por causas alheias ao controle do projeto.
- Conteúdo de sites de terceiros referenciados (mesmo quando oficiais).
- Resultados práticos (deferimento/indeferimento de benefícios, pareceres médicos, atendimentos).

Esta limitação **não exclui hipóteses de responsabilidade legal irrenunciável**,
inclusive em caso de dolo ou culpa grave comprovados.

O usuário deve validar informações relevantes com fonte oficial e profissional
habilitado antes de tomar decisões jurídicas, previdenciárias, financeiras ou de saúde.

## 7. Sugestões de correção

Encontrou conteúdo errado, desatualizado ou impreciso? Abra uma issue em [github.com/fabiotreze/nossodireito/issues](https://github.com/fabiotreze/nossodireito/issues) usando o template "Sugerir correção". Toda alteração editorial é registrada em `data/revisao_juridica.json`.

## 8. Licença do código

O código-fonte está sob a licença descrita em [`LICENSE`](../LICENSE). O conteúdo editorial (texto compilado a partir de fontes oficiais) é disponibilizado nos termos da licença do código e das licenças das fontes originais (em geral, conteúdo público do Governo Federal — uso livre conforme Lei 9.610/1998, art. 8º, IV).

## 9. Foro e legislação aplicável

Estes termos são regidos pela legislação brasileira. Eventuais questões serão resolvidas no foro do domicílio do mantenedor ou em foro eleito por acordo entre as partes.

## 10. Contato

E-mail técnico/jurídico (Encarregado/DPO informal): `38567767+fabiotreze@users.noreply.github.com`.

---

*Este documento é versionado em `docs/TERMOS-DE-USO.md` e segue o mesmo ciclo de release do projeto (`check_version_sync.mjs` valida paridade quando relevante).*
