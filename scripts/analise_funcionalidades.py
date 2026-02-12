#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análise Completa de Funcionalidades - NossoDireito
Compara funcionalidades implementadas vs testadas
"""

from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    app_js = (root / 'js' / 'app.js').read_text()
    test_e2e = (root / 'scripts' / 'test_e2e_automated.py').read_text()
    
    # Funcionalidades principais do site
    features = {
        '♿ Acessibilidade': {
            'Font Size Adjustment (A-, A, A+)': ['applyFontSize', 'FONT_STEPS', 'a11yFont'],
            'High Contrast Toggle': ['toggleContrast', 'high_contrast', 'a11yContrast'],
            'VLibras (LIBRAS)': ['ensureVL', 'VLibras', 'initVL'],
            'Text-to-Speech (Leitura de Voz)': ['startReading', 'speechSynthesis', 'a11yReadAloud'],
            'ARIA Attributes': ['aria-', 'role='],
            'Keyboard Navigation': ['keydown', 'tabindex', 'ArrowUp', 'ArrowDown']
        },
        '🔍 Busca e Matching': {
            'Semantic Search (performSearch)': ['performSearch', 'function performSearch'],
            'Text Normalization': ['normalize(', 'NFD'],
            'Scoring Algorithm': ['score', 'weight'],
            'Matching Engine': ['KEYWORD_MAP', 'keyword_map'],
            'CID Range Matching': ['CID_RANGE_MAP', 'cid-']
        },
        '📂 Categorias e Conteúdo': {
            'Render Categories Grid': ['renderCategories', 'categoryGrid'],
            'Show Category Details': ['showDetalhe', 'function showDetalhe'],
            'Base Legal Display': ['base_legal', 'renderBaseLegal'],
            'Requisitos Display': ['requisitos'],
            'Passo a Passo Display': ['passo_a_passo'],
            'Dicas e Observações': ['dicas', 'observacoes']
        },
        '✅ Checklist': {
            'LocalStorage Persistence': ['localStorage', 'STORAGE_PREFIX'],
            'Add Checklist Item': ['addChecklistItem', 'checklistContainer'],
            'Checkbox State Management': ['checkbox', 'checked'],
            'Progress Calculation': ['progress', 'percentage']
        },
        '📄 Documentos e Arquivos': {
            'File Upload (PDF/Images)': ['input type="file"', 'MAX_FILE_SIZE'],
            'Analyze Documents': ['analyzeSelectedDocuments', 'async function analyze'],
            'PDF Text Extraction': ['extractPdfText', 'pdf.js', 'pdfjs'],
            'IndexedDB Storage': ['indexedDB', 'DB_NAME', 'openDB'],
            'AES-256-GCM Encryption': ['encryptBuffer', 'crypto.subtle', 'AES-GCM'],
            'Decrypt File Data': ['decryptFileData', 'decrypt'],
            'Export PDF': ['exportPdf', 'window.print']
        },
        '🧭 Navegação e Histórico': {
            'Mobile Menu Toggle': ['menuToggle', 'hamburger'],
            'Scroll Spy (Active Section)': ['IntersectionObserver', 'isIntersecting'],
            'Back Button': ['voltarBtn', 'voltar'],
            'History Push State': ['history.pushState', 'pushState'],
            'Popstate Handler': ['popstate', 'addEventListener(.popstate)']
        },
        '📱 PWA e Offline': {
            'Service Worker': ['sw.js', 'service worker', 'navigator.serviceWorker'],
            'Cache Strategy': ['CACHE_VERSION', 'caches.open'],
            'Offline Support': ['offline', 'fetch'],
            'Manifest JSON': ['manifest.json', 'start_url']
        },
        '🎨 UI/UX': {
            'Toast Notifications': ['showToast', 'toast'],
            'Confirm Dialogs': ['confirmAction', 'dialog'],
            'Disclaimer Modal': ['disclaimerModal', 'acceptBtn'],
            'Loading States': ['loading', 'spinner'],
            'Error Handling': ['try', 'catch', 'error']
        }
    }
    
    print('='*80)
    print('📊 ANÁLISE COMPLETA DE FUNCIONALIDADES - NossoDireito')
    print('='*80)
    
    total_features = 0
    implemented = 0
    tested = 0
    not_tested = []
    
    for category, funcs in features.items():
        print(f'\n{category}')
        print('-'*80)
        
        for feature_name, patterns in funcs.items():
            total_features += 1
            
            # Verificar se está implementado
            is_implemented = any(pattern in app_js for pattern in patterns)
            
            # Verificar se está testado
            feature_keywords = feature_name.lower().replace('(', '').replace(')', '')
            is_tested = any(keyword in test_e2e.lower() for keyword in feature_keywords.split()[:2])
            
            if is_implemented:
                implemented += 1
            
            if is_tested:
                tested += 1
            else:
                if is_implemented:
                    not_tested.append((category, feature_name))
            
            # Status
            impl_icon = '✅' if is_implemented else '❌'
            test_icon = '🧪' if is_tested else '⚠️ '
            
            print(f'  {impl_icon} {test_icon} {feature_name}')
    
    print('\n' + '='*80)
    print('📈 ESTATÍSTICAS:')
    print('='*80)
    print(f'Total de funcionalidades: {total_features}')
    print(f'Implementadas: {implemented}/{total_features} ({implemented/total_features*100:.1f}%)')
    print(f'Testadas: {tested}/{total_features} ({tested/total_features*100:.1f}%)')
    print(f'Não testadas: {len(not_tested)} ({len(not_tested)/total_features*100:.1f}%)')
    
    if not_tested:
        print('\n' + '='*80)
        print('⚠️  FUNCIONALIDADES NÃO TESTADAS (implementadas mas sem testes):')
        print('='*80)
        for category, feature in not_tested:
            print(f'  • {category}: {feature}')
    
    print('\n' + '='*80)
    print('🎯 COBERTURA DE TESTES E2E:')
    print('='*80)
    
    # Analisar o que test_e2e_automated.py já testa
    test_methods = [
        line.strip() for line in test_e2e.split('\n') 
        if line.strip().startswith('def test_')
    ]
    
    print(f'\nTestes Implementados ({len(test_methods)}):')
    for method in test_methods:
        method_name = method.replace('def ', '').replace('(self)', '').replace(':', '')
        print(f'  ✅ {method_name}')
    
    print('\n' + '='*80)
    print('💡 RECOMENDAÇÕES:')
    print('='*80)
    
    missing_tests = [
        '♿ Acessibilidade Interativa (font size, contrast, VLibras)',
        '🧭 Navegação e History (pushState, popstate)',
        '🎨 UI/UX (toasts, modals, loading states)',
        '📂 Modal de Detalhes de Categoria',
        '✅ Checklist Progress Calculation',
        '🔍 Matching Engine com CID Ranges'
    ]
    
    print('\n🚀 Testes que devem ser adicionados para 100% de cobertura:')
    for i, test in enumerate(missing_tests, 1):
        print(f'  {i}. {test}')
    
    print('\n⚡ Opções para Testes E2E Completos:')
    print('  A) Playwright/Selenium - Testes browser reais (RECOMENDADO)')
    print('  B) Puppeteer - Testes headless browser')
    print('  C) Cypress - Testes interativos com UI')
    
    print('\n' + '='*80)

if __name__ == '__main__':
    main()
