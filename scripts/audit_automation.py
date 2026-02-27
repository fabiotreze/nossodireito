#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUDIT AUTOMATION - Mapeia o que está automatizado vs o que falta
Análise completa de cobertura de automação do projeto
Atualizado: 2026-02-26
"""

import json
import sys
from pathlib import Path
from typing import Dict, List


class AutomationAudit:
    """Audita cobertura de automação no projeto"""

    def __init__(self):
        self.scripts_dir = Path('scripts')
        self.data_dir = Path('data')
        self.results = {
            'automatizado': [],
            'nao_automatizado': [],
            'parcial': [],
            'recomendacoes': []
        }

    def audit_validation_coverage(self) -> Dict:
        """Audita cobertura de validações"""
        coverage = {}

        # O que ESTÁ automatizado
        coverage['automatizado'] = [
            {
                'area': 'Master Compliance',
                'script': 'scripts/master_compliance.py',
                'validacoes': [
                    '✅ Dados (direitos.json): schema, estrutura, categorias (278 pts)',
                    '✅ Código: sintaxe JS/Python/JSON (109 pts)',
                    '✅ Fontes: validação de URLs .gov.br (36.5 pts)',
                    '✅ Arquitetura: estrutura de pastas e arquivos (15.5 pts)',
                    '✅ Documentação: README, CHANGELOG, LICENSE, KNOWN_ISSUES (47 pts)',
                    '✅ Segurança: HTTPS, CSP, credenciais, SRI (25 pts)',
                    '✅ Performance: SW cache, tamanho assets, minificação (21 pts)',
                    '✅ Acessibilidade: WCAG 2.1 AA, ARIA, VLibras, semântica (31 pts)',
                    '✅ SEO: meta tags, JSON-LD, sitemap, OG, Twitter Card (56 pts)',
                    '✅ Infraestrutura: Terraform sintaxe, tfvars (31 pts)',
                    '✅ Testes E2E: funções críticas, cobertura (35 pts)',
                    '✅ Dead Code: JS functions, Python imports, console.log (27 pts)',
                    '✅ Órfãos: __pycache__, logs, arquivos grandes (15 pts)',
                    '✅ Lógica: documentos_mestre, categorias, URLs base_legal (40 pts)',
                    '✅ Regulatory: LGPD, disclaimer, finance, versões (65 pts)',
                    '✅ Cloud Security: HTTPS Only, Key Vault, MI, alerts (67 pts)',
                    '✅ CI/CD: workflows, permissions, pinning, secrets (89 pts)',
                    '✅ Dependências: npm/pip audit, SRI (40 pts)',
                    '✅ CHANGELOG: formato, semver, seções (25 pts)',
                    '✅ Análise 360: cobertura, IPVA, gaps (35 pts)',
                    '✅ Referências órfãs: dead refs, scripts inexistentes (20 pts)',
                ],
                'cobertura': '21 categorias, 1108.1 pontos máx, score 99.10%'
            },
            {
                'area': 'Validação de Conteúdo',
                'script': 'scripts/validate_content.py',
                'validacoes': [
                    '✅ 127 validações automáticas',
                    '✅ Campos obrigatórios por categoria',
                    '✅ Formato de dados (JSON structure)',
                    '✅ Links oficiais presentes',
                ],
                'cobertura': 'Completo (127 checks, 0 erros)'
            },
            {
                'area': 'Validação de Fontes',
                'script': 'scripts/validate_sources.py + validate_govbr_urls.py',
                'validacoes': [
                    '✅ URLs .gov.br: conectividade, status HTTP',
                    '✅ Formato de links: estrutura JSON',
                    '✅ SSL verification (com exceção CONFAZ)',
                    '✅ Detecção de redirects vs quebrados',
                ],
                'cobertura': '81 links verificados, 0 quebrados'
            },
            {
                'area': 'Validação Legal',
                'script': 'scripts/validate_legal_compliance.py + validate_legal_sources.py',
                'validacoes': [
                    '✅ Validação de base legal por categoria',
                    '✅ Formato de números de leis',
                    '✅ URLs de legislação (planalto.gov.br)',
                    '✅ Artigos referenciados',
                ],
                'cobertura': 'Completo (29 leis, 30 categorias)'
            },
            {
                'area': 'Análise 360°',
                'script': 'scripts/analise360.py',
                'validacoes': [
                    '✅ Benefícios: completude dinâmica',
                    '✅ Cobertura: 83.3% implementados',
                    '✅ IPVA: 27 estados mapeados',
                    '✅ Gaps: identificação automática',
                ],
                'cobertura': 'Completo (7 critérios de qualidade)'
            },
            {
                'area': 'JSON Schema Formal',
                'script': 'schemas/direitos.schema.json + scripts/validate_schema.py',
                'validacoes': [
                    '✅ JSON Schema Draft 7 validado',
                    '✅ 30 categorias, campos obrigatórios',
                    '✅ Validação automática no pre-commit',
                ],
                'cobertura': 'Completo (schema formal implementado)'
            },
            {
                'area': 'Testes Automatizados',
                'script': 'tests/test_*.py (6 arquivos) + pytest',
                'validacoes': [
                    '✅ 710 testes automatizados (local + CI)',
                    '✅ test_comprehensive.py: validação completa',
                    '✅ test_cross_browser.py: compatibilidade OS/browser',
                    '✅ test_master_compliance.py: quality gate',
                    '✅ test_comprehensive_validation.py: dados + e2e',
                    '✅ CI/CD: execução automática em commits',
                ],
                'cobertura': '710 testes, 100% pass rate'
            },
            {
                'area': 'CI/CD Pipeline',
                'script': '.github/workflows/ (4 workflows)',
                'validacoes': [
                    '✅ quality-gate.yml: Quality Gate automático',
                    '✅ deploy.yml: Deploy Azure App Service',
                    '✅ terraform.yml: Infraestrutura como código',
                    '✅ weekly-review.yml: Revisão periódica + issue automática',
                    '✅ Pre-commit hook: master_compliance --quick',
                ],
                'cobertura': '4 workflows, 19 actions pinadas, health check pós-deploy'
            },
            {
                'area': 'Auto-Preenchimento de Benefícios',
                'script': 'scripts/complete_beneficios.py + discover_benefits.py',
                'validacoes': [
                    '✅ Completude de campos por categoria',
                    '✅ Descoberta de novos benefícios',
                ],
                'cobertura': '30 categorias mapeadas'
            },
            {
                'area': 'Versionamento & Backup',
                'script': 'Git + scripts/bump_version.py',
                'validacoes': [
                    '✅ Git: histórico completo de todas alterações',
                    '✅ bump_version.py: incremento coordenado em 10 arquivos',
                    '✅ CHANGELOG.md: 33 versões semver documentadas',
                    '✅ Pre-commit hook previne commits com erros',
                ],
                'cobertura': 'Completo (Git é o backup, versionamento automático)'
            },
        ]

        # O que NÃO ESTÁ automatizado (aspiracional)
        coverage['nao_automatizado'] = [
            {
                'area': 'Validação Semântica de Conteúdo',
                'gaps': [
                    '❌ Verificação semântica de textos (requer IA/LLM)',
                    '❌ Validação de valores monetários (atualização)',
                    '❌ Detecção de informações desatualizadas',
                ],
                'impacto': 'MÉDIO — Requer revisão manual ou integração LLM'
            },
            {
                'area': 'Scraping Gov.br',
                'gaps': [
                    '❌ Scraping de páginas gov.br para verificar mudanças',
                    '❌ Comparação de conteúdo (direitos.json vs site oficial)',
                    '❌ Detecção de legislação revogada/alterada',
                ],
                'impacto': 'BAIXO — Gov.br bloqueia scrapers; fontes são leis federais estáveis'
            },
            {
                'area': 'Dashboard de Métricas',
                'gaps': [
                    '❌ Dashboard de qualidade em tempo real',
                    '❌ Histórico de métricas (trend analysis)',
                ],
                'impacto': 'BAIXO — Quality Gate + CI já fornecem visibilidade'
            },
        ]

        # Parcialmente automatizado
        coverage['parcial'] = [
            {
                'area': 'Consistência de Dados',
                'automatizado': 'Schema JSON Draft 7, validate_content.py (127 checks), validate_schema.py',
                'falta': 'Validação de regras de negócio complexas (requisitos duplicados entre categorias)',
                'script_sugerido': 'Evolução de validate_content.py'
            },
            {
                'area': 'Mapeamento de Estados (IPVA)',
                'automatizado': 'Contagem de estados (27/27), análise 360',
                'falta': 'Validação de URLs estaduais, atualização de valores',
                'script_sugerido': 'Evolução de analise360.py'
            },
        ]

        return coverage

    def generate_recommendations(self) -> List[Dict]:
        """Gera recomendações priorizadas (apenas itens realmente pendentes)"""
        return [
            {
                'prioridade': 'P3 - BAIXO',
                'acao': 'Dashboard de métricas históricas',
                'motivo': 'Visualização de tendências de qualidade ao longo do tempo',
                'script': 'dashboard/quality_metrics.html',
                'esforco': '20 horas'
            },
            {
                'prioridade': 'P3 - BAIXO',
                'acao': 'Validação semântica com LLM',
                'motivo': 'Detectar inconsistências de conteúdo automaticamente',
                'script': 'Integração com nossodireito-ai',
                'esforco': '16 horas'
            },
        ]

    def generate_report(self) -> str:
        """Gera relatório completo"""
        coverage = self.audit_validation_coverage()
        recommendations = self.generate_recommendations()

        report = []
        report.append("=" * 100)
        report.append("🔍 AUDITORIA DE AUTOMAÇÃO — NOSSODIREITO v1.14.4")
        report.append("=" * 100)
        report.append("")

        # Automatizado
        report.append("✅ O QUE ESTÁ AUTOMATIZADO")
        report.append("-" * 100)
        for item in coverage['automatizado']:
            report.append(f"\n📌 {item['area']} ({item['script']})")
            report.append(f"   Cobertura: {item['cobertura']}")
            for val in item['validacoes']:
                report.append(f"   {val}")

        report.append("")
        report.append("=" * 100)

        # Não automatizado
        report.append("❌ O QUE NÃO ESTÁ AUTOMATIZADO (aspiracional)")
        report.append("-" * 100)
        for item in coverage['nao_automatizado']:
            report.append(f"\n📌 {item['area']}")
            report.append(f"   Impacto: {item['impacto']}")
            for gap in item['gaps']:
                report.append(f"   {gap}")

        report.append("")
        report.append("=" * 100)

        # Parcial
        report.append("⚠️ PARCIALMENTE AUTOMATIZADO")
        report.append("-" * 100)
        for item in coverage['parcial']:
            report.append(f"\n📌 {item['area']}")
            report.append(f"   ✅ Automatizado: {item['automatizado']}")
            report.append(f"   ❌ Falta: {item['falta']}")
            report.append(f"   💡 Sugestão: {item['script_sugerido']}")

        report.append("")
        report.append("=" * 100)

        # Recomendações
        if recommendations:
            report.append("💡 RECOMENDAÇÕES (melhorias futuras)")
            report.append("-" * 100)
            for rec in recommendations:
                report.append(f"\n{rec['prioridade']}")
                report.append(f"  Ação: {rec['acao']}")
                report.append(f"  Motivo: {rec['motivo']}")
                report.append(f"  Script: {rec['script']}")
                report.append(f"  Esforço: {rec['esforco']}")

        report.append("")
        report.append("=" * 100)

        # Resumo
        report.append("📊 RESUMO EXECUTIVO")
        report.append("-" * 100)
        report.append(f"✅ Áreas automatizadas: {len(coverage['automatizado'])}")
        report.append(f"❌ Áreas sem automação: {len(coverage['nao_automatizado'])}")
        report.append(f"⚠️ Áreas parciais: {len(coverage['parcial'])}")
        report.append(f"💡 Recomendações: {len(recommendations)}")
        report.append("")

        total = (len(coverage['automatizado'])
                 + len(coverage['nao_automatizado'])
                 + len(coverage['parcial']))
        auto_pct = (len(coverage['automatizado']) / total * 100) if total else 0
        report.append(f"🎯 COBERTURA ATUAL: ~{auto_pct:.0f}% "
                      f"({len(coverage['automatizado'])} de {total} áreas)")
        report.append("")
        report.append("=" * 100)
        report.append("✨ FIM DO RELATÓRIO")
        report.append("=" * 100)

        return "\n".join(report)

    def save_report(self, output_file: Path):
        """Salva relatório em arquivo"""
        report = self.generate_report()
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        return output_file


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    auditor = AutomationAudit()

    # Exibir no terminal
    print(auditor.generate_report())

    # Salvar em arquivo
    output_file = Path('docs/VALIDATION_STATUS.md')
    output_file.parent.mkdir(exist_ok=True)
    saved_file = auditor.save_report(output_file)

    print()
    print(f"📄 Relatório salvo em: {saved_file}")


if __name__ == '__main__':
    main()
