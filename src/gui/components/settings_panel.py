"""Painel de configurações da aplicação.

Este módulo implementa um painel completo de configurações com abas
para backup, preferências gerais, validação e configurações avançadas.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Any, Callable, Optional
import json
import os
from pathlib import Path

from ...core import get_logger, config_manager
from ..themes import theme_manager


class SettingsPanel(ttk.Frame):
    """Painel de configurações da aplicação.
    
    Funcionalidades:
    - Configurações de backup automático
    - Preferências de interface
    - Configurações de validação
    - Configurações avançadas
    - Importar/exportar configurações
    """
    
    def __init__(self, parent, on_settings_changed: Callable[[Dict[str, Any]], None] = None, **kwargs):
        """Inicializa o painel de configurações.
        
        Args:
            parent: Widget pai.
            on_settings_changed: Callback chamado quando configurações mudam.
            **kwargs: Argumentos adicionais para ttk.Frame.
        """
        super().__init__(parent, **kwargs)
        
        self.logger = get_logger(__name__)
        self.on_settings_changed = on_settings_changed
        
        # Configurações atuais
        self.settings = self._load_settings()
        
        # Variáveis de interface
        self._setup_variables()
        
        # Configurar interface
        self._setup_ui()
        
        # Carregar valores atuais
        self._load_current_values()
        
    def _setup_variables(self):
        """Configura variáveis de interface."""
        # Backup
        self.backup_enabled = tk.BooleanVar()
        self.backup_path = tk.StringVar()
        self.backup_frequency = tk.StringVar()
        self.backup_retention = tk.IntVar()
        self.backup_compression = tk.BooleanVar()
        
        # Interface
        self.theme_name = tk.StringVar()
        self.auto_save = tk.BooleanVar()
        self.show_tooltips = tk.BooleanVar()
        self.confirm_actions = tk.BooleanVar()
        self.window_size = tk.StringVar()
        
        # Validação
        self.validate_on_load = tk.BooleanVar()
        self.strict_validation = tk.BooleanVar()
        self.max_file_size = tk.IntVar()
        self.allowed_extensions = tk.StringVar()
        
        # Avançado
        self.log_level = tk.StringVar()
        self.cache_enabled = tk.BooleanVar()
        self.cache_size = tk.IntVar()
        self.parallel_processing = tk.BooleanVar()
        self.max_workers = tk.IntVar()
        
    def _setup_ui(self):
        """Configura a interface do painel."""
        self.configure(style='Surface.TFrame', padding=10)
        
        # Título
        title_label = ttk.Label(self, text="Configurações", style='Heading.TLabel')
        title_label.grid(row=0, column=0, sticky='w', pady=(0, 20))
        
        # Notebook para abas
        self.notebook = ttk.Notebook(self, style='TNotebook')
        self.notebook.grid(row=1, column=0, sticky='nsew', pady=(0, 20))
        
        # Criar abas
        self._create_backup_tab()
        self._create_interface_tab()
        self._create_validation_tab()
        self._create_advanced_tab()
        
        # Frame de botões
        button_frame = ttk.Frame(self, style='Main.TFrame')
        button_frame.grid(row=2, column=0, sticky='ew')
        
        # Botões de ação
        ttk.Button(button_frame, text="Restaurar Padrões", 
                  command=self._restore_defaults,
                  style='Secondary.TButton').grid(row=0, column=0, sticky='w')
                  
        ttk.Button(button_frame, text="Importar", 
                  command=self._import_settings,
                  style='Secondary.TButton').grid(row=0, column=1, sticky='w', padx=(10, 0))
                  
        ttk.Button(button_frame, text="Exportar", 
                  command=self._export_settings,
                  style='Secondary.TButton').grid(row=0, column=2, sticky='w', padx=(10, 0))
                  
        button_frame.columnconfigure(3, weight=1)
        
        ttk.Button(button_frame, text="Cancelar", 
                  command=self._cancel_changes,
                  style='Secondary.TButton').grid(row=0, column=4, sticky='e', padx=(10, 0))
                  
        ttk.Button(button_frame, text="Aplicar", 
                  command=self._apply_settings,
                  style='Primary.TButton').grid(row=0, column=5, sticky='e', padx=(10, 0))
        
        # Configurar grid
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
    def _create_backup_tab(self):
        """Cria aba de configurações de backup."""
        backup_frame = ttk.Frame(self.notebook, style='Main.TFrame', padding=20)
        self.notebook.add(backup_frame, text="Backup")
        
        # Habilitar backup
        ttk.Checkbutton(backup_frame, text="Habilitar backup automático", 
                       variable=self.backup_enabled,
                       command=self._on_backup_enabled_changed,
                       style='TCheckbutton').grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 15))
        
        # Caminho do backup
        ttk.Label(backup_frame, text="Pasta de backup:", style='TLabel').grid(row=1, column=0, sticky='w', pady=(0, 5))
        
        path_frame = ttk.Frame(backup_frame, style='Main.TFrame')
        path_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(0, 15))
        path_frame.columnconfigure(0, weight=1)
        
        self.backup_path_entry = ttk.Entry(path_frame, textvariable=self.backup_path, 
                                          style='TEntry', state='readonly')
        self.backup_path_entry.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        
        ttk.Button(path_frame, text="Procurar", 
                  command=self._browse_backup_path,
                  style='Secondary.TButton').grid(row=0, column=1, sticky='e')
        
        # Frequência do backup
        ttk.Label(backup_frame, text="Frequência:", style='TLabel').grid(row=3, column=0, sticky='w', pady=(0, 5))
        
        frequency_combo = ttk.Combobox(backup_frame, textvariable=self.backup_frequency,
                                      values=["Diário", "Semanal", "Mensal", "Manual"],
                                      state='readonly', style='TCombobox')
        frequency_combo.grid(row=4, column=0, sticky='w', pady=(0, 15))
        
        # Retenção
        ttk.Label(backup_frame, text="Manter backups (dias):", style='TLabel').grid(row=5, column=0, sticky='w', pady=(0, 5))
        
        retention_spin = ttk.Spinbox(backup_frame, from_=1, to=365, 
                                    textvariable=self.backup_retention,
                                    style='TSpinbox', width=10)
        retention_spin.grid(row=6, column=0, sticky='w', pady=(0, 15))
        
        # Compressão
        ttk.Checkbutton(backup_frame, text="Comprimir backups", 
                       variable=self.backup_compression,
                       style='TCheckbutton').grid(row=7, column=0, sticky='w')
        
        backup_frame.columnconfigure(0, weight=1)
        
    def _create_interface_tab(self):
        """Cria aba de configurações de interface."""
        interface_frame = ttk.Frame(self.notebook, style='Main.TFrame', padding=20)
        self.notebook.add(interface_frame, text="Interface")
        
        # Tema
        ttk.Label(interface_frame, text="Tema:", style='TLabel').grid(row=0, column=0, sticky='w', pady=(0, 5))
        
        theme_combo = ttk.Combobox(interface_frame, textvariable=self.theme_name,
                                  values=["Moderno", "Escuro", "Clássico"],
                                  state='readonly', style='TCombobox')
        theme_combo.grid(row=1, column=0, sticky='w', pady=(0, 15))
        
        # Tamanho da janela
        ttk.Label(interface_frame, text="Tamanho da janela:", style='TLabel').grid(row=2, column=0, sticky='w', pady=(0, 5))
        
        size_combo = ttk.Combobox(interface_frame, textvariable=self.window_size,
                                 values=["800x600", "1024x768", "1280x720", "1920x1080", "Maximizada"],
                                 state='readonly', style='TCombobox')
        size_combo.grid(row=3, column=0, sticky='w', pady=(0, 15))
        
        # Opções gerais
        ttk.Checkbutton(interface_frame, text="Salvar automaticamente", 
                       variable=self.auto_save,
                       style='TCheckbutton').grid(row=4, column=0, sticky='w', pady=(0, 10))
        
        ttk.Checkbutton(interface_frame, text="Mostrar dicas de ferramentas", 
                       variable=self.show_tooltips,
                       style='TCheckbutton').grid(row=5, column=0, sticky='w', pady=(0, 10))
        
        ttk.Checkbutton(interface_frame, text="Confirmar ações importantes", 
                       variable=self.confirm_actions,
                       style='TCheckbutton').grid(row=6, column=0, sticky='w')
        
        interface_frame.columnconfigure(0, weight=1)
        
    def _create_validation_tab(self):
        """Cria aba de configurações de validação."""
        validation_frame = ttk.Frame(self.notebook, style='Main.TFrame', padding=20)
        self.notebook.add(validation_frame, text="Validação")
        
        # Validação automática
        ttk.Checkbutton(validation_frame, text="Validar ao carregar arquivos", 
                       variable=self.validate_on_load,
                       style='TCheckbutton').grid(row=0, column=0, sticky='w', pady=(0, 15))
        
        ttk.Checkbutton(validation_frame, text="Validação rigorosa", 
                       variable=self.strict_validation,
                       style='TCheckbutton').grid(row=1, column=0, sticky='w', pady=(0, 15))
        
        # Tamanho máximo de arquivo
        ttk.Label(validation_frame, text="Tamanho máximo de arquivo (MB):", 
                 style='TLabel').grid(row=2, column=0, sticky='w', pady=(0, 5))
        
        size_spin = ttk.Spinbox(validation_frame, from_=1, to=1000, 
                               textvariable=self.max_file_size,
                               style='TSpinbox', width=10)
        size_spin.grid(row=3, column=0, sticky='w', pady=(0, 15))
        
        # Extensões permitidas
        ttk.Label(validation_frame, text="Extensões permitidas (separadas por vírgula):", 
                 style='TLabel').grid(row=4, column=0, sticky='w', pady=(0, 5))
        
        ttk.Entry(validation_frame, textvariable=self.allowed_extensions, 
                 style='TEntry', width=40).grid(row=5, column=0, sticky='w')
        
        validation_frame.columnconfigure(0, weight=1)
        
    def _create_advanced_tab(self):
        """Cria aba de configurações avançadas."""
        advanced_frame = ttk.Frame(self.notebook, style='Main.TFrame', padding=20)
        self.notebook.add(advanced_frame, text="Avançado")
        
        # Nível de log
        ttk.Label(advanced_frame, text="Nível de log:", style='TLabel').grid(row=0, column=0, sticky='w', pady=(0, 5))
        
        log_combo = ttk.Combobox(advanced_frame, textvariable=self.log_level,
                                values=["DEBUG", "INFO", "WARNING", "ERROR"],
                                state='readonly', style='TCombobox')
        log_combo.grid(row=1, column=0, sticky='w', pady=(0, 15))
        
        # Cache
        ttk.Checkbutton(advanced_frame, text="Habilitar cache", 
                       variable=self.cache_enabled,
                       command=self._on_cache_enabled_changed,
                       style='TCheckbutton').grid(row=2, column=0, sticky='w', pady=(0, 10))
        
        ttk.Label(advanced_frame, text="Tamanho do cache (MB):", 
                 style='TLabel').grid(row=3, column=0, sticky='w', pady=(0, 5))
        
        self.cache_size_spin = ttk.Spinbox(advanced_frame, from_=10, to=1000, 
                                          textvariable=self.cache_size,
                                          style='TSpinbox', width=10)
        self.cache_size_spin.grid(row=4, column=0, sticky='w', pady=(0, 15))
        
        # Processamento paralelo
        ttk.Checkbutton(advanced_frame, text="Processamento paralelo", 
                       variable=self.parallel_processing,
                       command=self._on_parallel_enabled_changed,
                       style='TCheckbutton').grid(row=5, column=0, sticky='w', pady=(0, 10))
        
        ttk.Label(advanced_frame, text="Máximo de workers:", 
                 style='TLabel').grid(row=6, column=0, sticky='w', pady=(0, 5))
        
        self.max_workers_spin = ttk.Spinbox(advanced_frame, from_=1, to=16, 
                                           textvariable=self.max_workers,
                                           style='TSpinbox', width=10)
        self.max_workers_spin.grid(row=7, column=0, sticky='w')
        
        advanced_frame.columnconfigure(0, weight=1)
        
    def _load_settings(self) -> Dict[str, Any]:
        """Carrega configurações atuais.
        
        Returns:
            Dicionário com configurações.
        """
        try:
            # Tentar carregar do config_manager
            settings = {
                # Backup
                'backup_enabled': config_manager.get('backup.enabled', False),
                'backup_path': config_manager.get('backup.path', ''),
                'backup_frequency': config_manager.get('backup.frequency', 'Semanal'),
                'backup_retention': config_manager.get('backup.retention_days', 30),
                'backup_compression': config_manager.get('backup.compression', True),
                
                # Interface
                'theme_name': config_manager.get('ui.theme', 'Moderno'),
                'auto_save': config_manager.get('ui.auto_save', True),
                'show_tooltips': config_manager.get('ui.show_tooltips', True),
                'confirm_actions': config_manager.get('ui.confirm_actions', True),
                'window_size': config_manager.get('ui.window_size', '1024x768'),
                
                # Validação
                'validate_on_load': config_manager.get('validation.on_load', True),
                'strict_validation': config_manager.get('validation.strict', False),
                'max_file_size': config_manager.get('validation.max_file_size_mb', 100),
                'allowed_extensions': config_manager.get('validation.allowed_extensions', '.xlsx,.xls'),
                
                # Avançado
                'log_level': config_manager.get('logging.level', 'INFO'),
                'cache_enabled': config_manager.get('cache.enabled', True),
                'cache_size': config_manager.get('cache.size_mb', 100),
                'parallel_processing': config_manager.get('processing.parallel', True),
                'max_workers': config_manager.get('processing.max_workers', 4)
            }
            
            return settings
            
        except Exception as e:
            self.logger.warning(f"Erro ao carregar configurações: {e}")
            return self._get_default_settings()
            
    def _get_default_settings(self) -> Dict[str, Any]:
        """Retorna configurações padrão.
        
        Returns:
            Dicionário com configurações padrão.
        """
        return {
            # Backup
            'backup_enabled': False,
            'backup_path': str(Path.home() / 'Documents' / 'PulseBackups'),
            'backup_frequency': 'Semanal',
            'backup_retention': 30,
            'backup_compression': True,
            
            # Interface
            'theme_name': 'Moderno',
            'auto_save': True,
            'show_tooltips': True,
            'confirm_actions': True,
            'window_size': '1024x768',
            
            # Validação
            'validate_on_load': True,
            'strict_validation': False,
            'max_file_size': 100,
            'allowed_extensions': '.xlsx,.xls',
            
            # Avançado
            'log_level': 'INFO',
            'cache_enabled': True,
            'cache_size': 100,
            'parallel_processing': True,
            'max_workers': 4
        }
        
    def _load_current_values(self):
        """Carrega valores atuais nas variáveis de interface."""
        # Backup
        self.backup_enabled.set(self.settings['backup_enabled'])
        self.backup_path.set(self.settings['backup_path'])
        self.backup_frequency.set(self.settings['backup_frequency'])
        self.backup_retention.set(self.settings['backup_retention'])
        self.backup_compression.set(self.settings['backup_compression'])
        
        # Interface
        self.theme_name.set(self.settings['theme_name'])
        self.auto_save.set(self.settings['auto_save'])
        self.show_tooltips.set(self.settings['show_tooltips'])
        self.confirm_actions.set(self.settings['confirm_actions'])
        self.window_size.set(self.settings['window_size'])
        
        # Validação
        self.validate_on_load.set(self.settings['validate_on_load'])
        self.strict_validation.set(self.settings['strict_validation'])
        self.max_file_size.set(self.settings['max_file_size'])
        self.allowed_extensions.set(self.settings['allowed_extensions'])
        
        # Avançado
        self.log_level.set(self.settings['log_level'])
        self.cache_enabled.set(self.settings['cache_enabled'])
        self.cache_size.set(self.settings['cache_size'])
        self.parallel_processing.set(self.settings['parallel_processing'])
        self.max_workers.set(self.settings['max_workers'])
        
        # Atualizar estado dos controles
        self._on_backup_enabled_changed()
        self._on_cache_enabled_changed()
        self._on_parallel_enabled_changed()
        
    def _on_backup_enabled_changed(self):
        """Manipula mudança na habilitação de backup."""
        enabled = self.backup_enabled.get()
        state = 'normal' if enabled else 'disabled'
        
        # Habilitar/desabilitar controles de backup
        widgets = [self.backup_path_entry]
        for widget in widgets:
            widget.config(state=state)
            
    def _on_cache_enabled_changed(self):
        """Manipula mudança na habilitação de cache."""
        enabled = self.cache_enabled.get()
        state = 'normal' if enabled else 'disabled'
        self.cache_size_spin.config(state=state)
        
    def _on_parallel_enabled_changed(self):
        """Manipula mudança na habilitação de processamento paralelo."""
        enabled = self.parallel_processing.get()
        state = 'normal' if enabled else 'disabled'
        self.max_workers_spin.config(state=state)
        
    def _browse_backup_path(self):
        """Abre diálogo para selecionar pasta de backup."""
        current_path = self.backup_path.get()
        initial_dir = current_path if current_path and os.path.exists(current_path) else str(Path.home())
        
        path = filedialog.askdirectory(
            title="Selecionar pasta de backup",
            initialdir=initial_dir
        )
        
        if path:
            self.backup_path.set(path)
            
    def _restore_defaults(self):
        """Restaura configurações padrão."""
        if messagebox.askyesno("Confirmar", 
                              "Deseja restaurar todas as configurações para os valores padrão?"):
            self.settings = self._get_default_settings()
            self._load_current_values()
            
    def _import_settings(self):
        """Importa configurações de arquivo."""
        file_path = filedialog.askopenfilename(
            title="Importar configurações",
            filetypes=[("Arquivos JSON", "*.json"), ("Todos os arquivos", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_settings = json.load(f)
                    
                # Validar e mesclar configurações
                default_settings = self._get_default_settings()
                for key, value in imported_settings.items():
                    if key in default_settings:
                        self.settings[key] = value
                        
                self._load_current_values()
                messagebox.showinfo("Sucesso", "Configurações importadas com sucesso!")
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao importar configurações: {e}")
                
    def _export_settings(self):
        """Exporta configurações para arquivo."""
        file_path = filedialog.asksaveasfilename(
            title="Exportar configurações",
            defaultextension=".json",
            filetypes=[("Arquivos JSON", "*.json"), ("Todos os arquivos", "*.*")]
        )
        
        if file_path:
            try:
                current_settings = self._get_current_values()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(current_settings, f, indent=2, ensure_ascii=False)
                    
                messagebox.showinfo("Sucesso", "Configurações exportadas com sucesso!")
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar configurações: {e}")
                
    def _get_current_values(self) -> Dict[str, Any]:
        """Obtém valores atuais das variáveis de interface.
        
        Returns:
            Dicionário com valores atuais.
        """
        return {
            # Backup
            'backup_enabled': self.backup_enabled.get(),
            'backup_path': self.backup_path.get(),
            'backup_frequency': self.backup_frequency.get(),
            'backup_retention': self.backup_retention.get(),
            'backup_compression': self.backup_compression.get(),
            
            # Interface
            'theme_name': self.theme_name.get(),
            'auto_save': self.auto_save.get(),
            'show_tooltips': self.show_tooltips.get(),
            'confirm_actions': self.confirm_actions.get(),
            'window_size': self.window_size.get(),
            
            # Validação
            'validate_on_load': self.validate_on_load.get(),
            'strict_validation': self.strict_validation.get(),
            'max_file_size': self.max_file_size.get(),
            'allowed_extensions': self.allowed_extensions.get(),
            
            # Avançado
            'log_level': self.log_level.get(),
            'cache_enabled': self.cache_enabled.get(),
            'cache_size': self.cache_size.get(),
            'parallel_processing': self.parallel_processing.get(),
            'max_workers': self.max_workers.get()
        }
        
    def _apply_settings(self):
        """Aplica as configurações atuais."""
        try:
            current_values = self._get_current_values()
            
            # Salvar no config_manager
            for key, value in current_values.items():
                config_key = self._get_config_key(key)
                config_manager.set(config_key, value)
                
            # Atualizar configurações internas
            self.settings = current_values
            
            # Notificar callback
            if self.on_settings_changed:
                self.on_settings_changed(current_values)
                
            messagebox.showinfo("Sucesso", "Configurações aplicadas com sucesso!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao aplicar configurações: {e}")
            
    def _cancel_changes(self):
        """Cancela mudanças e restaura valores originais."""
        self._load_current_values()
        
    def _get_config_key(self, setting_key: str) -> str:
        """Converte chave de configuração para formato do config_manager.
        
        Args:
            setting_key: Chave da configuração.
            
        Returns:
            Chave formatada para config_manager.
        """
        key_mapping = {
            # Backup
            'backup_enabled': 'backup.enabled',
            'backup_path': 'backup.path',
            'backup_frequency': 'backup.frequency',
            'backup_retention': 'backup.retention_days',
            'backup_compression': 'backup.compression',
            
            # Interface
            'theme_name': 'ui.theme',
            'auto_save': 'ui.auto_save',
            'show_tooltips': 'ui.show_tooltips',
            'confirm_actions': 'ui.confirm_actions',
            'window_size': 'ui.window_size',
            
            # Validação
            'validate_on_load': 'validation.on_load',
            'strict_validation': 'validation.strict',
            'max_file_size': 'validation.max_file_size_mb',
            'allowed_extensions': 'validation.allowed_extensions',
            
            # Avançado
            'log_level': 'logging.level',
            'cache_enabled': 'cache.enabled',
            'cache_size': 'cache.size_mb',
            'parallel_processing': 'processing.parallel',
            'max_workers': 'processing.max_workers'
        }
        
        return key_mapping.get(setting_key, setting_key)
        
    def get_settings(self) -> Dict[str, Any]:
        """Obtém configurações atuais.
        
        Returns:
            Dicionário com configurações atuais.
        """
        return self.settings.copy()
        
    def update_setting(self, key: str, value: Any):
        """Atualiza uma configuração específica.
        
        Args:
            key: Chave da configuração.
            value: Novo valor.
        """
        if key in self.settings:
            self.settings[key] = value
            self._load_current_values()