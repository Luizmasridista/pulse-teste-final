"""Sistema de validação de dados para o projeto Pulse.

Este módulo implementa validações robustas para dados de planilhas,
garantindo integridade e consistência durante o processo de consolidação.
"""

import re
import pandas as pd
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

from .config import config
from .exceptions import ValidationError, DataValidationError
from .logger import get_logger
from .metrics import metrics_collector

logger = get_logger(__name__)


class ValidationSeverity(Enum):
    """Níveis de severidade de validação."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationRule(Enum):
    """Tipos de regras de validação."""
    REQUIRED = "required"
    TYPE_CHECK = "type_check"
    RANGE_CHECK = "range_check"
    FORMAT_CHECK = "format_check"
    UNIQUE_CHECK = "unique_check"
    REFERENCE_CHECK = "reference_check"
    CUSTOM = "custom"


@dataclass
class ValidationIssue:
    """Representa um problema de validação."""
    rule: ValidationRule
    severity: ValidationSeverity
    message: str
    column: Optional[str] = None
    row: Optional[int] = None
    value: Any = None
    expected: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "rule": self.rule.value,
            "severity": self.severity.value,
            "message": self.message,
            "column": self.column,
            "row": self.row,
            "value": str(self.value) if self.value is not None else None,
            "expected": str(self.expected) if self.expected is not None else None,
            "metadata": self.metadata
        }


@dataclass
class ValidationResult:
    """Resultado de validação."""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    warnings_count: int = 0
    errors_count: int = 0
    critical_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_issue(self, issue: ValidationIssue) -> None:
        """Adiciona um problema de validação."""
        self.issues.append(issue)
        
        if issue.severity == ValidationSeverity.WARNING:
            self.warnings_count += 1
        elif issue.severity == ValidationSeverity.ERROR:
            self.errors_count += 1
            self.is_valid = False
        elif issue.severity == ValidationSeverity.CRITICAL:
            self.critical_count += 1
            self.is_valid = False
    
    def get_issues_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """Retorna problemas por severidade."""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_issues_by_column(self, column: str) -> List[ValidationIssue]:
        """Retorna problemas por coluna."""
        return [issue for issue in self.issues if issue.column == column]
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "is_valid": self.is_valid,
            "total_issues": len(self.issues),
            "warnings_count": self.warnings_count,
            "errors_count": self.errors_count,
            "critical_count": self.critical_count,
            "issues": [issue.to_dict() for issue in self.issues],
            "metadata": self.metadata
        }


@dataclass
class ColumnSchema:
    """Schema de validação para uma coluna."""
    name: str
    data_type: type
    required: bool = False
    nullable: bool = True
    unique: bool = False
    min_value: Optional[Union[int, float, Decimal]] = None
    max_value: Optional[Union[int, float, Decimal]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    allowed_values: Optional[Set[Any]] = None
    custom_validators: List[Callable[[Any], bool]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate_value(self, value: Any, row_index: Optional[int] = None) -> List[ValidationIssue]:
        """Valida um valor individual.
        
        Args:
            value: Valor a validar
            row_index: Índice da linha (para relatórios)
            
        Returns:
            Lista de problemas encontrados
        """
        issues = []
        
        # Verifica se é nulo
        is_null = pd.isna(value) or value is None or (isinstance(value, str) and value.strip() == "")
        
        # Validação de campo obrigatório
        if self.required and is_null:
            issues.append(ValidationIssue(
                rule=ValidationRule.REQUIRED,
                severity=ValidationSeverity.ERROR,
                message=f"Campo obrigatório '{self.name}' está vazio",
                column=self.name,
                row=row_index,
                value=value
            ))
            return issues  # Para por aqui se é obrigatório e está vazio
        
        # Se é nulo e não é obrigatório, verifica se aceita nulos
        if is_null:
            if not self.nullable:
                issues.append(ValidationIssue(
                    rule=ValidationRule.TYPE_CHECK,
                    severity=ValidationSeverity.ERROR,
                    message=f"Campo '{self.name}' não aceita valores nulos",
                    column=self.name,
                    row=row_index,
                    value=value
                ))
            return issues  # Para por aqui se é nulo
        
        # Validação de tipo
        if not self._check_type(value):
            issues.append(ValidationIssue(
                rule=ValidationRule.TYPE_CHECK,
                severity=ValidationSeverity.ERROR,
                message=f"Tipo inválido para '{self.name}'. Esperado: {self.data_type.__name__}, Recebido: {type(value).__name__}",
                column=self.name,
                row=row_index,
                value=value,
                expected=self.data_type.__name__
            ))
            return issues  # Para por aqui se o tipo está errado
        
        # Converte para o tipo correto para validações subsequentes
        try:
            converted_value = self._convert_value(value)
        except Exception as e:
            issues.append(ValidationIssue(
                rule=ValidationRule.TYPE_CHECK,
                severity=ValidationSeverity.ERROR,
                message=f"Erro na conversão de tipo para '{self.name}': {str(e)}",
                column=self.name,
                row=row_index,
                value=value
            ))
            return issues
        
        # Validação de range (para números)
        if isinstance(converted_value, (int, float, Decimal)):
            if self.min_value is not None and converted_value < self.min_value:
                issues.append(ValidationIssue(
                    rule=ValidationRule.RANGE_CHECK,
                    severity=ValidationSeverity.ERROR,
                    message=f"Valor em '{self.name}' ({converted_value}) é menor que o mínimo permitido ({self.min_value})",
                    column=self.name,
                    row=row_index,
                    value=value,
                    expected=f">= {self.min_value}"
                ))
            
            if self.max_value is not None and converted_value > self.max_value:
                issues.append(ValidationIssue(
                    rule=ValidationRule.RANGE_CHECK,
                    severity=ValidationSeverity.ERROR,
                    message=f"Valor em '{self.name}' ({converted_value}) é maior que o máximo permitido ({self.max_value})",
                    column=self.name,
                    row=row_index,
                    value=value,
                    expected=f"<= {self.max_value}"
                ))
        
        # Validação de comprimento (para strings)
        if isinstance(converted_value, str):
            length = len(converted_value)
            
            if self.min_length is not None and length < self.min_length:
                issues.append(ValidationIssue(
                    rule=ValidationRule.FORMAT_CHECK,
                    severity=ValidationSeverity.ERROR,
                    message=f"Texto em '{self.name}' muito curto. Mínimo: {self.min_length}, Atual: {length}",
                    column=self.name,
                    row=row_index,
                    value=value,
                    expected=f"Mínimo {self.min_length} caracteres"
                ))
            
            if self.max_length is not None and length > self.max_length:
                issues.append(ValidationIssue(
                    rule=ValidationRule.FORMAT_CHECK,
                    severity=ValidationSeverity.ERROR,
                    message=f"Texto em '{self.name}' muito longo. Máximo: {self.max_length}, Atual: {length}",
                    column=self.name,
                    row=row_index,
                    value=value,
                    expected=f"Máximo {self.max_length} caracteres"
                ))
            
            # Validação de padrão regex
            if self.pattern and not re.match(self.pattern, converted_value):
                issues.append(ValidationIssue(
                    rule=ValidationRule.FORMAT_CHECK,
                    severity=ValidationSeverity.ERROR,
                    message=f"Formato inválido em '{self.name}'. Valor não corresponde ao padrão esperado",
                    column=self.name,
                    row=row_index,
                    value=value,
                    expected=f"Padrão: {self.pattern}"
                ))
        
        # Validação de valores permitidos
        if self.allowed_values and converted_value not in self.allowed_values:
            issues.append(ValidationIssue(
                rule=ValidationRule.REFERENCE_CHECK,
                severity=ValidationSeverity.ERROR,
                message=f"Valor inválido em '{self.name}'. Valores permitidos: {list(self.allowed_values)}",
                column=self.name,
                row=row_index,
                value=value,
                expected=list(self.allowed_values)
            ))
        
        # Validações customizadas
        for validator in self.custom_validators:
            try:
                if not validator(converted_value):
                    issues.append(ValidationIssue(
                        rule=ValidationRule.CUSTOM,
                        severity=ValidationSeverity.ERROR,
                        message=f"Validação customizada falhou para '{self.name}'",
                        column=self.name,
                        row=row_index,
                        value=value
                    ))
            except Exception as e:
                issues.append(ValidationIssue(
                    rule=ValidationRule.CUSTOM,
                    severity=ValidationSeverity.ERROR,
                    message=f"Erro na validação customizada para '{self.name}': {str(e)}",
                    column=self.name,
                    row=row_index,
                    value=value
                ))
        
        return issues
    
    def _check_type(self, value: Any) -> bool:
        """Verifica se o valor é do tipo correto."""
        if self.data_type == str:
            return True  # Qualquer coisa pode ser string
        elif self.data_type in (int, float):
            try:
                float(value)
                return True
            except (ValueError, TypeError):
                return False
        elif self.data_type == bool:
            return isinstance(value, bool) or str(value).lower() in ('true', 'false', '1', '0', 'sim', 'não', 'yes', 'no')
        elif self.data_type == datetime:
            return isinstance(value, (datetime, date)) or self._is_date_string(value)
        else:
            return isinstance(value, self.data_type)
    
    def _convert_value(self, value: Any) -> Any:
        """Converte valor para o tipo correto."""
        if self.data_type == str:
            return str(value)
        elif self.data_type == int:
            return int(float(value))  # Permite conversão de float para int
        elif self.data_type == float:
            return float(value)
        elif self.data_type == bool:
            if isinstance(value, bool):
                return value
            return str(value).lower() in ('true', '1', 'sim', 'yes')
        elif self.data_type == datetime:
            if isinstance(value, datetime):
                return value
            elif isinstance(value, date):
                return datetime.combine(value, datetime.min.time())
            else:
                return pd.to_datetime(value)
        else:
            return value
    
    def _is_date_string(self, value: Any) -> bool:
        """Verifica se uma string pode ser convertida para data."""
        try:
            pd.to_datetime(value)
            return True
        except Exception:
            return False


class DataValidator:
    """Validador principal de dados."""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.schemas: Dict[str, List[ColumnSchema]] = {}
        
        # Schemas padrão para planilhas do sistema
        self._setup_default_schemas()
        
        self.logger.info("DataValidator inicializado")
    
    def _setup_default_schemas(self) -> None:
        """Configura schemas padrão."""
        # Schema básico para planilhas financeiras
        financial_schema = [
            ColumnSchema("data", datetime, required=True),
            ColumnSchema("descricao", str, required=True, min_length=1, max_length=200),
            ColumnSchema("valor", float, required=True, min_value=0),
            ColumnSchema("categoria", str, required=False, max_length=50),
            ColumnSchema("observacoes", str, required=False, max_length=500)
        ]
        
        # Schema para dados de vendas
        sales_schema = [
            ColumnSchema("produto_id", str, required=True, pattern=r'^[A-Z0-9]{3,10}$'),
            ColumnSchema("produto_nome", str, required=True, min_length=1, max_length=100),
            ColumnSchema("quantidade", int, required=True, min_value=1),
            ColumnSchema("preco_unitario", float, required=True, min_value=0.01),
            ColumnSchema("desconto", float, required=False, min_value=0, max_value=100),
            ColumnSchema("vendedor", str, required=True, max_length=50)
        ]
        
        # Schema para dados de estoque
        inventory_schema = [
            ColumnSchema("codigo", str, required=True, unique=True),
            ColumnSchema("nome", str, required=True, min_length=1, max_length=100),
            ColumnSchema("quantidade_atual", int, required=True, min_value=0),
            ColumnSchema("quantidade_minima", int, required=True, min_value=0),
            ColumnSchema("preco_custo", float, required=True, min_value=0),
            ColumnSchema("ativo", bool, required=True)
        ]
        
        self.schemas = {
            "financial": financial_schema,
            "sales": sales_schema,
            "inventory": inventory_schema
        }
    
    def register_schema(self, schema_name: str, columns: List[ColumnSchema]) -> None:
        """Registra um novo schema de validação.
        
        Args:
            schema_name: Nome do schema
            columns: Lista de schemas de colunas
        """
        self.schemas[schema_name] = columns
        self.logger.info(f"Schema registrado: {schema_name}", columns_count=len(columns))
    
    def validate_dataframe(self, df: pd.DataFrame, schema_name: Optional[str] = None,
                          columns_schema: Optional[List[ColumnSchema]] = None) -> ValidationResult:
        """Valida um DataFrame.
        
        Args:
            df: DataFrame a validar
            schema_name: Nome do schema a usar
            columns_schema: Schema de colunas específico
            
        Returns:
            Resultado da validação
        """
        result = ValidationResult(is_valid=True)
        
        # Determina o schema a usar
        if columns_schema:
            schema = columns_schema
        elif schema_name and schema_name in self.schemas:
            schema = self.schemas[schema_name]
        else:
            # Schema automático baseado no DataFrame
            schema = self._infer_schema(df)
        
        # Valida estrutura básica
        self._validate_structure(df, schema, result)
        
        # Valida dados linha por linha
        self._validate_data(df, schema, result)
        
        # Valida unicidade
        self._validate_uniqueness(df, schema, result)
        
        # Registra métricas
        metrics_collector.record_metric(
            "validation_issues_count",
            len(result.issues),
            "count",
            "validation"
        )
        
        metrics_collector.record_metric(
            "validation_success_rate",
            1.0 if result.is_valid else 0.0,
            "rate",
            "validation"
        )
        
        self.logger.info(
            f"Validação concluída",
            is_valid=result.is_valid,
            issues_count=len(result.issues),
            warnings=result.warnings_count,
            errors=result.errors_count,
            critical=result.critical_count
        )
        
        return result
    
    def validate_file(self, file_path: Path, schema_name: Optional[str] = None) -> ValidationResult:
        """Valida um arquivo de planilha.
        
        Args:
            file_path: Caminho do arquivo
            schema_name: Nome do schema a usar
            
        Returns:
            Resultado da validação
        """
        try:
            # Carrega o arquivo
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
            else:
                result = ValidationResult(is_valid=False)
                result.add_issue(ValidationIssue(
                    rule=ValidationRule.TYPE_CHECK,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Formato de arquivo não suportado: {file_path.suffix}",
                    metadata={"file_path": str(file_path)}
                ))
                return result
            
            # Valida o DataFrame
            result = self.validate_dataframe(df, schema_name)
            result.metadata["file_path"] = str(file_path)
            result.metadata["file_size"] = file_path.stat().st_size
            result.metadata["rows_count"] = len(df)
            result.metadata["columns_count"] = len(df.columns)
            
            return result
            
        except Exception as e:
            result = ValidationResult(is_valid=False)
            result.add_issue(ValidationIssue(
                rule=ValidationRule.TYPE_CHECK,
                severity=ValidationSeverity.CRITICAL,
                message=f"Erro ao carregar arquivo: {str(e)}",
                metadata={"file_path": str(file_path)}
            ))
            return result
    
    def _validate_structure(self, df: pd.DataFrame, schema: List[ColumnSchema], result: ValidationResult) -> None:
        """Valida a estrutura do DataFrame."""
        # Verifica colunas obrigatórias
        required_columns = {col.name for col in schema if col.required}
        missing_columns = required_columns - set(df.columns)
        
        for col in missing_columns:
            result.add_issue(ValidationIssue(
                rule=ValidationRule.REQUIRED,
                severity=ValidationSeverity.CRITICAL,
                message=f"Coluna obrigatória ausente: {col}",
                column=col
            ))
        
        # Verifica colunas extras
        schema_columns = {col.name for col in schema}
        extra_columns = set(df.columns) - schema_columns
        
        for col in extra_columns:
            result.add_issue(ValidationIssue(
                rule=ValidationRule.REFERENCE_CHECK,
                severity=ValidationSeverity.WARNING,
                message=f"Coluna não reconhecida: {col}",
                column=col
            ))
    
    def _validate_data(self, df: pd.DataFrame, schema: List[ColumnSchema], result: ValidationResult) -> None:
        """Valida os dados do DataFrame."""
        schema_dict = {col.name: col for col in schema}
        
        for col_name in df.columns:
            if col_name not in schema_dict:
                continue  # Coluna não está no schema
            
            col_schema = schema_dict[col_name]
            
            # Valida cada valor na coluna
            for idx, value in enumerate(df[col_name]):
                issues = col_schema.validate_value(value, idx + 1)  # +1 para linha baseada em 1
                for issue in issues:
                    result.add_issue(issue)
    
    def _validate_uniqueness(self, df: pd.DataFrame, schema: List[ColumnSchema], result: ValidationResult) -> None:
        """Valida unicidade de colunas."""
        for col_schema in schema:
            if col_schema.unique and col_schema.name in df.columns:
                duplicates = df[df[col_schema.name].duplicated(keep=False)]
                
                if not duplicates.empty:
                    for idx in duplicates.index:
                        result.add_issue(ValidationIssue(
                            rule=ValidationRule.UNIQUE_CHECK,
                            severity=ValidationSeverity.ERROR,
                            message=f"Valor duplicado na coluna '{col_schema.name}'",
                            column=col_schema.name,
                            row=idx + 1,
                            value=df.loc[idx, col_schema.name]
                        ))
    
    def _infer_schema(self, df: pd.DataFrame) -> List[ColumnSchema]:
        """Infere schema automaticamente do DataFrame."""
        schema = []
        
        for col_name in df.columns:
            # Determina tipo baseado nos dados
            col_data = df[col_name].dropna()
            
            if col_data.empty:
                data_type = str
            elif pd.api.types.is_numeric_dtype(col_data):
                if pd.api.types.is_integer_dtype(col_data):
                    data_type = int
                else:
                    data_type = float
            elif pd.api.types.is_datetime64_any_dtype(col_data):
                data_type = datetime
            elif pd.api.types.is_bool_dtype(col_data):
                data_type = bool
            else:
                data_type = str
            
            # Verifica se tem valores nulos
            has_nulls = df[col_name].isna().any()
            
            schema.append(ColumnSchema(
                name=col_name,
                data_type=data_type,
                nullable=has_nulls,
                metadata={"inferred": True}
            ))
        
        return schema


# Instância global do validador
data_validator = DataValidator()


# Funções de conveniência
def validate_dataframe(df: pd.DataFrame, schema_name: Optional[str] = None) -> ValidationResult:
    """Função de conveniência para validar DataFrame."""
    return data_validator.validate_dataframe(df, schema_name)

def validate_file(file_path: Path, schema_name: Optional[str] = None) -> ValidationResult:
    """Função de conveniência para validar arquivo."""
    return data_validator.validate_file(file_path, schema_name)

def register_schema(schema_name: str, columns: List[ColumnSchema]) -> None:
    """Função de conveniência para registrar schema."""
    data_validator.register_schema(schema_name, columns)

# Validadores customizados comuns
def is_valid_email(email: str) -> bool:
    """Valida formato de email."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_cpf(cpf: str) -> bool:
    """Valida CPF brasileiro."""
    # Remove caracteres não numéricos
    cpf = re.sub(r'\D', '', cpf)
    
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    
    # Calcula dígitos verificadores
    def calculate_digit(cpf_digits, weights):
        total = sum(int(digit) * weight for digit, weight in zip(cpf_digits, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder
    
    first_digit = calculate_digit(cpf[:9], range(10, 1, -1))
    second_digit = calculate_digit(cpf[:10], range(11, 1, -1))
    
    return cpf[-2:] == f"{first_digit}{second_digit}"

def is_valid_cnpj(cnpj: str) -> bool:
    """Valida CNPJ brasileiro."""
    # Remove caracteres não numéricos
    cnpj = re.sub(r'\D', '', cnpj)
    
    if len(cnpj) != 14:
        return False
    
    # Calcula dígitos verificadores
    def calculate_digit(cnpj_digits, weights):
        total = sum(int(digit) * weight for digit, weight in zip(cnpj_digits, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder
    
    first_weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    second_weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    first_digit = calculate_digit(cnpj[:12], first_weights)
    second_digit = calculate_digit(cnpj[:13], second_weights)
    
    return cnpj[-2:] == f"{first_digit}{second_digit}"