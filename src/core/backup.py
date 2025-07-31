"""Sistema de backup para o projeto Pulse.

Este módulo implementa backup automático e versionamento de planilhas,
garantindo segurança e recuperação de dados.
"""

import os
import shutil
import zipfile
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import config
from .exceptions import BackupError, FileException
from .logger import get_logger
from .metrics import metrics_collector
from .cache import cache_manager

logger = get_logger(__name__)


class BackupType(Enum):
    """Tipos de backup."""
    FULL = "full"  # Backup completo
    INCREMENTAL = "incremental"  # Apenas alterações
    DIFFERENTIAL = "differential"  # Alterações desde último full
    SNAPSHOT = "snapshot"  # Snapshot pontual


class BackupStatus(Enum):
    """Status do backup."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CompressionLevel(Enum):
    """Níveis de compressão."""
    NONE = 0
    FAST = 1
    NORMAL = 6
    BEST = 9


@dataclass
class BackupMetadata:
    """Metadados de um backup."""
    backup_id: str
    backup_type: BackupType
    timestamp: datetime
    source_path: Path
    backup_path: Path
    file_count: int = 0
    total_size: int = 0
    compressed_size: int = 0
    duration: float = 0.0
    status: BackupStatus = BackupStatus.PENDING
    checksum: Optional[str] = None
    parent_backup_id: Optional[str] = None  # Para backups incrementais
    files_included: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "backup_id": self.backup_id,
            "backup_type": self.backup_type.value,
            "timestamp": self.timestamp.isoformat(),
            "source_path": str(self.source_path),
            "backup_path": str(self.backup_path),
            "file_count": self.file_count,
            "total_size": self.total_size,
            "compressed_size": self.compressed_size,
            "duration": self.duration,
            "status": self.status.value,
            "checksum": self.checksum,
            "parent_backup_id": self.parent_backup_id,
            "files_included": self.files_included,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackupMetadata':
        """Cria instância a partir de dicionário."""
        return cls(
            backup_id=data["backup_id"],
            backup_type=BackupType(data["backup_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source_path=Path(data["source_path"]),
            backup_path=Path(data["backup_path"]),
            file_count=data.get("file_count", 0),
            total_size=data.get("total_size", 0),
            compressed_size=data.get("compressed_size", 0),
            duration=data.get("duration", 0.0),
            status=BackupStatus(data.get("status", "pending")),
            checksum=data.get("checksum"),
            parent_backup_id=data.get("parent_backup_id"),
            files_included=data.get("files_included", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class BackupConfig:
    """Configuração de backup."""
    backup_dir: Path
    max_backups: int = 10
    compression_level: CompressionLevel = CompressionLevel.NORMAL
    include_patterns: List[str] = field(default_factory=lambda: ['*.xlsx', '*.xls', '*.csv'])
    exclude_patterns: List[str] = field(default_factory=lambda: ['~$*', '.tmp'])
    auto_cleanup: bool = True
    verify_integrity: bool = True
    parallel_processing: bool = True
    max_workers: int = 4


class BackupManager:
    """Gerenciador de backups."""
    
    def __init__(self, backup_config: Optional[BackupConfig] = None):
        self.config = backup_config or BackupConfig(
            backup_dir=config.BACKUP_DIR,
            max_backups=config.BACKUP_RETENTION_DAYS,
            compression_level=CompressionLevel.NORMAL
        )
        
        self.logger = get_logger(self.__class__.__name__)
        self._lock = threading.RLock()
        self._active_backups: Dict[str, BackupMetadata] = {}
        
        # Garante que diretório de backup existe
        self.config.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Carrega histórico de backups
        self._load_backup_history()
        
        self.logger.info(f"BackupManager inicializado: {self.config.backup_dir}")
    
    def create_backup(self, source_path: Path, backup_type: BackupType = BackupType.FULL,
                     backup_name: Optional[str] = None) -> BackupMetadata:
        """Cria um backup.
        
        Args:
            source_path: Caminho do arquivo/diretório a fazer backup
            backup_type: Tipo de backup
            backup_name: Nome personalizado do backup
            
        Returns:
            Metadados do backup criado
        """
        if not source_path.exists():
            raise BackupError(f"Caminho não existe: {source_path}")
        
        # Gera ID único para o backup
        timestamp = datetime.now()
        backup_id = self._generate_backup_id(source_path, timestamp, backup_name)
        
        # Cria metadados
        backup_path = self.config.backup_dir / f"{backup_id}.zip"
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=backup_type,
            timestamp=timestamp,
            source_path=source_path,
            backup_path=backup_path
        )
        
        with self._lock:
            self._active_backups[backup_id] = metadata
        
        try:
            # Executa backup
            self._execute_backup(metadata)
            
            # Salva metadados
            self._save_backup_metadata(metadata)
            
            # Limpeza automática
            if self.config.auto_cleanup:
                self._cleanup_old_backups()
            
            self.logger.info(
                f"Backup criado com sucesso: {backup_id}",
                backup_type=backup_type.value,
                file_count=metadata.file_count,
                size_mb=metadata.total_size / (1024 * 1024),
                duration=metadata.duration
            )
            
            return metadata
            
        except Exception as e:
            metadata.status = BackupStatus.FAILED
            self.logger.error(f"Erro ao criar backup {backup_id}: {e}")
            raise BackupError(f"Falha no backup: {e}") from e
        
        finally:
            with self._lock:
                if backup_id in self._active_backups:
                    del self._active_backups[backup_id]
    
    def restore_backup(self, backup_id: str, restore_path: Path, 
                      overwrite: bool = False) -> bool:
        """Restaura um backup.
        
        Args:
            backup_id: ID do backup a restaurar
            restore_path: Caminho onde restaurar
            overwrite: Se deve sobrescrever arquivos existentes
            
        Returns:
            True se restauração foi bem-sucedida
        """
        metadata = self.get_backup_metadata(backup_id)
        if not metadata:
            raise BackupError(f"Backup não encontrado: {backup_id}")
        
        if not metadata.backup_path.exists():
            raise BackupError(f"Arquivo de backup não existe: {metadata.backup_path}")
        
        try:
            # Verifica integridade
            if self.config.verify_integrity and not self._verify_backup_integrity(metadata):
                raise BackupError(f"Backup corrompido: {backup_id}")
            
            # Cria diretório de destino
            restore_path.mkdir(parents=True, exist_ok=True)
            
            # Extrai backup
            with zipfile.ZipFile(metadata.backup_path, 'r') as zip_file:
                for member in zip_file.namelist():
                    target_path = restore_path / member
                    
                    # Verifica se deve sobrescrever
                    if target_path.exists() and not overwrite:
                        self.logger.warning(f"Arquivo já existe, pulando: {target_path}")
                        continue
                    
                    # Extrai arquivo
                    zip_file.extract(member, restore_path)
            
            self.logger.info(f"Backup restaurado: {backup_id} -> {restore_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao restaurar backup {backup_id}: {e}")
            raise BackupError(f"Falha na restauração: {e}") from e
    
    def list_backups(self, source_path: Optional[Path] = None) -> List[BackupMetadata]:
        """Lista backups disponíveis.
        
        Args:
            source_path: Filtrar por caminho de origem
            
        Returns:
            Lista de metadados de backups
        """
        backups = []
        
        # Busca arquivos de metadados
        for metadata_file in self.config.backup_dir.glob("*.json"):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                metadata = BackupMetadata.from_dict(data)
                
                # Filtra por caminho se especificado
                if source_path is None or metadata.source_path == source_path:
                    backups.append(metadata)
                    
            except Exception as e:
                self.logger.warning(f"Erro ao carregar metadados {metadata_file}: {e}")
        
        # Ordena por timestamp (mais recente primeiro)
        backups.sort(key=lambda x: x.timestamp, reverse=True)
        
        return backups
    
    def get_backup_metadata(self, backup_id: str) -> Optional[BackupMetadata]:
        """Obtém metadados de um backup específico.
        
        Args:
            backup_id: ID do backup
            
        Returns:
            Metadados do backup ou None se não encontrado
        """
        metadata_file = self.config.backup_dir / f"{backup_id}.json"
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return BackupMetadata.from_dict(data)
        except Exception as e:
            self.logger.error(f"Erro ao carregar metadados {backup_id}: {e}")
            return None
    
    def delete_backup(self, backup_id: str) -> bool:
        """Deleta um backup.
        
        Args:
            backup_id: ID do backup a deletar
            
        Returns:
            True se deletado com sucesso
        """
        metadata = self.get_backup_metadata(backup_id)
        if not metadata:
            return False
        
        try:
            # Remove arquivo de backup
            if metadata.backup_path.exists():
                metadata.backup_path.unlink()
            
            # Remove metadados
            metadata_file = self.config.backup_dir / f"{backup_id}.json"
            if metadata_file.exists():
                metadata_file.unlink()
            
            self.logger.info(f"Backup deletado: {backup_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao deletar backup {backup_id}: {e}")
            return False
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas de backups.
        
        Returns:
            Dicionário com estatísticas
        """
        backups = self.list_backups()
        
        total_size = sum(backup.compressed_size for backup in backups)
        total_files = sum(backup.file_count for backup in backups)
        
        by_type = {}
        for backup_type in BackupType:
            count = len([b for b in backups if b.backup_type == backup_type])
            by_type[backup_type.value] = count
        
        return {
            "total_backups": len(backups),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "total_files": total_files,
            "by_type": by_type,
            "oldest_backup": backups[-1].timestamp.isoformat() if backups else None,
            "newest_backup": backups[0].timestamp.isoformat() if backups else None,
            "backup_directory": str(self.config.backup_dir)
        }
    
    def _execute_backup(self, metadata: BackupMetadata) -> None:
        """Executa o backup."""
        import time
        start_time = time.time()
        
        metadata.status = BackupStatus.IN_PROGRESS
        
        try:
            if metadata.source_path.is_file():
                self._backup_file(metadata)
            else:
                self._backup_directory(metadata)
            
            # Calcula checksum
            if self.config.verify_integrity:
                metadata.checksum = self._calculate_backup_checksum(metadata.backup_path)
            
            metadata.status = BackupStatus.COMPLETED
            metadata.duration = time.time() - start_time
            
        except Exception as e:
            metadata.status = BackupStatus.FAILED
            raise
    
    def _backup_file(self, metadata: BackupMetadata) -> None:
        """Faz backup de um arquivo único."""
        with zipfile.ZipFile(metadata.backup_path, 'w', 
                           compression=zipfile.ZIP_DEFLATED,
                           compresslevel=self.config.compression_level.value) as zip_file:
            
            zip_file.write(metadata.source_path, metadata.source_path.name)
            
            metadata.file_count = 1
            metadata.total_size = metadata.source_path.stat().st_size
            metadata.files_included = [str(metadata.source_path)]
        
        metadata.compressed_size = metadata.backup_path.stat().st_size
    
    def _backup_directory(self, metadata: BackupMetadata) -> None:
        """Faz backup de um diretório."""
        files_to_backup = self._get_files_to_backup(metadata.source_path)
        
        with zipfile.ZipFile(metadata.backup_path, 'w',
                           compression=zipfile.ZIP_DEFLATED,
                           compresslevel=self.config.compression_level.value) as zip_file:
            
            total_size = 0
            
            if self.config.parallel_processing and len(files_to_backup) > 10:
                # Processamento paralelo para muitos arquivos
                self._backup_files_parallel(zip_file, files_to_backup, metadata)
            else:
                # Processamento sequencial
                for file_path in files_to_backup:
                    relative_path = file_path.relative_to(metadata.source_path)
                    zip_file.write(file_path, relative_path)
                    total_size += file_path.stat().st_size
            
            metadata.file_count = len(files_to_backup)
            metadata.total_size = total_size
            metadata.files_included = [str(f) for f in files_to_backup]
        
        metadata.compressed_size = metadata.backup_path.stat().st_size
    
    def _backup_files_parallel(self, zip_file: zipfile.ZipFile, 
                              files: List[Path], metadata: BackupMetadata) -> None:
        """Faz backup de arquivos em paralelo."""
        # Nota: ZipFile não é thread-safe, então coletamos dados em paralelo
        # e escrevemos sequencialmente
        
        def read_file_data(file_path: Path) -> Tuple[Path, bytes, Path]:
            with open(file_path, 'rb') as f:
                data = f.read()
            relative_path = file_path.relative_to(metadata.source_path)
            return file_path, data, relative_path
        
        total_size = 0
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submete tarefas de leitura
            future_to_file = {executor.submit(read_file_data, f): f for f in files}
            
            # Processa resultados conforme completam
            for future in as_completed(future_to_file):
                try:
                    file_path, data, relative_path = future.result()
                    
                    # Escreve no zip (thread-safe porque é sequencial)
                    zip_file.writestr(str(relative_path), data)
                    total_size += len(data)
                    
                except Exception as e:
                    file_path = future_to_file[future]
                    self.logger.warning(f"Erro ao processar {file_path}: {e}")
        
        metadata.total_size = total_size
    
    def _get_files_to_backup(self, directory: Path) -> List[Path]:
        """Obtém lista de arquivos para backup."""
        files = []
        
        for pattern in self.config.include_patterns:
            files.extend(directory.rglob(pattern))
        
        # Remove duplicatas
        files = list(set(files))
        
        # Aplica filtros de exclusão
        filtered_files = []
        for file_path in files:
            if file_path.is_file():
                # Verifica padrões de exclusão
                exclude = False
                for exclude_pattern in self.config.exclude_patterns:
                    if file_path.match(exclude_pattern):
                        exclude = True
                        break
                
                if not exclude:
                    filtered_files.append(file_path)
        
        return filtered_files
    
    def _generate_backup_id(self, source_path: Path, timestamp: datetime, 
                           backup_name: Optional[str] = None) -> str:
        """Gera ID único para backup."""
        if backup_name:
            base_name = backup_name
        else:
            base_name = source_path.name
        
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp_str}"
    
    def _calculate_backup_checksum(self, backup_path: Path) -> str:
        """Calcula checksum do arquivo de backup."""
        hash_md5 = hashlib.md5()
        with open(backup_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _verify_backup_integrity(self, metadata: BackupMetadata) -> bool:
        """Verifica integridade do backup."""
        if not metadata.checksum:
            return True  # Sem checksum para verificar
        
        try:
            current_checksum = self._calculate_backup_checksum(metadata.backup_path)
            return current_checksum == metadata.checksum
        except Exception as e:
            self.logger.error(f"Erro ao verificar integridade: {e}")
            return False
    
    def _save_backup_metadata(self, metadata: BackupMetadata) -> None:
        """Salva metadados do backup."""
        metadata_file = self.config.backup_dir / f"{metadata.backup_id}.json"
        
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Erro ao salvar metadados: {e}")
            raise
    
    def _load_backup_history(self) -> None:
        """Carrega histórico de backups."""
        try:
            backups = self.list_backups()
            self.logger.info(f"Carregados {len(backups)} backups do histórico")
        except Exception as e:
            self.logger.warning(f"Erro ao carregar histórico: {e}")
    
    def _cleanup_old_backups(self) -> None:
        """Remove backups antigos conforme política de retenção."""
        try:
            backups = self.list_backups()
            
            if len(backups) <= self.config.max_backups:
                return
            
            # Remove backups mais antigos
            backups_to_remove = backups[self.config.max_backups:]
            
            for backup in backups_to_remove:
                self.delete_backup(backup.backup_id)
            
            self.logger.info(f"Removidos {len(backups_to_remove)} backups antigos")
            
        except Exception as e:
            self.logger.error(f"Erro na limpeza de backups: {e}")


class AutoBackupScheduler:
    """Agendador de backups automáticos."""
    
    def __init__(self, backup_manager: BackupManager):
        self.backup_manager = backup_manager
        self.logger = get_logger(self.__class__.__name__)
        
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._backup_schedules: Dict[str, Dict[str, Any]] = {}
    
    def schedule_backup(self, source_path: Path, interval_hours: int = 24,
                      backup_type: BackupType = BackupType.INCREMENTAL) -> str:
        """Agenda backup automático.
        
        Args:
            source_path: Caminho a fazer backup
            interval_hours: Intervalo em horas
            backup_type: Tipo de backup
            
        Returns:
            ID do agendamento
        """
        schedule_id = f"auto_{source_path.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self._backup_schedules[schedule_id] = {
            "source_path": source_path,
            "interval_hours": interval_hours,
            "backup_type": backup_type,
            "last_backup": None,
            "next_backup": datetime.now() + timedelta(hours=interval_hours)
        }
        
        self.logger.info(f"Backup agendado: {schedule_id} (intervalo: {interval_hours}h)")
        return schedule_id
    
    def start(self) -> None:
        """Inicia agendador."""
        if self._running:
            return
        
        self._running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        
        self.logger.info("Agendador de backups iniciado")
    
    def stop(self) -> None:
        """Para agendador."""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        
        self.logger.info("Agendador de backups parado")
    
    def _scheduler_loop(self) -> None:
        """Loop principal do agendador."""
        while self._running:
            try:
                now = datetime.now()
                
                for schedule_id, schedule in self._backup_schedules.items():
                    if now >= schedule["next_backup"]:
                        self._execute_scheduled_backup(schedule_id, schedule)
                
                # Verifica a cada minuto
                threading.Event().wait(60)
                
            except Exception as e:
                self.logger.error(f"Erro no agendador: {e}")
                threading.Event().wait(60)
    
    def _execute_scheduled_backup(self, schedule_id: str, schedule: Dict[str, Any]) -> None:
        """Executa backup agendado."""
        try:
            source_path = schedule["source_path"]
            backup_type = schedule["backup_type"]
            
            self.logger.info(f"Executando backup agendado: {schedule_id}")
            
            metadata = self.backup_manager.create_backup(source_path, backup_type)
            
            # Atualiza agendamento
            schedule["last_backup"] = datetime.now()
            schedule["next_backup"] = datetime.now() + timedelta(hours=schedule["interval_hours"])
            
            self.logger.info(f"Backup agendado concluído: {metadata.backup_id}")
            
        except Exception as e:
            self.logger.error(f"Erro em backup agendado {schedule_id}: {e}")


# Instância global do gerenciador de backup
backup_manager = BackupManager()


# Funções de conveniência
def create_backup(source_path: Path, backup_type: BackupType = BackupType.FULL) -> BackupMetadata:
    """Cria backup de um arquivo/diretório."""
    return backup_manager.create_backup(source_path, backup_type)

def restore_backup(backup_id: str, restore_path: Path, overwrite: bool = False) -> bool:
    """Restaura um backup."""
    return backup_manager.restore_backup(backup_id, restore_path, overwrite)

def list_backups(source_path: Optional[Path] = None) -> List[BackupMetadata]:
    """Lista backups disponíveis."""
    return backup_manager.list_backups(source_path)

def get_backup_stats() -> Dict[str, Any]:
    """Obtém estatísticas de backups."""
    return backup_manager.get_backup_stats()

def backup_master_spreadsheet(master_path: Optional[Path] = None) -> BackupMetadata:
    """Faz backup da planilha mestre.
    
    Args:
        master_path: Caminho da planilha mestre (usa config se None)
        
    Returns:
        Metadados do backup criado
    """
    if master_path is None:
        master_path = config.paths.mestre_dir
    
    return create_backup(master_path, BackupType.FULL)