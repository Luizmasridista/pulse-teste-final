"""Módulo de manipulação e análise de planilhas.

Este módulo contém funcionalidades para descoberta, validação e análise
de planilhas subordinadas no sistema Pulse.
"""

from .scanner import SpreadsheetScanner, SpreadsheetInfo
from .validator import (
    SpreadsheetValidator,
    SpreadsheetValidationResult,
    ValidationStatus
)
from .analyzer import (
    SpreadsheetAnalyzer,
    SpreadsheetAnalysis,
    SheetAnalysis,
    CellInfo,
    CellStyle,
    CellType
)

__all__ = [
    'SpreadsheetScanner',
    'SpreadsheetInfo',
    'SpreadsheetValidator',
    'SpreadsheetValidationResult',
    'ValidationStatus',
    'SpreadsheetAnalyzer',
    'SpreadsheetAnalysis',
    'SheetAnalysis',
    'CellInfo',
    'CellStyle',
    'CellType'
]