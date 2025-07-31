"""Componente de monitoramento de progresso.

Este módulo implementa um componente para exibir o progresso de operações
com barra de progresso, indicadores de status e logs em tempo real.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
from datetime import datetime
from threading import Lock

from ...core import get_logger
from ..themes import theme_manager


class ProgressMonitor(ttk.Frame):
    """Componente para monitoramento de progresso de operações.
    
    Funcionalidades:
    - Barra de progresso animada
    - Indicadores de status coloridos
    - Log de operações em tempo real
    - Estatísticas de progresso
    - Controle de cancelamento
    """
    
    def __init__(self, parent, title: str = "Progresso", 
                 show_log: bool = True,
                 on_cancel: Callable[[], None] = None,
                 **kwargs):
        """Inicializa o monitor de progresso.
        
        Args:
            parent: Widget pai.
            title: Título do componente.
            show_log: Se deve mostrar área de log.
            on_cancel: Callback para cancelamento.
            **kwargs: Argumentos adicionais para ttk.Frame.
        """
        super().__init__(parent, **kwargs)
        
        self.logger = get_logger(__name__)
        self.title = title
        self.show_log = show_log
        self.on_cancel = on_cancel
        
        # Estado interno
        self._current_value = 0
        self._max_value = 100
        self._is_running = False
        self._is_indeterminate = False
        self._start_time = None
        self._lock = Lock()
        
        # Variáveis de interface
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Pronto")
        self.details_var = tk.StringVar(value="")
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Configura a interface do componente."""
        # Frame principal
        self.configure(style='Surface.TFrame', padding=10)
        
        # Título
        title_label = ttk.Label(self, text=self.title, style='Subheading.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))
        
        # Frame de status
        status_frame = ttk.Frame(self, style='Main.TFrame')
        status_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        # Indicador de status
        self.status_indicator = tk.Canvas(status_frame, width=12, height=12, 
                                         highlightthickness=0)
        self.status_indicator.grid(row=0, column=0, sticky='w', padx=(0, 8))
        self._update_status_indicator('ready')
        
        # Label de status
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                     style='TLabel')
        self.status_label.grid(row=0, column=1, sticky='w')
        
        # Frame de progresso
        progress_frame = ttk.Frame(self, style='Main.TFrame')
        progress_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        # Barra de progresso
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                           style='TProgressbar', length=300)
        self.progress_bar.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        
        # Label de porcentagem
        self.percentage_label = ttk.Label(progress_frame, text="0%", 
                                         style='TLabel', width=6)
        self.percentage_label.grid(row=0, column=1, sticky='e')
        
        # Detalhes da operação
        self.details_label = ttk.Label(self, textvariable=self.details_var, 
                                      style='Secondary.TLabel')
        self.details_label.grid(row=3, column=0, columnspan=2, sticky='w', pady=(0, 10))
        
        # Frame de estatísticas
        stats_frame = ttk.Frame(self, style='Main.TFrame')
        stats_frame.grid(row=4, column=0, columnspan=2, sticky='ew', pady=(0, 10))
        
        # Tempo decorrido
        self.elapsed_label = ttk.Label(stats_frame, text="Tempo: --:--", 
                                      style='Secondary.TLabel')
        self.elapsed_label.grid(row=0, column=0, sticky='w')
        
        # Tempo estimado
        self.eta_label = ttk.Label(stats_frame, text="Restante: --:--", 
                                  style='Secondary.TLabel')
        self.eta_label.grid(row=0, column=1, sticky='w', padx=(20, 0))
        
        # Botão de cancelar
        if self.on_cancel:
            self.cancel_button = ttk.Button(self, text="Cancelar", 
                                           command=self._on_cancel_clicked,
                                           style='Secondary.TButton',
                                           state='disabled')
            self.cancel_button.grid(row=5, column=1, sticky='e', pady=(10, 0))
            
        # Área de log (se habilitada)
        if self.show_log:
            self._setup_log_area()
            
        # Configurar grid
        self.columnconfigure(0, weight=1)
        
    def _setup_log_area(self):
        """Configura área de log."""
        # Separador
        separator = ttk.Separator(self, orient='horizontal')
        separator.grid(row=6, column=0, columnspan=2, sticky='ew', pady=10)
        
        # Label do log
        log_label = ttk.Label(self, text="Log de Operações:", style='Subheading.TLabel')
        log_label.grid(row=7, column=0, columnspan=2, sticky='w', pady=(0, 5))
        
        # Frame do log
        log_frame = ttk.Frame(self, style='Main.TFrame')
        log_frame.grid(row=8, column=0, columnspan=2, sticky='nsew', pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Text widget para log
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD,
                               bg='white', fg=theme_manager.get_color('text_primary'),
                               font=theme_manager.get_font('monospace'),
                               state='disabled')
        self.log_text.grid(row=0, column=0, sticky='nsew')
        
        # Scrollbar para log
        log_scrollbar = ttk.Scrollbar(log_frame, orient='vertical', 
                                     command=self.log_text.yview)
        log_scrollbar.grid(row=0, column=1, sticky='ns')
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        # Configurar tags de cores para log
        self.log_text.tag_configure('info', foreground=theme_manager.get_color('info'))
        self.log_text.tag_configure('success', foreground=theme_manager.get_color('success'))
        self.log_text.tag_configure('warning', foreground=theme_manager.get_color('warning'))
        self.log_text.tag_configure('error', foreground=theme_manager.get_color('error'))
        
        # Expandir área de log
        self.rowconfigure(8, weight=1)
        
    def start_operation(self, max_value: int = 100, indeterminate: bool = False):
        """Inicia uma nova operação.
        
        Args:
            max_value: Valor máximo do progresso.
            indeterminate: Se o progresso é indeterminado.
        """
        with self._lock:
            self._current_value = 0
            self._max_value = max_value
            self._is_running = True
            self._is_indeterminate = indeterminate
            self._start_time = datetime.now()
            
        # Atualizar interface
        self.progress_var.set(0)
        self.status_var.set("Executando...")
        self.details_var.set("")
        self._update_status_indicator('running')
        
        if indeterminate:
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start()
            self.percentage_label.config(text="...")
        else:
            self.progress_bar.config(mode='determinate', maximum=max_value)
            self.percentage_label.config(text="0%")
            
        # Habilitar botão de cancelar
        if hasattr(self, 'cancel_button'):
            self.cancel_button.config(state='normal')
            
        self.log_message("Operação iniciada", 'info')
        
    def update_progress(self, value: int, details: str = ""):
        """Atualiza o progresso da operação.
        
        Args:
            value: Valor atual do progresso.
            details: Detalhes da operação atual.
        """
        if not self._is_running or self._is_indeterminate:
            return
            
        with self._lock:
            self._current_value = min(value, self._max_value)
            
        # Atualizar interface
        self.progress_var.set(self._current_value)
        percentage = (self._current_value / self._max_value) * 100
        self.percentage_label.config(text=f"{percentage:.0f}%")
        
        if details:
            self.details_var.set(details)
            
        # Atualizar estatísticas
        self._update_statistics()
        
    def complete_operation(self, success: bool = True, message: str = ""):
        """Completa a operação.
        
        Args:
            success: Se a operação foi bem-sucedida.
            message: Mensagem de conclusão.
        """
        with self._lock:
            self._is_running = False
            
        # Parar progresso indeterminado
        if self._is_indeterminate:
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate')
            
        # Atualizar interface
        if success:
            self.progress_var.set(self._max_value)
            self.percentage_label.config(text="100%")
            self.status_var.set("Concluído")
            self._update_status_indicator('success')
            log_tag = 'success'
        else:
            self.status_var.set("Erro")
            self._update_status_indicator('error')
            log_tag = 'error'
            
        if message:
            self.details_var.set(message)
            
        # Desabilitar botão de cancelar
        if hasattr(self, 'cancel_button'):
            self.cancel_button.config(state='disabled')
            
        # Atualizar estatísticas finais
        self._update_statistics()
        
        # Log de conclusão
        status_msg = "Operação concluída com sucesso" if success else "Operação falhou"
        if message:
            status_msg += f": {message}"
        self.log_message(status_msg, log_tag)
        
    def cancel_operation(self):
        """Cancela a operação atual."""
        with self._lock:
            self._is_running = False
            
        # Parar progresso indeterminado
        if self._is_indeterminate:
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate')
            
        # Atualizar interface
        self.status_var.set("Cancelado")
        self.details_var.set("Operação cancelada pelo usuário")
        self._update_status_indicator('warning')
        
        # Desabilitar botão de cancelar
        if hasattr(self, 'cancel_button'):
            self.cancel_button.config(state='disabled')
            
        self.log_message("Operação cancelada", 'warning')
        
    def reset(self):
        """Reseta o monitor para estado inicial."""
        with self._lock:
            self._current_value = 0
            self._max_value = 100
            self._is_running = False
            self._is_indeterminate = False
            self._start_time = None
            
        # Resetar interface
        self.progress_var.set(0)
        self.status_var.set("Pronto")
        self.details_var.set("")
        self.percentage_label.config(text="0%")
        self.elapsed_label.config(text="Tempo: --:--")
        self.eta_label.config(text="Restante: --:--")
        self._update_status_indicator('ready')
        
        # Limpar log
        if self.show_log:
            self.log_text.config(state='normal')
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state='disabled')
            
    def log_message(self, message: str, level: str = 'info'):
        """Adiciona mensagem ao log.
        
        Args:
            message: Mensagem a ser adicionada.
            level: Nível da mensagem (info, success, warning, error).
        """
        if not self.show_log:
            return
            
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, formatted_message, level)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        
    def _update_status_indicator(self, status: str):
        """Atualiza indicador visual de status.
        
        Args:
            status: Status atual (ready, running, success, warning, error).
        """
        colors = {
            'ready': theme_manager.get_color('secondary'),
            'running': theme_manager.get_color('info'),
            'success': theme_manager.get_color('success'),
            'warning': theme_manager.get_color('warning'),
            'error': theme_manager.get_color('error')
        }
        
        color = colors.get(status, colors['ready'])
        
        self.status_indicator.delete('all')
        self.status_indicator.create_oval(2, 2, 10, 10, fill=color, outline=color)
        
    def _update_statistics(self):
        """Atualiza estatísticas de tempo."""
        if not self._start_time:
            return
            
        elapsed = datetime.now() - self._start_time
        elapsed_str = str(elapsed).split('.')[0]  # Remove microssegundos
        self.elapsed_label.config(text=f"Tempo: {elapsed_str}")
        
        # Calcular ETA apenas se não for indeterminado e houver progresso
        if not self._is_indeterminate and self._current_value > 0:
            progress_ratio = self._current_value / self._max_value
            if progress_ratio > 0:
                total_estimated = elapsed.total_seconds() / progress_ratio
                remaining = total_estimated - elapsed.total_seconds()
                
                if remaining > 0:
                    remaining_str = str(datetime.fromtimestamp(remaining).strftime('%H:%M:%S'))
                    self.eta_label.config(text=f"Restante: {remaining_str}")
                else:
                    self.eta_label.config(text="Restante: 00:00:00")
                    
    def _on_cancel_clicked(self):
        """Manipula clique no botão cancelar."""
        if self.on_cancel:
            self.on_cancel()
        self.cancel_operation()
        
    def is_running(self) -> bool:
        """Verifica se uma operação está em execução.
        
        Returns:
            True se uma operação está em execução.
        """
        return self._is_running
        
    def get_progress(self) -> tuple:
        """Obtém progresso atual.
        
        Returns:
            Tupla (valor_atual, valor_máximo).
        """
        return (self._current_value, self._max_value)