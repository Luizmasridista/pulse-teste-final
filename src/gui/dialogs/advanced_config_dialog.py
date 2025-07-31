"""Diálogo de configurações avançadas.

Este módulo implementa um diálogo para configurações avançadas
do sistema, incluindo parâmetros técnicos e opções de desenvolvedor.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from typing import Dict, Any, Optional, Callable
from pathlib import Path
import json

from ...core import get_logger
from ..themes import theme_manager


class AdvancedConfigDialog:
    """Diálogo para configurações avançadas.
    
    Funcionalidades:
    - Configurações de performance
    - Parâmetros de validação
    - Configurações de logging
    - Opções de desenvolvedor
    - Configurações de cache
    - Parâmetros de sincronização
    """
    
    def __init__(self, parent, config: Dict[str, Any] = None, 
                 on_save: Optional[Callable] = None):
        """Inicializa o diálogo de configurações avançadas.
        
        Args:
            parent: Widget pai.
            config: Configurações atuais.
            on_save: Callback para salvar configurações.
        """
        self.parent = parent
        self.config = config or self._get_default_config()
        self.on_save = on_save
        self.logger = get_logger(__name__)
        
        # Variáveis de controle
        self.vars = {}
        self.result = None
        
        # Criar diálogo
        self.dialog = None
        self._create_dialog()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Retorna configuração padrão.
        
        Returns:
            Dicionário com configurações padrão.
        """
        return {
            'performance': {
                'max_workers': 4,
                'chunk_size': 1000,
                'memory_limit_mb': 512,
                'enable_parallel_processing': True,
                'cache_size_mb': 100
            },
            'validation': {
                'strict_mode': False,
                'validate_formulas': True,
                'check_data_types': True,
                'allow_empty_cells': True,
                'max_errors_per_file': 10
            },
            'logging': {
                'level': 'INFO',
                'enable_file_logging': True,
                'max_log_size_mb': 10,
                'backup_count': 5,
                'enable_debug_mode': False
            },
            'sync': {
                'auto_sync_interval': 300,
                'enable_real_time_sync': False,
                'conflict_resolution': 'newer_wins',
                'backup_before_sync': True,
                'max_sync_retries': 3
            },
            'developer': {
                'enable_profiling': False,
                'show_debug_info': False,
                'enable_experimental_features': False,
                'custom_scripts_path': '',
                'api_timeout': 30
            }
        }
        
    def _create_dialog(self):
        """Cria o diálogo."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Configurações Avançadas")
        self.dialog.geometry("700x600")
        self.dialog.resizable(True, True)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Configurar estilo
        self.dialog.configure(bg=theme_manager.get_color('surface'))
        
        # Centralizar na tela
        self._center_dialog()
        
        # Configurar conteúdo
        self._setup_content()
        
        # Configurar eventos
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.dialog.bind('<Escape>', lambda e: self._on_cancel())
        
    def _center_dialog(self):
        """Centraliza o diálogo na tela."""
        self.dialog.update_idletasks()
        
        # Obter dimensões
        width = 700
        height = 600
        
        # Calcular posição central
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        
    def _setup_content(self):
        """Configura o conteúdo do diálogo."""
        main_frame = ttk.Frame(self.dialog, style='Surface.TFrame', padding=15)
        main_frame.pack(fill='both', expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="Configurações Avançadas",
                               style='Heading.TLabel')
        title_label.pack(anchor='w', pady=(0, 15))
        
        # Notebook para categorias
        self.notebook = ttk.Notebook(main_frame, style='TNotebook')
        self.notebook.pack(fill='both', expand=True, pady=(0, 15))
        
        # Criar abas
        self._create_performance_tab()
        self._create_validation_tab()
        self._create_logging_tab()
        self._create_sync_tab()
        self._create_developer_tab()
        
        # Frame de botões
        button_frame = ttk.Frame(main_frame, style='Main.TFrame')
        button_frame.pack(fill='x')
        
        # Botões de ação
        ttk.Button(button_frame, text="Restaurar Padrões",
                  command=self._restore_defaults,
                  style='Secondary.TButton').pack(side='left')
                  
        ttk.Button(button_frame, text="Importar",
                  command=self._import_config,
                  style='Secondary.TButton').pack(side='left', padx=(10, 0))
                  
        ttk.Button(button_frame, text="Exportar",
                  command=self._export_config,
                  style='Secondary.TButton').pack(side='left', padx=(10, 0))
        
        # Botões principais
        ttk.Button(button_frame, text="Cancelar",
                  command=self._on_cancel,
                  style='Secondary.TButton').pack(side='right')
                  
        ttk.Button(button_frame, text="Aplicar",
                  command=self._on_apply,
                  style='Primary.TButton').pack(side='right', padx=(0, 10))
        
    def _create_performance_tab(self):
        """Cria aba de configurações de performance."""
        perf_frame = ttk.Frame(self.notebook, style='Main.TFrame', padding=15)
        self.notebook.add(perf_frame, text="Performance")
        
        # Configurações de processamento
        proc_label = ttk.Label(perf_frame, text="Processamento:", style='Subheading.TLabel')
        proc_label.pack(anchor='w', pady=(0, 10))
        
        proc_config_frame = ttk.LabelFrame(perf_frame, text="Configurações de Processamento",
                                          style='TLabelframe', padding=10)
        proc_config_frame.pack(fill='x', pady=(0, 15))
        
        # Max workers
        workers_frame = ttk.Frame(proc_config_frame, style='Main.TFrame')
        workers_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(workers_frame, text="Máximo de Workers:", style='TLabel').pack(side='left')
        self.vars['max_workers'] = tk.IntVar(value=self.config['performance']['max_workers'])
        workers_spin = ttk.Spinbox(workers_frame, from_=1, to=16, width=10,
                                  textvariable=self.vars['max_workers'])
        workers_spin.pack(side='right')
        
        # Chunk size
        chunk_frame = ttk.Frame(proc_config_frame, style='Main.TFrame')
        chunk_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(chunk_frame, text="Tamanho do Chunk:", style='TLabel').pack(side='left')
        self.vars['chunk_size'] = tk.IntVar(value=self.config['performance']['chunk_size'])
        chunk_spin = ttk.Spinbox(chunk_frame, from_=100, to=10000, width=10,
                                textvariable=self.vars['chunk_size'])
        chunk_spin.pack(side='right')
        
        # Parallel processing
        self.vars['enable_parallel_processing'] = tk.BooleanVar(
            value=self.config['performance']['enable_parallel_processing'])
        parallel_check = ttk.Checkbutton(proc_config_frame, 
                                        text="Habilitar processamento paralelo",
                                        variable=self.vars['enable_parallel_processing'],
                                        style='TCheckbutton')
        parallel_check.pack(anchor='w', pady=(5, 0))
        
        # Configurações de memória
        mem_label = ttk.Label(perf_frame, text="Memória:", style='Subheading.TLabel')
        mem_label.pack(anchor='w', pady=(10, 10))
        
        mem_config_frame = ttk.LabelFrame(perf_frame, text="Configurações de Memória",
                                         style='TLabelframe', padding=10)
        mem_config_frame.pack(fill='x')
        
        # Memory limit
        mem_frame = ttk.Frame(mem_config_frame, style='Main.TFrame')
        mem_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(mem_frame, text="Limite de Memória (MB):", style='TLabel').pack(side='left')
        self.vars['memory_limit_mb'] = tk.IntVar(value=self.config['performance']['memory_limit_mb'])
        mem_spin = ttk.Spinbox(mem_frame, from_=128, to=4096, width=10,
                              textvariable=self.vars['memory_limit_mb'])
        mem_spin.pack(side='right')
        
        # Cache size
        cache_frame = ttk.Frame(mem_config_frame, style='Main.TFrame')
        cache_frame.pack(fill='x')
        
        ttk.Label(cache_frame, text="Tamanho do Cache (MB):", style='TLabel').pack(side='left')
        self.vars['cache_size_mb'] = tk.IntVar(value=self.config['performance']['cache_size_mb'])
        cache_spin = ttk.Spinbox(cache_frame, from_=10, to=1024, width=10,
                                textvariable=self.vars['cache_size_mb'])
        cache_spin.pack(side='right')
        
    def _create_validation_tab(self):
        """Cria aba de configurações de validação."""
        val_frame = ttk.Frame(self.notebook, style='Main.TFrame', padding=15)
        self.notebook.add(val_frame, text="Validação")
        
        # Modo de validação
        mode_frame = ttk.LabelFrame(val_frame, text="Modo de Validação",
                                   style='TLabelframe', padding=10)
        mode_frame.pack(fill='x', pady=(0, 15))
        
        self.vars['strict_mode'] = tk.BooleanVar(value=self.config['validation']['strict_mode'])
        strict_check = ttk.Checkbutton(mode_frame, text="Modo Estrito",
                                      variable=self.vars['strict_mode'],
                                      style='TCheckbutton')
        strict_check.pack(anchor='w')
        
        # Opções de validação
        options_frame = ttk.LabelFrame(val_frame, text="Opções de Validação",
                                      style='TLabelframe', padding=10)
        options_frame.pack(fill='x', pady=(0, 15))
        
        self.vars['validate_formulas'] = tk.BooleanVar(
            value=self.config['validation']['validate_formulas'])
        formulas_check = ttk.Checkbutton(options_frame, text="Validar Fórmulas",
                                        variable=self.vars['validate_formulas'],
                                        style='TCheckbutton')
        formulas_check.pack(anchor='w', pady=(0, 5))
        
        self.vars['check_data_types'] = tk.BooleanVar(
            value=self.config['validation']['check_data_types'])
        types_check = ttk.Checkbutton(options_frame, text="Verificar Tipos de Dados",
                                     variable=self.vars['check_data_types'],
                                     style='TCheckbutton')
        types_check.pack(anchor='w', pady=(0, 5))
        
        self.vars['allow_empty_cells'] = tk.BooleanVar(
            value=self.config['validation']['allow_empty_cells'])
        empty_check = ttk.Checkbutton(options_frame, text="Permitir Células Vazias",
                                     variable=self.vars['allow_empty_cells'],
                                     style='TCheckbutton')
        empty_check.pack(anchor='w')
        
        # Limites
        limits_frame = ttk.LabelFrame(val_frame, text="Limites",
                                     style='TLabelframe', padding=10)
        limits_frame.pack(fill='x')
        
        errors_frame = ttk.Frame(limits_frame, style='Main.TFrame')
        errors_frame.pack(fill='x')
        
        ttk.Label(errors_frame, text="Máximo de Erros por Arquivo:", style='TLabel').pack(side='left')
        self.vars['max_errors_per_file'] = tk.IntVar(
            value=self.config['validation']['max_errors_per_file'])
        errors_spin = ttk.Spinbox(errors_frame, from_=1, to=100, width=10,
                                 textvariable=self.vars['max_errors_per_file'])
        errors_spin.pack(side='right')
        
    def _create_logging_tab(self):
        """Cria aba de configurações de logging."""
        log_frame = ttk.Frame(self.notebook, style='Main.TFrame', padding=15)
        self.notebook.add(log_frame, text="Logging")
        
        # Nível de log
        level_frame = ttk.LabelFrame(log_frame, text="Nível de Log",
                                    style='TLabelframe', padding=10)
        level_frame.pack(fill='x', pady=(0, 15))
        
        level_inner_frame = ttk.Frame(level_frame, style='Main.TFrame')
        level_inner_frame.pack(fill='x')
        
        ttk.Label(level_inner_frame, text="Nível:", style='TLabel').pack(side='left')
        self.vars['log_level'] = tk.StringVar(value=self.config['logging']['level'])
        level_combo = ttk.Combobox(level_inner_frame, textvariable=self.vars['log_level'],
                                  values=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                                  state='readonly', width=15)
        level_combo.pack(side='right')
        
        # Opções de arquivo
        file_frame = ttk.LabelFrame(log_frame, text="Arquivo de Log",
                                   style='TLabelframe', padding=10)
        file_frame.pack(fill='x', pady=(0, 15))
        
        self.vars['enable_file_logging'] = tk.BooleanVar(
            value=self.config['logging']['enable_file_logging'])
        file_check = ttk.Checkbutton(file_frame, text="Habilitar log em arquivo",
                                    variable=self.vars['enable_file_logging'],
                                    style='TCheckbutton')
        file_check.pack(anchor='w', pady=(0, 10))
        
        # Tamanho máximo
        size_frame = ttk.Frame(file_frame, style='Main.TFrame')
        size_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(size_frame, text="Tamanho Máximo (MB):", style='TLabel').pack(side='left')
        self.vars['max_log_size_mb'] = tk.IntVar(value=self.config['logging']['max_log_size_mb'])
        size_spin = ttk.Spinbox(size_frame, from_=1, to=100, width=10,
                               textvariable=self.vars['max_log_size_mb'])
        size_spin.pack(side='right')
        
        # Backup count
        backup_frame = ttk.Frame(file_frame, style='Main.TFrame')
        backup_frame.pack(fill='x')
        
        ttk.Label(backup_frame, text="Número de Backups:", style='TLabel').pack(side='left')
        self.vars['backup_count'] = tk.IntVar(value=self.config['logging']['backup_count'])
        backup_spin = ttk.Spinbox(backup_frame, from_=1, to=20, width=10,
                                 textvariable=self.vars['backup_count'])
        backup_spin.pack(side='right')
        
        # Debug
        debug_frame = ttk.LabelFrame(log_frame, text="Debug",
                                    style='TLabelframe', padding=10)
        debug_frame.pack(fill='x')
        
        self.vars['enable_debug_mode'] = tk.BooleanVar(
            value=self.config['logging']['enable_debug_mode'])
        debug_check = ttk.Checkbutton(debug_frame, text="Habilitar modo debug",
                                     variable=self.vars['enable_debug_mode'],
                                     style='TCheckbutton')
        debug_check.pack(anchor='w')
        
    def _create_sync_tab(self):
        """Cria aba de configurações de sincronização."""
        sync_frame = ttk.Frame(self.notebook, style='Main.TFrame', padding=15)
        self.notebook.add(sync_frame, text="Sincronização")
        
        # Auto sync
        auto_frame = ttk.LabelFrame(sync_frame, text="Sincronização Automática",
                                   style='TLabelframe', padding=10)
        auto_frame.pack(fill='x', pady=(0, 15))
        
        # Intervalo
        interval_frame = ttk.Frame(auto_frame, style='Main.TFrame')
        interval_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(interval_frame, text="Intervalo (segundos):", style='TLabel').pack(side='left')
        self.vars['auto_sync_interval'] = tk.IntVar(
            value=self.config['sync']['auto_sync_interval'])
        interval_spin = ttk.Spinbox(interval_frame, from_=60, to=3600, width=10,
                                   textvariable=self.vars['auto_sync_interval'])
        interval_spin.pack(side='right')
        
        # Real-time sync
        self.vars['enable_real_time_sync'] = tk.BooleanVar(
            value=self.config['sync']['enable_real_time_sync'])
        realtime_check = ttk.Checkbutton(auto_frame, text="Sincronização em tempo real",
                                        variable=self.vars['enable_real_time_sync'],
                                        style='TCheckbutton')
        realtime_check.pack(anchor='w')
        
        # Resolução de conflitos
        conflict_frame = ttk.LabelFrame(sync_frame, text="Resolução de Conflitos",
                                       style='TLabelframe', padding=10)
        conflict_frame.pack(fill='x', pady=(0, 15))
        
        conflict_inner_frame = ttk.Frame(conflict_frame, style='Main.TFrame')
        conflict_inner_frame.pack(fill='x')
        
        ttk.Label(conflict_inner_frame, text="Estratégia:", style='TLabel').pack(side='left')
        self.vars['conflict_resolution'] = tk.StringVar(
            value=self.config['sync']['conflict_resolution'])
        conflict_combo = ttk.Combobox(conflict_inner_frame, 
                                     textvariable=self.vars['conflict_resolution'],
                                     values=['newer_wins', 'manual', 'backup_both'],
                                     state='readonly', width=15)
        conflict_combo.pack(side='right')
        
        # Backup e retry
        backup_frame = ttk.LabelFrame(sync_frame, text="Backup e Retry",
                                     style='TLabelframe', padding=10)
        backup_frame.pack(fill='x')
        
        self.vars['backup_before_sync'] = tk.BooleanVar(
            value=self.config['sync']['backup_before_sync'])
        backup_check = ttk.Checkbutton(backup_frame, text="Backup antes da sincronização",
                                      variable=self.vars['backup_before_sync'],
                                      style='TCheckbutton')
        backup_check.pack(anchor='w', pady=(0, 10))
        
        retry_frame = ttk.Frame(backup_frame, style='Main.TFrame')
        retry_frame.pack(fill='x')
        
        ttk.Label(retry_frame, text="Máximo de Tentativas:", style='TLabel').pack(side='left')
        self.vars['max_sync_retries'] = tk.IntVar(value=self.config['sync']['max_sync_retries'])
        retry_spin = ttk.Spinbox(retry_frame, from_=1, to=10, width=10,
                                textvariable=self.vars['max_sync_retries'])
        retry_spin.pack(side='right')
        
    def _create_developer_tab(self):
        """Cria aba de configurações de desenvolvedor."""
        dev_frame = ttk.Frame(self.notebook, style='Main.TFrame', padding=15)
        self.notebook.add(dev_frame, text="Desenvolvedor")
        
        # Debug e profiling
        debug_frame = ttk.LabelFrame(dev_frame, text="Debug e Profiling",
                                    style='TLabelframe', padding=10)
        debug_frame.pack(fill='x', pady=(0, 15))
        
        self.vars['enable_profiling'] = tk.BooleanVar(
            value=self.config['developer']['enable_profiling'])
        profiling_check = ttk.Checkbutton(debug_frame, text="Habilitar profiling",
                                         variable=self.vars['enable_profiling'],
                                         style='TCheckbutton')
        profiling_check.pack(anchor='w', pady=(0, 5))
        
        self.vars['show_debug_info'] = tk.BooleanVar(
            value=self.config['developer']['show_debug_info'])
        debug_info_check = ttk.Checkbutton(debug_frame, text="Mostrar informações de debug",
                                          variable=self.vars['show_debug_info'],
                                          style='TCheckbutton')
        debug_info_check.pack(anchor='w', pady=(0, 5))
        
        self.vars['enable_experimental_features'] = tk.BooleanVar(
            value=self.config['developer']['enable_experimental_features'])
        experimental_check = ttk.Checkbutton(debug_frame, text="Habilitar recursos experimentais",
                                            variable=self.vars['enable_experimental_features'],
                                            style='TCheckbutton')
        experimental_check.pack(anchor='w')
        
        # Scripts customizados
        scripts_frame = ttk.LabelFrame(dev_frame, text="Scripts Customizados",
                                      style='TLabelframe', padding=10)
        scripts_frame.pack(fill='x', pady=(0, 15))
        
        scripts_path_frame = ttk.Frame(scripts_frame, style='Main.TFrame')
        scripts_path_frame.pack(fill='x')
        
        ttk.Label(scripts_path_frame, text="Caminho:", style='TLabel').pack(side='left')
        self.vars['custom_scripts_path'] = tk.StringVar(
            value=self.config['developer']['custom_scripts_path'])
        scripts_entry = ttk.Entry(scripts_path_frame, textvariable=self.vars['custom_scripts_path'])
        scripts_entry.pack(side='left', fill='x', expand=True, padx=(10, 10))
        
        ttk.Button(scripts_path_frame, text="Procurar",
                  command=self._browse_scripts_path,
                  style='Secondary.TButton').pack(side='right')
        
        # API
        api_frame = ttk.LabelFrame(dev_frame, text="API",
                                  style='TLabelframe', padding=10)
        api_frame.pack(fill='x')
        
        timeout_frame = ttk.Frame(api_frame, style='Main.TFrame')
        timeout_frame.pack(fill='x')
        
        ttk.Label(timeout_frame, text="Timeout (segundos):", style='TLabel').pack(side='left')
        self.vars['api_timeout'] = tk.IntVar(value=self.config['developer']['api_timeout'])
        timeout_spin = ttk.Spinbox(timeout_frame, from_=5, to=300, width=10,
                                  textvariable=self.vars['api_timeout'])
        timeout_spin.pack(side='right')
        
    def _browse_scripts_path(self):
        """Abre diálogo para selecionar pasta de scripts."""
        folder = filedialog.askdirectory(
            title="Selecionar Pasta de Scripts",
            initialdir=self.vars['custom_scripts_path'].get()
        )
        
        if folder:
            self.vars['custom_scripts_path'].set(folder)
            
    def _restore_defaults(self):
        """Restaura configurações padrão."""
        if messagebox.askyesno("Confirmar", 
                              "Deseja restaurar todas as configurações para os valores padrão?"):
            default_config = self._get_default_config()
            self._load_config_to_vars(default_config)
            
    def _load_config_to_vars(self, config: Dict[str, Any]):
        """Carrega configuração nas variáveis.
        
        Args:
            config: Configuração a carregar.
        """
        # Performance
        self.vars['max_workers'].set(config['performance']['max_workers'])
        self.vars['chunk_size'].set(config['performance']['chunk_size'])
        self.vars['memory_limit_mb'].set(config['performance']['memory_limit_mb'])
        self.vars['enable_parallel_processing'].set(config['performance']['enable_parallel_processing'])
        self.vars['cache_size_mb'].set(config['performance']['cache_size_mb'])
        
        # Validation
        self.vars['strict_mode'].set(config['validation']['strict_mode'])
        self.vars['validate_formulas'].set(config['validation']['validate_formulas'])
        self.vars['check_data_types'].set(config['validation']['check_data_types'])
        self.vars['allow_empty_cells'].set(config['validation']['allow_empty_cells'])
        self.vars['max_errors_per_file'].set(config['validation']['max_errors_per_file'])
        
        # Logging
        self.vars['log_level'].set(config['logging']['level'])
        self.vars['enable_file_logging'].set(config['logging']['enable_file_logging'])
        self.vars['max_log_size_mb'].set(config['logging']['max_log_size_mb'])
        self.vars['backup_count'].set(config['logging']['backup_count'])
        self.vars['enable_debug_mode'].set(config['logging']['enable_debug_mode'])
        
        # Sync
        self.vars['auto_sync_interval'].set(config['sync']['auto_sync_interval'])
        self.vars['enable_real_time_sync'].set(config['sync']['enable_real_time_sync'])
        self.vars['conflict_resolution'].set(config['sync']['conflict_resolution'])
        self.vars['backup_before_sync'].set(config['sync']['backup_before_sync'])
        self.vars['max_sync_retries'].set(config['sync']['max_sync_retries'])
        
        # Developer
        self.vars['enable_profiling'].set(config['developer']['enable_profiling'])
        self.vars['show_debug_info'].set(config['developer']['show_debug_info'])
        self.vars['enable_experimental_features'].set(config['developer']['enable_experimental_features'])
        self.vars['custom_scripts_path'].set(config['developer']['custom_scripts_path'])
        self.vars['api_timeout'].set(config['developer']['api_timeout'])
        
    def _import_config(self):
        """Importa configuração de arquivo."""
        file_path = filedialog.askopenfilename(
            title="Importar Configuração",
            filetypes=[("Arquivos JSON", "*.json"), ("Todos os arquivos", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_config = json.load(f)
                    
                # Validar estrutura básica
                required_sections = ['performance', 'validation', 'logging', 'sync', 'developer']
                if all(section in imported_config for section in required_sections):
                    self._load_config_to_vars(imported_config)
                    messagebox.showinfo("Sucesso", "Configuração importada com sucesso!")
                else:
                    messagebox.showerror("Erro", "Arquivo de configuração inválido.")
                    
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao importar configuração: {e}")
                
    def _export_config(self):
        """Exporta configuração atual."""
        file_path = filedialog.asksaveasfilename(
            title="Exportar Configuração",
            defaultextension=".json",
            filetypes=[("Arquivos JSON", "*.json"), ("Todos os arquivos", "*.*")]
        )
        
        if file_path:
            try:
                current_config = self._get_config_from_vars()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(current_config, f, indent=2, ensure_ascii=False)
                    
                messagebox.showinfo("Sucesso", "Configuração exportada com sucesso!")
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar configuração: {e}")
                
    def _get_config_from_vars(self) -> Dict[str, Any]:
        """Obtém configuração das variáveis.
        
        Returns:
            Dicionário com configuração atual.
        """
        return {
            'performance': {
                'max_workers': self.vars['max_workers'].get(),
                'chunk_size': self.vars['chunk_size'].get(),
                'memory_limit_mb': self.vars['memory_limit_mb'].get(),
                'enable_parallel_processing': self.vars['enable_parallel_processing'].get(),
                'cache_size_mb': self.vars['cache_size_mb'].get()
            },
            'validation': {
                'strict_mode': self.vars['strict_mode'].get(),
                'validate_formulas': self.vars['validate_formulas'].get(),
                'check_data_types': self.vars['check_data_types'].get(),
                'allow_empty_cells': self.vars['allow_empty_cells'].get(),
                'max_errors_per_file': self.vars['max_errors_per_file'].get()
            },
            'logging': {
                'level': self.vars['log_level'].get(),
                'enable_file_logging': self.vars['enable_file_logging'].get(),
                'max_log_size_mb': self.vars['max_log_size_mb'].get(),
                'backup_count': self.vars['backup_count'].get(),
                'enable_debug_mode': self.vars['enable_debug_mode'].get()
            },
            'sync': {
                'auto_sync_interval': self.vars['auto_sync_interval'].get(),
                'enable_real_time_sync': self.vars['enable_real_time_sync'].get(),
                'conflict_resolution': self.vars['conflict_resolution'].get(),
                'backup_before_sync': self.vars['backup_before_sync'].get(),
                'max_sync_retries': self.vars['max_sync_retries'].get()
            },
            'developer': {
                'enable_profiling': self.vars['enable_profiling'].get(),
                'show_debug_info': self.vars['show_debug_info'].get(),
                'enable_experimental_features': self.vars['enable_experimental_features'].get(),
                'custom_scripts_path': self.vars['custom_scripts_path'].get(),
                'api_timeout': self.vars['api_timeout'].get()
            }
        }
        
    def _on_apply(self):
        """Aplica configurações."""
        try:
            self.result = self._get_config_from_vars()
            
            if self.on_save:
                self.on_save(self.result)
                
            self._close_dialog()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao aplicar configurações: {e}")
            
    def _on_cancel(self):
        """Cancela e fecha diálogo."""
        self.result = None
        self._close_dialog()
        
    def _close_dialog(self):
        """Fecha o diálogo."""
        if self.dialog:
            self.dialog.grab_release()
            self.dialog.destroy()
            self.dialog = None
            
    def show(self) -> Optional[Dict[str, Any]]:
        """Mostra o diálogo e retorna resultado.
        
        Returns:
            Configuração selecionada ou None se cancelado.
        """
        if self.dialog:
            self.dialog.wait_window()
            
        return self.result