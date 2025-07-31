# DIAGRAMA VISUAL ASCII DA ARQUITETURA

## VISÃO GERAL DO SISTEMA

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           🖥️  CAMADA DE APRESENTAÇÃO                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │     CLI     │    │  API REST   │    │ Interface   │    │  Interface  │      │
│  │ Interface   │    │   FastAPI   │    │    Web      │    │   Tkinter   │      │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘      │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            ⚙️  CAMADA DE NEGÓCIO                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                        │
│  │    Core     │◄──►│  Validator  │◄──►│    Data     │                        │
│  │   Engine    │    │   System    │    │  Processor  │                        │
│  └─────────────┘    └─────────────┘    └─────────────┘                        │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            💾  CAMADA DE DADOS                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                        │
│  │ Spreadsheet │◄──►│    Data     │◄──►│    File     │                        │
│  │   Manager   │    │ Synchronizer│    │   Monitor   │                        │
│  └─────────────┘    └─────────────┘    └─────────────┘                        │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         🏗️  CAMADA DE INFRAESTRUTURA                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                        │
│  │   Sistema   │    │   Sistema   │    │   Sistema   │                        │
│  │ de Pastas   │    │ de Backup   │    │  de Logs    │                        │
│  └─────────────┘    └─────────────┘    └─────────────┘                        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## FLUXO DOS 10 PASSOS TÉCNICOS

```
🚀 INÍCIO
   │
   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 📁 PASSO 1: INICIALIZAÇÃO DO SISTEMA                                           │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                               │
│ │1.1 Check│→│1.2 Create│→│1.3 Valid│→│1.4 Init │                               │
│ │ Folders │ │ Missing │ │ Permiss │ │  Logs   │                               │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘                               │
└─────────────────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 🔍 PASSO 2: DESCOBERTA DE PLANILHAS SUBORDINADAS                               │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                   │
│ │2.1 Scan │→│2.2 Filter│→│2.3 Valid│→│2.4 Check│→│2.5 Log  │                   │
│ │ Folder  │ │ .xlsx   │ │Integrity│ │  Data   │ │ Results │                   │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘                   │
└─────────────────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 📊 PASSO 3: ANÁLISE DE ESTRUTURA E LAYOUT                                      │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                   │
│ │3.1 Load │→│3.2 Extract│→│3.3 Map │→│3.4 Find │→│3.5 Catalog│                 │
│ │Sheets   │ │ Headers │ │ Styles  │ │Formulas │ │ Visual  │                   │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘                   │
└─────────────────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 💾 PASSO 4: CRIAÇÃO DE BACKUP DA PLANILHA MESTRE                               │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                   │
│ │4.1 Check│→│4.2 Generate│→│4.3 Copy │→│4.4 Valid│→│4.5 Clean│                 │
│ │ Master  │ │Timestamp│ │to Backup│ │Integrity│ │  Old    │                   │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘                   │
└─────────────────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ ⚡ PASSO 5: PROCESSAMENTO DE DADOS DAS SUBORDINADAS                             │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                   │
│ │5.1 Load │→│5.2 Preserve│→│5.3 Extract│→│5.4 Concat│→│5.5 Remove│             │
│ │w/ Pandas│ │ DataTypes│ │ Header  │ │  Data   │ │ Duplicates│               │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘                   │
└─────────────────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 🎨 PASSO 6: PRESERVAÇÃO DE FÓRMULAS E ESTILOS                                  │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                   │
│ │6.1 Map  │→│6.2 Extract│→│6.3 Map  │→│6.4 Preserve│→│6.5 Keep │               │
│ │Formulas │ │ Unique  │ │Conditional│ │Validation│ │Hyperlinks│               │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘                   │
└─────────────────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 🔧 PASSO 7: CONSOLIDAÇÃO NA PLANILHA MESTRE                                    │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                   │
│ │7.1 Create│→│7.2 Apply │→│7.3 Insert│→│7.4 Apply│→│7.5 Recreate│              │
│ │Workbook │ │ Header  │ │  Data   │ │ Styles  │ │ Formulas │                │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘                   │
└─────────────────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 🚫 PASSO 8: MITIGAÇÃO DE DUPLICIDADE DE ELEMENTOS VISUAIS                      │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                   │
│ │8.1 Create│→│8.2 Register│→│8.3 Reuse│→│8.4 Optimize│→│8.5 Consolidate│        │
│ │Style Hash│ │ Applied │ │Existing │ │ Colors  │ │ Formatting │                │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘                   │
└─────────────────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ ✅ PASSO 9: VALIDAÇÃO E CONTROLE DE QUALIDADE                                  │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                   │
│ │9.1 Check│→│9.2 Valid │→│9.3 Confirm│→│9.4 Test │→│9.5 Generate│              │
│ │Integrity│ │Formulas │ │ Styles  │ │ Opening │ │ Report  │                  │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘                   │
└─────────────────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 🏁 PASSO 10: FINALIZAÇÃO E SALVAMENTO                                          │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                   │
│ │10.1 Save│→│10.2 Apply│→│10.3 Log │→│10.4 Clean│→│10.5 Notify│               │
│ │ Master  │ │Protection│ │ Success │ │  Temp   │ │Complete │                 │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘                   │
└─────────────────────────────────────────────────────────────────────────────────┘
   │
   ▼
✨ PROCESSO CONCLUÍDO
```

## ESTRUTURA DE PASTAS DO SISTEMA

```
backend/
├── 📁 SUBORDINADAS/
│   ├── 📊 planilha_vendas.xlsx      ← Input: Dados de vendas
│   ├── 📊 planilha_estoque.xlsx     ← Input: Dados de estoque  
│   ├── 📊 planilha_financeiro.xlsx  ← Input: Dados financeiros
│   └── 📊 planilha_rh.xlsx          ← Input: Dados de RH
│
├── 📁 MESTRE/
│   └── 📋 planilha_consolidada.xlsx ← Output: Resultado final
│
└── 📁 BACKUP/
    ├── 💾 2025-01-30_14-30-15_planilha_consolidada.xlsx
    ├── 💾 2025-01-30_09-15-22_planilha_consolidada.xlsx
    ├── 💾 2025-01-29_16-45-33_planilha_consolidada.xlsx
    └── 💾 ... (últimos 30 dias)
```

## FLUXO DE DADOS DETALHADO

```
📊 SUBORDINADAS          🔄 PROCESSAMENTO           📋 MESTRE
┌─────────────┐         ┌─────────────────┐        ┌─────────────┐
│ Vendas.xlsx │────────►│                 │       ┌┤Consolidada  │
├─────────────┤         │  🧠 CORE ENGINE │◄─────►││.xlsx        │
│Estoque.xlsx │────────►│                 │       ││             │
├─────────────┤         │ • Validação     │       ││ ┌─────────┐ │
│Financ.xlsx  │────────►│ • Consolidação  │       ││ │Headers  │ │
├─────────────┤         │ • Preservação   │       ││ ├─────────┤ │
│   RH.xlsx   │────────►│ • Otimização    │       ││ │ Vendas  │ │
└─────────────┘         └─────────────────┘       ││ │ Estoque │ │
                                │                 ││ │Financ.  │ │
                                ▼                 ││ │   RH    │ │
                        💾 BACKUP AUTOMÁTICO      ││ └─────────┘ │
                        ┌─────────────────┐       │└─────────────┘
                        │ Timestamp:      │       │
                        │ 2025-01-30      │       │ ✅ VALIDAÇÕES:
                        │ 14:30:15        │       │ • Fórmulas OK
                        └─────────────────┘       │ • Estilos OK
                                                  │ • Zero Duplicatas
                                                  └─────────────────
```

## COMPONENTES E BIBLIOTECAS

```
🏗️ INFRAESTRUTURA
┌─────────────────────────────────────────────────────────────┐
│ Sistema de Pastas    │ os.makedirs(), pathlib.Path()        │
│ Sistema de Backup    │ shutil.copy2(), datetime.now()       │
│ Sistema de Logs      │ logging.getLogger(), handlers        │
└─────────────────────────────────────────────────────────────┘

💾 MANIPULAÇÃO DE DADOS
┌─────────────────────────────────────────────────────────────┐
│ Leitura de Planilhas │ openpyxl.load_workbook()            │
│ Processamento        │ pandas.read_excel(), concat()        │
│ Escrita Otimizada    │ xlsxwriter.Workbook()                │
│ Validação Numérica   │ numpy.array(), dtype validation      │
└─────────────────────────────────────────────────────────────┘

🎨 ESTILOS E FORMATAÇÃO
┌─────────────────────────────────────────────────────────────┐
│ Estilos Únicos       │ openpyxl.styles, hashlib.md5()      │
│ Formatação Condicional│ openpyxl.formatting.rule           │
│ Cores e Fontes       │ openpyxl.styles.Color, Font         │
│ Bordas e Alinhamento │ openpyxl.styles.Border, Alignment   │
└─────────────────────────────────────────────────────────────┘

🔍 MONITORAMENTO
┌─────────────────────────────────────────────────────────────┐
│ Detecção de Mudanças │ os.path.getmtime(), file watchers   │
│ Validação de Arquivos│ try/except, file.exists()           │
│ Métricas de Performance│ time.time(), memory profiling     │
│ Relatórios de Qualidade│ custom validators, statistics    │
└─────────────────────────────────────────────────────────────┘
```

## TRATAMENTO DE ERROS POR PASSO

```
❌ PONTOS DE FALHA CRÍTICOS:

📁 Passo 1-2: Inicialização/Descoberta
├── Pasta não encontrada     → Criar automaticamente
├── Sem permissão de acesso  → Abortar com erro claro
└── Nenhuma planilha válida  → Notificar usuário

💾 Passo 4: Backup
├── Falha na criação        → ABORTAR PROCESSO COMPLETO
├── Espaço insuficiente     → Limpar backups antigos
└── Arquivo em uso          → Aguardar ou abortar

⚡ Passo 5: Processamento
├── Memória insuficiente    → Processar em chunks
├── Dados corrompidos       → Pular arquivo e registrar
└── Tipos incompatíveis     → Converter ou usar padrão

🔧 Passo 7: Consolidação
├── Fórmula inválida        → Converter para valor
├── Estilo não suportado    → Usar estilo padrão
└── Referência quebrada     → Ajustar automaticamente

✅ Passo 9: Validação
├── Arquivo não abre        → Rollback para backup
├── Dados inconsistentes    → Relatório de problemas
└── Performance baixa       → Otimizar na próxima versão
```

## MÉTRICAS DE SUCESSO

```
📊 KPIs DO SISTEMA:

🎯 Taxa de Sucesso: 99.5%
├── Consolidações bem-sucedidas
├── Zero perda de dados
└── Backups sempre criados

⏱️ Performance: < 3 minutos
├── Inicialização: 0.1s
├── Processamento: 2.0s
└── Finalização: 0.2s

🔒 Integridade: 100%
├── Fórmulas preservadas
├── Estilos mantidos
└── Zero duplicidade visual

💾 Backup: 100%
├── Criação automática
├── Validação de integridade
└── Limpeza de arquivos antigos
```

Este diagrama ASCII fornece uma visão clara e acessível da arquitetura completa do sistema, permitindo compreender rapidamente como cada componente interage e contribui para o objetivo final de consolidação de planilhas com zero duplicidade visual.