"""Módulo de diálogos da interface gráfica.

Este módulo contém diálogos personalizados para a aplicação,
incluindo confirmação, relatórios e configurações avançadas.
"""

from .confirmation_dialog import ConfirmationDialog
from .report_dialog import ReportDialog
from .advanced_config_dialog import AdvancedConfigDialog

__all__ = [
    'ConfirmationDialog',
    'ReportDialog', 
    'AdvancedConfigDialog'
]