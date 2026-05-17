## Descrição
<!-- O que muda e por quê. Link para issue se houver. -->

## Tipo de mudança

- [ ] 🐛 Bug fix
- [ ] ✨ Feature
- [ ] 📝 Documentação
- [ ] 🔒 Segurança
- [ ] ♻️ Refactor
- [ ] 🧪 Teste
- [ ] 🏗️ IaC (Terraform / GitHub Actions)
- [ ] 🚨 Breaking change

## Checklist

- [ ] Rodei `python3 -m pytest tests/ -q` localmente (excluindo Playwright) → 100% verde
- [ ] Se mudei `server.js` / `shared/` / `services/`: `node -e "require('./server.js')"` sobe sem erro
- [ ] Se mudei Terraform: `terraform fmt` + `tflint` + `checkov -d terraform/` sem novas falhas
- [ ] Atualizei `CHANGELOG.md` se for mudança visível ao usuário
- [ ] **LGPD**: confirmo que não adicionei coleta de dado pessoal, cookies de tracking, IP em logs ou storage externo

## Conformidade

- [ ] Disclaimer legal mantido (não substitui orientação profissional)
- [ ] Sem dependências com licença GPL/AGPL adicionadas
- [ ] Secrets via GitHub Secrets — nada hardcoded
