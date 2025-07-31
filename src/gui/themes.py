"""Sistema de temas para a interface gráfica.

Este módulo implementa temas modernos e personalizáveis para a interface
desktop do sistema Pulse.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class ColorScheme:
    """Esquema de cores para um tema."""
    primary: str
    secondary: str
    accent: str
    background: str
    surface: str
    text_primary: str
    text_secondary: str
    success: str
    warning: str
    error: str
    info: str


class Theme(ABC):
    """Classe base para temas."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nome do tema."""
        pass
    
    @property
    @abstractmethod
    def colors(self) -> ColorScheme:
        """Esquema de cores do tema."""
        pass
    
    @property
    @abstractmethod
    def fonts(self) -> Dict[str, tuple]:
        """Fontes do tema."""
        pass
    
    @abstractmethod
    def configure_styles(self, style: ttk.Style) -> None:
        """Configura estilos TTK para o tema."""
        pass


class ModernTheme(Theme):
    """Tema moderno com design clean e profissional."""
    
    @property
    def name(self) -> str:
        return "Modern"
    
    @property
    def colors(self) -> ColorScheme:
        return ColorScheme(
            primary="#2563eb",      # Azul moderno
            secondary="#64748b",    # Cinza azulado
            accent="#0ea5e9",       # Azul claro
            background="#ffffff",   # Branco
            surface="#f8fafc",      # Cinza muito claro
            text_primary="#1e293b", # Cinza escuro
            text_secondary="#64748b", # Cinza médio
            success="#10b981",      # Verde
            warning="#f59e0b",      # Amarelo
            error="#ef4444",        # Vermelho
            info="#3b82f6"          # Azul info
        )
    
    @property
    def fonts(self) -> Dict[str, tuple]:
        return {
            'default': ('Segoe UI', 9),
            'heading': ('Segoe UI', 12, 'bold'),
            'subheading': ('Segoe UI', 10, 'bold'),
            'small': ('Segoe UI', 8),
            'monospace': ('Consolas', 9)
        }
    
    def configure_styles(self, style: ttk.Style) -> None:
        """Configura estilos TTK para o tema moderno."""
        colors = self.colors
        
        # Configurar tema base
        style.theme_use('clam')
        
        # Frame principal
        style.configure('Main.TFrame',
                       background=colors.background,
                       relief='flat')
        
        # Frame de superfície
        style.configure('Surface.TFrame',
                       background=colors.surface,
                       relief='flat',
                       borderwidth=1)
        
        # Labels
        style.configure('TLabel',
                       background=colors.background,
                       foreground=colors.text_primary,
                       font=self.fonts['default'])
        
        style.configure('Heading.TLabel',
                       background=colors.background,
                       foreground=colors.text_primary,
                       font=self.fonts['heading'])
        
        style.configure('Subheading.TLabel',
                       background=colors.background,
                       foreground=colors.text_primary,
                       font=self.fonts['subheading'])
        
        style.configure('Secondary.TLabel',
                       background=colors.background,
                       foreground=colors.text_secondary,
                       font=self.fonts['default'])
        
        # Botões
        style.configure('TButton',
                       background=colors.primary,
                       foreground='white',
                       font=self.fonts['default'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(12, 8))
        
        style.map('TButton',
                 background=[('active', colors.accent),
                           ('pressed', colors.secondary)])
        
        # Botão secundário
        style.configure('Secondary.TButton',
                       background=colors.surface,
                       foreground=colors.text_primary,
                       font=self.fonts['default'],
                       borderwidth=1,
                       relief='solid',
                       padding=(12, 8))
        
        style.map('Secondary.TButton',
                 background=[('active', colors.secondary),
                           ('pressed', colors.primary)],
                 foreground=[('active', 'white'),
                           ('pressed', 'white')])
        
        # Botão de sucesso
        style.configure('Success.TButton',
                       background=colors.success,
                       foreground='white',
                       font=self.fonts['default'],
                       borderwidth=0,
                       padding=(12, 8))
        
        # Botão de erro
        style.configure('Error.TButton',
                       background=colors.error,
                       foreground='white',
                       font=self.fonts['default'],
                       borderwidth=0,
                       padding=(12, 8))
        
        # Entry
        style.configure('TEntry',
                       fieldbackground='white',
                       foreground=colors.text_primary,
                       borderwidth=1,
                       relief='solid',
                       padding=(8, 6))
        
        style.map('TEntry',
                 focuscolor=[('focus', colors.primary)])
        
        # Combobox
        style.configure('TCombobox',
                       fieldbackground='white',
                       foreground=colors.text_primary,
                       borderwidth=1,
                       relief='solid',
                       padding=(8, 6))
        
        # Progressbar
        style.configure('TProgressbar',
                       background=colors.primary,
                       troughcolor=colors.surface,
                       borderwidth=0,
                       lightcolor=colors.primary,
                       darkcolor=colors.primary)
        
        # Notebook
        style.configure('TNotebook',
                       background=colors.background,
                       borderwidth=0)
        
        style.configure('TNotebook.Tab',
                       background=colors.surface,
                       foreground=colors.text_primary,
                       padding=(12, 8),
                       borderwidth=0)
        
        style.map('TNotebook.Tab',
                 background=[('selected', colors.primary)],
                 foreground=[('selected', 'white')])
        
        # Treeview
        style.configure('Treeview',
                       background='white',
                       foreground=colors.text_primary,
                       fieldbackground='white',
                       borderwidth=1,
                       relief='solid')
        
        style.configure('Treeview.Heading',
                       background=colors.surface,
                       foreground=colors.text_primary,
                       font=self.fonts['subheading'],
                       borderwidth=1,
                       relief='solid')
        
        # Scrollbar
        style.configure('TScrollbar',
                       background=colors.surface,
                       troughcolor=colors.background,
                       borderwidth=0,
                       arrowcolor=colors.text_secondary)


class DarkTheme(Theme):
    """Tema escuro moderno."""
    
    @property
    def name(self) -> str:
        return "Dark"
    
    @property
    def colors(self) -> ColorScheme:
        return ColorScheme(
            primary="#3b82f6",      # Azul
            secondary="#6b7280",    # Cinza
            accent="#60a5fa",       # Azul claro
            background="#111827",   # Cinza muito escuro
            surface="#1f2937",      # Cinza escuro
            text_primary="#f9fafb", # Branco
            text_secondary="#d1d5db", # Cinza claro
            success="#10b981",      # Verde
            warning="#f59e0b",      # Amarelo
            error="#ef4444",        # Vermelho
            info="#3b82f6"          # Azul info
        )
    
    @property
    def fonts(self) -> Dict[str, tuple]:
        return {
            'default': ('Segoe UI', 9),
            'heading': ('Segoe UI', 12, 'bold'),
            'subheading': ('Segoe UI', 10, 'bold'),
            'small': ('Segoe UI', 8),
            'monospace': ('Consolas', 9)
        }
    
    def configure_styles(self, style: ttk.Style) -> None:
        """Configura estilos TTK para o tema escuro."""
        colors = self.colors
        
        # Configurar tema base
        style.theme_use('clam')
        
        # Frame principal
        style.configure('Main.TFrame',
                       background=colors.background,
                       relief='flat')
        
        # Frame de superfície
        style.configure('Surface.TFrame',
                       background=colors.surface,
                       relief='flat',
                       borderwidth=1)
        
        # Labels
        style.configure('TLabel',
                       background=colors.background,
                       foreground=colors.text_primary,
                       font=self.fonts['default'])
        
        style.configure('Heading.TLabel',
                       background=colors.background,
                       foreground=colors.text_primary,
                       font=self.fonts['heading'])
        
        # Botões e outros elementos seguem padrão similar ao tema claro
        # mas com cores adaptadas para o modo escuro
        
        style.configure('TButton',
                       background=colors.primary,
                       foreground='white',
                       font=self.fonts['default'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(12, 8))


class ThemeManager:
    """Gerenciador de temas da aplicação."""
    
    def __init__(self):
        """Inicializa o gerenciador de temas."""
        self._themes = {
            'modern': ModernTheme(),
            'dark': DarkTheme()
        }
        self._current_theme = 'modern'
        self._style = None
        
    def register_theme(self, name: str, theme: Theme) -> None:
        """Registra um novo tema.
        
        Args:
            name: Nome do tema.
            theme: Instância do tema.
        """
        self._themes[name] = theme
        
    def get_theme(self, name: str) -> Theme:
        """Obtém um tema pelo nome.
        
        Args:
            name: Nome do tema.
            
        Returns:
            Instância do tema.
            
        Raises:
            KeyError: Se o tema não existir.
        """
        if name not in self._themes:
            raise KeyError(f"Tema '{name}' não encontrado")
        return self._themes[name]
        
    def get_available_themes(self) -> list:
        """Obtém lista de temas disponíveis.
        
        Returns:
            Lista com nomes dos temas disponíveis.
        """
        return list(self._themes.keys())
        
    def set_current_theme(self, name: str) -> None:
        """Define o tema atual.
        
        Args:
            name: Nome do tema.
            
        Raises:
            KeyError: Se o tema não existir.
        """
        if name not in self._themes:
            raise KeyError(f"Tema '{name}' não encontrado")
        self._current_theme = name
        
    def get_current_theme(self) -> Theme:
        """Obtém o tema atual.
        
        Returns:
            Instância do tema atual.
        """
        return self._themes[self._current_theme]
        
    def apply_theme(self, root: tk.Tk, theme_name: str = None) -> None:
        """Aplica um tema à aplicação.
        
        Args:
            root: Janela raiz do Tkinter.
            theme_name: Nome do tema (usa o atual se None).
        """
        if theme_name:
            self.set_current_theme(theme_name)
            
        theme = self.get_current_theme()
        
        # Criar ou obter style
        if not self._style:
            self._style = ttk.Style(root)
            
        # Aplicar configurações do tema
        theme.configure_styles(self._style)
        
        # Configurar cores da janela raiz
        root.configure(bg=theme.colors.background)
        
    def get_color(self, color_name: str) -> str:
        """Obtém uma cor do tema atual.
        
        Args:
            color_name: Nome da cor.
            
        Returns:
            Código hexadecimal da cor.
        """
        theme = self.get_current_theme()
        return getattr(theme.colors, color_name, '#000000')
        
    def get_font(self, font_name: str) -> tuple:
        """Obtém uma fonte do tema atual.
        
        Args:
            font_name: Nome da fonte.
            
        Returns:
            Tupla com configuração da fonte.
        """
        theme = self.get_current_theme()
        return theme.fonts.get(font_name, ('Arial', 9))


# Instância global do gerenciador de temas
theme_manager = ThemeManager()