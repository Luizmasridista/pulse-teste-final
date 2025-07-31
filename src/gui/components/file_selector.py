"""Componente de seleção de arquivos e pastas.

Este módulo implementa um componente para seleção de pastas e arquivos
com suporte a drag-and-drop e validação.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Callable, Optional, List
import tkinterdnd2 as tkdnd

from ...core import get_logger
from ..themes import theme_manager


class FileSelector(ttk.Frame):
    """Componente para seleção de arquivos e pastas com drag-and-drop.
    
    Funcionalidades:
    - Seleção de pasta via diálogo
    - Drag-and-drop de pastas
    - Validação de caminhos
    - Callback para mudanças
    """
    
    def __init__(self, parent, title: str = "Selecionar Pasta", 
                 file_types: List[str] = None, 
                 on_selection_changed: Callable[[str], None] = None,
                 **kwargs):
        """Inicializa o seletor de arquivos.
        
        Args:
            parent: Widget pai.
            title: Título do componente.
            file_types: Tipos de arquivo aceitos (ex: ['.xlsx', '.xls']).
            on_selection_changed: Callback chamado quando seleção muda.
            **kwargs: Argumentos adicionais para ttk.Frame.
        """
        super().__init__(parent, **kwargs)
        
        self.logger = get_logger(__name__)
        self.title = title
        self.file_types = file_types or ['.xlsx', '.xls']
        self.on_selection_changed = on_selection_changed
        self._selected_path = ""
        
        self._setup_ui()
        self._setup_drag_drop()
        
    def _setup_ui(self):
        """Configura a interface do componente."""
        # Frame principal
        self.configure(style='Surface.TFrame', padding=10)
        
        # Título
        title_label = ttk.Label(self, text=self.title, style='Subheading.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 10))
        
        # Frame de seleção
        selection_frame = ttk.Frame(self, style='Main.TFrame')
        selection_frame.grid(row=1, column=0, columnspan=3, sticky='ew', pady=(0, 10))
        selection_frame.columnconfigure(1, weight=1)
        
        # Label do caminho
        path_label = ttk.Label(selection_frame, text="Caminho:", style='TLabel')
        path_label.grid(row=0, column=0, sticky='w', padx=(0, 10))
        
        # Entry do caminho
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(selection_frame, textvariable=self.path_var, 
                                   state='readonly', style='TEntry')
        self.path_entry.grid(row=0, column=1, sticky='ew', padx=(0, 10))
        
        # Botão de seleção
        self.browse_button = ttk.Button(selection_frame, text="Procurar...", 
                                       command=self._browse_folder, style='TButton')
        self.browse_button.grid(row=0, column=2, sticky='e')
        
        # Área de drag-and-drop
        self.drop_frame = tk.Frame(self, bg=theme_manager.get_color('surface'),
                                  relief='dashed', bd=2, height=80)
        self.drop_frame.grid(row=2, column=0, columnspan=3, sticky='ew', pady=(0, 10))
        self.drop_frame.grid_propagate(False)
        
        # Label da área de drop
        self.drop_label = tk.Label(self.drop_frame, 
                                  text="Arraste uma pasta aqui ou use o botão Procurar",
                                  bg=theme_manager.get_color('surface'),
                                  fg=theme_manager.get_color('text_secondary'),
                                  font=theme_manager.get_font('default'))
        self.drop_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Frame de informações
        self.info_frame = ttk.Frame(self, style='Main.TFrame')
        self.info_frame.grid(row=3, column=0, columnspan=3, sticky='ew')
        self.info_frame.columnconfigure(1, weight=1)
        
        # Status
        self.status_label = ttk.Label(self.info_frame, text="Nenhuma pasta selecionada", 
                                     style='Secondary.TLabel')
        self.status_label.grid(row=0, column=0, sticky='w')
        
        # Configurar grid
        self.columnconfigure(0, weight=1)
        
    def _setup_drag_drop(self):
        """Configura funcionalidade de drag-and-drop."""
        try:
            # Registrar área de drop
            self.drop_frame.drop_target_register(tkdnd.DND_FILES)
            self.drop_frame.dnd_bind('<<Drop>>', self._on_drop)
            self.drop_frame.dnd_bind('<<DragEnter>>', self._on_drag_enter)
            self.drop_frame.dnd_bind('<<DragLeave>>', self._on_drag_leave)
            
        except Exception as e:
            self.logger.warning(f"Drag-and-drop não disponível: {e}")
            # Atualizar label se drag-and-drop não estiver disponível
            self.drop_label.config(text="Use o botão Procurar para selecionar uma pasta")
            
    def _browse_folder(self):
        """Abre diálogo para seleção de pasta."""
        folder_path = filedialog.askdirectory(
            title=f"Selecionar {self.title}",
            initialdir=self._selected_path or Path.home()
        )
        
        if folder_path:
            self._set_selected_path(folder_path)
            
    def _on_drop(self, event):
        """Manipula evento de drop."""
        try:
            # Obter arquivos/pastas dropados
            files = self.drop_frame.tk.splitlist(event.data)
            
            if files:
                dropped_path = files[0]  # Usar primeiro item
                path = Path(dropped_path)
                
                # Verificar se é uma pasta
                if path.is_dir():
                    self._set_selected_path(str(path))
                else:
                    # Se for arquivo, usar pasta pai
                    self._set_selected_path(str(path.parent))
                    
        except Exception as e:
            self.logger.error(f"Erro no drag-and-drop: {e}")
            messagebox.showerror("Erro", f"Erro ao processar arquivo: {e}")
            
        finally:
            self._reset_drop_area()
            
    def _on_drag_enter(self, event):
        """Manipula entrada de drag."""
        self.drop_frame.config(bg=theme_manager.get_color('accent'), relief='solid')
        self.drop_label.config(bg=theme_manager.get_color('accent'),
                              text="Solte aqui para selecionar")
        
    def _on_drag_leave(self, event):
        """Manipula saída de drag."""
        self._reset_drop_area()
        
    def _reset_drop_area(self):
        """Reseta aparência da área de drop."""
        self.drop_frame.config(bg=theme_manager.get_color('surface'), relief='dashed')
        self.drop_label.config(bg=theme_manager.get_color('surface'),
                              text="Arraste uma pasta aqui ou use o botão Procurar")
        
    def _set_selected_path(self, path: str):
        """Define o caminho selecionado.
        
        Args:
            path: Caminho selecionado.
        """
        try:
            path_obj = Path(path)
            
            # Validar se existe
            if not path_obj.exists():
                messagebox.showerror("Erro", "O caminho selecionado não existe.")
                return
                
            # Validar se é pasta
            if not path_obj.is_dir():
                messagebox.showerror("Erro", "Por favor, selecione uma pasta.")
                return
                
            # Atualizar interface
            self._selected_path = str(path_obj)
            self.path_var.set(self._selected_path)
            
            # Atualizar status
            file_count = self._count_files_in_folder(path_obj)
            self.status_label.config(text=f"Pasta selecionada - {file_count} arquivos encontrados")
            
            # Chamar callback
            if self.on_selection_changed:
                self.on_selection_changed(self._selected_path)
                
            self.logger.info(f"Pasta selecionada: {self._selected_path}")
            
        except Exception as e:
            self.logger.error(f"Erro ao definir caminho: {e}")
            messagebox.showerror("Erro", f"Erro ao processar caminho: {e}")
            
    def _count_files_in_folder(self, folder_path: Path) -> int:
        """Conta arquivos suportados na pasta.
        
        Args:
            folder_path: Caminho da pasta.
            
        Returns:
            Número de arquivos suportados.
        """
        try:
            count = 0
            for file_path in folder_path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in self.file_types:
                    count += 1
            return count
        except Exception:
            return 0
            
    def get_selected_path(self) -> str:
        """Obtém o caminho selecionado.
        
        Returns:
            Caminho selecionado ou string vazia.
        """
        return self._selected_path
        
    def set_path(self, path: str):
        """Define o caminho programaticamente.
        
        Args:
            path: Caminho a ser definido.
        """
        if path and Path(path).exists():
            self._set_selected_path(path)
            
    def clear_selection(self):
        """Limpa a seleção atual."""
        self._selected_path = ""
        self.path_var.set("")
        self.status_label.config(text="Nenhuma pasta selecionada")
        
    def is_valid_selection(self) -> bool:
        """Verifica se há uma seleção válida.
        
        Returns:
            True se há uma seleção válida.
        """
        return bool(self._selected_path and Path(self._selected_path).exists())
        
    def enable(self):
        """Habilita o componente."""
        self.browse_button.config(state='normal')
        
    def disable(self):
        """Desabilita o componente."""
        self.browse_button.config(state='disabled')