# 🖥️ ESPECIFICAÇÕES TÉCNICAS - INTERFACE DESKTOP TKINTER

## 📋 VISÃO GERAL

A interface desktop será desenvolvida usando **Tkinter** nativo do Python 3.10+, proporcionando uma aplicação standalone moderna e intuitiva para o sistema de consolidação de planilhas.

## 🏗️ ARQUITETURA DA INTERFACE

### 📁 Estrutura de Diretórios
```
src/gui/
├── __init__.py                 # Inicialização do módulo GUI
├── main_window.py             # Janela principal da aplicação
├── app.py                     # Classe principal da aplicação
├── components/                # Componentes reutilizáveis
│   ├── __init__.py
│   ├── file_selector.py       # Seletor de arquivos e pastas
│   ├── progress_monitor.py    # Monitor de progresso
│   ├── settings_panel.py      # Painel de configurações
│   ├── log_viewer.py          # Visualizador de logs
│   └── status_bar.py          # Barra de status
├── dialogs/                   # Diálogos e janelas modais
│   ├── __init__.py
│   ├── confirmation_dialog.py # Diálogos de confirmação
│   ├── report_dialog.py       # Relatórios de consolidação
│   ├── settings_dialog.py     # Configurações avançadas
│   └── about_dialog.py        # Sobre a aplicação
├── themes/                    # Sistema de temas
│   ├── __init__.py
│   ├── theme_manager.py       # Gerenciador de temas
│   ├── light_theme.py         # Tema claro
│   └── dark_theme.py          # Tema escuro
└── utils/                     # Utilitários da interface
    ├── __init__.py
    ├── drag_drop.py           # Funcionalidades drag & drop
    ├── validators.py          # Validadores de interface
    └── helpers.py             # Funções auxiliares
```

## 🎨 DESIGN E USABILIDADE

### 🖼️ Layout Principal
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 📁 Arquivo  ✏️ Editar  🔧 Ferramentas  ❓ Ajuda                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 🏠 📁 ▶️ ⏸️ 🔄 ⚙️                                                                │ Toolbar
├─────────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────┐ ┌─────────────────────────────────────────┐ │
│ │        SELEÇÃO DE ARQUIVOS      │ │         MONITOR DE PROGRESSO            │ │
│ │                                 │ │                                         │ │
│ │ 📂 Pasta SUBORDINADAS:          │ │ ████████████████████░░░░ 80%            │ │
│ │ [Selecionar Pasta...]           │ │                                         │ │
│ │                                 │ │ 📊 Processando: arquivo_03.xlsx        │ │
│ │ 📄 Arquivo MESTRE:              │ │ ⏱️ Tempo restante: 2min 30s             │ │
│ │ [Selecionar Arquivo...]         │ │                                         │ │
│ │                                 │ │ 📝 Log de Operações:                   │ │
│ │ 💾 Pasta BACKUP:                │ │ ✅ arquivo_01.xlsx processado           │ │
│ │ [Selecionar Pasta...]           │ │ ✅ arquivo_02.xlsx processado           │ │
│ │                                 │ │ 🔄 arquivo_03.xlsx em andamento...      │ │
│ │ ┌─────────────────────────────┐ │ │                                         │ │
│ │ │     DRAG & DROP ZONE        │ │ │                                         │ │
│ │ │   Arraste arquivos aqui     │ │ │                                         │ │
│ │ └─────────────────────────────┘ │ │                                         │ │
│ └─────────────────────────────────┘ └─────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │                           PAINEL DE CONFIGURAÇÕES                          │ │
│ │ ☑️ Backup automático    🎨 Tema: Escuro    🌐 Idioma: Português            │ │
│ │ ☑️ Validação rigorosa   📊 Relatórios: Detalhados                         │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ✅ Sistema pronto | 📁 15 arquivos detectados | 💾 Último backup: 10:30      │ Status Bar
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 🎨 Sistema de Temas

#### Tema Claro (Padrão)
- **Cores primárias:** Azul (#0078D4), Branco (#FFFFFF)
- **Cores secundárias:** Cinza claro (#F3F2F1), Cinza escuro (#605E5C)
- **Acentos:** Verde (#107C10), Vermelho (#D13438), Laranja (#FF8C00)

#### Tema Escuro
- **Cores primárias:** Azul escuro (#1F1F1F), Cinza escuro (#2D2D30)
- **Cores secundárias:** Cinza médio (#3E3E42), Branco (#FFFFFF)
- **Acentos:** Verde claro (#4EC9B0), Vermelho claro (#F48771), Amarelo (#DCDCAA)

## 🔧 COMPONENTES TÉCNICOS

### 🏠 Janela Principal (main_window.py)
```python
class MainWindow(tk.Tk):
    """Janela principal da aplicação Tkinter."""
    
    def __init__(self):
        super().__init__()
        self.title("PULSE - Consolidador de Planilhas")
        self.geometry("1200x800")
        self.minsize(800, 600)
        
        # Configuração de temas
        self.theme_manager = ThemeManager()
        
        # Componentes principais
        self.file_selector = None
        self.progress_monitor = None
        self.settings_panel = None
        
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_status_bar()
        
    def _setup_ui(self):
        """Configura a interface principal."""
        # Layout com PanedWindow para redimensionamento
        
    def _setup_menu(self):
        """Configura o menu superior."""
        # Menu: Arquivo, Editar, Ferramentas, Ajuda
        
    def _setup_toolbar(self):
        """Configura a barra de ferramentas."""
        # Botões de ação rápida
        
    def _setup_status_bar(self):
        """Configura a barra de status."""
        # Informações do sistema em tempo real
```

### 📁 Seletor de Arquivos (file_selector.py)
```python
class FileSelector(ttk.Frame):
    """Widget para seleção de arquivos e pastas."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.subordinadas_path = tk.StringVar()
        self.mestre_path = tk.StringVar()
        self.backup_path = tk.StringVar()
        
        self._setup_ui()
        self._setup_drag_drop()
        
    def _setup_ui(self):
        """Configura a interface do seletor."""
        # Labels, Entry widgets, Buttons
        
    def _setup_drag_drop(self):
        """Configura funcionalidade drag & drop."""
        # Integração com tkinterdnd2 ou implementação nativa
        
    def validate_paths(self) -> bool:
        """Valida os caminhos selecionados."""
        # Verificação de existência e permissões
```

### 📊 Monitor de Progresso (progress_monitor.py)
```python
class ProgressMonitor(ttk.Frame):
    """Widget para monitoramento de progresso."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar()
        self.time_remaining_var = tk.StringVar()
        
        self._setup_ui()
        
    def update_progress(self, value: float, status: str = ""):
        """Atualiza o progresso da operação."""
        
    def add_log_entry(self, message: str, level: str = "INFO"):
        """Adiciona entrada no log visual."""
        
    def estimate_time_remaining(self, current: int, total: int, start_time: float):
        """Calcula tempo restante estimado."""
```

## 🚀 FUNCIONALIDADES AVANÇADAS

### 🖱️ Drag & Drop
- **Arquivos:** Arrastar arquivos .xlsx/.xls diretamente na interface
- **Pastas:** Arrastar pastas para seleção automática
- **Validação:** Verificação em tempo real de tipos de arquivo
- **Feedback Visual:** Indicadores visuais durante o arraste

### ⌨️ Atalhos de Teclado
- **Ctrl+O:** Abrir arquivo mestre
- **Ctrl+S:** Salvar configurações
- **Ctrl+R:** Executar consolidação
- **F5:** Atualizar lista de arquivos
- **F11:** Modo tela cheia
- **Ctrl+T:** Alternar tema
- **Ctrl+,:** Abrir configurações

### 📱 Responsividade
- **Redimensionamento:** Layout adaptável a diferentes tamanhos
- **Resolução:** Suporte a DPI alto (4K, Retina)
- **Orientação:** Otimização para telas widescreen

## 🔒 VALIDAÇÃO E SEGURANÇA

### ✅ Validação de Interface
- **Caminhos:** Verificação de existência e permissões
- **Formatos:** Validação de tipos de arquivo suportados
- **Espaço:** Verificação de espaço em disco disponível
- **Conflitos:** Detecção de arquivos em uso

### 🛡️ Tratamento de Erros
- **Diálogos Informativos:** Mensagens claras para o usuário
- **Recuperação:** Tentativas automáticas de recuperação
- **Logs:** Registro detalhado de erros para debugging

## 📊 INTEGRAÇÃO COM BACKEND

### 🔗 Comunicação com Core
```python
from src.core import ConsolidationEngine, ConfigManager
from src.spreadsheet import SpreadsheetProcessor

class GUIController:
    """Controlador para integração GUI-Backend."""
    
    def __init__(self):
        self.engine = ConsolidationEngine()
        self.config = ConfigManager()
        self.processor = SpreadsheetProcessor()
        
    async def start_consolidation(self, paths: dict, progress_callback):
        """Inicia processo de consolidação com callback de progresso."""
        
    def get_system_status(self) -> dict:
        """Obtém status atual do sistema."""
```

## 🧪 TESTES DE INTERFACE

### 🔬 Testes Automatizados
- **pytest-qt:** Testes de widgets e interações
- **unittest:** Testes de lógica de interface
- **Mock:** Simulação de operações de backend

### 👥 Testes de Usabilidade
- **Navegação:** Fluxo intuitivo de operações
- **Acessibilidade:** Suporte a leitores de tela
- **Performance:** Responsividade da interface

## 📈 MÉTRICAS E MONITORAMENTO

### 📊 Métricas de Interface
- **Tempo de resposta:** Latência de operações
- **Uso de memória:** Consumo de recursos
- **Erros de interface:** Exceções e falhas
- **Satisfação do usuário:** Feedback e usabilidade

## 🔄 ROADMAP DE DESENVOLVIMENTO

### Sprint 2 (Atual)
- ✅ Estrutura base da interface
- ✅ Janela principal e componentes básicos
- ✅ Sistema de temas
- ✅ Seleção de arquivos e drag & drop

### Sprint 3 (Futuro)
- 📊 Gráficos integrados com matplotlib
- 🔔 Sistema de notificações
- 🌐 Internacionalização (i18n)
- 📱 Modo compacto para telas pequenas

### Sprint 4 (Futuro)
- 🔌 Plugins e extensões
- 🎨 Editor de temas personalizado
- 📊 Dashboard avançado
- 🔄 Sincronização em nuvem

Esta especificação garante uma interface desktop moderna, intuitiva e robusta para o sistema de consolidação de planilhas, proporcionando uma experiência de usuário excepcional.