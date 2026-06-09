# 🎨 Guia de Customização de Branding

Este documento descreve como customizar o **NossoDireito** para sua própria marca ou organização. O projeto foi estruturado para facilitar forks e reutilização com mínima edição de código.

## ⚡ Quick Start (Template, Sem Terminal)

1. Clique em Use this template no repositório original.
2. Crie um novo repositório seu.
3. Edite `config.json` direto no GitHub (botão Edit this file).
4. Substitua logo/favicon em `images/`.
5. Faça deploy do seu pipeline.

Checklist: [.github/TEMPLATE_SETUP.md](../.github/TEMPLATE_SETUP.md)

Guard automático no CI:
- O workflow `Template Branding Guard` valida se `config.json` foi customizado.
- Em repositórios derivados do template, o CI falha se valores padrão permanecerem.
- No repositório original (`fabiotreze/nossodireito`), essa checagem é ignorada por design.

## 📋 Entender o Sistema de Configuração

Todo o branding está centralizado em um arquivo: **`config.json`**

Este arquivo define:
- 📦 **Organização**: nome, site, emails de contato
- 🎨 **Design**: cores, logos, favicon
- ⚖️ **Legal**: informações jurídicas, copyright
- 🔍 **SEO**: títulos, descrições de página

Quando você inicia o site, o arquivo é **carregado automaticamente** no navegador via `js/branding-cache.js` e substitui todos os hardcodes.

## 🔧 Como Customizar

### Opção 1 (Recomendada): Editar `config.json` no GitHub

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

### Opção 2: CI/CD sem shell local

Se você quiser automação, mantenha `config.json` versionado no seu repositório-template e deixe cada organização ajustar esse arquivo via GitHub Web UI antes do primeiro deploy.
Assim o fluxo continua 100% sem terminal para o usuário final.

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

### Azure App Service (Terraform)

1. Prepare `terraform.tfvars`:
   ```hcl
   custom_domain = "sua-org.com.br"
   project_name  = "sua-org-direitos"
   ```

2. Atualize `config.json` antes de fazer ZIP deploy

3. Deploy:
   ```bash
   terraform apply
   # Terraform automaticamente faz ZIP do código (incluindo config.json)
   ```

### Docker / Qualquer servidor

1. Customize `config.json`
2. Build:
   ```bash
   docker build -t sua-org-direitos .
   docker run -p 8080:8080 sua-org-direitos
   ```

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
R: Não. O fluxo oficial é 100% sem terminal, apenas com GitHub Template + edição de `config.json` na interface web.

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
3. ✅ Teste localmente: `npm start`
4. ✅ Deploy: `npm run build && npm start`
5. ✅ (Opcional) Fork + customize conteúdo de direitos

---

**Dúvidas?** Abra uma issue em [GitHub](https://github.com/fabiotreze/nossodireito/issues) com tag `branding`.
