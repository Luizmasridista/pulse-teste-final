"""Sistema de monitoramento de arquivos para o projeto Pulse.

Este módulo implementa monitoramento inteligente de alterações em planilhas,
detecção de modificações e sincronização automática.
"""

import os
import time
import hashlib
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Set, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None

from .config import config
from .exceptions import MonitoringError, FileException
from .logger import get_logger
from .metrics import metrics_collector
from .cache import cache_manager

logger = get_logger(__name__)


class ChangeType(Enum):
    """Tipos de alterações em arquivos."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"
    CONTENT_CHANGED = "content_changed"
    METADATA_CHANGED = "metadata_changed"


class MonitoringMode(Enum):
    """Modos de monitoramento."""
    POLLING = "polling"  # Verificação periódica
    REALTIME = "realtime"  # Monitoramento em tempo real (watchdog)
    HYBRID = "hybrid"  # Combinação de ambos


@dataclass
class FileChange:
    """Representa uma alteração em arquivo."""
    file_path: Path
    change_type: ChangeType
    timestamp: datetime
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    old_size: Optional[int] = None
    new_size: Optional[int] = None
    old_modified: Optional[datetime] = None
    new_modified: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "file_path": str(self.file_path),
            "change_type": self.change_type.value,
            "timestamp": self.timestamp.isoformat(),
            "old_hash": self.old_hash,
            "new_hash": self.new_hash,
            "old_size": self.old_size,
            "new_size": self.new_size,
            "old_modified": self.old_modified.isoformat() if self.old_modified else None,
            "new_modified": self.new_modified.isoformat() if self.new_modified else None,
            "metadata": self.metadata
        }


@dataclass
class FileSnapshot:
    """Snapshot de um arquivo em um momento específico."""
    file_path: Path
    exists: bool
    size: Optional[int] = None
    modified_time: Optional[datetime] = None
    content_hash: Optional[str] = None
    permissions: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_file(cls, file_path: Path, calculate_hash: bool = True) -> 'FileSnapshot':
        """Cria snapshot de um arquivo.
        
        Args:
            file_path: Caminho do arquivo
            calculate_hash: Se deve calcular hash do conteúdo
            
        Returns:
            Snapshot do arquivo
        """
        if not file_path.exists():
            return cls(file_path=file_path, exists=False)
        
        try:
            stat = file_path.stat()
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            size = stat.st_size
            permissions = oct(stat.st_mode)[-3:]
            
            content_hash = None
            if calculate_hash and file_path.is_file():
                content_hash = cls._calculate_file_hash(file_path)
            
            return cls(
                file_path=file_path,
                exists=True,
                size=size,
                modified_time=modified_time,
                content_hash=content_hash,
                permissions=permissions
            )
            
        except Exception as e:
            logger.warning(f"Erro ao criar snapshot de {file_path}: {e}")
            return cls(file_path=file_path, exists=False)
    
    @staticmethod
    def _calculate_file_hash(file_path: Path) -> str:
        """Calcula hash MD5 do arquivo."""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def compare_with(self, other: 'FileSnapshot') -> List[ChangeType]:
        """Compara com outro snapshot.
        
        Args:
            other: Outro snapshot para comparar
            
        Returns:
            Lista de tipos de alterações detectadas
        """
        changes = []
        
        # Arquivo criado
        if not self.exists and other.exists:
            changes.append(ChangeType.CREATED)
        
        # Arquivo deletado
        elif self.exists and not other.exists:
            changes.append(ChangeType.DELETED)
        
        # Arquivo modificado
        elif self.exists and other.exists:
            # Verifica conteúdo
            if self.content_hash and other.content_hash and self.content_hash != other.content_hash:
                changes.append(ChangeType.CONTENT_CHANGED)
            
            # Verifica metadados
            elif (self.size != other.size or 
                  self.modified_time != other.modified_time or 
                  self.permissions != other.permissions):
                changes.append(ChangeType.METADATA_CHANGED)
        
        return changes


class FileMonitorEventHandler(FileSystemEventHandler):
    """Handler de eventos do sistema de arquivos."""
    
    def __init__(self, monitor: 'FileMonitor'):
        super().__init__()
        self.monitor = monitor
        self.logger = get_logger(self.__class__.__name__)
    
    def on_modified(self, event):
        if not event.is_directory:
            self.monitor._queue_change(Path(event.src_path), ChangeType.MODIFIED)
    
    def on_created(self, event):
        if not event.is_directory:
            self.monitor._queue_change(Path(event.src_path), ChangeType.CREATED)
    
    def on_deleted(self, event):
        if not event.is_directory:
            self.monitor._queue_change(Path(event.src_path), ChangeType.DELETED)
    
    def on_moved(self, event):
        if not event.is_directory:
            self.monitor._queue_change(Path(event.dest_path), ChangeType.MOVED)


class FileMonitor:
    """Monitor de arquivos com suporte a diferentes modos."""
    
    def __init__(self, mode: MonitoringMode = MonitoringMode.HYBRID):
        self.mode = mode
        self.logger = get_logger(self.__class__.__name__)
        
        # Estado interno
        self._watched_files: Dict[Path, FileSnapshot] = {}
        self._watched_directories: Set[Path] = set()
        self._callbacks: List[Callable[[FileChange], None]] = []
        self._running = False
        self._polling_interval = config.monitoring.polling_interval
        
        # Threading
        self._polling_thread: Optional[threading.Thread] = None
        self._processing_thread: Optional[threading.Thread] = None
        self._change_queue: Queue = Queue()
        self._lock = threading.RLock()
        
        # Watchdog (tempo real)
        self._observer: Optional[Observer] = None
        self._event_handler: Optional[FileMonitorEventHandler] = None
        
        # Estatísticas
        self._stats = {
            "changes_detected": 0,
            "files_monitored": 0,
            "directories_monitored": 0,
            "last_scan": None,
            "scan_duration": 0
        }
        
        self.logger.info(f"FileMonitor inicializado com modo: {mode.value}")
    
    def add_file(self, file_path: Path, calculate_hash: bool = True) -> None:
        """Adiciona arquivo para monitoramento.
        
        Args:
            file_path: Caminho do arquivo
            calculate_hash: Se deve calcular hash inicial
        """
        with self._lock:
            snapshot = FileSnapshot.from_file(file_path, calculate_hash)
            self._watched_files[file_path] = snapshot
            self._stats["files_monitored"] = len(self._watched_files)
            
            self.logger.debug(f"Arquivo adicionado ao monitoramento: {file_path}")
    
    def add_directory(self, directory_path: Path, recursive: bool = True, 
                     file_patterns: Optional[List[str]] = None) -> None:
        """Adiciona diretório para monitoramento.
        
        Args:
            directory_path: Caminho do diretório
            recursive: Se deve monitorar subdiretórios
            file_patterns: Padrões de arquivos a monitorar (ex: ['*.xlsx', '*.csv'])
        """
        if not directory_path.exists() or not directory_path.is_dir():
            raise MonitoringError(f"Diretório inválido: {directory_path}")
        
        with self._lock:
            self._watched_directories.add(directory_path)
            
            # Adiciona arquivos existentes
            patterns = file_patterns or ['*']
            for pattern in patterns:
                if recursive:
                    files = directory_path.rglob(pattern)
                else:
                    files = directory_path.glob(pattern)
                
                for file_path in files:
                    if file_path.is_file():
                        self.add_file(file_path)
            
            self._stats["directories_monitored"] = len(self._watched_directories)
            
            self.logger.info(f"Diretório adicionado ao monitoramento: {directory_path}")
    
    def remove_file(self, file_path: Path) -> None:
        """Remove arquivo do monitoramento."""
        with self._lock:
            if file_path in self._watched_files:
                del self._watched_files[file_path]
                self._stats["files_monitored"] = len(self._watched_files)
                self.logger.debug(f"Arquivo removido do monitoramento: {file_path}")
    
    def add_callback(self, callback: Callable[[FileChange], None]) -> None:
        """Adiciona callback para alterações.
        
        Args:
            callback: Função a ser chamada quando houver alterações
        """
        self._callbacks.append(callback)
        self.logger.debug(f"Callback adicionado: {callback.__name__}")
    
    def start(self) -> None:
        """Inicia o monitoramento."""
        if self._running:
            self.logger.warning("Monitor já está em execução")
            return
        
        self._running = True
        
        # Inicia thread de processamento de mudanças
        self._processing_thread = threading.Thread(target=self._process_changes, daemon=True)
        self._processing_thread.start()
        
        # Inicia monitoramento em tempo real (se disponível e configurado)
        if (self.mode in [MonitoringMode.REALTIME, MonitoringMode.HYBRID] and 
            WATCHDOG_AVAILABLE and self._watched_directories):
            self._start_realtime_monitoring()
        
        # Inicia polling (se configurado)
        if self.mode in [MonitoringMode.POLLING, MonitoringMode.HYBRID]:
            self._start_polling()
        
        self.logger.info("Monitoramento iniciado")
    
    def stop(self) -> None:
        """Para o monitoramento."""
        if not self._running:
            return
        
        self._running = False
        
        # Para watchdog
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
        
        # Para threads
        if self._polling_thread:
            self._polling_thread.join(timeout=5)
        
        if self._processing_thread:
            self._processing_thread.join(timeout=5)
        
        self.logger.info("Monitoramento parado")
    
    def scan_now(self) -> List[FileChange]:
        """Executa varredura imediata.
        
        Returns:
            Lista de alterações detectadas
        """
        start_time = time.time()
        changes = []
        
        with self._lock:
            for file_path, old_snapshot in self._watched_files.items():
                new_snapshot = FileSnapshot.from_file(file_path)
                change_types = old_snapshot.compare_with(new_snapshot)
                
                for change_type in change_types:
                    change = FileChange(
                        file_path=file_path,
                        change_type=change_type,
                        timestamp=datetime.now(),
                        old_hash=old_snapshot.content_hash,
                        new_hash=new_snapshot.content_hash,
                        old_size=old_snapshot.size,
                        new_size=new_snapshot.size,
                        old_modified=old_snapshot.modified_time,
                        new_modified=new_snapshot.modified_time
                    )
                    changes.append(change)
                
                # Atualiza snapshot
                self._watched_files[file_path] = new_snapshot
        
        scan_duration = time.time() - start_time
        self._stats["last_scan"] = datetime.now()
        self._stats["scan_duration"] = scan_duration
        
        # Processa alterações
        for change in changes:
            self._notify_callbacks(change)
        
        if changes:
            self.logger.info(f"Varredura detectou {len(changes)} alterações em {scan_duration:.2f}s")
        
        return changes
    
    def get_file_status(self, file_path: Path) -> Optional[FileSnapshot]:
        """Obtém status atual de um arquivo.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Snapshot atual do arquivo ou None se não monitorado
        """
        with self._lock:
            return self._watched_files.get(file_path)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do monitor."""
        with self._lock:
            return self._stats.copy()
    
    def _start_realtime_monitoring(self) -> None:
        """Inicia monitoramento em tempo real."""
        if not WATCHDOG_AVAILABLE:
            self.logger.warning("Watchdog não disponível, usando apenas polling")
            return
        
        self._observer = Observer()
        self._event_handler = FileMonitorEventHandler(self)
        
        for directory in self._watched_directories:
            self._observer.schedule(self._event_handler, str(directory), recursive=True)
        
        self._observer.start()
        self.logger.info("Monitoramento em tempo real iniciado")
    
    def _start_polling(self) -> None:
        """Inicia polling."""
        self._polling_thread = threading.Thread(target=self._polling_loop, daemon=True)
        self._polling_thread.start()
        self.logger.info(f"Polling iniciado (intervalo: {self._polling_interval}s)")
    
    def _polling_loop(self) -> None:
        """Loop principal de polling."""
        while self._running:
            try:
                self.scan_now()
                time.sleep(self._polling_interval)
            except Exception as e:
                self.logger.error(f"Erro no polling: {e}")
                time.sleep(self._polling_interval)
    
    def _queue_change(self, file_path: Path, change_type: ChangeType) -> None:
        """Adiciona alteração à fila de processamento."""
        try:
            self._change_queue.put((file_path, change_type, datetime.now()), timeout=1)
        except Exception as e:
            self.logger.warning(f"Erro ao enfileirar alteração: {e}")
    
    def _process_changes(self) -> None:
        """Processa alterações da fila."""
        while self._running:
            try:
                file_path, change_type, timestamp = self._change_queue.get(timeout=1)
                
                # Cria objeto de alteração
                with self._lock:
                    old_snapshot = self._watched_files.get(file_path)
                
                new_snapshot = FileSnapshot.from_file(file_path)
                
                change = FileChange(
                    file_path=file_path,
                    change_type=change_type,
                    timestamp=timestamp,
                    old_hash=old_snapshot.content_hash if old_snapshot else None,
                    new_hash=new_snapshot.content_hash,
                    old_size=old_snapshot.size if old_snapshot else None,
                    new_size=new_snapshot.size,
                    old_modified=old_snapshot.modified_time if old_snapshot else None,
                    new_modified=new_snapshot.modified_time
                )
                
                # Atualiza snapshot
                with self._lock:
                    self._watched_files[file_path] = new_snapshot
                
                # Notifica callbacks
                self._notify_callbacks(change)
                
                self._change_queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Erro ao processar alteração: {e}")
    
    def _notify_callbacks(self, change: FileChange) -> None:
        """Notifica callbacks sobre alteração."""
        self._stats["changes_detected"] += 1
        
        # Registra métricas
        metrics_collector.record_metric(
            "file_changes_detected",
            1,
            "count",
            "monitoring",
            {"change_type": change.change_type.value}
        )
        
        # Cache da alteração
        cache_key = f"file_change_{change.file_path}_{change.timestamp.isoformat()}"
        cache_manager.set(cache_key, change.to_dict(), ttl=3600)  # 1 hora
        
        # Notifica callbacks
        for callback in self._callbacks:
            try:
                callback(change)
            except Exception as e:
                self.logger.error(f"Erro em callback {callback.__name__}: {e}")
        
        self.logger.debug(f"Alteração detectada: {change.file_path} ({change.change_type.value})")


class SpreadsheetMonitor:
    """Monitor especializado para planilhas."""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.file_monitor = FileMonitor(MonitoringMode.HYBRID)
        
        # Configurações específicas para planilhas
        self.supported_extensions = {'.xlsx', '.xls', '.csv', '.ods'}
        self.sync_callbacks: List[Callable[[Path], None]] = []
        
        # Adiciona callback para alterações
        self.file_monitor.add_callback(self._handle_spreadsheet_change)
        
        self.logger.info("SpreadsheetMonitor inicializado")
    
    def monitor_subordinate_directory(self, directory: Path) -> None:
        """Monitora diretório de planilhas subordinadas.
        
        Args:
            directory: Diretório a monitorar
        """
        if not directory.exists():
            raise MonitoringError(f"Diretório não existe: {directory}")
        
        # Padrões para planilhas
        patterns = [f"*{ext}" for ext in self.supported_extensions]
        
        self.file_monitor.add_directory(directory, recursive=True, file_patterns=patterns)
        self.logger.info(f"Monitorando planilhas em: {directory}")
    
    def add_sync_callback(self, callback: Callable[[Path], None]) -> None:
        """Adiciona callback para sincronização.
        
        Args:
            callback: Função a ser chamada quando planilha for alterada
        """
        self.sync_callbacks.append(callback)
        self.logger.debug(f"Callback de sincronização adicionado: {callback.__name__}")
    
    def start(self) -> None:
        """Inicia monitoramento."""
        self.file_monitor.start()
        self.logger.info("Monitoramento de planilhas iniciado")
    
    def stop(self) -> None:
        """Para monitoramento."""
        self.file_monitor.stop()
        self.logger.info("Monitoramento de planilhas parado")
    
    def get_monitored_files(self) -> List[Path]:
        """Retorna lista de arquivos monitorados."""
        return list(self.file_monitor._watched_files.keys())
    
    def _handle_spreadsheet_change(self, change: FileChange) -> None:
        """Manipula alterações em planilhas."""
        # Verifica se é planilha
        if change.file_path.suffix.lower() not in self.supported_extensions:
            return
        
        # Log da alteração
        self.logger.info(
            f"Planilha alterada: {change.file_path.name} ({change.change_type.value})",
            file_path=str(change.file_path),
            change_type=change.change_type.value,
            timestamp=change.timestamp.isoformat()
        )
        
        # Notifica callbacks de sincronização
        if change.change_type in [ChangeType.MODIFIED, ChangeType.CONTENT_CHANGED]:
            for callback in self.sync_callbacks:
                try:
                    callback(change.file_path)
                except Exception as e:
                    self.logger.error(f"Erro em callback de sincronização: {e}")
        
        # Registra métricas específicas
        metrics_collector.record_metric(
            "spreadsheet_changes",
            1,
            "count",
            "monitoring",
            {
                "file_extension": change.file_path.suffix.lower(),
                "change_type": change.change_type.value
            }
        )


# Instância global do monitor de planilhas
spreadsheet_monitor = SpreadsheetMonitor()


# Funções de conveniência
def start_monitoring(subordinate_dir: Optional[Path] = None) -> None:
    """Inicia monitoramento de planilhas.
    
    Args:
        subordinate_dir: Diretório de planilhas subordinadas (usa config se None)
    """
    if subordinate_dir is None:
        subordinate_dir = config.paths.subordinadas_dir
    
    spreadsheet_monitor.monitor_subordinate_directory(subordinate_dir)
    spreadsheet_monitor.start()

def stop_monitoring() -> None:
    """Para monitoramento de planilhas."""
    spreadsheet_monitor.stop()

def add_sync_callback(callback: Callable[[Path], None]) -> None:
    """Adiciona callback de sincronização."""
    spreadsheet_monitor.add_sync_callback(callback)

def get_monitoring_stats() -> Dict[str, Any]:
    """Obtém estatísticas de monitoramento."""
    return spreadsheet_monitor.file_monitor.get_stats()