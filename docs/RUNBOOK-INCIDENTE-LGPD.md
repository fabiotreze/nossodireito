# Runbook — Incidente de Segurança com Dados Pessoais (LGPD)

> Procedimento operacional conforme Resolução CD/ANPD nº 15/2024
> (comunicação de incidentes de segurança).

## 1. Critérios de ativação

Um incidente deve ser comunicado à ANPD quando puder acarretar **risco ou
dano relevante** aos titulares (Art. 48, LGPD; Art. 5º, Res. 15/2024):

- Dados sensíveis (saúde, biometria).
- Dados de crianças, adolescentes ou idosos.
- Dados financeiros ou de autenticação.
- Dados em larga escala.
- Possibilidade de discriminação, dano material ou moral.

## 2. Linha do tempo obrigatória

| Etapa | Prazo | Referência |
|-------|-------|------------|
| Detecção e contenção imediata | T+0 | Boas práticas |
| Comunicação à ANPD | **3 dias úteis** a partir do conhecimento | Res. 15/2024, Art. 6º |
| Comunicação aos titulares | **3 dias úteis** (mesmo prazo) | Res. 15/2024, Art. 9º |
| Comunicação complementar (se necessário) | 20 dias úteis | Res. 15/2024, Art. 7º |
| Registro interno do incidente | Imediato + retenção **5 anos** | Res. 15/2024, Art. 15 |

## 3. Comunicação à ANPD — 12 campos obrigatórios (Art. 6º, §1º)

| # | Campo |
|---|-------|
| 1 | Identificação do controlador (nome/CNPJ/CPF) |
| 2 | Identificação do Encarregado e canal de contato |
| 3 | Indicação se é comunicação preliminar ou complementar |
| 4 | Descrição da natureza dos dados pessoais afetados |
| 5 | Informações sobre os titulares envolvidos (categorias e quantidade) |
| 6 | Indicação das medidas técnicas e de segurança utilizadas (pré-incidente) |
| 7 | Riscos relacionados ao incidente e possíveis impactos aos titulares |
| 8 | Motivos da demora (se comunicação fora do prazo) |
| 9 | Medidas adotadas para reverter ou mitigar os efeitos |
| 10 | Data do conhecimento do incidente |
| 11 | Descrição do incidente (causa, cronologia e consequência) |
| 12 | Total de titulares afetados |

**Canal:** formulário eletrônico em [gov.br/anpd](https://www.gov.br/anpd/pt-br/assuntos/incidente-de-seguranca)

## 4. Comunicação aos titulares — 7 campos (Art. 9º)

| # | Campo |
|---|-------|
| 1 | Descrição da natureza dos dados afetados |
| 2 | Informações sobre os titulares envolvidos |
| 3 | Riscos relacionados ao incidente |
| 4 | Medidas já adotadas para mitigar |
| 5 | Medidas que os titulares podem adotar |
| 6 | Dados de contato do Encarregado |
| 7 | Data do conhecimento do incidente |

**Requisitos de linguagem:**
- Clara, acessível, em português.
- Sem jargão técnico desnecessário.
- Multicanal: e-mail direto se possível; caso contrário, banner no portal.

## 5. Procedimento passo a passo

### 5.1 Contenção (T+0)

```bash
# 1. Isolar recurso comprometido
az webapp stop --name nossodireito-app --resource-group rg-nossodireito

# 2. Revogar credenciais potencialmente expostas
az keyvault secret set-attributes --vault-name kv-nossodireito \
  --name <secret-name> --enabled false

# 3. Bloquear IP/range suspeito no WAF (se aplicável)
# 4. Preservar logs para forensics (NÃO deletar)
```

### 5.2 Avaliação (T+0 a T+4h)

- [ ] Identificar vetor de ataque.
- [ ] Determinar dados potencialmente expostos.
- [ ] Estimar número de titulares afetados.
- [ ] Classificar severidade: Baixa / Média / Alta / Crítica.
- [ ] Decidir se atinge limiar de comunicação (Seção 1).

### 5.3 Comunicação ANPD (até T+3 dias úteis)

- [ ] Preencher os 12 campos (Seção 3).
- [ ] Submeter via formulário eletrônico da ANPD.
- [ ] Salvar protocolo/comprovante.
- [ ] Se informação incompleta, marcar como "comunicação preliminar" e
      agendar complementar em até 20 dias úteis.

### 5.4 Comunicação aos titulares (até T+3 dias úteis)

- [ ] Redigir comunicação com os 7 campos (Seção 4).
- [ ] Publicar banner no portal ([nossodireito.fabiotreze.com](https://nossodireito.fabiotreze.com)).
- [ ] Se e-mail disponível, enviar individualmente.
- [ ] Registrar canal e data de comunicação.

### 5.5 Registro interno

- [ ] Documentar no log de incidentes (arquivo privado, não público).
- [ ] Incluir: data, natureza, dados afetados, titulares, medidas, decisão
      de comunicação, justificativa.
- [ ] Reter por **mínimo 5 anos** (Res. 15/2024, Art. 15).

### 5.6 Pós-incidente

- [ ] Root cause analysis (RCA).
- [ ] Atualizar medidas de segurança.
- [ ] Atualizar RIPD se necessário.
- [ ] Revisar este runbook com lições aprendidas.

## 6. Contatos de emergência

| Papel | Nome | Canal |
|-------|------|-------|
| Encarregado (DPO) | Fabio Rodrigues Vieira Costa | `dpo@fabiotreze.com` |
| ANPD | Autoridade Nacional | [gov.br/anpd](https://www.gov.br/anpd) |
| Azure Support | Microsoft | Portal Azure → Support |

## 7. Modelo de registro de incidente

```yaml
incidente:
  id: "INC-YYYY-NNN"
  data_conhecimento: ""
  data_comunicacao_anpd: ""
  data_comunicacao_titulares: ""
  natureza: ""
  dados_afetados: []
  titulares_estimados: 0
  severidade: ""  # Baixa|Média|Alta|Crítica
  comunicado_anpd: false
  comunicado_titulares: false
  medidas_adotadas: []
  rca_concluida: false
  protocolo_anpd: ""
```

## 8. Referências normativas

- Lei 13.709/2018 (LGPD), Art. 48
- Resolução CD/ANPD nº 15/2024 (comunicação de incidentes)
- Resolução CD/ANPD nº 4/2023 (RIPD)
- Resolução CD/ANPD nº 2/2022 (agentes de pequeno porte)
- Marco Civil da Internet (Lei 12.965/2014), Art. 15

## 9. Histórico de revisões

| Versão | Data | Alteração |
|--------|------|-----------|
| 1.0 | 2026-05-31 | Versão inicial conforme Res. CD/ANPD 15/2024 |
