"""Testes unitários para o módulo validator.

Testa as funcionalidades de validação de integridade
e verificação de planilhas vazias.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from spreadsheet.validator import (
    SpreadsheetValidator, SpreadsheetValidationResult, ValidationStatus
)


class TestValidationStatus(unittest.TestCase):
    """Testes para o enum ValidationStatus."""
    
    def test_validation_status_values(self):
        """Testa valores do enum ValidationStatus."""
        self.assertEqual(ValidationStatus.VALID.value, "valid")
        self.assertEqual(ValidationStatus.INVALID.value, "invalid")
        self.assertEqual(ValidationStatus.ERROR.value, "error")
        
    def test_validation_status_comparison(self):
        """Testa comparação de status."""
        self.assertEqual(ValidationStatus.VALID, ValidationStatus.VALID)
        self.assertNotEqual(ValidationStatus.VALID, ValidationStatus.INVALID)


class TestSpreadsheetValidationResult(unittest.TestCase):
    """Testes para a classe SpreadsheetValidationResult."""
    
    def test_init_valid(self):
        """Testa inicialização com resultado válido."""
        result = SpreadsheetValidationResult(
            file_path="/test/file.xlsx",
            status=ValidationStatus.VALID,
            errors=[],
            warnings=[],
            metadata={"sheets": 3}
        )
        
        self.assertEqual(result.file_path, "/test/file.xlsx")
        self.assertEqual(result.status, ValidationStatus.VALID)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.warnings), 0)
        self.assertEqual(result.metadata["sheets"], 3)
        
    def test_init_invalid(self):
        """Testa inicialização com resultado inválido."""
        errors = ["Arquivo vazio", "Formato inválido"]
        warnings = ["Planilha muito grande"]
        
        result = SpreadsheetValidationResult(
            file_path="/test/file.xlsx",
            status=ValidationStatus.INVALID,
            errors=errors,
            warnings=warnings
        )
        
        self.assertEqual(result.status, ValidationStatus.INVALID)
        self.assertEqual(len(result.errors), 2)
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("Arquivo vazio", result.errors)
        self.assertIn("Planilha muito grande", result.warnings)
        
    def test_is_valid_property(self):
        """Testa propriedade is_valid."""
        valid_result = SpreadsheetValidationResult(
            "/test/file.xlsx", ValidationStatus.VALID, [], []
        )
        invalid_result = SpreadsheetValidationResult(
            "/test/file.xlsx", ValidationStatus.INVALID, ["erro"], []
        )
        error_result = SpreadsheetValidationResult(
            "/test/file.xlsx", ValidationStatus.ERROR, ["erro"], []
        )
        
        self.assertTrue(valid_result.is_valid)
        self.assertFalse(invalid_result.is_valid)
        self.assertFalse(error_result.is_valid)
        
    def test_has_errors_property(self):
        """Testa propriedade has_errors."""
        no_errors = SpreadsheetValidationResult(
            "/test/file.xlsx", ValidationStatus.VALID, [], []
        )
        with_errors = SpreadsheetValidationResult(
            "/test/file.xlsx", ValidationStatus.INVALID, ["erro"], []
        )
        
        self.assertFalse(no_errors.has_errors)
        self.assertTrue(with_errors.has_errors)
        
    def test_has_warnings_property(self):
        """Testa propriedade has_warnings."""
        no_warnings = SpreadsheetValidationResult(
            "/test/file.xlsx", ValidationStatus.VALID, [], []
        )
        with_warnings = SpreadsheetValidationResult(
            "/test/file.xlsx", ValidationStatus.VALID, [], ["aviso"]
        )
        
        self.assertFalse(no_warnings.has_warnings)
        self.assertTrue(with_warnings.has_warnings)
        
    def test_str_representation(self):
        """Testa representação string."""
        result = SpreadsheetValidationResult(
            "/test/file.xlsx", ValidationStatus.VALID, [], []
        )
        str_repr = str(result)
        
        self.assertIn("file.xlsx", str_repr)
        self.assertIn("VALID", str_repr)
        
    def test_repr_representation(self):
        """Testa representação repr."""
        result = SpreadsheetValidationResult(
            "/test/file.xlsx", ValidationStatus.VALID, [], []
        )
        repr_str = repr(result)
        
        self.assertIn("SpreadsheetValidationResult", repr_str)
        self.assertIn("file.xlsx", repr_str)


class TestSpreadsheetValidator(unittest.TestCase):
    """Testes para a classe SpreadsheetValidator."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        self.validator = SpreadsheetValidator()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Limpeza após os testes."""
        shutil.rmtree(self.temp_dir)
        
    def _create_test_file(self, name: str, content: bytes = b"test"):
        """Cria arquivo de teste.
        
        Args:
            name: Nome do arquivo.
            content: Conteúdo do arquivo em bytes.
            
        Returns:
            Path: Caminho do arquivo criado.
        """
        file_path = Path(self.temp_dir) / name
        file_path.write_bytes(content)
        return file_path
        
    def test_init(self):
        """Testa inicialização do validator."""
        validator = SpreadsheetValidator()
        self.assertIsNotNone(validator.logger)
        
    def test_validate_file_not_exists(self):
        """Testa validação de arquivo inexistente."""
        result = self.validator.validate_file("/path/that/does/not/exist.xlsx")
        
        self.assertEqual(result.status, ValidationStatus.ERROR)
        self.assertTrue(result.has_errors)
        self.assertIn("não encontrado", result.errors[0].lower())
        
    def test_validate_file_empty(self):
        """Testa validação de arquivo vazio."""
        file_path = self._create_test_file("empty.xlsx", b"")
        
        result = self.validator.validate_file(str(file_path))
        
        self.assertEqual(result.status, ValidationStatus.INVALID)
        self.assertTrue(result.has_errors)
        self.assertIn("vazio", result.errors[0].lower())
        
    def test_validate_file_too_small(self):
        """Testa validação de arquivo muito pequeno."""
        file_path = self._create_test_file("small.xlsx", b"x" * 10)  # 10 bytes
        
        result = self.validator.validate_file(str(file_path))
        
        self.assertEqual(result.status, ValidationStatus.INVALID)
        self.assertTrue(result.has_errors)
        self.assertIn("pequeno", result.errors[0].lower())
        
    def test_validate_file_wrong_extension(self):
        """Testa validação de arquivo com extensão incorreta."""
        file_path = self._create_test_file("test.txt", b"x" * 2048)  # 2KB
        
        result = self.validator.validate_file(str(file_path))
        
        self.assertEqual(result.status, ValidationStatus.INVALID)
        self.assertTrue(result.has_errors)
        self.assertIn("extensão", result.errors[0].lower())
        
    @patch('openpyxl.load_workbook')
    def test_validate_file_valid_xlsx(self, mock_load_workbook):
        """Testa validação de arquivo XLSX válido."""
        # Mock do workbook
        mock_workbook = MagicMock()
        mock_workbook.sheetnames = ['Sheet1', 'Sheet2']
        
        # Mock da worksheet
        mock_worksheet = MagicMock()
        mock_worksheet.max_row = 10
        mock_worksheet.max_column = 5
        mock_workbook.__getitem__.return_value = mock_worksheet
        
        mock_load_workbook.return_value = mock_workbook
        
        file_path = self._create_test_file("valid.xlsx", b"x" * 2048)  # 2KB
        
        result = self.validator.validate_file(str(file_path))
        
        self.assertEqual(result.status, ValidationStatus.VALID)
        self.assertFalse(result.has_errors)
        self.assertEqual(result.metadata['sheets_count'], 2)
        self.assertEqual(result.metadata['total_rows'], 20)  # 2 sheets * 10 rows
        
    @patch('xlrd.open_workbook')
    def test_validate_file_valid_xls(self, mock_open_workbook):
        """Testa validação de arquivo XLS válido."""
        # Mock do workbook
        mock_workbook = MagicMock()
        mock_workbook.nsheets = 2
        mock_workbook.sheet_names.return_value = ['Sheet1', 'Sheet2']
        
        # Mock da worksheet
        mock_sheet = MagicMock()
        mock_sheet.nrows = 10
        mock_sheet.ncols = 5
        mock_workbook.sheet_by_index.return_value = mock_sheet
        
        mock_open_workbook.return_value = mock_workbook
        
        file_path = self._create_test_file("valid.xls", b"x" * 2048)  # 2KB
        
        result = self.validator.validate_file(str(file_path))
        
        self.assertEqual(result.status, ValidationStatus.VALID)
        self.assertFalse(result.has_errors)
        self.assertEqual(result.metadata['sheets_count'], 2)
        
    @patch('openpyxl.load_workbook')
    def test_validate_file_empty_sheets(self, mock_load_workbook):
        """Testa validação de arquivo com planilhas vazias."""
        # Mock do workbook com planilhas vazias
        mock_workbook = MagicMock()
        mock_workbook.sheetnames = ['Sheet1']
        
        # Mock da worksheet vazia
        mock_worksheet = MagicMock()
        mock_worksheet.max_row = 1  # Apenas cabeçalho
        mock_worksheet.max_column = 1
        mock_workbook.__getitem__.return_value = mock_worksheet
        
        mock_load_workbook.return_value = mock_workbook
        
        file_path = self._create_test_file("empty_sheets.xlsx", b"x" * 2048)  # 2KB
        
        result = self.validator.validate_file(str(file_path))
        
        self.assertEqual(result.status, ValidationStatus.INVALID)
        self.assertTrue(result.has_errors)
        self.assertIn("vazia", result.errors[0].lower())
        
    @patch('openpyxl.load_workbook')
    def test_validate_file_corrupted(self, mock_load_workbook):
        """Testa validação de arquivo corrompido."""
        mock_load_workbook.side_effect = Exception("Arquivo corrompido")
        
        file_path = self._create_test_file("corrupted.xlsx", b"x" * 2048)  # 2KB
        
        result = self.validator.validate_file(str(file_path))
        
        self.assertEqual(result.status, ValidationStatus.ERROR)
        self.assertTrue(result.has_errors)
        self.assertIn("erro", result.errors[0].lower())
        
    @patch('openpyxl.load_workbook')
    def test_validate_file_large_file_warning(self, mock_load_workbook):
        """Testa validação de arquivo grande com aviso."""
        # Mock do workbook
        mock_workbook = MagicMock()
        mock_workbook.sheetnames = ['Sheet1']
        
        # Mock da worksheet
        mock_worksheet = MagicMock()
        mock_worksheet.max_row = 10
        mock_worksheet.max_column = 5
        mock_workbook.__getitem__.return_value = mock_worksheet
        
        mock_load_workbook.return_value = mock_workbook
        
        # Criar arquivo grande (> 50MB)
        large_content = b"x" * (60 * 1024 * 1024)  # 60MB
        file_path = self._create_test_file("large.xlsx", large_content)
        
        result = self.validator.validate_file(str(file_path))
        
        self.assertEqual(result.status, ValidationStatus.VALID)
        self.assertTrue(result.has_warnings)
        self.assertIn("grande", result.warnings[0].lower())
        
    def test_validate_multiple_files_empty_list(self):
        """Testa validação de lista vazia."""
        results = self.validator.validate_multiple_files([])
        self.assertEqual(len(results), 0)
        
    def test_validate_multiple_files_mixed(self):
        """Testa validação de múltiplos arquivos com resultados mistos."""
        # Criar arquivos de teste
        valid_file = self._create_test_file("valid.xlsx", b"x" * 2048)  # 2KB
        invalid_file = self._create_test_file("invalid.txt", b"x" * 2048)  # 2KB
        nonexistent_file = "/path/that/does/not/exist.xlsx"
        
        files = [str(valid_file), str(invalid_file), nonexistent_file]
        
        with patch('openpyxl.load_workbook') as mock_load:
            # Mock para arquivo válido
            mock_workbook = MagicMock()
            mock_workbook.sheetnames = ['Sheet1']
            mock_worksheet = MagicMock()
            mock_worksheet.max_row = 10
            mock_worksheet.max_column = 5
            mock_workbook.__getitem__.return_value = mock_worksheet
            mock_load.return_value = mock_workbook
            
            results = self.validator.validate_multiple_files(files)
            
        self.assertEqual(len(results), 3)
        
        # Verificar resultados
        valid_result = results[str(valid_file)]
        invalid_result = results[str(invalid_file)]
        error_result = results[nonexistent_file]
        
        self.assertEqual(valid_result.status, ValidationStatus.VALID)
        self.assertEqual(invalid_result.status, ValidationStatus.INVALID)
        self.assertEqual(error_result.status, ValidationStatus.ERROR)
        
    def test_is_excel_file(self):
        """Testa verificação de arquivo Excel."""
        self.assertTrue(self.validator._is_excel_file("test.xlsx"))
        self.assertTrue(self.validator._is_excel_file("test.xls"))
        self.assertTrue(self.validator._is_excel_file("TEST.XLSX"))  # Case insensitive
        
        self.assertFalse(self.validator._is_excel_file("test.csv"))
        self.assertFalse(self.validator._is_excel_file("test.txt"))
        self.assertFalse(self.validator._is_excel_file("test"))
        
    @patch('openpyxl.load_workbook')
    def test_validate_xlsx_file_success(self, mock_load_workbook):
        """Testa validação bem-sucedida de arquivo XLSX."""
        # Mock do workbook
        mock_workbook = MagicMock()
        mock_workbook.sheetnames = ['Sheet1', 'Sheet2', 'Sheet3']
        
        # Mock das worksheets
        mock_worksheet1 = MagicMock()
        mock_worksheet1.max_row = 100
        mock_worksheet1.max_column = 10
        
        mock_worksheet2 = MagicMock()
        mock_worksheet2.max_row = 50
        mock_worksheet2.max_column = 8
        
        mock_worksheet3 = MagicMock()
        mock_worksheet3.max_row = 25
        mock_worksheet3.max_column = 5
        
        mock_workbook.__getitem__.side_effect = [
            mock_worksheet1, mock_worksheet2, mock_worksheet3
        ]
        
        mock_load_workbook.return_value = mock_workbook
        
        file_path = self._create_test_file("test.xlsx", b"x" * 2048)  # 2KB
        
        result = self.validator._validate_xlsx_file(str(file_path))
        
        self.assertEqual(result.status, ValidationStatus.VALID)
        self.assertEqual(result.metadata['sheets_count'], 3)
        self.assertEqual(result.metadata['total_rows'], 175)  # 100 + 50 + 25
        self.assertEqual(result.metadata['total_columns'], 23)  # 10 + 8 + 5
        
    @patch('xlrd.open_workbook')
    def test_validate_xls_file_success(self, mock_open_workbook):
        """Testa validação bem-sucedida de arquivo XLS."""
        # Mock do workbook
        mock_workbook = MagicMock()
        mock_workbook.nsheets = 2
        mock_workbook.sheet_names.return_value = ['Sheet1', 'Sheet2']
        
        # Mock das sheets
        mock_sheet1 = MagicMock()
        mock_sheet1.nrows = 100
        mock_sheet1.ncols = 10
        
        mock_sheet2 = MagicMock()
        mock_sheet2.nrows = 50
        mock_sheet2.ncols = 8
        
        mock_workbook.sheet_by_index.side_effect = [mock_sheet1, mock_sheet2]
        
        mock_open_workbook.return_value = mock_workbook
        
        file_path = self._create_test_file("test.xls", b"x" * 2048)  # 2KB
        
        result = self.validator._validate_xls_file(str(file_path))
        
        self.assertEqual(result.status, ValidationStatus.VALID)
        self.assertEqual(result.metadata['sheets_count'], 2)
        self.assertEqual(result.metadata['total_rows'], 150)  # 100 + 50
        self.assertEqual(result.metadata['total_columns'], 18)  # 10 + 8
        
    def test_check_file_size_valid(self):
        """Testa verificação de tamanho válido."""
        file_path = self._create_test_file("test.xlsx", b"x" * 2048)  # 2KB
        
        errors, warnings = self.validator._check_file_size(str(file_path))
        
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(warnings), 0)
        
    def test_check_file_size_empty(self):
        """Testa verificação de arquivo vazio."""
        file_path = self._create_test_file("empty.xlsx", b"")
        
        errors, warnings = self.validator._check_file_size(str(file_path))
        
        self.assertEqual(len(errors), 1)
        self.assertIn("vazio", errors[0].lower())
        
    def test_check_file_size_too_small(self):
        """Testa verificação de arquivo muito pequeno."""
        file_path = self._create_test_file("small.xlsx", b"x" * 10)
        
        errors, warnings = self.validator._check_file_size(str(file_path))
        
        self.assertEqual(len(errors), 1)
        self.assertIn("pequeno", errors[0].lower())
        
    def test_check_file_size_large_warning(self):
        """Testa verificação de arquivo grande com aviso."""
        # Criar arquivo grande (> 50MB)
        large_content = b"x" * (60 * 1024 * 1024)  # 60MB
        file_path = self._create_test_file("large.xlsx", large_content)
        
        errors, warnings = self.validator._check_file_size(str(file_path))
        
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(warnings), 1)
        self.assertIn("grande", warnings[0].lower())


class TestSpreadsheetValidatorIntegration(unittest.TestCase):
    """Testes de integração para o SpreadsheetValidator."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        self.validator = SpreadsheetValidator()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Limpeza após os testes."""
        shutil.rmtree(self.temp_dir)
        
    def test_real_world_validation_scenario(self):
        """Testa cenário de validação do mundo real."""
        # Criar arquivos diversos para teste
        files_to_test = [
            ("valid_large.xlsx", b"x" * 2000, ValidationStatus.VALID),
            ("empty_file.xlsx", b"", ValidationStatus.INVALID),
            ("too_small.xlsx", b"x" * 10, ValidationStatus.INVALID),
            ("wrong_extension.txt", b"x" * 2048, ValidationStatus.INVALID),  # 2KB
        ]
        
        created_files = []
        for filename, content, expected_status in files_to_test:
            file_path = Path(self.temp_dir) / filename
            file_path.write_bytes(content)
            created_files.append((str(file_path), expected_status))
            
        # Adicionar arquivo inexistente
        created_files.append(("/nonexistent/file.xlsx", ValidationStatus.ERROR))
        
        # Mock para arquivos válidos
        with patch('openpyxl.load_workbook') as mock_load:
            mock_workbook = MagicMock()
            mock_workbook.sheetnames = ['Sheet1']
            mock_worksheet = MagicMock()
            mock_worksheet.max_row = 10
            mock_worksheet.max_column = 5
            mock_workbook.__getitem__.return_value = mock_worksheet
            mock_load.return_value = mock_workbook
            
            # Validar múltiplos arquivos
            file_paths = [file_path for file_path, _ in created_files]
            results = self.validator.validate_multiple_files(file_paths)
            
        # Verificar resultados
        self.assertEqual(len(results), len(created_files))
        
        for file_path, expected_status in created_files:
            result = results[file_path]
            self.assertEqual(result.status, expected_status)
            
            if expected_status == ValidationStatus.VALID:
                self.assertFalse(result.has_errors)
            else:
                self.assertTrue(result.has_errors or result.status == ValidationStatus.ERROR)


if __name__ == '__main__':
    unittest.main()