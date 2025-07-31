"""Diálogo de relatórios.

Este módulo implementa um diálogo para exibir relatórios detalhados
de operações, incluindo estatísticas, logs e exportação.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import csv
from pathlib import Path

from ...core import get_logger
from ..themes import theme_manager


class ReportData:
    """Classe para estruturar dados do relatório."""
    
    def __init__(self, title: str, operation: str, start_time: datetime, 
                 end_time: datetime, success: bool = True):
        """Inicializa dados do relatório.
        
        Args:
            title: Título do relatório.
            operation: Tipo de operação.
            start_time: Hora de início.
            end_time: Hora de término.
            success: Se a operação foi bem-sucedida.
        """
        self.title = title
        self.operation = operation
        self.start_time = start_time
        self.end_time = end_time
        self.success = success
        self.duration = end_time - start_time
        
        # Dados detalhados
        self.statistics: Dict[str, Any] = {}
        self.files_processed: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.logs: List[Dict[str, Any]] = []
        
    def add_statistic(self, key: str, value: Any, description: str = ""):
        """Adiciona estatística ao relatório.
        
        Args:
            key: Chave da estatística.
            value: Valor da estatística.
            description: Descrição da estatística.
        """
        self.statistics[key] = {
            'value': value,
            'description': description
        }
        
    def add_file_processed(self, file_path: str, status: str, 
                          details: Dict[str, Any] = None):
        """Adiciona arquivo processado.
        
        Args:
            file_path: Caminho do arquivo.
            status: Status do processamento.
            details: Detalhes adicionais.
        """
        self.files_processed.append({
            'file_path': file_path,
            'status': status,
            'details': details or {},
            'timestamp': datetime.now()
        })
        
    def add_error(self, message: str, file_path: str = "", details: str = ""):
        """Adiciona erro ao relatório.
        
        Args:
            message: Mensagem de erro.
            file_path: Arquivo relacionado ao erro.
            details: Detalhes do erro.
        """
        self.errors.append({
            'message': message,
            'file_path': file_path,
            'details': details,
            'timestamp': datetime.now()
        })
        
    def add_warning(self, message: str, file_path: str = "", details: str = ""):
        """Adiciona aviso ao relatório.
        
        Args:
            message: Mensagem de aviso.
            file_path: Arquivo relacionado ao aviso.
            details: Detalhes do aviso.
        """
        self.warnings.append({
            'message': message,
            'file_path': file_path,
            'details': details,
            'timestamp': datetime.now()
        })
        
    def add_log(self, level: str, message: str, details: str = ""):
        """Adiciona entrada de log.
        
        Args:
            level: Nível do log (INFO, WARNING, ERROR).
            message: Mensagem do log.
            details: Detalhes adicionais.
        """
        self.logs.append({
            'level': level,
            'message': message,
            'details': details,
            'timestamp': datetime.now()
        })


class ReportDialog:
    """Diálogo para exibir relatórios detalhados.
    
    Funcionalidades:
    - Visão geral da operação
    - Estatísticas detalhadas
    - Lista de arquivos processados
    - Logs de erros e avisos
    - Exportação em múltiplos formatos
    """
    
    def __init__(self, parent, report_data: ReportData):
        """Inicializa o diálogo de relatório.
        
        Args:
            parent: Widget pai.
            report_data: Dados do relatório.
        """
        self.parent = parent
        self.report_data = report_data
        self.logger = get_logger(__name__)
        
        # Criar diálogo
        self.dialog = None
        self._create_dialog()
        
    def _create_dialog(self):
        """Cria o diálogo."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"Relatório - {self.report_data.title}")
        self.dialog.geometry("800x600")
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
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
        self.dialog.bind('<Escape>', lambda e: self._on_close())
        
    def _center_dialog(self):
        """Centraliza o diálogo na tela."""
        self.dialog.update_idletasks()
        
        # Obter dimensões
        width = 800
        height = 600
        
        # Calcular posição central
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        
    def _setup_content(self):
        """Configura o conteúdo do diálogo."""
        main_frame = ttk.Frame(self.dialog, style='Surface.TFrame', padding=10)
        main_frame.pack(fill='both', expand=True)
        
        # Cabeçalho
        self._create_header(main_frame)
        
        # Notebook para abas
        self.notebook = ttk.Notebook(main_frame, style='TNotebook')
        self.notebook.pack(fill='both', expand=True, pady=(10, 0))
        
        # Criar abas
        self._create_overview_tab()
        self._create_files_tab()
        self._create_issues_tab()
        self._create_logs_tab()
        
        # Frame de botões
        button_frame = ttk.Frame(main_frame, style='Main.TFrame')
        button_frame.pack(fill='x', pady=(10, 0))
        
        # Botões de exportação
        ttk.Button(button_frame, text="Exportar JSON",
                  command=self._export_json,
                  style='Secondary.TButton').pack(side='left')
                  
        ttk.Button(button_frame, text="Exportar CSV",
                  command=self._export_csv,
                  style='Secondary.TButton').pack(side='left', padx=(10, 0))
                  
        ttk.Button(button_frame, text="Exportar TXT",
                  command=self._export_txt,
                  style='Secondary.TButton').pack(side='left', padx=(10, 0))
        
        # Botão fechar
        ttk.Button(button_frame, text="Fechar",
                  command=self._on_close,
                  style='Primary.TButton').pack(side='right')
        
    def _create_header(self, parent):
        """Cria cabeçalho do relatório.
        
        Args:
            parent: Widget pai.
        """
        header_frame = ttk.Frame(parent, style='Surface.TFrame')
        header_frame.pack(fill='x', pady=(0, 10))
        
        # Título
        title_label = ttk.Label(header_frame, text=self.report_data.title,
                               style='Heading.TLabel')
        title_label.pack(anchor='w')
        
        # Informações básicas
        info_frame = ttk.Frame(header_frame, style='Main.TFrame')
        info_frame.pack(fill='x', pady=(5, 0))
        
        # Status
        status_text = "✓ Concluído com sucesso" if self.report_data.success else "✗ Falhou"
        status_color = theme_manager.get_color('success') if self.report_data.success else theme_manager.get_color('error')
        
        status_label = ttk.Label(info_frame, text=status_text, style='TLabel')
        status_label.pack(side='left')
        
        # Duração
        duration_text = f"Duração: {self.report_data.duration}"
        duration_label = ttk.Label(info_frame, text=duration_text, style='Secondary.TLabel')
        duration_label.pack(side='right')
        
        # Horários
        time_text = f"Início: {self.report_data.start_time.strftime('%H:%M:%S')} | Fim: {self.report_data.end_time.strftime('%H:%M:%S')}"
        time_label = ttk.Label(header_frame, text=time_text, style='Secondary.TLabel')
        time_label.pack(anchor='w', pady=(2, 0))
        
    def _create_overview_tab(self):
        """Cria aba de visão geral."""
        overview_frame = ttk.Frame(self.notebook, style='Main.TFrame', padding=15)
        self.notebook.add(overview_frame, text="Visão Geral")
        
        # Estatísticas principais
        stats_label = ttk.Label(overview_frame, text="Estatísticas:", style='Subheading.TLabel')
        stats_label.pack(anchor='w', pady=(0, 10))
        
        # Frame de estatísticas
        stats_frame = ttk.Frame(overview_frame, style='Secondary.TFrame', padding=10)
        stats_frame.pack(fill='x', pady=(0, 15))
        
        # Exibir estatísticas
        row = 0
        for key, stat_data in self.report_data.statistics.items():
            # Nome da estatística
            name_label = ttk.Label(stats_frame, text=f"{key}:", style='TLabel')
            name_label.grid(row=row, column=0, sticky='w', padx=(0, 10))
            
            # Valor
            value_label = ttk.Label(stats_frame, text=str(stat_data['value']), 
                                   style='Bold.TLabel')
            value_label.grid(row=row, column=1, sticky='w')
            
            # Descrição (se disponível)
            if stat_data.get('description'):
                desc_label = ttk.Label(stats_frame, text=stat_data['description'], 
                                      style='Secondary.TLabel')
                desc_label.grid(row=row, column=2, sticky='w', padx=(10, 0))
                
            row += 1
            
        # Resumo de problemas
        if self.report_data.errors or self.report_data.warnings:
            issues_label = ttk.Label(overview_frame, text="Problemas Encontrados:", 
                                    style='Subheading.TLabel')
            issues_label.pack(anchor='w', pady=(10, 5))
            
            issues_frame = ttk.Frame(overview_frame, style='Secondary.TFrame', padding=10)
            issues_frame.pack(fill='x')
            
            if self.report_data.errors:
                error_text = f"Erros: {len(self.report_data.errors)}"
                error_label = ttk.Label(issues_frame, text=error_text, 
                                       style='Error.TLabel')
                error_label.pack(anchor='w')
                
            if self.report_data.warnings:
                warning_text = f"Avisos: {len(self.report_data.warnings)}"
                warning_label = ttk.Label(issues_frame, text=warning_text, 
                                         style='Warning.TLabel')
                warning_label.pack(anchor='w')
                
    def _create_files_tab(self):
        """Cria aba de arquivos processados."""
        files_frame = ttk.Frame(self.notebook, style='Main.TFrame', padding=10)
        self.notebook.add(files_frame, text=f"Arquivos ({len(self.report_data.files_processed)})")
        
        # Treeview para arquivos
        columns = ('arquivo', 'status', 'detalhes')
        self.files_tree = ttk.Treeview(files_frame, columns=columns, show='headings')
        
        # Configurar colunas
        self.files_tree.heading('arquivo', text='Arquivo')
        self.files_tree.heading('status', text='Status')
        self.files_tree.heading('detalhes', text='Detalhes')
        
        self.files_tree.column('arquivo', width=300)
        self.files_tree.column('status', width=100)
        self.files_tree.column('detalhes', width=200)
        
        # Scrollbars
        files_v_scroll = ttk.Scrollbar(files_frame, orient='vertical', 
                                      command=self.files_tree.yview)
        files_h_scroll = ttk.Scrollbar(files_frame, orient='horizontal', 
                                      command=self.files_tree.xview)
        
        self.files_tree.configure(yscrollcommand=files_v_scroll.set,
                                 xscrollcommand=files_h_scroll.set)
        
        # Layout
        self.files_tree.grid(row=0, column=0, sticky='nsew')
        files_v_scroll.grid(row=0, column=1, sticky='ns')
        files_h_scroll.grid(row=1, column=0, sticky='ew')
        
        files_frame.columnconfigure(0, weight=1)
        files_frame.rowconfigure(0, weight=1)
        
        # Preencher dados
        for file_data in self.report_data.files_processed:
            file_name = Path(file_data['file_path']).name
            status = file_data['status']
            details = str(file_data.get('details', {}))
            
            self.files_tree.insert('', 'end', values=(file_name, status, details))
            
    def _create_issues_tab(self):
        """Cria aba de problemas (erros e avisos)."""
        issues_frame = ttk.Frame(self.notebook, style='Main.TFrame', padding=10)
        total_issues = len(self.report_data.errors) + len(self.report_data.warnings)
        self.notebook.add(issues_frame, text=f"Problemas ({total_issues})")
        
        # Treeview para problemas
        columns = ('tipo', 'arquivo', 'mensagem', 'hora')
        self.issues_tree = ttk.Treeview(issues_frame, columns=columns, show='headings')
        
        # Configurar colunas
        self.issues_tree.heading('tipo', text='Tipo')
        self.issues_tree.heading('arquivo', text='Arquivo')
        self.issues_tree.heading('mensagem', text='Mensagem')
        self.issues_tree.heading('hora', text='Hora')
        
        self.issues_tree.column('tipo', width=80)
        self.issues_tree.column('arquivo', width=200)
        self.issues_tree.column('mensagem', width=300)
        self.issues_tree.column('hora', width=100)
        
        # Scrollbars
        issues_v_scroll = ttk.Scrollbar(issues_frame, orient='vertical', 
                                       command=self.issues_tree.yview)
        issues_h_scroll = ttk.Scrollbar(issues_frame, orient='horizontal', 
                                       command=self.issues_tree.xview)
        
        self.issues_tree.configure(yscrollcommand=issues_v_scroll.set,
                                  xscrollcommand=issues_h_scroll.set)
        
        # Layout
        self.issues_tree.grid(row=0, column=0, sticky='nsew')
        issues_v_scroll.grid(row=0, column=1, sticky='ns')
        issues_h_scroll.grid(row=1, column=0, sticky='ew')
        
        issues_frame.columnconfigure(0, weight=1)
        issues_frame.rowconfigure(0, weight=1)
        
        # Preencher erros
        for error in self.report_data.errors:
            file_name = Path(error['file_path']).name if error['file_path'] else "-"
            time_str = error['timestamp'].strftime('%H:%M:%S')
            
            item = self.issues_tree.insert('', 'end', 
                                          values=("ERRO", file_name, error['message'], time_str))
            self.issues_tree.set(item, 'tipo', "ERRO")
            
        # Preencher avisos
        for warning in self.report_data.warnings:
            file_name = Path(warning['file_path']).name if warning['file_path'] else "-"
            time_str = warning['timestamp'].strftime('%H:%M:%S')
            
            item = self.issues_tree.insert('', 'end', 
                                          values=("AVISO", file_name, warning['message'], time_str))
            
    def _create_logs_tab(self):
        """Cria aba de logs detalhados."""
        logs_frame = ttk.Frame(self.notebook, style='Main.TFrame', padding=10)
        self.notebook.add(logs_frame, text=f"Logs ({len(self.report_data.logs)})")
        
        # Text widget para logs
        self.logs_text = tk.Text(logs_frame, wrap=tk.WORD,
                                bg=theme_manager.get_color('background'),
                                fg=theme_manager.get_color('text_primary'),
                                font=theme_manager.get_font('monospace'))
        
        # Scrollbar para logs
        logs_scroll = ttk.Scrollbar(logs_frame, orient='vertical', 
                                   command=self.logs_text.yview)
        self.logs_text.configure(yscrollcommand=logs_scroll.set)
        
        # Layout
        self.logs_text.grid(row=0, column=0, sticky='nsew')
        logs_scroll.grid(row=0, column=1, sticky='ns')
        
        logs_frame.columnconfigure(0, weight=1)
        logs_frame.rowconfigure(0, weight=1)
        
        # Configurar tags de cores
        self.logs_text.tag_configure('INFO', foreground=theme_manager.get_color('info'))
        self.logs_text.tag_configure('WARNING', foreground=theme_manager.get_color('warning'))
        self.logs_text.tag_configure('ERROR', foreground=theme_manager.get_color('error'))
        
        # Preencher logs
        for log_entry in self.report_data.logs:
            timestamp = log_entry['timestamp'].strftime('%H:%M:%S')
            level = log_entry['level']
            message = log_entry['message']
            
            log_line = f"[{timestamp}] {level}: {message}\n"
            self.logs_text.insert(tk.END, log_line, level)
            
        self.logs_text.config(state='disabled')
        
    def _export_json(self):
        """Exporta relatório em formato JSON."""
        file_path = filedialog.asksaveasfilename(
            title="Exportar Relatório JSON",
            defaultextension=".json",
            filetypes=[("Arquivos JSON", "*.json"), ("Todos os arquivos", "*.*")]
        )
        
        if file_path:
            try:
                report_dict = self._serialize_report()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(report_dict, f, indent=2, ensure_ascii=False, default=str)
                    
                messagebox.showinfo("Sucesso", "Relatório exportado com sucesso!")
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar relatório: {e}")
                
    def _export_csv(self):
        """Exporta arquivos processados em formato CSV."""
        file_path = filedialog.asksaveasfilename(
            title="Exportar Arquivos CSV",
            defaultextension=".csv",
            filetypes=[("Arquivos CSV", "*.csv"), ("Todos os arquivos", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # Cabeçalho
                    writer.writerow(['Arquivo', 'Status', 'Detalhes', 'Timestamp'])
                    
                    # Dados
                    for file_data in self.report_data.files_processed:
                        writer.writerow([
                            file_data['file_path'],
                            file_data['status'],
                            str(file_data.get('details', {})),
                            file_data['timestamp'].isoformat()
                        ])
                        
                messagebox.showinfo("Sucesso", "Arquivos exportados com sucesso!")
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar CSV: {e}")
                
    def _export_txt(self):
        """Exporta relatório em formato texto."""
        file_path = filedialog.asksaveasfilename(
            title="Exportar Relatório TXT",
            defaultextension=".txt",
            filetypes=[("Arquivos de Texto", "*.txt"), ("Todos os arquivos", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    # Cabeçalho
                    f.write(f"RELATÓRIO: {self.report_data.title}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    # Informações básicas
                    f.write(f"Operação: {self.report_data.operation}\n")
                    f.write(f"Início: {self.report_data.start_time}\n")
                    f.write(f"Fim: {self.report_data.end_time}\n")
                    f.write(f"Duração: {self.report_data.duration}\n")
                    f.write(f"Status: {'Sucesso' if self.report_data.success else 'Falha'}\n\n")
                    
                    # Estatísticas
                    if self.report_data.statistics:
                        f.write("ESTATÍSTICAS:\n")
                        f.write("-" * 20 + "\n")
                        for key, stat_data in self.report_data.statistics.items():
                            f.write(f"{key}: {stat_data['value']}\n")
                        f.write("\n")
                        
                    # Arquivos processados
                    if self.report_data.files_processed:
                        f.write("ARQUIVOS PROCESSADOS:\n")
                        f.write("-" * 25 + "\n")
                        for file_data in self.report_data.files_processed:
                            f.write(f"- {file_data['file_path']} ({file_data['status']})\n")
                        f.write("\n")
                        
                    # Erros
                    if self.report_data.errors:
                        f.write("ERROS:\n")
                        f.write("-" * 10 + "\n")
                        for error in self.report_data.errors:
                            f.write(f"- {error['message']}\n")
                            if error['file_path']:
                                f.write(f"  Arquivo: {error['file_path']}\n")
                        f.write("\n")
                        
                    # Avisos
                    if self.report_data.warnings:
                        f.write("AVISOS:\n")
                        f.write("-" * 10 + "\n")
                        for warning in self.report_data.warnings:
                            f.write(f"- {warning['message']}\n")
                            if warning['file_path']:
                                f.write(f"  Arquivo: {warning['file_path']}\n")
                                
                messagebox.showinfo("Sucesso", "Relatório exportado com sucesso!")
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar relatório: {e}")
                
    def _serialize_report(self) -> Dict[str, Any]:
        """Serializa dados do relatório para dicionário.
        
        Returns:
            Dicionário com dados do relatório.
        """
        return {
            'title': self.report_data.title,
            'operation': self.report_data.operation,
            'start_time': self.report_data.start_time.isoformat(),
            'end_time': self.report_data.end_time.isoformat(),
            'duration': str(self.report_data.duration),
            'success': self.report_data.success,
            'statistics': self.report_data.statistics,
            'files_processed': self.report_data.files_processed,
            'errors': self.report_data.errors,
            'warnings': self.report_data.warnings,
            'logs': self.report_data.logs
        }
        
    def _on_close(self):
        """Manipula fechamento do diálogo."""
        if self.dialog:
            self.dialog.grab_release()
            self.dialog.destroy()
            self.dialog = None
            
    def show(self):
        """Mostra o diálogo."""
        if self.dialog:
            self.dialog.wait_window()