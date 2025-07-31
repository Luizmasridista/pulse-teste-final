"""Sistema de validação de permissões para o projeto Pulse.

Este módulo implementa validações de permissões de diretórios e arquivos,
garantindo que o sistema tenha acesso adequado aos recursos necessários.
"""

import os
import stat
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from .config import config
from .exceptions import DirectoryPermissionError, DirectoryNotFoundError
from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class PermissionResult:
    """Resultado de validação de permissões."""
    path: str
    exists: bool
    readable: bool
    writable: bool
    executable: bool
    size_mb: float
    free_space_mb: float
    error_message: Optional[str] = None
    
    @property
    def is_valid(self) -> bool:
        """Retorna True se todas as permissões necessárias estão disponíveis."""
        return self.exists and self.readable and self.writable and self.error_message is None
    
    def to_dict(self) -> Dict:
        """Converte o resultado para dicionário."""
        return {
            "path": self.path,
            "exists": self.exists,
            "readable": self.readable,
            "writable": self.writable,
            "executable": self.executable,
            "size_mb": self.size_mb,
            "free_space_mb": self.free_space_mb,
            "is_valid": self.is_valid,
            "error_message": self.error_message
        }


class PermissionValidator:
    """Validador de permissões do sistema."""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    def validate_directory(self, directory_path: Path, 
                         require_read: bool = True,
                         require_write: bool = True,
                         require_execute: bool = False,
                         min_free_space_mb: float = 100.0) -> PermissionResult:
        """Valida permissões de um diretório.
        
        Args:
            directory_path: Caminho do diretório
            require_read: Se requer permissão de leitura
            require_write: Se requer permissão de escrita
            require_execute: Se requer permissão de execução
            min_free_space_mb: Espaço livre mínimo em MB
            
        Returns:
            PermissionResult com o resultado da validação
        """
        path_str = str(directory_path)
        
        try:
            # Verifica se o diretório existe
            exists = directory_path.exists()
            if not exists:
                return PermissionResult(
                    path=path_str,
                    exists=False,
                    readable=False,
                    writable=False,
                    executable=False,
                    size_mb=0.0,
                    free_space_mb=0.0,
                    error_message=f"Diretório não existe: {path_str}"
                )
            
            # Verifica se é realmente um diretório
            if not directory_path.is_dir():
                return PermissionResult(
                    path=path_str,
                    exists=True,
                    readable=False,
                    writable=False,
                    executable=False,
                    size_mb=0.0,
                    free_space_mb=0.0,
                    error_message=f"Caminho não é um diretório: {path_str}"
                )
            
            # Testa permissões
            readable = os.access(directory_path, os.R_OK)
            writable = os.access(directory_path, os.W_OK)
            executable = os.access(directory_path, os.X_OK)
            
            # Calcula tamanho do diretório
            size_mb = self._calculate_directory_size(directory_path)
            
            # Calcula espaço livre
            free_space_mb = self._get_free_space(directory_path)
            
            # Valida requisitos
            error_messages = []
            
            if require_read and not readable:
                error_messages.append("Permissão de leitura negada")
            
            if require_write and not writable:
                error_messages.append("Permissão de escrita negada")
            
            if require_execute and not executable:
                error_messages.append("Permissão de execução negada")
            
            if free_space_mb < min_free_space_mb:
                error_messages.append(f"Espaço insuficiente: {free_space_mb:.2f}MB < {min_free_space_mb}MB")
            
            error_message = "; ".join(error_messages) if error_messages else None
            
            result = PermissionResult(
                path=path_str,
                exists=True,
                readable=readable,
                writable=writable,
                executable=executable,
                size_mb=size_mb,
                free_space_mb=free_space_mb,
                error_message=error_message
            )
            
            self.logger.debug(f"Validação de diretório: {path_str}", **result.to_dict())
            return result
            
        except Exception as e:
            error_msg = f"Erro ao validar diretório {path_str}: {str(e)}"
            self.logger.error(error_msg)
            return PermissionResult(
                path=path_str,
                exists=False,
                readable=False,
                writable=False,
                executable=False,
                size_mb=0.0,
                free_space_mb=0.0,
                error_message=error_msg
            )
    
    def validate_file(self, file_path: Path,
                     require_read: bool = True,
                     require_write: bool = False,
                     max_size_mb: Optional[float] = None) -> PermissionResult:
        """Valida permissões de um arquivo.
        
        Args:
            file_path: Caminho do arquivo
            require_read: Se requer permissão de leitura
            require_write: Se requer permissão de escrita
            max_size_mb: Tamanho máximo permitido em MB
            
        Returns:
            PermissionResult com o resultado da validação
        """
        path_str = str(file_path)
        
        try:
            # Verifica se o arquivo existe
            exists = file_path.exists()
            if not exists:
                # Para arquivos, não existir pode ser válido se não requer leitura
                if require_read:
                    return PermissionResult(
                        path=path_str,
                        exists=False,
                        readable=False,
                        writable=False,
                        executable=False,
                        size_mb=0.0,
                        free_space_mb=0.0,
                        error_message=f"Arquivo não existe: {path_str}"
                    )
                else:
                    # Valida o diretório pai para escrita
                    parent_dir = file_path.parent
                    return self.validate_directory(parent_dir, require_read=False, require_write=True)
            
            # Verifica se é realmente um arquivo
            if not file_path.is_file():
                return PermissionResult(
                    path=path_str,
                    exists=True,
                    readable=False,
                    writable=False,
                    executable=False,
                    size_mb=0.0,
                    free_space_mb=0.0,
                    error_message=f"Caminho não é um arquivo: {path_str}"
                )
            
            # Testa permissões
            readable = os.access(file_path, os.R_OK)
            writable = os.access(file_path, os.W_OK)
            executable = os.access(file_path, os.X_OK)
            
            # Calcula tamanho do arquivo
            size_mb = file_path.stat().st_size / (1024 * 1024)
            
            # Calcula espaço livre no diretório pai
            free_space_mb = self._get_free_space(file_path.parent)
            
            # Valida requisitos
            error_messages = []
            
            if require_read and not readable:
                error_messages.append("Permissão de leitura negada")
            
            if require_write and not writable:
                error_messages.append("Permissão de escrita negada")
            
            if max_size_mb and size_mb > max_size_mb:
                error_messages.append(f"Arquivo muito grande: {size_mb:.2f}MB > {max_size_mb}MB")
            
            error_message = "; ".join(error_messages) if error_messages else None
            
            result = PermissionResult(
                path=path_str,
                exists=True,
                readable=readable,
                writable=writable,
                executable=executable,
                size_mb=size_mb,
                free_space_mb=free_space_mb,
                error_message=error_message
            )
            
            self.logger.debug(f"Validação de arquivo: {path_str}", **result.to_dict())
            return result
            
        except Exception as e:
            error_msg = f"Erro ao validar arquivo {path_str}: {str(e)}"
            self.logger.error(error_msg)
            return PermissionResult(
                path=path_str,
                exists=False,
                readable=False,
                writable=False,
                executable=False,
                size_mb=0.0,
                free_space_mb=0.0,
                error_message=error_msg
            )
    
    def validate_system_directories(self) -> Dict[str, PermissionResult]:
        """Valida todos os diretórios do sistema.
        
        Returns:
            Dicionário com resultados de validação para cada diretório
        """
        directories = {
            "subordinadas": (config.SUBORDINADAS_DIR, True, True),  # read, write
            "mestre": (config.MESTRE_DIR, True, True),
            "backup": (config.BACKUP_DIR, True, True),
            "logs": (config.PROJECT_ROOT / "logs", False, True),  # só write
        }
        
        results = {}
        
        for name, (path, require_read, require_write) in directories.items():
            result = self.validate_directory(
                path,
                require_read=require_read,
                require_write=require_write,
                min_free_space_mb=50.0  # 50MB mínimo
            )
            results[name] = result
            
            if not result.is_valid:
                self.logger.warning(
                    f"Problema no diretório {name}: {result.error_message}",
                    directory=name,
                    path=str(path),
                    **result.to_dict()
                )
        
        return results
    
    def ensure_directories_with_permissions(self) -> Dict[str, bool]:
        """Cria diretórios necessários e valida permissões.
        
        Returns:
            Dicionário indicando sucesso para cada diretório
        """
        results = {}
        
        # Primeiro, tenta criar os diretórios
        try:
            config.ensure_directories()
            self.logger.info("Diretórios criados/verificados com sucesso")
        except Exception as e:
            self.logger.error(f"Erro ao criar diretórios: {str(e)}")
            return {"error": False}
        
        # Depois, valida as permissões
        validation_results = self.validate_system_directories()
        
        for name, result in validation_results.items():
            results[name] = result.is_valid
            
            if not result.is_valid:
                self.logger.error(
                    f"Falha na validação do diretório {name}",
                    **result.to_dict()
                )
        
        return results
    
    def _calculate_directory_size(self, directory_path: Path) -> float:
        """Calcula o tamanho total de um diretório em MB."""
        try:
            total_size = 0
            for file_path in directory_path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size / (1024 * 1024)
        except Exception:
            return 0.0
    
    def _get_free_space(self, path: Path) -> float:
        """Retorna o espaço livre em MB no sistema de arquivos."""
        try:
            if hasattr(os, 'statvfs'):  # Unix/Linux
                statvfs = os.statvfs(path)
                free_bytes = statvfs.f_frsize * statvfs.f_bavail
            else:  # Windows
                import shutil
                _, _, free_bytes = shutil.disk_usage(path)
            
            return free_bytes / (1024 * 1024)
        except Exception:
            return 0.0


# Instância global do validador
permission_validator = PermissionValidator()

# Funções de conveniência
def validate_directory(directory_path: Path, **kwargs) -> PermissionResult:
    """Função de conveniência para validar diretório."""
    return permission_validator.validate_directory(directory_path, **kwargs)

def validate_file(file_path: Path, **kwargs) -> PermissionResult:
    """Função de conveniência para validar arquivo."""
    return permission_validator.validate_file(file_path, **kwargs)

def validate_system_directories() -> Dict[str, PermissionResult]:
    """Função de conveniência para validar diretórios do sistema."""
    return permission_validator.validate_system_directories()

def ensure_directories_with_permissions() -> Dict[str, bool]:
    """Função de conveniência para criar e validar diretórios."""
    return permission_validator.ensure_directories_with_permissions()