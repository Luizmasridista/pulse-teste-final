"""Sistema de logging estruturado para o projeto Pulse.

Este módulo configura e gerencia o sistema de logs do projeto,
com suporte a diferentes níveis, rotação de arquivos e formatação estruturada.
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
from datetime import datetime

from .config import config
from .exceptions import PulseBaseException


class PulseLogger:
    """Gerenciador de logs do sistema Pulse."""
    
    def __init__(self):
        self._configured = False
        self._log_dir = config.PROJECT_ROOT / "logs"
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Configura o sistema de logging."""
        if self._configured:
            return
        
        # Remove handlers padrão do loguru
        logger.remove()
        
        # Cria diretório de logs se não existir
        self._log_dir.mkdir(exist_ok=True)
        
        # Configuração do console
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
            level=config.LOG_LEVEL,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        
        # Configuração do arquivo principal
        logger.add(
            self._log_dir / "pulse.log",
            format=config.LOG_FORMAT,
            level=config.LOG_LEVEL,
            rotation=config.LOG_ROTATION,
            retention=config.LOG_RETENTION,
            compression="zip",
            backtrace=True,
            diagnose=True,
            serialize=False
        )
        
        # Arquivo específico para erros
        logger.add(
            self._log_dir / "pulse_errors.log",
            format=config.LOG_FORMAT,
            level="ERROR",
            rotation="50 MB",
            retention="60 days",
            compression="zip",
            backtrace=True,
            diagnose=True,
            serialize=False
        )
        
        # Arquivo JSON para logs estruturados
        logger.add(
            self._log_dir / "pulse_structured.json",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            level="INFO",
            rotation="100 MB",
            retention="30 days",
            compression="zip",
            serialize=True
        )
        
        self._configured = True
        logger.info("Sistema de logging inicializado com sucesso")
    
    def get_logger(self, name: Optional[str] = None) -> "logger":
        """Retorna uma instância do logger."""
        if name:
            return logger.bind(module=name)
        return logger
    
    def log_operation_start(self, operation: str, **kwargs) -> str:
        """Registra o início de uma operação."""
        operation_id = f"{operation}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        logger.info(
            f"Iniciando operação: {operation}",
            operation_id=operation_id,
            operation=operation,
            **kwargs
        )
        return operation_id
    
    def log_operation_end(self, operation_id: str, success: bool = True, **kwargs) -> None:
        """Registra o fim de uma operação."""
        status = "SUCESSO" if success else "FALHA"
        level = "info" if success else "error"
        
        getattr(logger, level)(
            f"Operação finalizada: {status}",
            operation_id=operation_id,
            success=success,
            **kwargs
        )
    
    def log_file_operation(self, operation: str, file_path: str, **kwargs) -> None:
        """Registra operações em arquivos."""
        logger.info(
            f"Operação em arquivo: {operation}",
            operation=operation,
            file_path=file_path,
            file_size=self._get_file_size(file_path),
            **kwargs
        )
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = "", **kwargs) -> None:
        """Registra métricas de performance."""
        logger.info(
            f"Métrica de performance: {metric_name} = {value}{unit}",
            metric_name=metric_name,
            metric_value=value,
            metric_unit=unit,
            **kwargs
        )
    
    def log_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Registra exceções de forma estruturada."""
        context = context or {}
        
        if isinstance(exception, PulseBaseException):
            logger.error(
                f"Exceção do sistema: {exception.message}",
                error_code=exception.error_code,
                error_details=exception.details,
                **context
            )
        else:
            logger.exception(
                f"Exceção não tratada: {str(exception)}",
                error_type=type(exception).__name__,
                **context
            )
    
    def log_consolidation_stats(self, stats: Dict[str, Any]) -> None:
        """Registra estatísticas de consolidação."""
        logger.info(
            "Estatísticas de consolidação",
            **stats
        )
    
    def log_backup_operation(self, backup_path: str, original_path: str, success: bool = True) -> None:
        """Registra operações de backup."""
        level = "info" if success else "error"
        status = "criado" if success else "falhou"
        
        getattr(logger, level)(
            f"Backup {status}: {backup_path}",
            backup_path=backup_path,
            original_path=original_path,
            backup_size=self._get_file_size(backup_path) if success else 0,
            success=success
        )
    
    def log_validation_result(self, validation_type: str, file_path: str, 
                            is_valid: bool, details: Optional[Dict[str, Any]] = None) -> None:
        """Registra resultados de validação."""
        level = "info" if is_valid else "warning"
        status = "válido" if is_valid else "inválido"
        
        getattr(logger, level)(
            f"Validação {validation_type}: arquivo {status}",
            validation_type=validation_type,
            file_path=file_path,
            is_valid=is_valid,
            validation_details=details or {}
        )
    
    def _get_file_size(self, file_path: str) -> int:
        """Retorna o tamanho do arquivo em bytes."""
        try:
            return os.path.getsize(file_path)
        except (OSError, FileNotFoundError):
            return 0
    
    def create_context_logger(self, **context) -> "logger":
        """Cria um logger com contexto específico."""
        return logger.bind(**context)
    
    def flush_logs(self) -> None:
        """Força a escrita de todos os logs pendentes."""
        # O loguru não tem método flush explícito, mas podemos usar complete()
        logger.complete()


# Instância global do logger
pulse_logger = PulseLogger()

# Funções de conveniência para uso direto
def get_logger(name: Optional[str] = None):
    """Função de conveniência para obter um logger."""
    return pulse_logger.get_logger(name)

def log_operation_start(operation: str, **kwargs) -> str:
    """Função de conveniência para registrar início de operação."""
    return pulse_logger.log_operation_start(operation, **kwargs)

def log_operation_end(operation_id: str, success: bool = True, **kwargs) -> None:
    """Função de conveniência para registrar fim de operação."""
    pulse_logger.log_operation_end(operation_id, success, **kwargs)

def log_exception(exception: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """Função de conveniência para registrar exceções."""
    pulse_logger.log_exception(exception, context)

def log_file_operation(operation: str, file_path: str, **kwargs) -> None:
    """Função de conveniência para registrar operações em arquivos."""
    pulse_logger.log_file_operation(operation, file_path, **kwargs)

def log_performance_metric(metric_name: str, value: float, unit: str = "", **kwargs) -> None:
    """Função de conveniência para registrar métricas de performance."""
    pulse_logger.log_performance_metric(metric_name, value, unit, **kwargs)

# Logger padrão para uso geral
logger = get_logger()