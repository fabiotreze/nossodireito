# 🎨 Guia de Customização de Branding

**Versão:** 1.43.48

Este documento descreve como customizar o **NossoDireito** para sua própria marca ou organização usando o fluxo de template do GitHub, sem depender de terminal local.

## ⚡ Quick Start (Template, GitHub Web UI)

1. Clique em Use this template no repositório original.
2. Crie um novo repositório seu.
3. Abra uma issue com o template `Template onboarding` para pedir tudo que precisa existir antes do primeiro deploy.
4. Edite `config.json` direto no GitHub.
5. Substitua logo/favicon em `images/`.
6. Configure `Settings` > `Secrets and variables` > `Actions` no novo repositório.
7. Execute o deploy pela aba `Actions`.

Checklist: [.github/TEMPLATE_SETUP.md](../.github/TEMPLATE_SETUP.md)
Issue de onboarding: [../.github/ISSUE_TEMPLATE/template_onboarding.yml](../.github/ISSUE_TEMPLATE/template_onboarding.yml)

Guard automático no CI:
- O workflow `Template Branding Guard` valida se `config.json` foi customizado.
- Em repositórios derivados do template, o CI falha se valores padrão permanecerem.
- No repositório original (`fabiotreze/nossodireito`), essa checagem é ignorada por design.
- O `Quality Gate` do repositório original também valida a integridade desse fluxo de onboarding para evitar drift entre template, docs e CI.

## 📋 Entender o Sistema de Configuração

Todo o branding está centralizado em um arquivo: **`config.json`**

Este arquivo define:
- 📦 **Organização**: nome, site, emails de contato
- 🎨 **Design**: cores, logos, favicon
- ⚖️ **Legal**: informações jurídicas, copyright
- 🔍 **SEO**: títulos, descrições de página

Quando você inicia o site, o arquivo é **carregado automaticamente** no navegador via `js/branding-cache.js` e substitui todos os hardcodes.

## 🔧 Como Customizar

### Opção recomendada: editar `config.json` no GitHub

```json
{
  "branding": {
    "organizationName": "Sua Organização",
    "organizationSlug": "sua-org",
    "tagline": "Seu tagline aqui",
    "websiteUrl": "https://seu-dominio.com.br",
    "siteName": "Sua Marca",
    "copyrightNotice": "Sua Org — Descrição"
  },
  "contact": {
    "email": "contato@sua-org.com.br",
    "dpo": "dpo@sua-org.com.br",
    "supportPhone": "+55 11 9999-9999"
  },
  "design": {
    "primaryColor": "#000000",
    "primaryColorDark": "#1a1a1a",
    "logo": {
      "light": "/images/seu-logo.webp",
      "dark": "/images/seu-logo-dark.webp",
      "favicon": "/images/favicon.ico"
    }
  },
  "legal": {
    "legalName": "Sua Organização Legal",
    "year": 2026,
    "termsUrl": "/termos-de-uso.html",
    "privacyUrl": "/privacidade.html"
  },
  "seo": {
    "siteTitle": "Seu Título | Sua Marca",
    "siteDescription": "Sua descrição para buscadores"
  }
}
```

O fluxo oficial é manter `config.json` versionado no seu repositório-template e ajustar esse arquivo pela GitHub Web UI antes do primeiro deploy.
Assim o processo continua 100% sem terminal para o usuário final.

## 🖼️ Atualizar Logos e Imagens

1. **Adicione seus arquivos** em `/images/`:
   - `sua-logo.webp` (versão clara)
   - `sua-logo-dark.webp` (versão escura para dark mode)
   - `favicon.ico` (ícone da aba)
   - `apple-touch-icon.png` (ícone para iOS)

2. **Atualize `config.json`**:
   ```json
   "design": {
     "logo": {
       "light": "/images/sua-logo.webp",
       "dark": "/images/sua-logo-dark.webp",
       "favicon": "/images/favicon.ico"
     }
   }
   ```

## 🎨 Customizar Cores

As cores são aplicadas via CSS variables. Você pode customizar:

1. **Cor Primária** (botões, links, destaque):
   ```json
   "design": {
     "primaryColor": "#1e40af",
     "primaryColorDark": "#1e3a8a"
   }
   ```

2. **Dark Mode** é automático
   - Claro: `primaryColor`
   - Escuro: `primaryColorDark` (usa `primaryColorDark` em modo escuro)

3. **CSS Override** (opcional):
   Você pode editar `css/styles.css` e override as variáveis CSS:
   ```css
   :root {
     --primary: #SEU_COR_AQUI;
     --primary-dark: #SUA_COR_ESCURA_AQUI;
   }
   ```

## 📱 Conteúdo Dinâmico

Alguns textos são gerados dinamicamente a partir do `config.json`:

### Títulos da Página
- `config.seo.siteTitle` → `<title>` + Open Graph `og:title`
- `config.seo.siteDescription` → `<meta name="description">`

### Emails / Contatos
Aparece em:
- Banners de contato
- Footers
- Políticas de privacidade

Use `window.CONTACT.email` no seu código:
```javascript
console.log(window.CONTACT.email);  // "contato@sua-org.com.br"
```

### Informações Legais
Use `window.LEGAL`:
```javascript
console.log(window.LEGAL.legalName);  // "Sua Organização Legal"
console.log(window.LEGAL.year);       // 2026
```

## 🚀 Deploy com Branding Customizado

### GitHub Actions + Azure App Service

Se você usar os workflows já incluídos no template, faça tudo pela interface do GitHub:

Antes do primeiro deploy, solicite ou confirme estes itens com antecedência:

1. `ARM_CLIENT_ID`
2. `ARM_TENANT_ID`
3. `ARM_SUBSCRIPTION_ID`
4. valor de `SEO_PRERENDER_MODE` (`home-only` ou `prerender`)
5. autorização para habilitar `Actions` no novo repositório

1. Abra `Settings` > `Secrets and variables` > `Actions`.
2. Cadastre os secrets `ARM_CLIENT_ID`, `ARM_TENANT_ID` e `ARM_SUBSCRIPTION_ID`.
3. Em `Variables`, ajuste `SEO_PRERENDER_MODE` se quiser `home-only` ou `prerender`.
4. Volte para a aba `Actions`.
5. Execute o workflow de deploy ou faça merge em `main`, conforme a estratégia do seu repositório.

O workflow de deploy agora falha cedo com mensagem clara se esses itens estiverem ausentes ou inválidos.

### Outros ambientes

Se sua organização usar outro destino de deploy, mantenha a mesma ideia operacional:

1. Customize `config.json` no GitHub.
2. Faça upload das imagens em `images/`.
3. Configure secrets/variables na interface do provedor e do GitHub.
4. Dispare o pipeline pelo painel web correspondente.

## 🔒 Segurança

- **Nenhuma informação sensível** deve estar em `config.json`
- Secrets (chaves de API, credenciais) vão em **variáveis de ambiente** (Azure Key Vault, GitHub Secrets, etc.)
- `config.json` é **servido publicamente** — é apenas customização de branding

## ❓ FAQ

**P: Preciso customizar o conteúdo das categorias de direitos?**
R: Não! `config.json` é **apenas para branding**. O conteúdo de direitos fica em `data/direitos.json`. Para customizar, você precisa editar aquele arquivo ou criar seu próprio catálogo.

**P: Posso manter meu próprio config.json no repositório?**
R: Sim. No fluxo de template, basta editar `config.json` no GitHub e commitar pela interface web.

**P: E se eu quiser customizar também o conteúdo de direitos?**
R: Você pode:
   1. Fork o repositório
   2. Editar `data/direitos.json` com seus próprios direitos
   3. Customizar `config.json` com seu branding
   4. Deploy como seu próprio repositório

**P: Preciso usar terminal para configurar marca?**
R: Não. O fluxo oficial é 100% sem terminal, usando GitHub Template, edição web de arquivos e configuração de Actions/Secrets nas telas do repositório.

## 📝 Arquivos Chave

| Arquivo | Propósito |
|---------|-----------|
| `config.json` | Branding centralizado |
| `js/branding-cache.js` | Carrega config e aplica ao DOM |
| `.github/TEMPLATE_SETUP.md` | Checklist de setup via template |
| `.github/workflows/template-branding-guard.yml` | Bloqueia branding padrão em repositórios derivados |
| `.gitignore` | Exclui secrets / temporários |
| `data/direitos.json` | Conteúdo de direitos (customizável) |

## 🆘 Troubleshooting

**Deploy falha antes do Azure Login:**
- Abra `Settings` > `Secrets and variables` > `Actions`
- Confirme `ARM_CLIENT_ID`, `ARM_TENANT_ID` e `ARM_SUBSCRIPTION_ID`
- Revise `SEO_PRERENDER_MODE` com valor `home-only` ou `prerender`
- Rode novamente o workflow pela aba `Actions`

**Branding não aparece:**
- Verifique se `config.json` está na raiz do projeto
- Abra DevTools > Console e procure por erros de fetch
- Limpe cache do navegador (Ctrl+Shift+Del)

**Cores não aparecem:**
- Recarregue a página (Ctrl+F5)
- Verifique se `design.primaryColor` é um hex válido

**Email de contato não aparece:**
- Confirme que `contact.email` está preenchido em `config.json`
- Procure por `window.CONTACT` no console

## 📚 Próximas Etapas

1. ✅ Customize `config.json`
2. ✅ Atualize imagens em `/images/`
3. ✅ Configure `Settings` > `Secrets and variables` > `Actions`
4. ✅ Rode o deploy pela aba `Actions`
5. ✅ (Opcional) Customize também o conteúdo em `data/direitos.json`

Este documento entra no mesmo ciclo de bump/versionamento dos demais docs versionados do projeto.

---

**Dúvidas?** Abra uma issue em [GitHub](https://github.com/fabiotreze/nossodireito/issues) com tag `branding`.
