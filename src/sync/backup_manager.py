#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Backup Automático para Planilhas Consolidadas

Este módulo implementa o sistema de backup automático conforme especificado
no Passo 4 dos REQUISITOS TÉCNICOS.md, incluindo:
- Verificação de existência da planilha mestre
- Geração de timestamp para backup
- Cópia segura para pasta BACKUP
- Validação de integridade do backup
- Sistema de limpeza de backups antigos

Autor: Agente trae2.0
Data: 2025-01-30
"""

import os
import shutil
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Tuple
import logging
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

from ..core.logger import get_logger
from ..core.exceptions import BackupError, ValidationError
from ..core.config import Config


class BackupManager:
    """
    Gerenciador de backup automático para planilhas consolidadas.
    
    Implementa todas as funcionalidades do Passo 4 dos requisitos técnicos:
    - Backup automático antes de cada consolidação
    - Nomenclatura padronizada: YYYY-MM-DD_HH-MM-SS_planilha_consolidada.xlsx
    - Validação de integridade dos backups
    - Limpeza automática de backups antigos (30 dias)
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Inicializa o gerenciador de backup.
        
        Args:
            config: Configuração do sistema (opcional)
        """
        self.config = config or Config()
        self.logger = get_logger(__name__)
        
        # Definir caminhos das pastas
        self.master_folder = Path(self.config.MESTRE_DIR)
        self.backup_folder = Path(self.config.BACKUP_DIR)
        
        # Configurações de backup
        self.retention_days = self.config.BACKUP_RETENTION_DAYS
        self.master_filename = self.config.MESTRE_FILENAME
        
        # Garantir que as pastas existam
        self._ensure_folders_exist()
    
    def _ensure_folders_exist(self) -> None:
        """
        Garante que as pastas necessárias existam.
        
        Raises:
            BackupError: Se não for possível criar as pastas
        """
        try:
            self.master_folder.mkdir(parents=True, exist_ok=True)
            self.backup_folder.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Pastas de backup verificadas: {self.backup_folder}")
        except Exception as e:
            raise BackupError(f"Erro ao criar pastas de backup: {e}")
    
    def create_backup(self) -> Optional[Path]:
        """
        Cria backup da planilha mestre atual (Passo 4.1-4.4).
        
        Returns:
            Path do backup criado ou None se não houver planilha mestre
            
        Raises:
            BackupError: Se houver erro durante o backup
        """
        try:
            # Passo 4.1: Verificar existência da planilha mestre
            master_path = self._get_master_file_path()
            if not master_path:
                self.logger.info("Nenhuma planilha mestre encontrada para backup")
                return None
            
            # Passo 4.2: Gerar timestamp para backup
            backup_filename = self._generate_backup_filename()
            backup_path = self.backup_folder / backup_filename
            
            self.logger.info(f"Iniciando backup: {master_path} -> {backup_path}")
            
            # Passo 4.3: Copiar planilha mestre para pasta BACKUP
            shutil.copy2(master_path, backup_path)
            
            # Passo 4.4: Validar integridade do backup criado
            if self._validate_backup_integrity(master_path, backup_path):
                self.logger.info(f"Backup criado com sucesso: {backup_path}")
                
                # Passo 4.5: Limpar backups antigos
                self._cleanup_old_backups()
                
                return backup_path
            else:
                # Remover backup inválido
                backup_path.unlink(missing_ok=True)
                raise BackupError("Falha na validação de integridade do backup")
                
        except Exception as e:
            self.logger.error(f"Erro ao criar backup: {e}")
            raise BackupError(f"Erro ao criar backup: {e}")
    
    def _get_master_file_path(self) -> Optional[Path]:
        """
        Localiza o arquivo da planilha mestre.
        
        Returns:
            Path da planilha mestre ou None se não encontrada
        """
        master_path = self.master_folder / self.master_filename
        
        if master_path.exists() and master_path.is_file():
            return master_path
        
        # Procurar por qualquer arquivo .xlsx na pasta mestre
        xlsx_files = list(self.master_folder.glob('*.xlsx'))
        if xlsx_files:
            return xlsx_files[0]  # Retorna o primeiro encontrado
        
        return None
    
    def _generate_backup_filename(self) -> str:
        """
        Gera nome padronizado para o backup (Passo 4.2).
        
        Formato: YYYY-MM-DD_HH-MM-SS_planilha_consolidada.xlsx
        
        Returns:
            Nome do arquivo de backup
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return f"{timestamp}_planilha_consolidada.xlsx"
    
    def _validate_backup_integrity(self, original_path: Path, backup_path: Path) -> bool:
        """
        Valida a integridade do backup criado (Passo 4.4).
        
        Args:
            original_path: Caminho do arquivo original
            backup_path: Caminho do backup
            
        Returns:
            True se o backup é válido, False caso contrário
        """
        try:
            # Verificar se o backup existe e tem tamanho similar
            if not backup_path.exists():
                self.logger.error("Arquivo de backup não existe")
                return False
            
            original_size = original_path.stat().st_size
            backup_size = backup_path.stat().st_size
            
            if backup_size == 0:
                self.logger.error("Backup está vazio")
                return False
            
            # Permitir diferença de até 1% no tamanho
            size_diff_percent = abs(original_size - backup_size) / original_size * 100
            if size_diff_percent > 1.0:
                self.logger.warning(f"Diferença significativa no tamanho: {size_diff_percent:.2f}%")
            
            # Validar que o backup pode ser aberto como planilha Excel
            try:
                wb = load_workbook(backup_path, read_only=True)
                wb.close()
                self.logger.debug("Backup validado como planilha Excel válida")
            except InvalidFileException:
                self.logger.error("Backup não é uma planilha Excel válida")
                return False
            
            # Comparar checksums MD5 para garantir integridade
            original_checksum = self._calculate_file_checksum(original_path)
            backup_checksum = self._calculate_file_checksum(backup_path)
            
            if original_checksum == backup_checksum:
                self.logger.debug("Checksums coincidem - backup íntegro")
                return True
            else:
                self.logger.error("Checksums diferentes - possível corrupção")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro na validação de integridade: {e}")
            return False
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """
        Calcula checksum MD5 de um arquivo.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Checksum MD5 em hexadecimal
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _cleanup_old_backups(self) -> None:
        """
        Remove backups antigos conforme política de retenção (Passo 4.5).
        
        Mantém apenas backups dos últimos N dias (configurável).
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            removed_count = 0
            
            # Listar todos os arquivos de backup
            backup_files = list(self.backup_folder.glob('*_planilha_consolidada.xlsx'))
            
            for backup_file in backup_files:
                try:
                    # Extrair data do nome do arquivo
                    filename = backup_file.stem
                    date_part = filename.split('_')[0] + '_' + filename.split('_')[1]
                    file_date = datetime.strptime(date_part, "%Y-%m-%d_%H-%M-%S")
                    
                    if file_date < cutoff_date:
                        backup_file.unlink()
                        removed_count += 1
                        self.logger.debug(f"Backup antigo removido: {backup_file.name}")
                        
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Não foi possível processar arquivo: {backup_file.name} - {e}")
                    continue
            
            if removed_count > 0:
                self.logger.info(f"Limpeza concluída: {removed_count} backups antigos removidos")
            else:
                self.logger.debug("Nenhum backup antigo para remover")
                
        except Exception as e:
            self.logger.error(f"Erro na limpeza de backups antigos: {e}")
    
    def list_backups(self) -> List[Tuple[Path, datetime]]:
        """
        Lista todos os backups disponíveis com suas datas.
        
        Returns:
            Lista de tuplas (caminho_do_backup, data_criacao)
        """
        backups = []
        
        try:
            backup_files = list(self.backup_folder.glob('*_planilha_consolidada.xlsx'))
            
            for backup_file in backup_files:
                try:
                    # Extrair data do nome do arquivo
                    filename = backup_file.stem
                    date_part = filename.split('_')[0] + '_' + filename.split('_')[1]
                    file_date = datetime.strptime(date_part, "%Y-%m-%d_%H-%M-%S")
                    backups.append((backup_file, file_date))
                except (ValueError, IndexError):
                    continue
            
            # Ordenar por data (mais recente primeiro)
            backups.sort(key=lambda x: x[1], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Erro ao listar backups: {e}")
        
        return backups
    
    def restore_backup(self, backup_path: Path) -> bool:
        """
        Restaura um backup específico como planilha mestre.
        
        Args:
            backup_path: Caminho do backup a ser restaurado
            
        Returns:
            True se a restauração foi bem-sucedida
            
        Raises:
            BackupError: Se houver erro durante a restauração
        """
        try:
            if not backup_path.exists():
                raise BackupError(f"Backup não encontrado: {backup_path}")
            
            master_path = self.master_folder / self.master_filename
            
            # Criar backup da planilha mestre atual antes de restaurar
            if master_path.exists():
                current_backup = self.create_backup()
                self.logger.info(f"Backup atual criado antes da restauração: {current_backup}")
            
            # Copiar backup para pasta mestre
            shutil.copy2(backup_path, master_path)
            
            # Validar restauração
            if self._validate_backup_integrity(backup_path, master_path):
                self.logger.info(f"Backup restaurado com sucesso: {backup_path} -> {master_path}")
                return True
            else:
                raise BackupError("Falha na validação após restauração")
                
        except Exception as e:
            self.logger.error(f"Erro ao restaurar backup: {e}")
            raise BackupError(f"Erro ao restaurar backup: {e}")
    
    def get_backup_statistics(self) -> dict:
        """
        Retorna estatísticas dos backups.
        
        Returns:
            Dicionário com estatísticas dos backups
        """
        try:
            backups = self.list_backups()
            
            if not backups:
                return {
                    'total_backups': 0,
                    'oldest_backup': None,
                    'newest_backup': None,
                    'total_size_mb': 0
                }
            
            total_size = sum(backup[0].stat().st_size for backup in backups)
            
            return {
                'total_backups': len(backups),
                'oldest_backup': backups[-1][1].strftime('%Y-%m-%d %H:%M:%S'),
                'newest_backup': backups[0][1].strftime('%Y-%m-%d %H:%M:%S'),
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular estatísticas: {e}")
            return {}
    
    def check_disk_space(self, required_mb: float = 100) -> bool:
        """
        Verifica se há espaço suficiente em disco para backup.
        
        Args:
            required_mb: Espaço mínimo necessário em MB
            
        Returns:
            True se há espaço suficiente
        """
        try:
            stat = shutil.disk_usage(self.backup_folder)
            free_mb = stat.free / (1024 * 1024)
            
            if free_mb < required_mb:
                self.logger.warning(f"Espaço em disco insuficiente: {free_mb:.2f}MB disponível, {required_mb}MB necessário")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar espaço em disco: {e}")
            return False