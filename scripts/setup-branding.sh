#!/bin/bash

# NossoDireito — Interactive Branding Setup
# Esta script ajuda a customizar config.json para fork/customizações
# Uso: bash scripts/setup-branding.sh

set -e

CONFIG_FILE="config.json"
RESET_COLOR='\033[0m'
BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'

echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════${RESET_COLOR}"
echo -e "${BOLD}   NossoDireito — Setup Interativo de Branding${RESET_COLOR}"
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════${RESET_COLOR}\n"

# Helpers
get_current_value() {
    local key="$1"
    jq -r "$key" "$CONFIG_FILE" 2>/dev/null || echo ""
}

set_value() {
    local key="$1"
    local value="$2"
    jq "$key = \"$value\"" "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
}

# Menu
echo -e "${BOLD}Selecione o que deseja customizar:${RESET_COLOR}\n"
echo "1) 📦 Informações da Organização (nome, site, email)"
echo "2) 🎨 Design (cores, logos)"
echo "3) ⚖️  Informações Legais"
echo "4) 🔍 SEO (títulos, descrições)"
echo "5) ✅ Revisar tudo e sair"
echo ""
read -p "Opção (1-5): " option

case $option in
    1)
        echo -e "\n${BOLD}═ ORGANIZAÇÃO ═${RESET_COLOR}\n"
        
        read -p "Nome da organização [$(get_current_value '.branding.organizationName')]: " org_name
        [ ! -z "$org_name" ] && set_value '.branding.organizationName' "$org_name"
        
        read -p "Slug (minúsculas, sem espaços) [$(get_current_value '.branding.organizationSlug')]: " org_slug
        [ ! -z "$org_slug" ] && set_value '.branding.organizationSlug' "$org_slug"
        
        read -p "URL do site [$(get_current_value '.branding.websiteUrl')]: " website_url
        [ ! -z "$website_url" ] && set_value '.branding.websiteUrl' "$website_url"
        
        read -p "Email de contato [$(get_current_value '.contact.email')]: " email
        [ ! -z "$email" ] && set_value '.contact.email' "$email"
        
        read -p "Email DPO [$(get_current_value '.contact.dpo')]: " dpo
        [ ! -z "$dpo" ] && set_value '.contact.dpo' "$dpo"
        
        echo -e "\n${GREEN}✓ Organização atualizada!${RESET_COLOR}\n"
        ;;
    
    2)
        echo -e "\n${BOLD}═ DESIGN ═${RESET_COLOR}\n"
        
        read -p "Cor primária (hex) [$(get_current_value '.design.primaryColor')]: " primary_color
        [ ! -z "$primary_color" ] && set_value '.design.primaryColor' "$primary_color"
        
        read -p "Cor primária escura (hex) [$(get_current_value '.design.primaryColorDark')]: " primary_dark
        [ ! -z "$primary_dark" ] && set_value '.design.primaryColorDark' "$primary_dark"
        
        read -p "Path logo light [$(get_current_value '.design.logo.light')]: " logo_light
        [ ! -z "$logo_light" ] && set_value '.design.logo.light' "$logo_light"
        
        read -p "Path favicon [$(get_current_value '.design.logo.favicon')]: " favicon
        [ ! -z "$favicon" ] && set_value '.design.logo.favicon' "$favicon"
        
        echo -e "\n${GREEN}✓ Design atualizado!${RESET_COLOR}\n"
        ;;
    
    3)
        echo -e "\n${BOLD}═ LEGAL ═${RESET_COLOR}\n"
        
        read -p "Nome legal [$(get_current_value '.legal.legalName')]: " legal_name
        [ ! -z "$legal_name" ] && set_value '.legal.legalName' "$legal_name"
        
        read -p "Aviso copyright [$(get_current_value '.branding.copyrightNotice')]: " copyright
        [ ! -z "$copyright" ] && set_value '.branding.copyrightNotice' "$copyright"
        
        echo -e "\n${GREEN}✓ Legal atualizado!${RESET_COLOR}\n"
        ;;
    
    4)
        echo -e "\n${BOLD}═ SEO ═${RESET_COLOR}\n"
        
        read -p "Título do site: " site_title
        [ ! -z "$site_title" ] && set_value '.seo.siteTitle' "$site_title"
        
        read -p "Descrição: " site_desc
        [ ! -z "$site_desc" ] && set_value '.seo.siteDescription' "$site_desc"
        
        echo -e "\n${GREEN}✓ SEO atualizado!${RESET_COLOR}\n"
        ;;
    
    5)
        echo -e "\n${BOLD}═ REVISÃO FINAL ═${RESET_COLOR}\n"
        jq '.' "$CONFIG_FILE"
        echo -e "\n${GREEN}✓ Setup concluído! Você pode editar config.json manualmente se necessário.${RESET_COLOR}\n"
        exit 0
        ;;
    
    *)
        echo -e "${RED}Opção inválida${RESET_COLOR}"
        exit 1
        ;;
esac

# Recursively ask if user wants to configure more
read -p "Deseja customizar mais alguma coisa? (s/n): " more
if [[ "$more" =~ ^[Ss]$ ]]; then
    exec bash "$0"
else
    echo -e "\n${GREEN}✓ Setup concluído!${RESET_COLOR}\n"
    echo -e "${BOLD}Próximos passos:${RESET_COLOR}"
    echo "1. Revise config.json manualmente se necessário"
    echo "2. Execute: npm start"
    echo "3. Teste o site em http://localhost:8080"
    echo ""
fi
