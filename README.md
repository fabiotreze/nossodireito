# ⚖️ NossoDireito

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

## 🔒 Privacidade (LGPD)

- **Nenhum dado pessoal** é coletado, armazenado ou enviado a servidores
- **Zero cookies** de rastreamento
- Todo o processamento ocorre **no navegador do usuário**
- Enquadramento: LGPD Art. 4º, I — tratamento por pessoa natural para fins exclusivamente privados e não econômicos

## 🛠 Tecnologia

| Componente | Tecnologia |
|---|---|
| Frontend | HTML5 + CSS3 + Vanilla JavaScript |
| Base de dados | JSON estático (`data/direitos.json`) |
| Armazenamento | `localStorage` (apenas checklist e disclaimer) |
| Hospedagem | GitHub Pages |
| Backend | Nenhum |
| Analytics | Nenhum |
| Cookies | Nenhum |

## 📁 Estrutura

```
nossodireito/
├── index.html              # Página principal
├── css/
│   └── styles.css          # CSS responsivo + dark mode
├── js/
│   └── app.js              # Busca, navegação, checklist
├── data/
│   └── direitos.json       # Base de conhecimento (8 categorias)
└── README.md
```

## 🚀 Como rodar localmente

Basta abrir `index.html` no navegador, ou usar um servidor local:

```bash
# Com Python
cd nossodireito
python -m http.server 8000

# Com Node.js
npx serve .
```

Acesse `http://localhost:8000`

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

---

*Feito com 💙 para as famílias que precisam de informação acessível.*
