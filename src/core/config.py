"""Configurações do sistema de consolidação de planilhas.

Este módulo contém todas as configurações centralizadas do sistema,
incluindo caminhos, parâmetros de processamento e configurações de logging.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional


class Config:
    """Classe de configuração principal do sistema."""
    
    # Configurações de diretórios
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    BACKEND_ROOT = PROJECT_ROOT / "backend"
    
    # Pastas principais do backend
    SUBORDINADAS_DIR = BACKEND_ROOT / "SUBORDINADAS"
    MESTRE_DIR = BACKEND_ROOT / "MESTRE"
    BACKUP_DIR = BACKEND_ROOT / "BACKUP"
    
    # Configurações de arquivos
    MESTRE_FILENAME = "planilha_consolidada.xlsx"
    BACKUP_FILENAME_FORMAT = "{timestamp}_planilha_consolidada.xlsx"
    
    # Extensões de arquivo suportadas
    SUPPORTED_EXTENSIONS = [".xlsx", ".xls"]
    
    # Configurações de backup
    BACKUP_RETENTION_DAYS = 30
    BACKUP_TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"
    
    # Configurações de processamento
    MAX_CONCURRENT_FILES = 10
    CHUNK_SIZE = 1000  # Para processamento de grandes planilhas
    
    # Configurações de validação
    MIN_ROWS_REQUIRED = 2  # Cabeçalho + pelo menos 1 linha de dados
    MAX_FILE_SIZE_MB = 100
    
    # Configurações de logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    LOG_ROTATION = "10 MB"
    LOG_RETENTION = "30 days"
    
    # Configurações de performance
    MEMORY_LIMIT_MB = 512
    TIMEOUT_SECONDS = 300
    
    # Configurações de cache
    CACHE_MAX_SIZE = 1000
    CACHE_TTL = 3600  # 1 hora em segundos
    CACHE_ENABLED = True
    
    # Configurações de monitoramento
    class monitoring:
        polling_interval = 5.0  # segundos
        enable_file_watching = True
        max_events_per_second = 100
        debounce_delay = 1.0  # segundos
    
    @classmethod
    def get_mestre_path(cls) -> Path:
        """Retorna o caminho completo da planilha mestre."""
        return cls.MESTRE_DIR / cls.MESTRE_FILENAME
    
    @classmethod
    def get_backup_path(cls, timestamp: str) -> Path:
        """Retorna o caminho completo para um backup com timestamp."""
        filename = cls.BACKUP_FILENAME_FORMAT.format(timestamp=timestamp)
        return cls.BACKUP_DIR / filename
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Cria os diretórios necessários se não existirem."""
        directories = [
            cls.BACKEND_ROOT,
            cls.SUBORDINADAS_DIR,
            cls.MESTRE_DIR,
            cls.BACKUP_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate_permissions(cls) -> Dict[str, bool]:
        """Valida permissões de leitura/escrita nos diretórios."""
        permissions = {}
        directories = {
            "subordinadas": cls.SUBORDINADAS_DIR,
            "mestre": cls.MESTRE_DIR,
            "backup": cls.BACKUP_DIR
        }
        
        for name, directory in directories.items():
            try:
                # Testa leitura
                can_read = os.access(directory, os.R_OK)
                # Testa escrita
                can_write = os.access(directory, os.W_OK)
                permissions[name] = can_read and can_write
            except Exception:
                permissions[name] = False
        
        return permissions
    
    @classmethod
    def get_environment_config(cls) -> Dict[str, str]:
        """Retorna configurações baseadas em variáveis de ambiente."""
        return {
            "log_level": os.getenv("PULSE_LOG_LEVEL", cls.LOG_LEVEL),
            "max_file_size": os.getenv("PULSE_MAX_FILE_SIZE", str(cls.MAX_FILE_SIZE_MB)),
            "backup_retention": os.getenv("PULSE_BACKUP_RETENTION", str(cls.BACKUP_RETENTION_DAYS)),
        }


class DevelopmentConfig(Config):
    """Configurações para ambiente de desenvolvimento."""
    LOG_LEVEL = "DEBUG"
    BACKUP_RETENTION_DAYS = 7
    

class ProductionConfig(Config):
    """Configurações para ambiente de produção."""
    LOG_LEVEL = "WARNING"
    BACKUP_RETENTION_DAYS = 90
    MEMORY_LIMIT_MB = 1024


class TestConfig(Config):
    """Configurações para ambiente de teste."""
    LOG_LEVEL = "DEBUG"
    BACKUP_RETENTION_DAYS = 1
    SUBORDINADAS_DIR = Config.PROJECT_ROOT / "tests" / "data" / "subordinadas"
    MESTRE_DIR = Config.PROJECT_ROOT / "tests" / "data" / "mestre"
    BACKUP_DIR = Config.PROJECT_ROOT / "tests" / "data" / "backup"


# Configuração ativa baseada na variável de ambiente
ENVIRONMENT = os.getenv("PULSE_ENV", "development").lower()

if ENVIRONMENT == "production":
    config = ProductionConfig()
elif ENVIRONMENT == "test":
    config = TestConfig()
else:
    config = DevelopmentConfig()