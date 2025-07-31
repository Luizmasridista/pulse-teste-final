"""Sistema de métricas de performance para o projeto Pulse.

Este módulo implementa coleta, análise e relatórios de métricas de performance
para monitorar a eficiência do sistema de consolidação de planilhas.
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from contextlib import contextmanager
from functools import wraps

from .config import config
from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetric:
    """Métrica individual de performance."""
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    category: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte a métrica para dicionário."""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "category": self.category,
            "metadata": self.metadata
        }


@dataclass
class OperationStats:
    """Estatísticas de uma operação."""
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    memory_start_mb: float = 0.0
    memory_end_mb: float = 0.0
    memory_peak_mb: float = 0.0
    cpu_percent: float = 0.0
    files_processed: int = 0
    rows_processed: int = 0
    errors_count: int = 0
    success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def memory_used_mb(self) -> float:
        """Memória utilizada durante a operação."""
        return self.memory_end_mb - self.memory_start_mb
    
    @property
    def processing_rate_rows_per_second(self) -> float:
        """Taxa de processamento em linhas por segundo."""
        if self.duration_seconds > 0 and self.rows_processed > 0:
            return self.rows_processed / self.duration_seconds
        return 0.0
    
    @property
    def processing_rate_files_per_second(self) -> float:
        """Taxa de processamento em arquivos por segundo."""
        if self.duration_seconds > 0 and self.files_processed > 0:
            return self.files_processed / self.duration_seconds
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte as estatísticas para dicionário."""
        return {
            "operation_name": self.operation_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "memory_start_mb": self.memory_start_mb,
            "memory_end_mb": self.memory_end_mb,
            "memory_peak_mb": self.memory_peak_mb,
            "memory_used_mb": self.memory_used_mb,
            "cpu_percent": self.cpu_percent,
            "files_processed": self.files_processed,
            "rows_processed": self.rows_processed,
            "processing_rate_rows_per_second": self.processing_rate_rows_per_second,
            "processing_rate_files_per_second": self.processing_rate_files_per_second,
            "errors_count": self.errors_count,
            "success": self.success,
            "metadata": self.metadata
        }


class MetricsCollector:
    """Coletor de métricas de performance."""
    
    def __init__(self, max_history: int = 1000):
        self.logger = get_logger(self.__class__.__name__)
        self.max_history = max_history
        
        # Armazenamento de métricas
        self.metrics: deque = deque(maxlen=max_history)
        self.operation_stats: deque = deque(maxlen=max_history)
        
        # Operações ativas
        self.active_operations: Dict[str, OperationStats] = {}
        
        # Contadores e agregações
        self.counters: Dict[str, int] = defaultdict(int)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        
        # Lock para thread safety
        self._lock = threading.Lock()
        
        # Processo atual para monitoramento
        self.process = psutil.Process()
        
        self.logger.info("MetricsCollector inicializado", max_history=max_history)
    
    def record_metric(self, name: str, value: float, unit: str = "", 
                     category: str = "general", **metadata) -> None:
        """Registra uma métrica individual.
        
        Args:
            name: Nome da métrica
            value: Valor da métrica
            unit: Unidade de medida
            category: Categoria da métrica
            **metadata: Metadados adicionais
        """
        with self._lock:
            metric = PerformanceMetric(
                name=name,
                value=value,
                unit=unit,
                category=category,
                metadata=metadata
            )
            self.metrics.append(metric)
            
            self.logger.debug(
                f"Métrica registrada: {name}",
                **metric.to_dict()
            )
    
    def start_operation(self, operation_name: str, **metadata) -> str:
        """Inicia o monitoramento de uma operação.
        
        Args:
            operation_name: Nome da operação
            **metadata: Metadados adicionais
            
        Returns:
            ID único da operação
        """
        operation_id = f"{operation_name}_{int(time.time() * 1000)}"
        
        with self._lock:
            stats = OperationStats(
                operation_name=operation_name,
                start_time=datetime.now(),
                memory_start_mb=self._get_memory_usage(),
                metadata=metadata
            )
            self.active_operations[operation_id] = stats
            
            self.logger.info(
                f"Operação iniciada: {operation_name}",
                operation_id=operation_id,
                **metadata
            )
        
        return operation_id
    
    def end_operation(self, operation_id: str, success: bool = True, 
                     files_processed: int = 0, rows_processed: int = 0,
                     errors_count: int = 0, **metadata) -> Optional[OperationStats]:
        """Finaliza o monitoramento de uma operação.
        
        Args:
            operation_id: ID da operação
            success: Se a operação foi bem-sucedida
            files_processed: Número de arquivos processados
            rows_processed: Número de linhas processadas
            errors_count: Número de erros
            **metadata: Metadados adicionais
            
        Returns:
            Estatísticas da operação ou None se não encontrada
        """
        with self._lock:
            if operation_id not in self.active_operations:
                self.logger.warning(f"Operação não encontrada: {operation_id}")
                return None
            
            stats = self.active_operations.pop(operation_id)
            stats.end_time = datetime.now()
            stats.duration_seconds = (stats.end_time - stats.start_time).total_seconds()
            stats.memory_end_mb = self._get_memory_usage()
            stats.memory_peak_mb = max(stats.memory_start_mb, stats.memory_end_mb)
            stats.cpu_percent = self._get_cpu_usage()
            stats.success = success
            stats.files_processed = files_processed
            stats.rows_processed = rows_processed
            stats.errors_count = errors_count
            stats.metadata.update(metadata)
            
            self.operation_stats.append(stats)
            
            # Registra métricas derivadas
            self.record_metric(
                f"{stats.operation_name}_duration",
                stats.duration_seconds,
                "seconds",
                "performance"
            )
            
            self.record_metric(
                f"{stats.operation_name}_memory_used",
                stats.memory_used_mb,
                "MB",
                "memory"
            )
            
            if stats.rows_processed > 0:
                self.record_metric(
                    f"{stats.operation_name}_processing_rate",
                    stats.processing_rate_rows_per_second,
                    "rows/sec",
                    "throughput"
                )
            
            self.logger.info(
                f"Operação finalizada: {stats.operation_name}",
                operation_id=operation_id,
                **stats.to_dict()
            )
        
        return stats
    
    def increment_counter(self, counter_name: str, value: int = 1) -> None:
        """Incrementa um contador.
        
        Args:
            counter_name: Nome do contador
            value: Valor a incrementar
        """
        with self._lock:
            self.counters[counter_name] += value
            
            self.logger.debug(
                f"Contador incrementado: {counter_name}",
                counter=counter_name,
                value=value,
                total=self.counters[counter_name]
            )
    
    def record_timer(self, timer_name: str, duration_seconds: float) -> None:
        """Registra um tempo de execução.
        
        Args:
            timer_name: Nome do timer
            duration_seconds: Duração em segundos
        """
        with self._lock:
            self.timers[timer_name].append(duration_seconds)
            
            # Mantém apenas os últimos N valores
            if len(self.timers[timer_name]) > self.max_history:
                self.timers[timer_name] = self.timers[timer_name][-self.max_history:]
            
            self.logger.debug(
                f"Timer registrado: {timer_name}",
                timer=timer_name,
                duration=duration_seconds
            )
    
    @contextmanager
    def measure_operation(self, operation_name: str, **metadata):
        """Context manager para medir uma operação.
        
        Args:
            operation_name: Nome da operação
            **metadata: Metadados adicionais
            
        Yields:
            Função para atualizar estatísticas da operação
        """
        operation_id = self.start_operation(operation_name, **metadata)
        
        def update_stats(files_processed: int = 0, rows_processed: int = 0, 
                        errors_count: int = 0, **update_metadata):
            """Atualiza estatísticas da operação ativa."""
            if operation_id in self.active_operations:
                stats = self.active_operations[operation_id]
                stats.files_processed = files_processed
                stats.rows_processed = rows_processed
                stats.errors_count = errors_count
                stats.metadata.update(update_metadata)
        
        try:
            yield update_stats
            self.end_operation(operation_id, success=True)
        except Exception as e:
            self.end_operation(operation_id, success=False, errors_count=1)
            raise
    
    def get_system_metrics(self) -> Dict[str, float]:
        """Coleta métricas do sistema.
        
        Returns:
            Dicionário com métricas do sistema
        """
        try:
            return {
                "memory_usage_mb": self._get_memory_usage(),
                "memory_percent": self.process.memory_percent(),
                "cpu_percent": self._get_cpu_usage(),
                "disk_usage_percent": psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 0.0,
                "open_files_count": len(self.process.open_files()) if hasattr(self.process, 'open_files') else 0,
                "threads_count": self.process.num_threads()
            }
        except Exception as e:
            self.logger.error(f"Erro ao coletar métricas do sistema: {str(e)}")
            return {}
    
    def get_operation_summary(self, operation_name: Optional[str] = None,
                            last_n: Optional[int] = None) -> Dict[str, Any]:
        """Gera resumo de operações.
        
        Args:
            operation_name: Filtrar por nome da operação
            last_n: Últimas N operações
            
        Returns:
            Resumo das operações
        """
        with self._lock:
            operations = list(self.operation_stats)
            
            if operation_name:
                operations = [op for op in operations if op.operation_name == operation_name]
            
            if last_n:
                operations = operations[-last_n:]
            
            if not operations:
                return {"total_operations": 0}
            
            # Calcula estatísticas
            durations = [op.duration_seconds for op in operations]
            memory_usage = [op.memory_used_mb for op in operations]
            success_count = sum(1 for op in operations if op.success)
            
            return {
                "total_operations": len(operations),
                "success_rate": success_count / len(operations) if operations else 0,
                "avg_duration_seconds": sum(durations) / len(durations) if durations else 0,
                "min_duration_seconds": min(durations) if durations else 0,
                "max_duration_seconds": max(durations) if durations else 0,
                "avg_memory_usage_mb": sum(memory_usage) / len(memory_usage) if memory_usage else 0,
                "total_files_processed": sum(op.files_processed for op in operations),
                "total_rows_processed": sum(op.rows_processed for op in operations),
                "total_errors": sum(op.errors_count for op in operations),
                "operations": [op.to_dict() for op in operations[-10:]]  # Últimas 10
            }
    
    def get_metrics_report(self, category: Optional[str] = None,
                          last_minutes: int = 60) -> Dict[str, Any]:
        """Gera relatório de métricas.
        
        Args:
            category: Filtrar por categoria
            last_minutes: Métricas dos últimos N minutos
            
        Returns:
            Relatório de métricas
        """
        cutoff_time = datetime.now() - timedelta(minutes=last_minutes)
        
        with self._lock:
            metrics = [
                m for m in self.metrics 
                if m.timestamp >= cutoff_time and (not category or m.category == category)
            ]
            
            if not metrics:
                return {"total_metrics": 0}
            
            # Agrupa por nome
            metrics_by_name = defaultdict(list)
            for metric in metrics:
                metrics_by_name[metric.name].append(metric.value)
            
            # Calcula estatísticas por métrica
            metrics_stats = {}
            for name, values in metrics_by_name.items():
                metrics_stats[name] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "latest": values[-1] if values else 0
                }
            
            return {
                "total_metrics": len(metrics),
                "time_range_minutes": last_minutes,
                "categories": list(set(m.category for m in metrics)),
                "metrics_stats": metrics_stats,
                "counters": dict(self.counters),
                "system_metrics": self.get_system_metrics()
            }
    
    def _get_memory_usage(self) -> float:
        """Retorna uso de memória em MB."""
        try:
            return self.process.memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Retorna uso de CPU em porcentagem."""
        try:
            return self.process.cpu_percent()
        except Exception:
            return 0.0


# Instância global do coletor
metrics_collector = MetricsCollector()


# Decoradores para medição automática
def measure_performance(operation_name: Optional[str] = None, 
                       category: str = "function"):
    """Decorador para medir performance de funções.
    
    Args:
        operation_name: Nome da operação (usa nome da função se None)
        category: Categoria da métrica
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with metrics_collector.measure_operation(op_name) as update_stats:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    metrics_collector.record_metric(
                        f"{op_name}_execution_time",
                        duration,
                        "seconds",
                        category
                    )
                    
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    metrics_collector.record_metric(
                        f"{op_name}_execution_time",
                        duration,
                        "seconds",
                        category,
                        error=str(e)
                    )
                    raise
        
        return wrapper
    return decorator


# Funções de conveniência
def record_metric(name: str, value: float, unit: str = "", 
                 category: str = "general", **metadata) -> None:
    """Função de conveniência para registrar métrica."""
    metrics_collector.record_metric(name, value, unit, category, **metadata)

def start_operation(operation_name: str, **metadata) -> str:
    """Função de conveniência para iniciar operação."""
    return metrics_collector.start_operation(operation_name, **metadata)

def end_operation(operation_id: str, **kwargs) -> Optional[OperationStats]:
    """Função de conveniência para finalizar operação."""
    return metrics_collector.end_operation(operation_id, **kwargs)

def increment_counter(counter_name: str, value: int = 1) -> None:
    """Função de conveniência para incrementar contador."""
    metrics_collector.increment_counter(counter_name, value)

def get_metrics_report(**kwargs) -> Dict[str, Any]:
    """Função de conveniência para obter relatório de métricas."""
    return metrics_collector.get_metrics_report(**kwargs)