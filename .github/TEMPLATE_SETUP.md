# Template Setup (GitHub Web UI)

Use este passo a passo depois de clicar em Use this template.

## 1. Criar o repositório pela interface do GitHub

1. Clique em Use this template no repositório original.
2. Escolha o nome do novo repositório.
3. Marque a visibilidade desejada.
4. Clique em Create repository from template.
5. Abra uma issue usando o template `Template onboarding` para reunir branding, contatos, secrets Azure e responsável pelo primeiro deploy.

## 2. Customizar o branding no navegador

1. Abra `config.json` no novo repositório.
2. Clique em Edit this file.
3. Substitua pelo menos estes valores padrão:
	- `branding.organizationName`
	- `branding.organizationSlug`
	- `branding.websiteUrl`
	- `branding.siteName`
	- `contact.email`
	- `contact.dpo`
	- `design.primaryColor`
	- `design.primaryColorDark`
	- `seo.siteTitle`
	- `seo.siteDescription`
4. Clique em Commit changes.

## 3. Trocar logo e favicon pelo GitHub

1. Abra a pasta `images/`.
2. Use Add file > Upload files.
3. Envie seus arquivos de logo e favicon.
4. Se os nomes mudarem, volte em `config.json` e atualize os caminhos.

## 4. Configurar o deploy nas telas do repositório

Se você usar o workflow de deploy já versionado neste projeto:

Antes do primeiro run, peça ou separe antecipadamente:

- `ARM_CLIENT_ID` do app registration usado pelo deploy
- `ARM_TENANT_ID` do tenant Azure/Entra
- `ARM_SUBSCRIPTION_ID` da subscription de destino
- valor de `SEO_PRERENDER_MODE` (`home-only` ou `prerender`)
- confirmação de que a aba `Actions` está habilitada no repositório

1. Abra `Settings` > `Secrets and variables` > `Actions`.
2. Em `Secrets`, cadastre:
	- `ARM_CLIENT_ID`
	- `ARM_TENANT_ID`
	- `ARM_SUBSCRIPTION_ID`
3. Em `Variables`, revise `SEO_PRERENDER_MODE` se quiser `home-only` ou `prerender`.
4. Abra a aba `Actions`.
5. Habilite os workflows, se o GitHub pedir confirmação.

## 5. Validar antes do primeiro deploy

1. Abra a aba `Actions` e confirme se o workflow `Template Branding Guard` ficou verde.
2. Se ele falhar, ainda há valores padrão no `config.json`.
3. Se o workflow `Deploy Azure App Service` falhar no preflight, faltam secrets/variables obrigatórios em `Settings` > `Secrets and variables` > `Actions`.
4. Use a busca do GitHub no repositório e revise ocorrências de:
	- `nossodireito.fabiotreze.com`
	- `NossoDireito`
5. Ajuste textos legais, institucionais e de contato que precisem refletir sua organização.

## 6. Executar o primeiro deploy sem terminal

1. Abra `Actions`.
2. Se houver gatilho automático no seu fluxo, faça merge em `main`.
3. Mudanças em `config.json` e em `images/` também entram no fluxo de deploy automático do template.
4. Se usar execução manual, abra o workflow correspondente e clique em `Run workflow`.
5. Acompanhe os checks direto no GitHub até o fim.

## Resultado esperado

- Seu repositório passa no `Template Branding Guard`.
- O preflight do workflow de deploy não acusa secrets/variables ausentes.
- Seu branding deixa de usar os valores padrão do template.
- O deploy roda inteiramente via interface do GitHub.
