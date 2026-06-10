#!/usr/bin/env node
/**
 * Guard do fluxo de template/onboarding.
 *
 * Objetivo: falhar no CI quando o repositório perder a trilha mínima para uso
 * como GitHub Template via Web UI. Isso evita drift entre README, docs,
 * workflow de branding e os secrets esperados pelo deploy.
 */
import { readFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));

function read(rel) {
  return readFileSync(join(ROOT, rel), "utf8");
}

const requiredFiles = [
  "README.md",
  ".github/TEMPLATE_SETUP.md",
  ".github/ISSUE_TEMPLATE/template_onboarding.yml",
  "docs/BRANDING.md",
  ".github/workflows/deploy.yml",
  ".github/workflows/template-branding-guard.yml",
  "scripts/check_branding_customized.mjs",
  "config.json",
  "package.json",
];

const violations = [];

for (const rel of requiredFiles) {
  if (!existsSync(join(ROOT, rel))) {
    violations.push(`arquivo obrigatório ausente: ${rel}`);
  }
}

if (violations.length === 0) {
  const pkg = JSON.parse(read("package.json"));
  const scripts = pkg.scripts || {};
  const readme = read("README.md");
  const templateSetup = read(".github/TEMPLATE_SETUP.md");
  const onboardingTemplate = read(".github/ISSUE_TEMPLATE/template_onboarding.yml");
  const branding = read("docs/BRANDING.md");
  const workflow = read(".github/workflows/template-branding-guard.yml");
  const deployWorkflow = read(".github/workflows/deploy.yml");

  const expectations = [
    [scripts["check:branding"] === "node scripts/check_branding_customized.mjs", "package.json deve expor script check:branding canônico"],
    [scripts["check:template"] === "node scripts/check_template_onboarding.mjs", "package.json deve expor script check:template"],
    [scripts["check:docs"]?.includes("check_template_onboarding.mjs"), "check:docs deve incluir o guard de template/onboarding"],
    [/Use this template/i.test(readme), "README.md deve orientar uso via Use this template"],
    [/\.github\/TEMPLATE_SETUP\.md/.test(readme), "README.md deve apontar para .github/TEMPLATE_SETUP.md"],
    [/docs\/BRANDING\.md/.test(readme), "README.md deve apontar para docs/BRANDING.md"],
    [/GitHub Web UI/i.test(readme), "README.md deve deixar explícito o fluxo via GitHub Web UI"],
    [/Create repository from template/.test(templateSetup), ".github/TEMPLATE_SETUP.md deve cobrir a criação a partir do template"],
    [/Settings` > `Secrets and variables` > `Actions`/.test(templateSetup), ".github/TEMPLATE_SETUP.md deve documentar Settings > Secrets and variables > Actions"],
    [/ARM_CLIENT_ID/.test(templateSetup) && /ARM_TENANT_ID/.test(templateSetup) && /ARM_SUBSCRIPTION_ID/.test(templateSetup), ".github/TEMPLATE_SETUP.md deve listar os secrets de deploy esperados"],
    [/SEO_PRERENDER_MODE/.test(templateSetup), ".github/TEMPLATE_SETUP.md deve mencionar a variável SEO_PRERENDER_MODE"],
    [/Run workflow/.test(templateSetup), ".github/TEMPLATE_SETUP.md deve mencionar execução do workflow pela interface do GitHub"],
    [/(solicite|peça) ou separe antecipadamente/i.test(templateSetup), ".github/TEMPLATE_SETUP.md deve antecipar os itens a solicitar antes do primeiro run"],
    [/\*\*Versão:\*\*\s*[0-9]+\.[0-9]+\.[0-9]+/.test(branding), "docs/BRANDING.md deve ser documento versionado"],
    [/GitHub Web UI/i.test(branding), "docs/BRANDING.md deve descrever fluxo via GitHub Web UI"],
    [/Template Branding Guard/.test(branding), "docs/BRANDING.md deve mencionar o Template Branding Guard"],
    [/Quality Gate/.test(branding), "docs/BRANDING.md deve mencionar cobertura no Quality Gate"],
    [/solicite ou confirme estes itens com antecedência/i.test(branding), "docs/BRANDING.md deve antecipar os pré-requisitos do deploy"],
    [/github\.repository != 'fabiotreze\/nossodireito'/.test(workflow), "template-branding-guard.yml deve manter a exceção do upstream"],
    [/npm run check:branding/.test(workflow), "template-branding-guard.yml deve executar npm run check:branding"],
    [/^\s*-\s+"config\.json"/m.test(deployWorkflow), "deploy.yml deve disparar em mudanças de config.json"],
    [/ARM_CLIENT_ID/.test(deployWorkflow) && /ARM_TENANT_ID/.test(deployWorkflow) && /ARM_SUBSCRIPTION_ID/.test(deployWorkflow), "deploy.yml deve consumir os secrets ARM_* esperados"],
    [/SEO_PRERENDER_MODE/.test(deployWorkflow), "deploy.yml deve usar a variável SEO_PRERENDER_MODE"],
    [/status\.html/.test(deployWorkflow) && /historico-aceite\.html/.test(deployWorkflow) && /privacidade\.html/.test(deployWorkflow) && /termos-de-uso\.html/.test(deployWorkflow), "deploy.yml deve cobrir as páginas raiz obrigatórias no filtro de paths"],
    [/Validar pré-requisitos do deploy/.test(deployWorkflow), "deploy.yml deve validar secrets/variables antes do Azure Login"],
    [/Template Deploy Preflight/.test(deployWorkflow), "deploy.yml deve publicar resumo acionável quando faltar configuração"],
    [/ARM_CLIENT_ID/.test(onboardingTemplate) && /ARM_TENANT_ID/.test(onboardingTemplate) && /ARM_SUBSCRIPTION_ID/.test(onboardingTemplate), "issue template de onboarding deve coletar os secrets ARM_* necessários"],
    [/SEO_PRERENDER_MODE/.test(onboardingTemplate), "issue template de onboarding deve coletar a variável SEO_PRERENDER_MODE"],
    [/Actions/.test(onboardingTemplate), "issue template de onboarding deve lembrar a habilitação de Actions"],
  ];

  for (const [ok, message] of expectations) {
    if (!ok) violations.push(message);
  }
}

if (violations.length > 0) {
  console.error(`❌ ${violations.length} problema(s) no fluxo de template/onboarding:`);
  for (const violation of violations) {
    console.error(`  - ${violation}`);
  }
  process.exit(1);
}

console.log("✅ Fluxo de template/onboarding íntegro no README, docs, scripts e workflow.");