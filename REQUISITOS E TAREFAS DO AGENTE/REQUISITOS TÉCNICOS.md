# REQUISITOS TÉCNICOS

## Descrição
Este arquivo define os requisitos técnicos necessários para o desenvolvimento e execução do projeto de consolidação de planilhas.

## SISTEMA DE CONSOLIDAÇÃO DE PLANILHAS

### Objetivo Principal
Criar um sistema robusto que consolide planilhas subordinadas em uma planilha mestre, preservando fórmulas, estilos e layouts, evitando duplicidade de elementos visuais e criando backups automáticos.

### Estrutura de Pastas Backend
```
backend/
├── SUBORDINADAS/
│   ├── planilha_vendas.xlsx
│   ├── planilha_estoque.xlsx
│   └── planilha_financeiro.xlsx
├── MESTRE/
│   └── planilha_consolidada.xlsx
└── BACKUP/
    ├── 2025-01-30_planilha_consolidada.xlsx
    ├── 2025-01-29_planilha_consolidada.xlsx
    └── ...
```

## FLUXO TÉCNICO DETALHADO

### 1. INICIALIZAÇÃO DO SISTEMA
**1.1** Verificar estrutura de pastas (SUBORDINADAS, MESTRE, BACKUP)
**1.2** Criar pastas ausentes automaticamente usando `os.makedirs()`
**1.3** Validar permissões de leitura/escrita nas pastas
**1.4** Inicializar sistema de logs com `logging`

### 2. DESCOBERTA E VALIDAÇÃO DE PLANILHAS SUBORDINADAS
**2.1** Escanear pasta SUBORDINADAS usando `os.listdir()` e `glob.glob()`
**2.2** Filtrar apenas arquivos .xlsx, .xls usando `pathlib.Path.suffix`
**2.3** Validar integridade de cada arquivo com `openpyxl.load_workbook()`
**2.4** Verificar se planilhas possuem dados válidos (não vazias)
**2.5** Registrar planilhas encontradas em log estruturado

### 3. ANÁLISE DE ESTRUTURA E LAYOUT
**3.1** Carregar cada planilha subordinada com `openpyxl.load_workbook(data_only=False)`
**3.2** Extrair informações de cabeçalho da primeira linha de cada planilha
**3.3** Mapear estilos de células usando `openpyxl.styles`
**3.4** Identificar fórmulas existentes com `cell.data_type == 'f'`
**3.5** Catalogar elementos visuais (bordas, cores, fontes) para evitar duplicidade

### 4. CRIAÇÃO DE BACKUP DA PLANILHA MESTRE
**4.1** Verificar existência da planilha mestre atual
**4.2** Gerar nome do backup com timestamp: `YYYY-MM-DD_HH-MM-SS_planilha_consolidada.xlsx`
**4.3** Copiar planilha mestre para pasta BACKUP usando `shutil.copy2()`
**4.4** Validar integridade do backup criado
**4.5** Limpar backups antigos (manter apenas últimos 30 dias)

### 5. PROCESSAMENTO DE DADOS DAS SUBORDINADAS
**5.1** Carregar dados de cada planilha subordinada com `pandas.read_excel()`
**5.2** Preservar tipos de dados originais usando `dtype` específicos
**5.3** Extrair apenas um cabeçalho único (da primeira planilha processada)
**5.4** Concatenar dados de todas as subordinadas usando `pandas.concat()`
**5.5** Remover duplicatas se existirem usando `drop_duplicates()`

### 6. PRESERVAÇÃO DE FÓRMULAS E ESTILOS
**6.1** Criar dicionário de mapeamento de fórmulas por célula
**6.2** Extrair estilos únicos para evitar duplicidade visual
**6.3** Mapear formatação condicional existente
**6.4** Preservar validação de dados das células
**6.5** Manter hiperlinks e comentários

### 7. CONSOLIDAÇÃO NA PLANILHA MESTRE
**7.1** Criar nova workbook mestre usando `openpyxl.Workbook()`
**7.2** Aplicar cabeçalho único na primeira linha
**7.3** Inserir dados consolidados preservando tipos
**7.4** Aplicar estilos únicos evitando duplicidade
**7.5** Recriar fórmulas ajustando referências de células

### 8. MITIGAÇÃO DE DUPLICIDADE DE ELEMENTOS VISUAIS
**8.1** Criar hash único para cada estilo visual
**8.2** Manter registro de estilos já aplicados
**8.3** Reutilizar estilos existentes em vez de criar novos
**8.4** Otimizar paleta de cores para evitar redundância
**8.5** Consolidar formatações condicionais similares

### 9. VALIDAÇÃO E CONTROLE DE QUALIDADE
**9.1** Verificar integridade dos dados consolidados
**9.2** Validar se todas as fórmulas funcionam corretamente
**9.3** Confirmar preservação de estilos visuais
**9.4** Testar abertura da planilha consolidada
**9.5** Gerar relatório de consolidação com estatísticas

### 10. FINALIZAÇÃO E SALVAMENTO
**10.1** Salvar planilha mestre na pasta MESTRE
**10.2** Aplicar proteção contra alterações acidentais
**10.3** Gerar log de sucesso com timestamp
**10.4** Limpar arquivos temporários
**10.5** Notificar conclusão do processo

## Requisitos de Sistema

### Ambiente de Desenvolvimento
- **Sistema Operacional:** Windows 10/11, Linux, macOS
- **Python:** Versão 3.10 ou superior
- **IDE:** Visual Studio Code, PyCharm, ou similar
- **Git:** Para controle de versão

### Dependências Python Específicas
```python
# Manipulação de planilhas (CORE)
openpyxl>=3.1.0          # Manipulação avançada de Excel
xlsxwriter>=3.0.0        # Criação otimizada de planilhas
pandas>=1.5.0            # Processamento de dados
numpy>=1.24.0            # Operações numéricas

# Interface Gráfica Desktop (TKINTER)
tkinter>=8.6             # Interface gráfica nativa Python
ttk>=8.6                 # Widgets modernos do Tkinter
ttkthemes>=3.2.2         # Temas modernos para TTK
pillow>=9.0.0            # Manipulação de imagens para interface
matplotlib>=3.6.0        # Gráficos integrados na interface

# Manipulação de arquivos e sistema
pathlib>=1.0.0           # Manipulação de caminhos
shutil>=1.0.0            # Operações de arquivo
os>=1.0.0                # Operações do sistema
glob>=1.0.0              # Busca de arquivos

# Data e tempo
datetime>=1.0.0          # Manipulação de timestamps

# Hashing e validação
hashlib>=1.0.0           # Criação de hashes para estilos

# Logs e monitoramento
logging>=1.0.0           # Sistema de logs

# Testes e qualidade
pytest>=7.2.0
pytest-cov>=4.0.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
```

### Requisitos de Performance para Consolidação
- **Memória RAM:** Mínimo 8GB, recomendado 16GB para processar planilhas grandes
- **Processamento:** Multi-core para processamento paralelo de múltiplas subordinadas
- **Armazenamento:** SSD obrigatório para operações rápidas de I/O durante consolidação
- **Tempo de Resposta:** Consolidação deve completar em máximo 5 minutos para até 50 planilhas
- **Throughput:** Capacidade de processar até 1GB de dados de planilhas por execução

### Requisitos de Segurança Específicos
- **Validação de Arquivos:** Verificação de integridade antes do processamento
- **Backup Seguro:** Criptografia AES-256 para backups sensíveis
- **Controle de Acesso:** Permissões específicas para pastas SUBORDINADAS, MESTRE e BACKUP
- **Logs de Auditoria:** Rastreamento completo de todas as operações de consolidação
- **Proteção contra Corrupção:** Validação de checksums para detectar arquivos corrompidos

### Requisitos de Interface Gráfica Desktop (Tkinter)
- **Framework:** Tkinter nativo do Python 3.10+ com TTK para widgets modernos
- **Temas:** Suporte a temas escuros e claros usando ttkthemes
- **Responsividade:** Interface adaptável a diferentes resoluções de tela
- **Usabilidade:** Design intuitivo com drag-and-drop para seleção de arquivos
- **Feedback Visual:** Barras de progresso, indicadores de status e notificações
- **Integração:** Visualização de gráficos usando matplotlib embarcado
- **Acessibilidade:** Suporte a atalhos de teclado e navegação por tabs

### Requisitos de Integração do Sistema
- **Sistema de Arquivos:** Suporte completo para Windows, Linux e macOS
- **Formatos Suportados:** Excel (.xlsx, .xls), LibreOffice Calc (.ods)
- **APIs Futuras:** Preparação para integração com Google Sheets e SharePoint
- **Monitoramento:** Sistema de logs estruturados para debugging
- **Notificações:** Sistema de alertas para falhas de consolidação
- **Interface Desktop:** Aplicação standalone com Tkinter para uso local

## CONTROLES DE QUALIDADE E VALIDAÇÃO

### Validações Obrigatórias
**V1.** Verificar se pasta SUBORDINADAS contém pelo menos uma planilha válida
**V2.** Validar se todas as planilhas subordinadas possuem estrutura compatível
**V3.** Confirmar que backup foi criado antes de iniciar consolidação
**V4.** Verificar integridade da planilha mestre após consolidação
**V5.** Validar que nenhuma fórmula foi quebrada no processo

### Tratamento de Erros
**E1.** Arquivo subordinado corrompido → Pular e registrar em log
**E2.** Pasta MESTRE inacessível → Abortar processo e notificar
**E3.** Falha na criação de backup → Abortar consolidação
**E4.** Memória insuficiente → Processar em chunks menores
**E5.** Fórmula inválida → Converter para valor e registrar warning

## Padrões e Convenções
- **Código:** PEP 8 com foco em legibilidade para manutenção
- **Documentação:** Docstrings detalhados para cada função de consolidação
- **Testes:** Cobertura mínima de 90% para funções críticas de consolidação
- **Versionamento:** Semantic Versioning (SemVer) com tags para releases
- **Nomenclatura:** Convenção clara para arquivos de backup (YYYY-MM-DD_HH-MM-SS)

## Compatibilidade e Formatos
- **Formatos Primários:** Excel (.xlsx) - formato principal
- **Formatos Secundários:** Excel legado (.xls), LibreOffice (.ods)
- **Encoding:** UTF-8 para garantir compatibilidade internacional
- **Versões Excel:** Compatibilidade com Excel 2016 ou superior
- **Limitações:** Máximo 1.048.576 linhas por planilha consolidada

## MÉTRICAS DE SUCESSO

### KPIs do Sistema
- **Taxa de Sucesso:** 99.5% de consolidações bem-sucedidas
- **Tempo Médio:** Consolidação completa em menos de 3 minutos
- **Integridade:** 100% de preservação de fórmulas e estilos
- **Backup:** 100% de criação de backups antes da consolidação
- **Zero Duplicidade:** Eliminação completa de elementos visuais duplicados