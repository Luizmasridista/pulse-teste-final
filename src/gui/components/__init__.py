"""Componentes da interface gráfica.

Este módulo contém os componentes reutilizáveis da interface desktop.
"""

from .file_selector import FileSelector
from .progress_monitor import ProgressMonitor
from .settings_panel import SettingsPanel

__all__ = [
    'FileSelector',
    'ProgressMonitor',
    'SettingsPanel'
]