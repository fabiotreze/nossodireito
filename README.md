<p align="center">
  <img src="images/nossodireito.png" alt="NossoDireito" width="120">
</p>

# ⚖️ NossoDireito

[![Quality Gate](https://img.shields.io/badge/Quality%20Gate-100.0%2F100-brightgreen?style=flat-square)](https://github.com/fabiotreze/nossodireito/actions)
[![Deploy](https://img.shields.io/badge/Deploy-Azure%20App%20Service-0078D4?style=flat-square&logo=microsoft-azure)](https://nossodireito.fabiotreze.com)
[![Security](https://img.shields.io/badge/Security-AES--GCM--256%20%7C%20CSP%20%7C%20SRI-green?style=flat-square&logo=letsencrypt)](SECURITY.md)
[![LGPD](https://img.shields.io/badge/LGPD-Zero%20Data%20Collection-blue?style=flat-square)](SECURITY.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.2.3-informational?style=flat-square)](CHANGELOG.md)

**Recebeu um laudo? Vem que a gente te ajuda.**

Guia gratuito, sem fins lucrativos, com direitos, benefícios e passo a passo para famílias de pessoas com deficiência (PcD) no Brasil.

🌐 **[nossodireito.fabiotreze.com](https://nossodireito.fabiotreze.com)**

---

## 🎯 O que é

Uma pessoa recebe um laudo de deficiência — TEA, síndrome de Down, deficiência física, visual, auditiva, intelectual — e a primeira pergunta é: **"E agora?"**

O NossoDireito organiza, em linguagem simples, as informações oficiais do governo brasileiro sobre:

- **BPC/LOAS** — Benefício de Prestação Continuada (1 salário mínimo)
- **CIPTEA** — Carteira de Identificação da Pessoa com TEA
- **Educação Inclusiva** — Matrícula obrigatória, multa por recusa
- **Plano de Saúde** — Cobertura obrigatória, como reclamar na ANS
- **SUS/Terapias** — Terapias e medicamentos gratuitos
- **Transporte** — Passe Livre federal, isenção de IPVA
- **Trabalho** — Cotas PcD (2% a 5%), proteção contra demissão
- **FGTS** — Saque para PcD ou dependente PcD
- **Moradia** — Minha Casa Minha Vida com prioridade PcD

## ♿ Acessibilidade

- **🔊 Ouvir** — Leitura em voz alta (Web Speech API nativa, sem dependência)
- **🤟 Libras** — Tradução em Libras via VLibras (governo federal)
- **A± Fonte** — Ajuste de tamanho de fonte
- **🔲 Contraste** — Modo alto contraste
- **PWA** — Instalável no celular, funciona offline

## 🔒 Privacidade (LGPD)

- **Nenhum dado pessoal** é coletado, armazenado ou enviado a servidores
- **Zero cookies** de rastreamento
- Todo o processamento ocorre **no navegador do usuário**
- Enquadramento: LGPD Art. 4º, I — tratamento por pessoa natural para fins exclusivamente privados e não econômicos

## 🛠 Tecnologia

| Componente | Tecnologia |
|---|---|
| Frontend | HTML5 + CSS3 + Vanilla JavaScript |
| Acessibilidade | Web Speech API (TTS) + VLibras (Libras) |
| PWA | Service Worker + manifest.json (offline) |
| Server | Node.js 20 LTS (`server.js`) |
| Base de dados | JSON estático (`data/direitos.json`) |
| Criptografia | AES-GCM-256 via Web Crypto API |
| Hospedagem | Azure App Service B1 Linux |
| SSL | PFX próprio via Azure Key Vault (SNI) |
| IaC | Terraform (azurerm ~>4.0) |
| CI/CD | GitHub Actions (Quality Gate + zip deploy) |
| Monitoramento | Azure Application Insights |
| Analytics de usuário | Nenhum (client-side) |
| Cookies | Nenhum |

## 📁 Estrutura

```
nossodireito/
├── index.html              # Página principal
├── index.min.html          # HTML minificado (produção)
├── server.js               # Servidor Node.js (App Service)
├── package.json            # Dependências (applicationinsights)
├── sw.js                   # Service Worker (PWA offline)
├── manifest.json           # PWA manifest
├── robots.txt              # Diretivas de rastreamento
├── sitemap.xml             # Mapa do site para SEO
├── css/
│   └── styles.css          # CSS responsivo + dark mode
├── js/
│   └── app.js              # Busca, navegação, TTS, VLibras, criptografia
├── data/
│   ├── direitos.json       # Base de conhecimento (9 categorias)
│   └── matching_engine.json # Keywords de análise de documentos
├── images/                 # Favicons, OG image e logo
├── scripts/
│   └── validate_sources.py # Validação de URLs + legislação + CID
├── codereview/
│   └── codereview.py       # Quality Gate (17 categorias, 160 checks)
├── terraform/              # Infraestrutura como código
│   ├── main.tf             # App Service + Key Vault + SSL
│   ├── variables.tf        # Variáveis multi-ambiente
│   ├── outputs.tf          # Outputs pós-apply
│   └── providers.tf        # Provider azurerm ~>4.0
├── .github/workflows/
│   ├── deploy.yml          # CI/CD push → deploy
│   ├── quality-gate.yml    # Quality Gate PR check
│   ├── terraform.yml       # IaC manual dispatch
│   └── weekly-review.yml   # Issue automática semanal
├── CHANGELOG.md
├── GOVERNANCE.md
├── SECURITY.md
├── SECURITY_AUDIT.md
├── LICENSE
└── README.md
```

## 🚀 Instalação e uso local

```bash
cd nossodireito
node server.js
# ou simplesmente:
python -m http.server 8000
```

Acesse `http://localhost:8080` (Node) ou `http://localhost:8000` (Python)

## ⚠️ Aviso Legal

Este site é um **guia informacional** e **NÃO constitui**:
- Assessoria ou consultoria jurídica
- Orientação médica ou de saúde
- Substituição a profissionais qualificados

As informações são compiladas de **fontes oficiais** do governo brasileiro (gov.br) e podem estar desatualizadas. **Sempre verifique as fontes originais** e consulte profissionais qualificados.

**Para orientação profissional gratuita:** procure a **Defensoria Pública** ou o **CRAS** da sua cidade.

## 📚 Principais leis referenciadas

- [Lei 8.742/1993 (LOAS)](https://www.planalto.gov.br/ccivil_03/leis/l8742.htm)
- [Lei 12.764/2012 (Berenice Piana — TEA)](https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2012/lei/l12764.htm)
- [Lei 13.146/2015 (Estatuto da Pessoa com Deficiência)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm)
- [Lei 13.977/2020 (Romeo Mion — CIPTEA)](https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2020/lei/l13977.htm)
- [Lei 13.709/2018 (LGPD)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)

## 📄 Licença

MIT — Código livre para reutilização. As informações legais são de domínio público.

## 🏷️ Aviso sobre Marcas

Este é um projeto **open source, gratuito e sem fins lucrativos**, de caráter exclusivamente **educacional e informativo**. **NÃO presta, oferece ou comercializa serviços jurídicos** de qualquer natureza. Não possui vínculo com escritórios de advocacia, lawtechs ou entidades que prestem serviços jurídicos. O nome "NossoDireito" identifica exclusivamente este software de código aberto. Marcas registradas mencionadas pertencem aos seus respectivos titulares.

---

*Feito com 💙 para as famílias que precisam de informação acessível.*
