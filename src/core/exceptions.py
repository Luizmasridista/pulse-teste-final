"""Exceções personalizadas do sistema de consolidação de planilhas.

Este módulo define todas as exceções específicas do sistema,
organizadas por categoria e com mensagens de erro detalhadas.
"""

from typing import Optional, List, Any


class PulseBaseException(Exception):
    """Exceção base para todas as exceções do sistema Pulse."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[dict] = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"
    
    def to_dict(self) -> dict:
        """Converte a exceção para dicionário para logging estruturado."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


# Exceções de Sistema e Infraestrutura
class SystemException(PulseBaseException):
    """Exceções relacionadas ao sistema e infraestrutura."""
    pass


class DirectoryException(SystemException):
    """Exceções relacionadas a diretórios e permissões."""
    pass


class DirectoryNotFoundError(DirectoryException):
    """Diretório não encontrado."""
    
    def __init__(self, directory_path: str):
        super().__init__(
            f"Diretório não encontrado: {directory_path}",
            "DIR_NOT_FOUND",
            {"directory_path": directory_path}
        )


class DirectoryPermissionError(DirectoryException):
    """Permissões insuficientes no diretório."""
    
    def __init__(self, directory_path: str, required_permissions: List[str]):
        super().__init__(
            f"Permissões insuficientes no diretório {directory_path}. Requerido: {', '.join(required_permissions)}",
            "DIR_PERMISSION_ERROR",
            {"directory_path": directory_path, "required_permissions": required_permissions}
        )


# Exceções de Arquivo e Planilha
class FileException(PulseBaseException):
    """Exceções relacionadas a arquivos."""
    pass


class FileNotFoundError(FileException):
    """Arquivo não encontrado."""
    
    def __init__(self, file_path: str):
        super().__init__(
            f"Arquivo não encontrado: {file_path}",
            "FILE_NOT_FOUND",
            {"file_path": file_path}
        )


class FileCorruptedError(FileException):
    """Arquivo corrompido ou inválido."""
    
    def __init__(self, file_path: str, corruption_details: str):
        super().__init__(
            f"Arquivo corrompido: {file_path}. Detalhes: {corruption_details}",
            "FILE_CORRUPTED",
            {"file_path": file_path, "corruption_details": corruption_details}
        )


class FileSizeError(FileException):
    """Arquivo muito grande."""
    
    def __init__(self, file_path: str, file_size_mb: float, max_size_mb: float):
        super().__init__(
            f"Arquivo muito grande: {file_path} ({file_size_mb:.2f}MB). Máximo permitido: {max_size_mb}MB",
            "FILE_TOO_LARGE",
            {"file_path": file_path, "file_size_mb": file_size_mb, "max_size_mb": max_size_mb}
        )


class UnsupportedFileFormatError(FileException):
    """Formato de arquivo não suportado."""
    
    def __init__(self, file_path: str, file_extension: str, supported_extensions: List[str]):
        super().__init__(
            f"Formato não suportado: {file_path} ({file_extension}). Suportados: {', '.join(supported_extensions)}",
            "UNSUPPORTED_FORMAT",
            {"file_path": file_path, "file_extension": file_extension, "supported_extensions": supported_extensions}
        )


# Exceções de Planilha
class SpreadsheetException(PulseBaseException):
    """Exceções relacionadas ao processamento de planilhas."""
    pass


class EmptySpreadsheetError(SpreadsheetException):
    """Planilha vazia ou sem dados válidos."""
    
    def __init__(self, file_path: str):
        super().__init__(
            f"Planilha vazia ou sem dados válidos: {file_path}",
            "EMPTY_SPREADSHEET",
            {"file_path": file_path}
        )


class InvalidHeaderError(SpreadsheetException):
    """Cabeçalho inválido ou incompatível."""
    
    def __init__(self, file_path: str, expected_headers: List[str], found_headers: List[str]):
        super().__init__(
            f"Cabeçalho incompatível em {file_path}. Esperado: {expected_headers}, Encontrado: {found_headers}",
            "INVALID_HEADER",
            {"file_path": file_path, "expected_headers": expected_headers, "found_headers": found_headers}
        )


class FormulaError(SpreadsheetException):
    """Erro ao processar fórmulas."""
    
    def __init__(self, file_path: str, cell_reference: str, formula: str, error_details: str):
        super().__init__(
            f"Erro na fórmula {cell_reference} em {file_path}: {formula}. Detalhes: {error_details}",
            "FORMULA_ERROR",
            {"file_path": file_path, "cell_reference": cell_reference, "formula": formula, "error_details": error_details}
        )


class StyleError(SpreadsheetException):
    """Erro ao processar estilos de célula."""
    
    def __init__(self, file_path: str, cell_reference: str, style_details: str):
        super().__init__(
            f"Erro no estilo da célula {cell_reference} em {file_path}: {style_details}",
            "STYLE_ERROR",
            {"file_path": file_path, "cell_reference": cell_reference, "style_details": style_details}
        )


# Exceções de Sincronização
class SyncException(PulseBaseException):
    """Exceções relacionadas à sincronização de dados."""
    pass


class ConsolidationError(SyncException):
    """Erro durante o processo de consolidação."""
    
    def __init__(self, stage: str, error_details: str, affected_files: Optional[List[str]] = None):
        super().__init__(
            f"Erro na consolidação (estágio: {stage}): {error_details}",
            "CONSOLIDATION_ERROR",
            {"stage": stage, "error_details": error_details, "affected_files": affected_files or []}
        )


class BackupError(SyncException):
    """Erro durante criação ou validação de backup."""
    
    def __init__(self, backup_path: str, error_details: str):
        super().__init__(
            f"Erro no backup {backup_path}: {error_details}",
            "BACKUP_ERROR",
            {"backup_path": backup_path, "error_details": error_details}
        )


class ValidationError(SyncException):
    """Erro durante validação de dados."""
    
    def __init__(self, validation_type: str, error_details: str, failed_items: Optional[List[str]] = None):
        super().__init__(
            f"Falha na validação ({validation_type}): {error_details}",
            "VALIDATION_ERROR",
            {"validation_type": validation_type, "error_details": error_details, "failed_items": failed_items or []}
        )


# Exceções de Performance
class PerformanceException(PulseBaseException):
    """Exceções relacionadas à performance do sistema."""
    pass


class TimeoutError(PerformanceException):
    """Operação excedeu o tempo limite."""
    
    def __init__(self, operation: str, timeout_seconds: int):
        super().__init__(
            f"Timeout na operação '{operation}' após {timeout_seconds} segundos",
            "OPERATION_TIMEOUT",
            {"operation": operation, "timeout_seconds": timeout_seconds}
        )


class MemoryError(PerformanceException):
    """Limite de memória excedido."""
    
    def __init__(self, current_usage_mb: float, limit_mb: float):
        super().__init__(
            f"Limite de memória excedido: {current_usage_mb:.2f}MB / {limit_mb}MB",
            "MEMORY_LIMIT_EXCEEDED",
            {"current_usage_mb": current_usage_mb, "limit_mb": limit_mb}
        )


# Exceções de API
class APIException(PulseBaseException):
    """Exceções relacionadas à API REST."""
    pass


class InvalidRequestError(APIException):
    """Requisição inválida."""
    
    def __init__(self, request_details: str, validation_errors: List[str]):
        super().__init__(
            f"Requisição inválida: {request_details}",
            "INVALID_REQUEST",
            {"request_details": request_details, "validation_errors": validation_errors}
        )


class AuthenticationError(APIException):
    """Erro de autenticação."""
    
    def __init__(self, auth_method: str):
        super().__init__(
            f"Falha na autenticação usando {auth_method}",
            "AUTH_FAILED",
            {"auth_method": auth_method}
        )


class AuthorizationError(APIException):
    """Erro de autorização."""
    
    def __init__(self, required_permission: str, user_permissions: List[str]):
        super().__init__(
            f"Permissão insuficiente. Requerido: {required_permission}, Usuário possui: {', '.join(user_permissions)}",
            "INSUFFICIENT_PERMISSION",
            {"required_permission": required_permission, "user_permissions": user_permissions}
        )


# Função utilitária para captura de exceções
def handle_exception(func):
    """Decorator para captura e tratamento de exceções."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PulseBaseException:
            # Re-raise exceções conhecidas
            raise
        except Exception as e:
            # Converte exceções desconhecidas em PulseBaseException
            raise PulseBaseException(
                f"Erro inesperado em {func.__name__}: {str(e)}",
                "UNEXPECTED_ERROR",
                {"function": func.__name__, "original_error": str(e), "error_type": type(e).__name__}
            ) from e
    return wrapper