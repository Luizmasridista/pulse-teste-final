"""Módulo core do projeto Pulse.

Este módulo contém os componentes fundamentais do sistema de consolidação
de planilhas, incluindo configuração, logging, cache, validação e backup.
"""

from .config import config, Config
from .exceptions import (
    PulseBaseException,
    SystemException,
    FileException,
    SpreadsheetException,
    SyncException,
    PerformanceException,
    APIException,
    BackupError,
    handle_exception
)
from .logger import get_logger
from .metrics import (
    metrics_collector,
    PerformanceMetric,
    OperationStats,
    measure_performance
)
from .cache import cache_manager, cached
from .validation import (
    DataValidator,
    ValidationSeverity,
    ValidationRule,
    ValidationResult,
    ColumnSchema,
    validate_dataframe,
    validate_file
)
from .monitoring import (
    FileMonitor,
    SpreadsheetMonitor,
    ChangeType,
    MonitoringMode,
    start_monitoring,
    stop_monitoring
)
from .backup import (
    backup_manager,
    BackupManager,
    BackupType,
    BackupStatus,
    create_backup,
    restore_backup,
    list_backups,
    backup_master_spreadsheet
)
from .permissions import (
    PermissionValidator,
    PermissionResult,
    validate_system_directories
)

# Versão do módulo
__version__ = "1.0.0"

# Componentes principais exportados
__all__ = [
    # Configuração
    "config",
    "Config",
    
    # Exceções
    "PulseBaseException",
    "SystemException",
    "FileException",
    "SpreadsheetException",
    "SyncException",
    "PerformanceException",
    "APIException",
    "BackupError",
    "handle_exception",
    
    # Logging
    "get_logger",
    "setup_logging",
    
    # Métricas
    "metrics_collector",
    "PerformanceMetric",
    "OperationStats",
    "measure_performance",
    
    # Cache
    "cache_manager",
    "cached",
    
    # Validação
    "DataValidator",
    "ValidationSeverity",
    "ValidationRule",
    "ValidationResult",
    "ColumnSchema",
    "validate_dataframe",
    "validate_file",
    
    # Monitoramento
    "FileMonitor",
    "SpreadsheetMonitor",
    "ChangeType",
    "MonitoringMode",
    "start_monitoring",
    "stop_monitoring",
    
    # Backup
    "backup_manager",
    "BackupManager",
    "BackupType",
    "BackupStatus",
    "create_backup",
    "restore_backup",
    "list_backups",
    "backup_master_spreadsheet",
    
    # Permissões
    "PermissionValidator",
    "PermissionResult",
    "validate_system_permissions"
]


def initialize_core_system():
    """Inicializa o sistema core do Pulse.
    
    Esta função deve ser chamada no início da aplicação para:
    - Configurar o sistema de logging
    - Validar permissões de diretórios
    - Inicializar cache e métricas
    - Verificar configurações
    
    Returns:
        bool: True se inicialização foi bem-sucedida
    """
    logger = get_logger("core.init")
    
    try:
        logger.info("Inicializando sistema core do Pulse...")
        
        # 1. Configurar logging
        setup_logging()
        logger.info("Sistema de logging configurado")
        
        # 2. Validar permissões
        from .permissions import validate_system_permissions
        if not validate_system_permissions():
            logger.error("Falha na validação de permissões")
            return False
        logger.info("Permissões validadas com sucesso")
        
        # 3. Inicializar cache
        cache_manager.clear_expired()
        logger.info("Sistema de cache inicializado")
        
        # 4. Verificar configurações
        if not config.validate():
            logger.error("Configurações inválidas")
            return False
        logger.info("Configurações validadas")
        
        # 5. Inicializar métricas
        metrics_collector.start_collection()
        logger.info("Sistema de métricas inicializado")
        
        logger.info("Sistema core inicializado com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro na inicialização do sistema core: {e}")
        return False


def shutdown_core_system():
    """Finaliza o sistema core do Pulse.
    
    Esta função deve ser chamada ao finalizar a aplicação para:
    - Parar monitoramento
    - Salvar cache
    - Finalizar métricas
    - Limpar recursos
    """
    logger = get_logger("core.shutdown")
    
    try:
        logger.info("Finalizando sistema core do Pulse...")
        
        # 1. Parar monitoramento
        stop_monitoring()
        logger.info("Monitoramento parado")
        
        # 2. Salvar cache
        cache_manager.save_to_disk()
        logger.info("Cache salvo")
        
        # 3. Finalizar métricas
        metrics_collector.stop_collection()
        logger.info("Sistema de métricas finalizado")
        
        logger.info("Sistema core finalizado com sucesso")
        
    except Exception as e:
        logger.error(f"Erro na finalização do sistema core: {e}")


def get_system_status():
    """Obtém status do sistema core.
    
    Returns:
        dict: Dicionário com status dos componentes
    """
    try:
        return {
            "core_version": __version__,
            "config_valid": config.validate(),
            "cache_stats": cache_manager.get_stats(),
            "metrics_stats": metrics_collector.get_stats(),
            "backup_stats": backup_manager.get_backup_stats(),
            "permissions_valid": validate_system_permissions()
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }