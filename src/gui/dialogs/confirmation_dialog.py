"""Diálogo de confirmação personalizado.

Este módulo implementa um diálogo de confirmação moderno e customizável
com diferentes tipos de ações e níveis de severidade.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any, Callable
from enum import Enum

from ...core import get_logger
from ..themes import theme_manager


class ConfirmationType(Enum):
    """Tipos de confirmação disponíveis."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    QUESTION = "question"
    DELETE = "delete"
    OVERWRITE = "overwrite"


class ConfirmationResult(Enum):
    """Resultados possíveis do diálogo."""
    YES = "yes"
    NO = "no"
    CANCEL = "cancel"
    OK = "ok"


class ConfirmationDialog:
    """Diálogo de confirmação personalizado.
    
    Funcionalidades:
    - Diferentes tipos de confirmação
    - Ícones e cores personalizadas
    - Botões configuráveis
    - Checkbox "Não perguntar novamente"
    - Detalhes expansíveis
    """
    
    def __init__(self, parent, title: str, message: str,
                 confirmation_type: ConfirmationType = ConfirmationType.QUESTION,
                 details: Optional[str] = None,
                 show_dont_ask: bool = False,
                 custom_buttons: Optional[Dict[str, str]] = None,
                 on_result: Optional[Callable[[ConfirmationResult, bool], None]] = None):
        """Inicializa o diálogo de confirmação.
        
        Args:
            parent: Widget pai.
            title: Título do diálogo.
            message: Mensagem principal.
            confirmation_type: Tipo de confirmação.
            details: Detalhes adicionais (expansíveis).
            show_dont_ask: Se deve mostrar checkbox "Não perguntar novamente".
            custom_buttons: Botões personalizados {resultado: texto}.
            on_result: Callback chamado com resultado e estado do "não perguntar".
        """
        self.parent = parent
        self.title = title
        self.message = message
        self.confirmation_type = confirmation_type
        self.details = details
        self.show_dont_ask = show_dont_ask
        self.custom_buttons = custom_buttons
        self.on_result = on_result
        
        self.logger = get_logger(__name__)
        
        # Estado do diálogo
        self.result = ConfirmationResult.CANCEL
        self.dont_ask_again = False
        self.details_visible = False
        
        # Variáveis de interface
        self.dont_ask_var = tk.BooleanVar()
        
        # Criar diálogo
        self.dialog = None
        self._create_dialog()
        
    def _create_dialog(self):
        """Cria o diálogo."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Configurar estilo
        self.dialog.configure(bg=theme_manager.get_color('surface'))
        
        # Centralizar na tela
        self._center_dialog()
        
        # Configurar conteúdo
        self._setup_content()
        
        # Configurar eventos
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
        self.dialog.bind('<Escape>', lambda e: self._on_close())
        
    def _center_dialog(self):
        """Centraliza o diálogo na tela."""
        self.dialog.update_idletasks()
        
        # Obter dimensões
        width = 400
        height = 200
        
        # Calcular posição central
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        
    def _setup_content(self):
        """Configura o conteúdo do diálogo."""
        main_frame = ttk.Frame(self.dialog, style='Surface.TFrame', padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Frame do cabeçalho
        header_frame = ttk.Frame(main_frame, style='Main.TFrame')
        header_frame.pack(fill='x', pady=(0, 15))
        
        # Ícone
        icon_label = self._create_icon(header_frame)
        icon_label.pack(side='left', padx=(0, 15))
        
        # Mensagem
        message_label = ttk.Label(header_frame, text=self.message, 
                                 style='TLabel', wraplength=300)
        message_label.pack(side='left', fill='x', expand=True)
        
        # Detalhes (se fornecidos)
        if self.details:
            self._create_details_section(main_frame)
            
        # Checkbox "Não perguntar novamente"
        if self.show_dont_ask:
            dont_ask_check = ttk.Checkbutton(main_frame, 
                                           text="Não perguntar novamente",
                                           variable=self.dont_ask_var,
                                           style='TCheckbutton')
            dont_ask_check.pack(anchor='w', pady=(10, 0))
            
        # Frame de botões
        button_frame = ttk.Frame(main_frame, style='Main.TFrame')
        button_frame.pack(fill='x', pady=(15, 0))
        
        self._create_buttons(button_frame)
        
    def _create_icon(self, parent) -> ttk.Label:
        """Cria ícone baseado no tipo de confirmação.
        
        Args:
            parent: Widget pai.
            
        Returns:
            Label com ícone.
        """
        # Mapear tipos para símbolos e cores
        icon_config = {
            ConfirmationType.INFO: ("ℹ", theme_manager.get_color('info')),
            ConfirmationType.WARNING: ("⚠", theme_manager.get_color('warning')),
            ConfirmationType.ERROR: ("✕", theme_manager.get_color('error')),
            ConfirmationType.QUESTION: ("?", theme_manager.get_color('primary')),
            ConfirmationType.DELETE: ("🗑", theme_manager.get_color('error')),
            ConfirmationType.OVERWRITE: ("⚠", theme_manager.get_color('warning'))
        }
        
        symbol, color = icon_config.get(self.confirmation_type, ("?", theme_manager.get_color('primary')))
        
        # Criar canvas para ícone
        canvas = tk.Canvas(parent, width=32, height=32, 
                          highlightthickness=0,
                          bg=theme_manager.get_color('surface'))
        
        # Desenhar círculo de fundo
        canvas.create_oval(2, 2, 30, 30, fill=color, outline=color)
        
        # Desenhar símbolo
        canvas.create_text(16, 16, text=symbol, fill='white', 
                          font=theme_manager.get_font('heading'))
        
        return canvas
        
    def _create_details_section(self, parent):
        """Cria seção de detalhes expansível.
        
        Args:
            parent: Widget pai.
        """
        # Botão para expandir/recolher detalhes
        self.details_button = ttk.Button(parent, text="▶ Mostrar detalhes",
                                        command=self._toggle_details,
                                        style='Link.TButton')
        self.details_button.pack(anchor='w', pady=(10, 0))
        
        # Frame de detalhes (inicialmente oculto)
        self.details_frame = ttk.Frame(parent, style='Secondary.TFrame', padding=10)
        
        # Text widget para detalhes
        self.details_text = tk.Text(self.details_frame, height=6, wrap=tk.WORD,
                                   bg=theme_manager.get_color('background'),
                                   fg=theme_manager.get_color('text_secondary'),
                                   font=theme_manager.get_font('monospace'),
                                   state='disabled')
        self.details_text.pack(fill='both', expand=True)
        
        # Inserir texto dos detalhes
        self.details_text.config(state='normal')
        self.details_text.insert('1.0', self.details)
        self.details_text.config(state='disabled')
        
    def _toggle_details(self):
        """Alterna visibilidade dos detalhes."""
        if self.details_visible:
            # Ocultar detalhes
            self.details_frame.pack_forget()
            self.details_button.config(text="▶ Mostrar detalhes")
            self.details_visible = False
            
            # Redimensionar janela
            self.dialog.geometry("400x200")
        else:
            # Mostrar detalhes
            self.details_frame.pack(fill='both', expand=True, pady=(5, 0))
            self.details_button.config(text="▼ Ocultar detalhes")
            self.details_visible = True
            
            # Redimensionar janela
            self.dialog.geometry("400x350")
            
        # Recentrar diálogo
        self._center_dialog()
        
    def _create_buttons(self, parent):
        """Cria botões do diálogo.
        
        Args:
            parent: Widget pai.
        """
        # Usar botões personalizados se fornecidos
        if self.custom_buttons:
            buttons = self.custom_buttons
        else:
            # Botões padrão baseados no tipo
            buttons = self._get_default_buttons()
            
        # Criar botões da direita para esquerda
        button_configs = list(buttons.items())
        button_configs.reverse()
        
        for i, (result_key, button_text) in enumerate(button_configs):
            result = ConfirmationResult(result_key)
            
            # Determinar estilo do botão
            if result in [ConfirmationResult.YES, ConfirmationResult.OK]:
                style = 'Primary.TButton'
            elif result == ConfirmationResult.NO:
                style = 'Secondary.TButton'
            else:
                style = 'Secondary.TButton'
                
            button = ttk.Button(parent, text=button_text,
                               command=lambda r=result: self._on_button_click(r),
                               style=style)
            button.pack(side='right', padx=(10, 0) if i > 0 else (0, 0))
            
            # Definir botão padrão
            if result in [ConfirmationResult.YES, ConfirmationResult.OK]:
                button.focus_set()
                self.dialog.bind('<Return>', lambda e, r=result: self._on_button_click(r))
                
    def _get_default_buttons(self) -> Dict[str, str]:
        """Obtém botões padrão baseados no tipo.
        
        Returns:
            Dicionário com botões padrão.
        """
        if self.confirmation_type in [ConfirmationType.DELETE, ConfirmationType.OVERWRITE]:
            return {
                ConfirmationResult.YES.value: "Sim",
                ConfirmationResult.NO.value: "Não",
                ConfirmationResult.CANCEL.value: "Cancelar"
            }
        elif self.confirmation_type == ConfirmationType.ERROR:
            return {
                ConfirmationResult.OK.value: "OK"
            }
        else:
            return {
                ConfirmationResult.YES.value: "Sim",
                ConfirmationResult.NO.value: "Não"
            }
            
    def _on_button_click(self, result: ConfirmationResult):
        """Manipula clique em botão.
        
        Args:
            result: Resultado selecionado.
        """
        self.result = result
        self.dont_ask_again = self.dont_ask_var.get()
        
        # Chamar callback se fornecido
        if self.on_result:
            self.on_result(self.result, self.dont_ask_again)
            
        self._close_dialog()
        
    def _on_close(self):
        """Manipula fechamento do diálogo."""
        self.result = ConfirmationResult.CANCEL
        self.dont_ask_again = False
        
        if self.on_result:
            self.on_result(self.result, self.dont_ask_again)
            
        self._close_dialog()
        
    def _close_dialog(self):
        """Fecha o diálogo."""
        if self.dialog:
            self.dialog.grab_release()
            self.dialog.destroy()
            self.dialog = None
            
    def show(self) -> tuple:
        """Mostra o diálogo e aguarda resultado.
        
        Returns:
            Tupla (resultado, não_perguntar_novamente).
        """
        if self.dialog:
            self.dialog.wait_window()
            
        return (self.result, self.dont_ask_again)
        
    @staticmethod
    def show_info(parent, title: str, message: str, details: Optional[str] = None) -> ConfirmationResult:
        """Mostra diálogo de informação.
        
        Args:
            parent: Widget pai.
            title: Título do diálogo.
            message: Mensagem.
            details: Detalhes opcionais.
            
        Returns:
            Resultado do diálogo.
        """
        dialog = ConfirmationDialog(parent, title, message, 
                                   ConfirmationType.INFO, details)
        result, _ = dialog.show()
        return result
        
    @staticmethod
    def show_warning(parent, title: str, message: str, details: Optional[str] = None) -> ConfirmationResult:
        """Mostra diálogo de aviso.
        
        Args:
            parent: Widget pai.
            title: Título do diálogo.
            message: Mensagem.
            details: Detalhes opcionais.
            
        Returns:
            Resultado do diálogo.
        """
        dialog = ConfirmationDialog(parent, title, message, 
                                   ConfirmationType.WARNING, details)
        result, _ = dialog.show()
        return result
        
    @staticmethod
    def show_error(parent, title: str, message: str, details: Optional[str] = None) -> ConfirmationResult:
        """Mostra diálogo de erro.
        
        Args:
            parent: Widget pai.
            title: Título do diálogo.
            message: Mensagem.
            details: Detalhes opcionais.
            
        Returns:
            Resultado do diálogo.
        """
        dialog = ConfirmationDialog(parent, title, message, 
                                   ConfirmationType.ERROR, details)
        result, _ = dialog.show()
        return result
        
    @staticmethod
    def ask_yes_no(parent, title: str, message: str, 
                   show_dont_ask: bool = False) -> tuple:
        """Pergunta sim/não.
        
        Args:
            parent: Widget pai.
            title: Título do diálogo.
            message: Mensagem.
            show_dont_ask: Se deve mostrar "não perguntar novamente".
            
        Returns:
            Tupla (resultado, não_perguntar_novamente).
        """
        dialog = ConfirmationDialog(parent, title, message, 
                                   ConfirmationType.QUESTION,
                                   show_dont_ask=show_dont_ask)
        return dialog.show()
        
    @staticmethod
    def confirm_delete(parent, item_name: str, details: Optional[str] = None) -> tuple:
        """Confirma exclusão de item.
        
        Args:
            parent: Widget pai.
            item_name: Nome do item a ser excluído.
            details: Detalhes adicionais.
            
        Returns:
            Tupla (resultado, não_perguntar_novamente).
        """
        title = "Confirmar Exclusão"
        message = f"Tem certeza que deseja excluir '{item_name}'?\n\nEsta ação não pode ser desfeita."
        
        dialog = ConfirmationDialog(parent, title, message, 
                                   ConfirmationType.DELETE, details,
                                   show_dont_ask=True)
        return dialog.show()
        
    @staticmethod
    def confirm_overwrite(parent, file_name: str) -> tuple:
        """Confirma sobrescrita de arquivo.
        
        Args:
            parent: Widget pai.
            file_name: Nome do arquivo.
            
        Returns:
            Tupla (resultado, não_perguntar_novamente).
        """
        title = "Confirmar Sobrescrita"
        message = f"O arquivo '{file_name}' já existe.\n\nDeseja sobrescrever?"
        
        dialog = ConfirmationDialog(parent, title, message, 
                                   ConfirmationType.OVERWRITE,
                                   show_dont_ask=True)
        return dialog.show()