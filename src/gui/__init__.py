"""Módulo de interface gráfica do usuário (GUI).

Este módulo contém a implementação da interface desktop usando Tkinter,
incluindo janela principal, componentes e temas modernos.
"""

from .main_window import MainWindow
from .components import (
    FileSelector,
    ProgressMonitor,
    SettingsPanel
)
from .dialogs import (
    ConfirmationDialog,
    ReportDialog,
    AdvancedSettingsDialog
)
from .themes import ThemeManager, ModernTheme

__all__ = [
    'MainWindow',
    'FileSelector',
    'ProgressMonitor',
    'SettingsPanel',
    'ConfirmationDialog',
    'ReportDialog',
    'AdvancedSettingsDialog',
    'ThemeManager',
    'ModernTheme'
]