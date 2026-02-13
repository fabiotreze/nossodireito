#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTO BACKUP — Backup Automático Diário com Versionamento

Cria backups automáticos de arquivos críticos com versionamento Git.

PRIORIDADE: P0 (crítico - prevenir perda de dados)
ESFORÇO: 4h
FREQUÊNCIA: DIÁRIO (recomendado: 00:00 via cron/Task Scheduler)

FUNCIONALIDADES:
1. Backup incremental de data/, docs/, scripts/, index.html, css/, js/
2. Versionamento com Git tags (backup-YYYY-MM-DD-HHMMSS)
3. Compressão ZIP com timestamp
4. Limpeza automática de backups antigos (mantém últimos 30 dias)
5. Relatório de backup em JSON
6. Notificação de sucesso/falha

USO:
    python scripts/auto_backup.py                  # Backup completo
    python scripts/auto_backup.py --dir data       # Backup específico
    python scripts/auto_backup.py --keep-days 60   # Manter 60 dias
"""

import argparse
import json
import subprocess
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List


class AutoBackup:
    """Gerenciador de backups automáticos"""

    def __init__(self, root: Path, backup_dir: Path = None, keep_days: int = 30):
        """
        Args:
            root: Diretório raiz do projeto
            backup_dir: Diretório para armazenar backups (padrão: root/backups)
            keep_days: Dias de retenção de backups
        """
        self.root = root
        self.backup_dir = backup_dir or (root / "backups")
        self.keep_days = keep_days
        self.timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        self.backup_name = f"backup-{self.timestamp}"

        # Diretórios críticos para backup
        self.critical_dirs = ["data", "docs", "scripts", "css", "js"]
        self.critical_files = ["index.html", "package.json", "requirements.txt", "README.md"]

        # Criar diretório de backups se não existir
        self.backup_dir.mkdir(exist_ok=True)

        # Relatório de backup
        self.report: Dict[str, Any] = {
            "timestamp": self.timestamp,
            "status": "in_progress",
            "files_backed_up": [],
            "git_tag": None,
            "zip_file": None,
            "errors": []
        }

    def is_git_repo(self) -> bool:
        """Verifica se o diretório é um repositório Git"""
        return (self.root / ".git").exists()

    def create_git_tag(self) -> str:
        """Cria tag Git para o backup"""
        if not self.is_git_repo():
            self.report["errors"].append("Não é um repositório Git - tag não criada")
            return None

        tag_name = f"backup-{self.timestamp}"

        try:
            # Checa se há mudanças para commitar
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=True
            )

            has_changes = bool(result.stdout.strip())

            if has_changes:
                # Add all changes
                subprocess.run(["git", "add", "."], cwd=self.root, check=True)

                # Commit
                commit_msg = f"[AUTO BACKUP] {self.timestamp}"
                subprocess.run(
                    ["git", "commit", "-m", commit_msg],
                    cwd=self.root,
                    check=True,
                    capture_output=True
                )

            # Create tag
            subprocess.run(
                ["git", "tag", "-a", tag_name, "-m", f"Auto backup {self.timestamp}"],
                cwd=self.root,
                check=True,
                capture_output=True
            )

            self.report["git_tag"] = tag_name
            return tag_name

        except subprocess.CalledProcessError as e:
            error_msg = f"Erro ao criar tag Git: {e}"
            self.report["errors"].append(error_msg)
            return None

    def create_zip_backup(self, dirs: List[str] = None) -> Path:
        """
        Cria arquivo ZIP com backup dos arquivos críticos

        Args:
            dirs: Lista de diretórios para backup (padrão: critical_dirs)

        Returns:
            Path do arquivo ZIP criado
        """
        dirs = dirs or self.critical_dirs
        zip_path = self.backup_dir / f"{self.backup_name}.zip"

        print(f"📦 Criando backup comprimido: {zip_path.name}")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Backup de diretórios
            for dir_name in dirs:
                dir_path = self.root / dir_name
                if not dir_path.exists():
                    print(f"   ⚠️ Diretório não encontrado: {dir_name}")
                    continue

                print(f"   📁 {dir_name}/")
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(self.root)
                        zipf.write(file_path, arcname)
                        self.report["files_backed_up"].append(str(arcname))

            # Backup de arquivos críticos
            for file_name in self.critical_files:
                file_path = self.root / file_name
                if file_path.exists():
                    print(f"   📄 {file_name}")
                    zipf.write(file_path, file_name)
                    self.report["files_backed_up"].append(file_name)

        self.report["zip_file"] = str(zip_path.name)
        return zip_path

    def cleanup_old_backups(self):
        """Remove backups antigos (mantém apenas keep_days)"""
        cutoff_date = datetime.now() - timedelta(days=self.keep_days)
        removed_count = 0

        print(f"🧹 Limpando backups anteriores a {cutoff_date.strftime('%Y-%m-%d')}...")

        for backup_file in self.backup_dir.glob("backup-*.zip"):
            # Extrai timestamp do nome do arquivo
            try:
                # backup-2026-02-12-145220.zip → 2026-02-12-145220
                timestamp_str = backup_file.stem.replace("backup-", "")
                backup_date = datetime.strptime(timestamp_str, "%Y-%m-%d-%H%M%S")

                if backup_date < cutoff_date:
                    backup_file.unlink()
                    removed_count += 1
                    print(f"   🗑️ Removido: {backup_file.name}")

            except (ValueError, IndexError):
                # Nome de arquivo não reconhecido - ignorar
                continue

        if removed_count == 0:
            print("   ✅ Nenhum backup antigo para remover")
        else:
            print(f"   ✅ {removed_count} backup(s) antigo(s) removido(s)")

    def save_report(self):
        """Salva relatório de backup em JSON"""
        report_path = self.backup_dir / f"{self.backup_name}.json"

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)

        print(f"   📊 Relatório: {report_path.name}")

    def run(self, dirs: List[str] = None) -> bool:
        """
        Executa backup completo

        Args:
            dirs: Diretórios para backup (padrão: critical_dirs)

        Returns:
            True se sucesso, False se erro
        """
        print("=" * 80)
        print("💾 AUTO BACKUP — Backup Automático com Versionamento")
        print("=" * 80)
        print()
        print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📂 Diretório: {self.root}")
        print(f"💾 Destino: {self.backup_dir}")
        print(f"🗓️ Retenção: {self.keep_days} dias")
        print()

        try:
            # 1. Git tag (se aplicável)
            if self.is_git_repo():
                print("🏷️ PASSO 1: Criando tag Git...")
                tag = self.create_git_tag()
                if tag:
                    print(f"   ✅ Tag criada: {tag}")
                else:
                    print(f"   ⚠️ Tag não criada (sem mudanças ou erro)")
                print()

            # 2. Criar ZIP
            print("📦 PASSO 2: Criando backup comprimido...")
            zip_path = self.create_zip_backup(dirs)
            zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
            print(f"   ✅ Backup criado: {zip_path.name} ({zip_size_mb:.2f} MB)")
            print()

            # 3. Limpeza
            print("🧹 PASSO 3: Limpando backups antigos...")
            self.cleanup_old_backups()
            print()

            # 4. Relatório
            self.report["status"] = "success"
            self.save_report()

            # 5. Resumo
            print("=" * 80)
            print("📊 RESUMO DO BACKUP")
            print("=" * 80)
            print()
            print(f"✅ Status: SUCESSO")
            print(f"📦 Arquivo: {zip_path.name} ({zip_size_mb:.2f} MB)")
            print(f"📄 Arquivos salvos: {len(self.report['files_backed_up'])}")
            if self.report["git_tag"]:
                print(f"🏷️ Git tag: {self.report['git_tag']}")
            print()

            print("🎯 PRÓXIMOS PASSOS:")
            print("   1. Agende execução diária (cron/Task Scheduler)")
            print("   2. Configure backup na nuvem (OneDrive/Google Drive)")
            print("   3. Teste restauração periodicamente")
            print()
            print("=" * 80)
            print("✨ BACKUP CONCLUÍDO COM SUCESSO")
            print("=" * 80)

            return True

        except Exception as e:
            self.report["status"] = "error"
            self.report["errors"].append(str(e))
            self.save_report()

            print()
            print("=" * 80)
            print("❌ ERRO NO BACKUP")
            print("=" * 80)
            print()
            print(f"Erro: {e}")
            print()

            return False


def main():
    """CLI principal"""
    parser = argparse.ArgumentParser(
        description="Auto Backup — Backup automático diário com versionamento"
    )
    parser.add_argument(
        "--dir",
        nargs="+",
        help="Diretórios específicos para backup (padrão: data, docs, scripts, css, js)"
    )
    parser.add_argument(
        "--keep-days",
        type=int,
        default=30,
        help="Dias de retenção de backups (padrão: 30)"
    )

    args = parser.parse_args()

    # Paths
    root = Path(__file__).parent.parent

    # Executar backup
    backup = AutoBackup(root, keep_days=args.keep_days)
    success = backup.run(dirs=args.dir)

    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
