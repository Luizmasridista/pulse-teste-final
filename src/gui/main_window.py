"""Janela principal da interface gráfica.

Este módulo implementa a janela principal da aplicação desktop
com Tkinter, integrando todos os componentes e funcionalidades.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import threading
import asyncio

from ..core import get_logger, ConfigManager
from ..spreadsheet import (
    SpreadsheetScanner, SpreadsheetValidator, SpreadsheetAnalyzer,
    SpreadsheetInfo, ValidationStatus
)
from .themes import theme_manager, ModernTheme, DarkTheme
from .components import FileSelector, ProgressMonitor, SettingsPanel
from .dialogs import ConfirmationDialog, ReportDialog, AdvancedConfigDialog, ReportData


class MainWindow:
    """Janela principal da aplicação.
    
    Funcionalidades:
    - Interface moderna com temas
    - Seleção de pastas e arquivos
    - Monitoramento de progresso
    - Configurações e preferências
    - Relatórios detalhados
    - Integração com funcionalidades do core
    """
    
    def __init__(self):
        """Inicializa a janela principal."""
        self.logger = get_logger(__name__)
        self.config_manager = ConfigManager()
        
        # Estado da aplicação
        self.current_operation = None
        self.operation_cancelled = False
        self.subordinadas_path = ""
        self.master_file_path = ""
        
        # Componentes
        self.scanner = SpreadsheetScanner()
        self.validator = SpreadsheetValidator()
        self.analyzer = SpreadsheetAnalyzer()
        
        # Interface
        self.root = None
        self.file_selector = None
        self.progress_monitor = None
        self.settings_panel = None
        
        # Dados
        self.discovered_files: List[SpreadsheetInfo] = []
        self.validation_results = {}
        self.analysis_results = {}
        
        self._create_main_window()
        
    def _create_main_window(self):
        """Cria a janela principal."""
        self.root = tk.Tk()
        self.root.title("Pulse - Consolidador de Planilhas")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Configurar ícone (se disponível)
        try:
            # self.root.iconbitmap('assets/icon.ico')
            pass
        except:
            pass
            
        # Aplicar tema inicial
        theme_manager.set_theme(ModernTheme())
        theme_manager.apply_theme(self.root)
        
        # Configurar estilo
        self.root.configure(bg=theme_manager.get_color('background'))
        
        # Configurar layout
        self._setup_layout()
        
        # Configurar menu
        self._setup_menu()
        
        # Configurar eventos
        self._setup_events()
        
        # Centralizar janela
        self._center_window()
        
    def _setup_layout(self):
        """Configura o layout da janela."""
        # Frame principal
        main_frame = ttk.Frame(self.root, style='Main.TFrame', padding=10)
        main_frame.pack(fill='both', expand=True)
        
        # Cabeçalho
        self._create_header(main_frame)
        
        # Área de conteúdo
        content_frame = ttk.Frame(main_frame, style='Surface.TFrame')
        content_frame.pack(fill='both', expand=True, pady=(10, 0))
        
        # Configurar grid
        content_frame.columnconfigure(0, weight=2)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # Painel esquerdo - Seleção e progresso
        left_panel = ttk.Frame(content_frame, style='Main.TFrame', padding=10)
        left_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        
        # Painel direito - Configurações
        right_panel = ttk.Frame(content_frame, style='Secondary.TFrame', padding=10)
        right_panel.grid(row=0, column=1, sticky='nsew', padx=(5, 0))
        
        # Configurar painéis
        self._setup_left_panel(left_panel)
        self._setup_right_panel(right_panel)
        
        # Barra de status
        self._create_status_bar(main_frame)
        
    def _create_header(self, parent):
        """Cria cabeçalho da aplicação.
        
        Args:
            parent: Widget pai.
        """
        header_frame = ttk.Frame(parent, style='Surface.TFrame', padding=15)
        header_frame.pack(fill='x')
        
        # Título
        title_label = ttk.Label(header_frame, text="Pulse - Consolidador de Planilhas",
                               style='Title.TLabel')
        title_label.pack(side='left')
        
        # Botões de ação
        action_frame = ttk.Frame(header_frame, style='Main.TFrame')
        action_frame.pack(side='right')
        
        ttk.Button(action_frame, text="Descobrir",
                  command=self._start_discovery,
                  style='Primary.TButton').pack(side='left', padx=(0, 10))
                  
        ttk.Button(action_frame, text="Validar",
                  command=self._start_validation,
                  style='Secondary.TButton').pack(side='left', padx=(0, 10))
                  
        ttk.Button(action_frame, text="Analisar",
                  command=self._start_analysis,
                  style='Secondary.TButton').pack(side='left', padx=(0, 10))
                  
        ttk.Button(action_frame, text="Consolidar",
                  command=self._start_consolidation,
                  style='Success.TButton').pack(side='left')
        
    def _setup_left_panel(self, parent):
        """Configura painel esquerdo.
        
        Args:
            parent: Widget pai.
        """
        # Seletor de arquivos
        selector_frame = ttk.LabelFrame(parent, text="Seleção de Arquivos",
                                       style='TLabelframe', padding=10)
        selector_frame.pack(fill='x', pady=(0, 10))
        
        self.file_selector = FileSelector(
            selector_frame,
            on_selection_changed=self._on_file_selection_changed
        )
        
        # Monitor de progresso
        progress_frame = ttk.LabelFrame(parent, text="Progresso",
                                       style='TLabelframe', padding=10)
        progress_frame.pack(fill='both', expand=True)
        
        self.progress_monitor = ProgressMonitor(
            progress_frame,
            on_cancel=self._cancel_operation
        )
        
    def _setup_right_panel(self, parent):
        """Configura painel direito.
        
        Args:
            parent: Widget pai.
        """
        # Painel de configurações
        self.settings_panel = SettingsPanel(parent)
        
    def _setup_menu(self):
        """Configura menu da aplicação."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menu Arquivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Novo Projeto", command=self._new_project)
        file_menu.add_command(label="Abrir Projeto", command=self._open_project)
        file_menu.add_command(label="Salvar Projeto", command=self._save_project)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self._quit_application)
        
        # Menu Ferramentas
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ferramentas", menu=tools_menu)
        tools_menu.add_command(label="Descobrir Planilhas", command=self._start_discovery)
        tools_menu.add_command(label="Validar Planilhas", command=self._start_validation)
        tools_menu.add_command(label="Analisar Estrutura", command=self._start_analysis)
        tools_menu.add_separator()
        tools_menu.add_command(label="Configurações Avançadas", command=self._show_advanced_config)
        
        # Menu Visualizar
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Visualizar", menu=view_menu)
        view_menu.add_command(label="Tema Moderno", command=lambda: self._change_theme('modern'))
        view_menu.add_command(label="Tema Escuro", command=lambda: self._change_theme('dark'))
        view_menu.add_separator()
        view_menu.add_command(label="Relatório de Descoberta", command=self._show_discovery_report)
        view_menu.add_command(label="Relatório de Validação", command=self._show_validation_report)
        
        # Menu Ajuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        help_menu.add_command(label="Sobre", command=self._show_about)
        help_menu.add_command(label="Documentação", command=self._show_documentation)
        
    def _create_status_bar(self, parent):
        """Cria barra de status.
        
        Args:
            parent: Widget pai.
        """
        self.status_bar = ttk.Frame(parent, style='Secondary.TFrame', padding=5)
        self.status_bar.pack(fill='x', pady=(10, 0))
        
        # Status text
        self.status_var = tk.StringVar(value="Pronto")
        status_label = ttk.Label(self.status_bar, textvariable=self.status_var,
                                style='Secondary.TLabel')
        status_label.pack(side='left')
        
        # Informações adicionais
        info_frame = ttk.Frame(self.status_bar, style='Main.TFrame')
        info_frame.pack(side='right')
        
        self.files_count_var = tk.StringVar(value="Arquivos: 0")
        files_label = ttk.Label(info_frame, textvariable=self.files_count_var,
                               style='Secondary.TLabel')
        files_label.pack(side='right', padx=(10, 0))
        
    def _setup_events(self):
        """Configura eventos da janela."""
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.bind('<Control-n>', lambda e: self._new_project())
        self.root.bind('<Control-o>', lambda e: self._open_project())
        self.root.bind('<Control-s>', lambda e: self._save_project())
        self.root.bind('<F5>', lambda e: self._start_discovery())
        
    def _center_window(self):
        """Centraliza a janela na tela."""
        self.root.update_idletasks()
        
        # Obter dimensões
        width = 1200
        height = 800
        
        # Calcular posição central
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def _on_file_selection_changed(self, subordinadas_path: str, master_file: str):
        """Manipula mudança na seleção de arquivos.
        
        Args:
            subordinadas_path: Caminho da pasta SUBORDINADAS.
            master_file: Caminho do arquivo mestre.
        """
        self.subordinadas_path = subordinadas_path
        self.master_file_path = master_file
        
        self.logger.info(f"Seleção alterada - Subordinadas: {subordinadas_path}, Mestre: {master_file}")
        self._update_status("Arquivos selecionados")
        
    def _cancel_operation(self):
        """Cancela operação atual."""
        self.operation_cancelled = True
        self._update_status("Operação cancelada")
        self.logger.info("Operação cancelada pelo usuário")
        
    def _start_discovery(self):
        """Inicia descoberta de planilhas."""
        if not self.subordinadas_path:
            messagebox.showwarning("Aviso", "Selecione a pasta SUBORDINADAS primeiro.")
            return
            
        if self.current_operation:
            messagebox.showwarning("Aviso", "Uma operação já está em andamento.")
            return
            
        # Confirmar operação
        if not ConfirmationDialog(
            self.root,
            "Descobrir Planilhas",
            f"Deseja escanear a pasta:\n{self.subordinadas_path}?",
            "question"
        ).show():
            return
            
        self.current_operation = "discovery"
        self.operation_cancelled = False
        
        # Executar em thread separada
        thread = threading.Thread(target=self._run_discovery, daemon=True)
        thread.start()
        
    def _run_discovery(self):
        """Executa descoberta de planilhas."""
        try:
            self._update_status("Descobrindo planilhas...")
            self.progress_monitor.start_operation("Descoberta de Planilhas")
            
            # Escanear pasta
            self.discovered_files = self.scanner.scan_folder(self.subordinadas_path)
            
            if self.operation_cancelled:
                return
                
            # Atualizar interface
            self.root.after(0, self._on_discovery_completed)
            
        except Exception as e:
            self.logger.error(f"Erro na descoberta: {e}")
            self.root.after(0, lambda: self._on_operation_error("descoberta", str(e)))
            
        finally:
            self.current_operation = None
            
    def _on_discovery_completed(self):
        """Manipula conclusão da descoberta."""
        count = len(self.discovered_files)
        self.files_count_var.set(f"Arquivos: {count}")
        self._update_status(f"Descoberta concluída - {count} arquivos encontrados")
        
        self.progress_monitor.complete_operation(f"Descobertos {count} arquivos")
        
        # Mostrar relatório
        if count > 0:
            self._show_discovery_report()
        else:
            messagebox.showinfo("Resultado", "Nenhuma planilha encontrada na pasta selecionada.")
            
    def _start_validation(self):
        """Inicia validação de planilhas."""
        if not self.discovered_files:
            messagebox.showwarning("Aviso", "Execute a descoberta primeiro.")
            return
            
        if self.current_operation:
            messagebox.showwarning("Aviso", "Uma operação já está em andamento.")
            return
            
        self.current_operation = "validation"
        self.operation_cancelled = False
        
        # Executar em thread separada
        thread = threading.Thread(target=self._run_validation, daemon=True)
        thread.start()
        
    def _run_validation(self):
        """Executa validação de planilhas."""
        try:
            self._update_status("Validando planilhas...")
            self.progress_monitor.start_operation("Validação de Planilhas")
            
            # Validar arquivos
            file_paths = [file_info.file_path for file_info in self.discovered_files]
            self.validation_results = self.validator.validate_multiple_files(file_paths)
            
            if self.operation_cancelled:
                return
                
            # Atualizar interface
            self.root.after(0, self._on_validation_completed)
            
        except Exception as e:
            self.logger.error(f"Erro na validação: {e}")
            self.root.after(0, lambda: self._on_operation_error("validação", str(e)))
            
        finally:
            self.current_operation = None
            
    def _on_validation_completed(self):
        """Manipula conclusão da validação."""
        valid_count = sum(1 for result in self.validation_results.values() 
                         if result.status == ValidationStatus.VALID)
        total_count = len(self.validation_results)
        
        self._update_status(f"Validação concluída - {valid_count}/{total_count} válidos")
        self.progress_monitor.complete_operation(f"Validados {total_count} arquivos")
        
        # Mostrar relatório
        self._show_validation_report()
        
    def _start_analysis(self):
        """Inicia análise de planilhas."""
        if not self.validation_results:
            messagebox.showwarning("Aviso", "Execute a validação primeiro.")
            return
            
        if self.current_operation:
            messagebox.showwarning("Aviso", "Uma operação já está em andamento.")
            return
            
        self.current_operation = "analysis"
        self.operation_cancelled = False
        
        # Executar em thread separada
        thread = threading.Thread(target=self._run_analysis, daemon=True)
        thread.start()
        
    def _run_analysis(self):
        """Executa análise de planilhas."""
        try:
            self._update_status("Analisando planilhas...")
            self.progress_monitor.start_operation("Análise de Planilhas")
            
            # Analisar apenas arquivos válidos
            valid_files = [file_path for file_path, result in self.validation_results.items()
                          if result.status == ValidationStatus.VALID]
            
            self.analysis_results = {}
            for file_path in valid_files:
                if self.operation_cancelled:
                    return
                    
                analysis = self.analyzer.analyze_file(file_path)
                self.analysis_results[file_path] = analysis
                
            # Atualizar interface
            self.root.after(0, self._on_analysis_completed)
            
        except Exception as e:
            self.logger.error(f"Erro na análise: {e}")
            self.root.after(0, lambda: self._on_operation_error("análise", str(e)))
            
        finally:
            self.current_operation = None
            
    def _on_analysis_completed(self):
        """Manipula conclusão da análise."""
        count = len(self.analysis_results)
        self._update_status(f"Análise concluída - {count} arquivos analisados")
        self.progress_monitor.complete_operation(f"Analisados {count} arquivos")
        
        messagebox.showinfo("Sucesso", f"Análise concluída para {count} arquivos.")
        
    def _start_consolidation(self):
        """Inicia consolidação de planilhas."""
        if not self.analysis_results:
            messagebox.showwarning("Aviso", "Execute a análise primeiro.")
            return
            
        if not self.master_file_path:
            messagebox.showwarning("Aviso", "Selecione o arquivo mestre primeiro.")
            return
            
        # Confirmar consolidação
        if not ConfirmationDialog(
            self.root,
            "Consolidar Planilhas",
            f"Deseja consolidar {len(self.analysis_results)} planilhas no arquivo mestre?\n\n"
            f"Arquivo mestre: {Path(self.master_file_path).name}",
            "question"
        ).show():
            return
            
        messagebox.showinfo("Em Desenvolvimento", 
                           "A funcionalidade de consolidação será implementada na próxima sprint.")
        
    def _on_operation_error(self, operation: str, error: str):
        """Manipula erro em operação.
        
        Args:
            operation: Nome da operação.
            error: Mensagem de erro.
        """
        self._update_status(f"Erro na {operation}")
        self.progress_monitor.complete_operation(f"Erro na {operation}", success=False)
        messagebox.showerror("Erro", f"Erro na {operation}:\n{error}")
        
    def _show_discovery_report(self):
        """Mostra relatório de descoberta."""
        if not self.discovered_files:
            messagebox.showinfo("Relatório", "Nenhuma descoberta realizada ainda.")
            return
            
        # Criar dados do relatório
        report_data = ReportData(
            title="Relatório de Descoberta",
            operation="discovery",
            start_time=datetime.now(),
            end_time=datetime.now(),
            success=True
        )
        
        # Adicionar estatísticas
        report_data.add_statistic("total_files", len(self.discovered_files), "Total de arquivos encontrados")
        
        # Adicionar arquivos
        for file_info in self.discovered_files:
            report_data.add_file_processed(
                file_info.file_path,
                "Descoberto",
                {
                    "size": file_info.size_bytes,
                    "modified": file_info.last_modified.isoformat(),
                    "extension": file_info.extension
                }
            )
            
        # Mostrar diálogo
        ReportDialog(self.root, report_data).show()
        
    def _show_validation_report(self):
        """Mostra relatório de validação."""
        if not self.validation_results:
            messagebox.showinfo("Relatório", "Nenhuma validação realizada ainda.")
            return
            
        # Criar dados do relatório
        report_data = ReportData(
            title="Relatório de Validação",
            operation="validation",
            start_time=datetime.now(),
            end_time=datetime.now(),
            success=True
        )
        
        # Contar resultados
        valid_count = sum(1 for result in self.validation_results.values() 
                         if result.status == ValidationStatus.VALID)
        invalid_count = len(self.validation_results) - valid_count
        
        # Adicionar estatísticas
        report_data.add_statistic("total_files", len(self.validation_results), "Total de arquivos validados")
        report_data.add_statistic("valid_files", valid_count, "Arquivos válidos")
        report_data.add_statistic("invalid_files", invalid_count, "Arquivos inválidos")
        
        # Adicionar resultados
        for file_path, result in self.validation_results.items():
            status_text = "Válido" if result.status == ValidationStatus.VALID else "Inválido"
            report_data.add_file_processed(file_path, status_text, {"errors": len(result.errors)})
            
            # Adicionar erros
            for error in result.errors:
                report_data.add_error(error, file_path)
                
        # Mostrar diálogo
        ReportDialog(self.root, report_data).show()
        
    def _show_advanced_config(self):
        """Mostra configurações avançadas."""
        config = self.config_manager.get_all_config()
        
        dialog = AdvancedConfigDialog(
            self.root,
            config,
            on_save=self._save_advanced_config
        )
        
        result = dialog.show()
        if result:
            messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")
            
    def _save_advanced_config(self, config: Dict[str, Any]):
        """Salva configurações avançadas.
        
        Args:
            config: Configurações a salvar.
        """
        try:
            # Salvar cada seção
            for section, values in config.items():
                for key, value in values.items():
                    self.config_manager.set(f"{section}.{key}", value)
                    
            self.logger.info("Configurações avançadas salvas")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar configurações: {e}")
            raise
            
    def _change_theme(self, theme_name: str):
        """Altera tema da aplicação.
        
        Args:
            theme_name: Nome do tema.
        """
        if theme_name == 'modern':
            theme_manager.set_theme(ModernTheme())
        elif theme_name == 'dark':
            theme_manager.set_theme(DarkTheme())
            
        theme_manager.apply_theme(self.root)
        self._update_status(f"Tema alterado para {theme_name}")
        
    def _new_project(self):
        """Cria novo projeto."""
        if messagebox.askyesno("Novo Projeto", "Deseja criar um novo projeto? Dados não salvos serão perdidos."):
            self._reset_application_state()
            self._update_status("Novo projeto criado")
            
    def _open_project(self):
        """Abre projeto existente."""
        file_path = filedialog.askopenfilename(
            title="Abrir Projeto",
            filetypes=[("Projetos Pulse", "*.pulse"), ("Todos os arquivos", "*.*")]
        )
        
        if file_path:
            # TODO: Implementar carregamento de projeto
            messagebox.showinfo("Em Desenvolvimento", "Funcionalidade em desenvolvimento.")
            
    def _save_project(self):
        """Salva projeto atual."""
        file_path = filedialog.asksaveasfilename(
            title="Salvar Projeto",
            defaultextension=".pulse",
            filetypes=[("Projetos Pulse", "*.pulse"), ("Todos os arquivos", "*.*")]
        )
        
        if file_path:
            # TODO: Implementar salvamento de projeto
            messagebox.showinfo("Em Desenvolvimento", "Funcionalidade em desenvolvimento.")
            
    def _reset_application_state(self):
        """Reseta estado da aplicação."""
        self.discovered_files.clear()
        self.validation_results.clear()
        self.analysis_results.clear()
        self.subordinadas_path = ""
        self.master_file_path = ""
        
        self.files_count_var.set("Arquivos: 0")
        self.file_selector.reset()
        self.progress_monitor.reset()
        
    def _show_about(self):
        """Mostra informações sobre a aplicação."""
        about_text = (
            "Pulse - Consolidador de Planilhas\n\n"
            "Versão: 1.0.0\n"
            "Desenvolvido com Python e Tkinter\n\n"
            "Sistema avançado para descoberta, validação,\n"
            "análise e consolidação de planilhas Excel."
        )
        
        messagebox.showinfo("Sobre", about_text)
        
    def _show_documentation(self):
        """Mostra documentação."""
        messagebox.showinfo("Documentação", "Documentação disponível em: docs/README.md")
        
    def _update_status(self, message: str):
        """Atualiza status da aplicação.
        
        Args:
            message: Mensagem de status.
        """
        self.status_var.set(message)
        self.root.update_idletasks()
        
    def _quit_application(self):
        """Encerra aplicação."""
        if self.current_operation:
            if not messagebox.askyesno("Confirmar", 
                                     "Uma operação está em andamento. Deseja realmente sair?"):
                return
                
        self._on_closing()
        
    def _on_closing(self):
        """Manipula fechamento da janela."""
        try:
            # Cancelar operações em andamento
            if self.current_operation:
                self.operation_cancelled = True
                
            # Salvar configurações
            self.config_manager.save_config()
            
            # Fechar janela
            self.root.quit()
            self.root.destroy()
            
        except Exception as e:
            self.logger.error(f"Erro ao fechar aplicação: {e}")
            
    def run(self):
        """Executa a aplicação."""
        try:
            self.logger.info("Iniciando aplicação Pulse")
            self._update_status("Aplicação iniciada")
            self.root.mainloop()
            
        except Exception as e:
            self.logger.error(f"Erro na execução da aplicação: {e}")
            messagebox.showerror("Erro Fatal", f"Erro na aplicação: {e}")
            
        finally:
            self.logger.info("Aplicação encerrada")


def main():
    """Função principal para executar a aplicação."""
    try:
        app = MainWindow()
        app.run()
    except Exception as e:
        print(f"Erro ao iniciar aplicação: {e}")
        

if __name__ == "__main__":
    main()