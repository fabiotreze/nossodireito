# scripts/legacy/

Scripts arquivados em 2026-05-27 durante a simplificação do pipeline.

Não são chamados por nenhum workflow ativo nem pelo pre-commit. Mantidos por:
- referência histórica
- possibilidade de reativação manual

## Conteúdo

### Agents descontinuados (substituídos por monitoramento manual quinzenal)
- `agent_community_insights.py`
- `agent_compliance_drift.py`
- `agent_conecta_govbr_sync.py`
- `agent_content_freshness_monitor.py`
- `agent_dependency_intelligence.py`
- `agent_documentation_keeper.py`
- `agent_legal_source_auditor.py`
- `agent_lexml_law_drift.py`
- `agent_performance_watchdog.py`

### Descoberta / freshness
- `discover_benefits.py` — descoberta automática de novos benefícios PcD
- `check_sources_freshness.py` — checagem de janelas de 90 dias

### Migrações one-shot (já executadas)
- `add_5_servicos_federais.py`
- `add_cids_to_categorias.py`
- `add_moradia_assistida_pos_pais.py`

## Como reativar
```bash
git mv scripts/legacy/<nome>.py scripts/<nome>.py
mv .github/workflows/<workflow>.yml.disabled .github/workflows/<workflow>.yml
```
