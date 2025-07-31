"""Testes de integração para o sistema de consolidação de planilhas.

Testa a integração entre os módulos scanner, validator e analyzer,
simulando fluxos completos de descoberta, validação e análise.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from spreadsheet.scanner import SpreadsheetScanner, SpreadsheetInfo
from spreadsheet.validator import SpreadsheetValidator, ValidationStatus
from spreadsheet.analyzer import SpreadsheetAnalyzer


class TestSystemIntegration(unittest.TestCase):
    """Testes de integração do sistema completo."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        self.temp_dir = tempfile.mkdtemp()
        self.subordinadas_dir = Path(self.temp_dir) / "SUBORDINADAS"
        self.subordinadas_dir.mkdir()
        
        # Inicializar componentes
        self.scanner = SpreadsheetScanner()
        self.validator = SpreadsheetValidator()
        self.analyzer = SpreadsheetAnalyzer()
        
    def tearDown(self):
        """Limpeza após os testes."""
        shutil.rmtree(self.temp_dir)
        
    def _create_test_file(self, name: str, content: bytes = b"test_content"):
        """Cria arquivo de teste.
        
        Args:
            name: Nome do arquivo.
            content: Conteúdo do arquivo em bytes.
            
        Returns:
            Path: Caminho do arquivo criado.
        """
        file_path = self.subordinadas_dir / name
        file_path.write_bytes(content)
        return file_path
        
    def test_complete_discovery_validation_flow(self):
        """Testa fluxo completo de descoberta e validação."""
        # Criar arquivos de teste
        valid_files = [
            self._create_test_file("vendas_2024.xlsx", b"x" * 1000),
            self._create_test_file("estoque.xlsx", b"x" * 2000),
            self._create_test_file("relatorio.xls", b"x" * 1500),
        ]
        
        invalid_files = [
            self._create_test_file("dados.csv", b"csv,data"),
            self._create_test_file("vazio.xlsx", b""),
            self._create_test_file("pequeno.xlsx", b"x" * 10),
        ]
        
        # 1. Descoberta
        discovered_files = self.scanner.scan_folder(str(self.subordinadas_dir))
        
        # Verificar descoberta
        self.assertEqual(len(discovered_files), 6)  # Todos os arquivos
        
        excel_files = [f for f in discovered_files if f.is_excel]
        self.assertEqual(len(excel_files), 5)  # Apenas arquivos Excel
        
        # 2. Validação
        excel_paths = [f.file_path for f in excel_files]
        
        with patch('openpyxl.load_workbook') as mock_xlsx, \
             patch('xlrd.open_workbook') as mock_xls:
            
            # Mock para arquivos XLSX válidos
            mock_workbook = MagicMock()
            mock_workbook.sheetnames = ['Sheet1']
            mock_worksheet = MagicMock()
            mock_worksheet.max_row = 10
            mock_worksheet.max_column = 5
            mock_workbook.__getitem__.return_value = mock_worksheet
            mock_xlsx.return_value = mock_workbook
            
            # Mock para arquivos XLS válidos
            mock_xls_workbook = MagicMock()
            mock_xls_workbook.nsheets = 1
            mock_xls_workbook.sheet_names.return_value = ['Sheet1']
            mock_xls_sheet = MagicMock()
            mock_xls_sheet.nrows = 10
            mock_xls_sheet.ncols = 5
            mock_xls_workbook.sheet_by_index.return_value = mock_xls_sheet
            mock_xls.return_value = mock_xls_workbook
            
            validation_results = self.validator.validate_multiple_files(excel_paths)
            
        # Verificar resultados de validação
        self.assertEqual(len(validation_results), 5)
        
        valid_results = [r for r in validation_results.values() if r.is_valid]
        invalid_results = [r for r in validation_results.values() if not r.is_valid]
        
        self.assertEqual(len(valid_results), 3)  # Arquivos válidos
        self.assertEqual(len(invalid_results), 2)  # Arquivos inválidos
        
    def test_discovery_validation_analysis_pipeline(self):
        """Testa pipeline completo: descoberta → validação → análise."""
        # Criar arquivo de teste
        test_file = self._create_test_file("analise_teste.xlsx", b"x" * 1000)
        
        # 1. Descoberta
        discovered_files = self.scanner.scan_folder(str(self.subordinadas_dir))
        excel_files = [f for f in discovered_files if f.is_excel]
        
        self.assertEqual(len(excel_files), 1)
        self.assertEqual(excel_files[0].file_path, str(test_file))
        
        # 2. Validação
        with patch('openpyxl.load_workbook') as mock_load:
            mock_workbook = MagicMock()
            mock_workbook.sheetnames = ['Dados', 'Resumo']
            
            # Mock da primeira worksheet
            mock_ws1 = MagicMock()
            mock_ws1.max_row = 100
            mock_ws1.max_column = 10
            
            # Mock da segunda worksheet
            mock_ws2 = MagicMock()
            mock_ws2.max_row = 50
            mock_ws2.max_column = 5
            
            mock_workbook.__getitem__.side_effect = [mock_ws1, mock_ws2]
            mock_load.return_value = mock_workbook
            
            validation_result = self.validator.validate_file(str(test_file))
            
        # Verificar validação
        self.assertTrue(validation_result.is_valid)
        self.assertEqual(validation_result.metadata['sheets_count'], 2)
        
        # 3. Análise (apenas se válido)
        if validation_result.is_valid:
            with patch('openpyxl.load_workbook') as mock_load:
                # Mock mais detalhado para análise
                mock_workbook = MagicMock()
                mock_workbook.sheetnames = ['Dados', 'Resumo']
                
                # Mock da worksheet com dados
                mock_ws = MagicMock()
                mock_ws.title = 'Dados'
                mock_ws.max_row = 100
                mock_ws.max_column = 10
                
                # Mock das células
                mock_cells = []
                for row in range(1, 6):
                    row_cells = []
                    for col in range(1, 6):
                        mock_cell = MagicMock()
                        if row == 1:
                            mock_cell.value = f"Header_{col}"
                            mock_cell.data_type = 's'  # string
                        else:
                            mock_cell.value = f"Data_{row}_{col}"
                            mock_cell.data_type = 's'
                        mock_cell.font = MagicMock()
                        mock_cell.font.bold = (row == 1)
                        mock_cell.fill = MagicMock()
                        mock_cell.fill.start_color = MagicMock()
                        mock_cell.fill.start_color.rgb = "FFFFFF"
                        row_cells.append(mock_cell)
                    mock_cells.append(row_cells)
                
                mock_ws.iter_rows.return_value = mock_cells
                mock_workbook.__getitem__.return_value = mock_ws
                mock_workbook.__iter__.return_value = [mock_ws]
                mock_load.return_value = mock_workbook
                
                analysis_result = self.analyzer.analyze_spreadsheet(str(test_file))
                
            # Verificar análise
            self.assertIsNotNone(analysis_result)
            self.assertEqual(analysis_result.file_path, str(test_file))
            self.assertGreater(len(analysis_result.sheets), 0)
            
    def test_error_handling_in_pipeline(self):
        """Testa tratamento de erros no pipeline completo."""
        # Criar arquivos problemáticos
        files = [
            self._create_test_file("corrupted.xlsx", b"not_excel_content"),
            self._create_test_file("empty.xlsx", b""),
            self._create_test_file("normal.txt", b"text_file"),
        ]
        
        # 1. Descoberta (deve funcionar)
        discovered_files = self.scanner.scan_folder(str(self.subordinadas_dir))
        self.assertEqual(len(discovered_files), 3)
        
        excel_files = [f for f in discovered_files if f.is_excel]
        self.assertEqual(len(excel_files), 2)  # Apenas .xlsx
        
        # 2. Validação (deve capturar erros)
        excel_paths = [f.file_path for f in excel_files]
        
        with patch('openpyxl.load_workbook') as mock_load:
            # Simular erro de arquivo corrompido
            mock_load.side_effect = Exception("Arquivo corrompido")
            
            validation_results = self.validator.validate_multiple_files(excel_paths)
            
        # Verificar que erros foram capturados
        self.assertEqual(len(validation_results), 2)
        
        for result in validation_results.values():
            self.assertFalse(result.is_valid)
            self.assertTrue(result.has_errors or result.status == ValidationStatus.ERROR)
            
    def test_performance_with_multiple_files(self):
        """Testa performance com múltiplos arquivos."""
        # Criar múltiplos arquivos
        num_files = 10
        created_files = []
        
        for i in range(num_files):
            file_path = self._create_test_file(f"file_{i:03d}.xlsx", b"x" * 1000)
            created_files.append(file_path)
            
        # Descoberta
        import time
        start_time = time.time()
        
        discovered_files = self.scanner.scan_folder(str(self.subordinadas_dir))
        
        discovery_time = time.time() - start_time
        
        # Verificar descoberta
        self.assertEqual(len(discovered_files), num_files)
        self.assertLess(discovery_time, 5.0)  # Deve ser rápido
        
        # Validação em lote
        excel_paths = [f.file_path for f in discovered_files]
        
        start_time = time.time()
        
        with patch('openpyxl.load_workbook') as mock_load:
            mock_workbook = MagicMock()
            mock_workbook.sheetnames = ['Sheet1']
            mock_worksheet = MagicMock()
            mock_worksheet.max_row = 10
            mock_worksheet.max_column = 5
            mock_workbook.__getitem__.return_value = mock_worksheet
            mock_load.return_value = mock_workbook
            
            validation_results = self.validator.validate_multiple_files(excel_paths)
            
        validation_time = time.time() - start_time
        
        # Verificar validação
        self.assertEqual(len(validation_results), num_files)
        self.assertLess(validation_time, 10.0)  # Deve ser razoavelmente rápido
        
        # Verificar que todos são válidos
        valid_count = sum(1 for r in validation_results.values() if r.is_valid)
        self.assertEqual(valid_count, num_files)
        
    def test_subdirectory_scanning(self):
        """Testa escaneamento de subdiretórios."""
        # Criar estrutura de subdiretórios
        sub_dir1 = self.subordinadas_dir / "2024" / "janeiro"
        sub_dir2 = self.subordinadas_dir / "2024" / "fevereiro"
        sub_dir3 = self.subordinadas_dir / "backup"
        
        for sub_dir in [sub_dir1, sub_dir2, sub_dir3]:
            sub_dir.mkdir(parents=True)
            
        # Criar arquivos em diferentes níveis
        files = [
            self.subordinadas_dir / "principal.xlsx",
            sub_dir1 / "vendas_jan.xlsx",
            sub_dir2 / "vendas_fev.xlsx",
            sub_dir3 / "backup_dados.xlsx",
        ]
        
        for file_path in files:
            file_path.write_bytes(b"x" * 1000)
            
        # Escaneamento recursivo
        discovered_files = self.scanner.scan_folder(
            str(self.subordinadas_dir)
        )
        
        # Verificar descoberta
        excel_files = [f for f in discovered_files if f.is_excel]
        self.assertEqual(len(excel_files), 4)
        
        # Verificar caminhos
        found_paths = {f.file_path for f in excel_files}
        expected_paths = {str(f) for f in files}
        
        self.assertEqual(found_paths, expected_paths)
        
    def test_file_filtering_and_sorting(self):
        """Testa filtragem e ordenação de arquivos."""
        # Criar arquivos com diferentes características
        import time
        
        files_data = [
            ("z_ultimo.xlsx", b"x" * 500),
            ("a_primeiro.xlsx", b"x" * 2000),
            ("m_meio.xlsx", b"x" * 1000),
            ("dados.csv", b"csv,data"),
            ("temp.tmp", b"temp"),
        ]
        
        created_files = []
        for filename, content in files_data:
            file_path = self._create_test_file(filename, content)
            created_files.append(file_path)
            time.sleep(0.1)  # Garantir diferentes timestamps
            
        # Descoberta
        discovered_files = self.scanner.scan_folder(str(self.subordinadas_dir))
        
        # Filtrar apenas Excel
        excel_files = [f for f in discovered_files if f.is_excel]
        self.assertEqual(len(excel_files), 3)
        
        # Verificar ordenação por nome
        excel_names = [Path(f.file_path).name for f in excel_files]
        expected_order = ["a_primeiro.xlsx", "m_meio.xlsx", "z_ultimo.xlsx"]
        self.assertEqual(excel_names, expected_order)
        
        # Verificar propriedades dos arquivos
        for excel_file in excel_files:
            self.assertTrue(excel_file.size > 0)
            self.assertIsNotNone(excel_file.modified_date)
            self.assertIn(excel_file.extension, ['.xlsx', '.xls'])
            
    def test_integration_with_logging(self):
        """Testa integração com sistema de logging."""
        # Criar arquivos para teste
        valid_file = self._create_test_file("valid.xlsx", b"x" * 1000)
        invalid_file = self._create_test_file("invalid.xlsx", b"")
        
        # Capturar logs
        import logging
        from io import StringIO
        
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        
        # Configurar logging para os componentes
        for component in [self.scanner, self.validator, self.analyzer]:
            component.logger.addHandler(handler)
            component.logger.setLevel(logging.DEBUG)
            
        try:
            # Executar operações
            discovered_files = self.scanner.scan_folder(str(self.subordinadas_dir))
            excel_files = [f for f in discovered_files if f.is_excel]
            
            with patch('openpyxl.load_workbook') as mock_load:
                mock_workbook = MagicMock()
                mock_workbook.sheetnames = ['Sheet1']
                mock_worksheet = MagicMock()
                mock_worksheet.max_row = 10
                mock_worksheet.max_column = 5
                mock_workbook.__getitem__.return_value = mock_worksheet
                mock_load.return_value = mock_workbook
                
                excel_paths = [f.file_path for f in excel_files]
                validation_results = self.validator.validate_multiple_files(excel_paths)
                
            # Verificar logs
            log_output = log_capture.getvalue()
            
            # Deve conter logs de descoberta
            self.assertIn("Escaneando diretório", log_output)
            self.assertIn("arquivos encontrados", log_output)
            
            # Deve conter logs de validação
            self.assertIn("Validando arquivo", log_output)
            
        finally:
            # Limpar handlers
            for component in [self.scanner, self.validator, self.analyzer]:
                component.logger.removeHandler(handler)


class TestComponentInteraction(unittest.TestCase):
    """Testes de interação entre componentes específicos."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Limpeza após os testes."""
        shutil.rmtree(self.temp_dir)
        
    def test_scanner_validator_data_flow(self):
        """Testa fluxo de dados entre scanner e validator."""
        # Criar arquivo
        file_path = Path(self.temp_dir) / "test.xlsx"
        file_path.write_bytes(b"x" * 1000)
        
        # Scanner
        scanner = SpreadsheetScanner()
        discovered_files = scanner.scan_folder(self.temp_dir)
        
        self.assertEqual(len(discovered_files), 1)
        
        # Extrair informações do scanner
        spreadsheet_info = discovered_files[0]
        self.assertIsInstance(spreadsheet_info, SpreadsheetInfo)
        
        # Usar informações no validator
        validator = SpreadsheetValidator()
        
        with patch('openpyxl.load_workbook') as mock_load:
            mock_workbook = MagicMock()
            mock_workbook.sheetnames = ['Sheet1']
            mock_worksheet = MagicMock()
            mock_worksheet.max_row = 10
            mock_worksheet.max_column = 5
            mock_workbook.__getitem__.return_value = mock_worksheet
            mock_load.return_value = mock_workbook
            
            validation_result = validator.validate_file(spreadsheet_info.file_path)
            
        # Verificar consistência dos dados
        self.assertEqual(validation_result.file_path, spreadsheet_info.file_path)
        self.assertTrue(validation_result.is_valid)
        
    def test_validator_analyzer_data_flow(self):
        """Testa fluxo de dados entre validator e analyzer."""
        # Criar arquivo
        file_path = Path(self.temp_dir) / "test.xlsx"
        file_path.write_bytes(b"x" * 1000)
        
        # Validator
        validator = SpreadsheetValidator()
        
        with patch('openpyxl.load_workbook') as mock_load:
            mock_workbook = MagicMock()
            mock_workbook.sheetnames = ['Sheet1', 'Sheet2']
            mock_worksheet = MagicMock()
            mock_worksheet.max_row = 10
            mock_worksheet.max_column = 5
            mock_workbook.__getitem__.return_value = mock_worksheet
            mock_load.return_value = mock_workbook
            
            validation_result = validator.validate_file(str(file_path))
            
        # Usar resultado da validação no analyzer
        if validation_result.is_valid:
            analyzer = SpreadsheetAnalyzer()
            
            with patch('openpyxl.load_workbook') as mock_load:
                # Mock mais detalhado para análise
                mock_workbook = MagicMock()
                mock_workbook.sheetnames = ['Sheet1', 'Sheet2']
                
                mock_ws = MagicMock()
                mock_ws.title = 'Sheet1'
                mock_ws.max_row = 10
                mock_ws.max_column = 5
                
                # Mock das células
                mock_cells = []
                for row in range(1, 4):
                    row_cells = []
                    for col in range(1, 4):
                        mock_cell = MagicMock()
                        mock_cell.value = f"Cell_{row}_{col}"
                        mock_cell.data_type = 's'
                        mock_cell.font = MagicMock()
                        mock_cell.font.bold = False
                        mock_cell.fill = MagicMock()
                        mock_cell.fill.start_color = MagicMock()
                        mock_cell.fill.start_color.rgb = "FFFFFF"
                        row_cells.append(mock_cell)
                    mock_cells.append(row_cells)
                
                mock_ws.iter_rows.return_value = mock_cells
                mock_workbook.__getitem__.return_value = mock_ws
                mock_workbook.__iter__.return_value = [mock_ws]
                mock_load.return_value = mock_workbook
                
                analysis_result = analyzer.analyze_spreadsheet(validation_result.file_path)
                
            # Verificar consistência
            self.assertEqual(analysis_result.file_path, validation_result.file_path)
            self.assertEqual(
                len(analysis_result.sheets), 
                validation_result.metadata['sheets_count']
            )


if __name__ == '__main__':
    unittest.main()