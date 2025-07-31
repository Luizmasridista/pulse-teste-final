"""Testes unitários para o módulo scanner.

Testa as funcionalidades de descoberta e escaneamento
de planilhas na pasta SUBORDINADAS.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from spreadsheet.scanner import SpreadsheetScanner, SpreadsheetInfo


class TestSpreadsheetInfo(unittest.TestCase):
    """Testes para a classe SpreadsheetInfo."""
    
    def test_init(self):
        """Testa inicialização da SpreadsheetInfo."""
        file_path = Path("/test/file.xlsx")
        size = 1024
        modified = datetime.now()
        extension = ".xlsx"
        
        info = SpreadsheetInfo(
            name="file.xlsx",
            path=file_path,
            size=size,
            modified_date=modified,
            extension=extension
        )
        
        self.assertEqual(info.path, file_path)
        self.assertEqual(info.size_bytes, size)
        self.assertEqual(info.last_modified, modified)
        self.assertEqual(info.extension, extension)
        self.assertEqual(info.name, "file.xlsx")
        
    def test_size_mb_property(self):
        """Testa propriedade size_mb."""
        info = SpreadsheetInfo(
            name="file.xlsx",
            path=Path("/test/file.xlsx"),
            size=2048000,
            modified_date=datetime.now(),
            extension=".xlsx"
        )
        self.assertAlmostEqual(info.size_mb, 1.95, places=2)
        
    def test_is_excel_property(self):
        """Testa propriedade is_excel."""
        xlsx_info = SpreadsheetInfo(
            name="file.xlsx",
            path=Path("/test/file.xlsx"),
            size=1024,
            modified_date=datetime.now(),
            extension=".xlsx"
        )
        xls_info = SpreadsheetInfo(
            name="file.xls",
            path=Path("/test/file.xls"),
            size=1024,
            modified_date=datetime.now(),
            extension=".xls"
        )
        csv_info = SpreadsheetInfo(
            name="file.csv",
            path=Path("/test/file.csv"),
            size=1024,
            modified_date=datetime.now(),
            extension=".csv"
        )
        
        self.assertTrue(xlsx_info.is_excel)
        self.assertTrue(xls_info.is_excel)
        self.assertFalse(csv_info.is_excel)
        
    def test_str_representation(self):
        """Testa representação string."""
        info = SpreadsheetInfo(
            name="file.xlsx",
            path=Path("/test/file.xlsx"),
            size=1024,
            modified_date=datetime.now(),
            extension=".xlsx"
        )
        str_repr = str(info)
        
        self.assertIn("file.xlsx", str_repr)
        self.assertIn("1.00 KB", str_repr)
        
    def test_repr_representation(self):
        """Testa representação repr."""
        info = SpreadsheetInfo(
            name="file.xlsx",
            path=Path("/test/file.xlsx"),
            size=1024,
            modified_date=datetime.now(),
            extension=".xlsx"
        )
        repr_str = repr(info)
        
        self.assertIn("SpreadsheetInfo", repr_str)
        self.assertIn("file.xlsx", repr_str)


class TestSpreadsheetScanner(unittest.TestCase):
    """Testes para a classe SpreadsheetScanner."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        self.scanner = SpreadsheetScanner()
        self.temp_dir = tempfile.mkdtemp()
        self.test_folder = Path(self.temp_dir) / "SUBORDINADAS"
        self.test_folder.mkdir()
        
    def tearDown(self):
        """Limpeza após os testes."""
        shutil.rmtree(self.temp_dir)
        
    def _create_test_file(self, name: str, content: str = None):
        """Cria arquivo de teste.
        
        Args:
            name: Nome do arquivo.
            content: Conteúdo do arquivo.
            
        Returns:
            Path: Caminho do arquivo criado.
        """
        if content is None:
            # Criar conteúdo de 2KB para passar na verificação de tamanho mínimo
            content = "x" * 2048
        
        file_path = self.test_folder / name
        file_path.write_text(content)
        return file_path
        
    def test_init(self):
        """Testa inicialização do scanner."""
        scanner = SpreadsheetScanner()
        self.assertIsNotNone(scanner.logger)
        
    def test_scan_folder_empty(self):
        """Testa escaneamento de pasta vazia."""
        result = self.scanner.scan_folder(str(self.test_folder))
        self.assertEqual(len(result), 0)
        
    def test_scan_folder_with_excel_files(self):
        """Testa escaneamento com arquivos Excel."""
        # Criar arquivos de teste
        self._create_test_file("test1.xlsx")
        self._create_test_file("test2.xls")
        self._create_test_file("test3.csv")  # Não deve ser incluído
        self._create_test_file("test4.txt")  # Não deve ser incluído
        
        result = self.scanner.scan_folder(str(self.test_folder))
        
        # Deve encontrar apenas os arquivos Excel
        self.assertEqual(len(result), 2)
        
        # Verificar nomes dos arquivos
        names = [info.name for info in result]
        self.assertIn("test1.xlsx", names)
        self.assertIn("test2.xls", names)
        self.assertNotIn("test3.csv", names)
        self.assertNotIn("test4.txt", names)
        
    def test_scan_folder_with_subdirectories(self):
        """Testa escaneamento com subdiretórios."""
        # Criar subdiretório
        subdir = self.test_folder / "subdir"
        subdir.mkdir()
        
        # Criar arquivos
        self._create_test_file("root.xlsx")
        (subdir / "sub.xlsx").write_text("test")
        
        result = self.scanner.scan_folder(str(self.test_folder))
        
        # Deve encontrar arquivos em subdiretórios também
        self.assertEqual(len(result), 2)
        
        names = [info.name for info in result]
        self.assertIn("root.xlsx", names)
        self.assertIn("sub.xlsx", names)
        
    def test_scan_folder_nonexistent(self):
        """Testa escaneamento de pasta inexistente."""
        from spreadsheet.scanner import FileException
        with self.assertRaises(FileException):
            self.scanner.scan_folder("/path/that/does/not/exist")
            
    def test_scan_folder_not_directory(self):
        """Testa escaneamento de arquivo ao invés de pasta."""
        from spreadsheet.scanner import FileException
        file_path = self._create_test_file("test.txt")
        
        with self.assertRaises(FileException):
            self.scanner.scan_folder(str(file_path))
            
    def test_is_excel_file(self):
        """Testa verificação de arquivo Excel."""
        self.assertTrue(self.scanner._is_excel_file("test.xlsx"))
        self.assertTrue(self.scanner._is_excel_file("test.xls"))
        self.assertTrue(self.scanner._is_excel_file("TEST.XLSX"))  # Case insensitive
        
        self.assertFalse(self.scanner._is_excel_file("test.csv"))
        self.assertFalse(self.scanner._is_excel_file("test.txt"))
        self.assertFalse(self.scanner._is_excel_file("test"))
        
    def test_get_file_info(self):
        """Testa obtenção de informações do arquivo."""
        file_path = self._create_test_file("test.xlsx", "test content")
        
        info = self.scanner._get_file_info(str(file_path))
        
        self.assertIsInstance(info, SpreadsheetInfo)
        self.assertEqual(info.name, "test.xlsx")
        self.assertEqual(info.extension, ".xlsx")
        self.assertGreater(info.size_bytes, 0)
        self.assertIsInstance(info.last_modified, datetime)
        
    def test_scan_folder_with_hidden_files(self):
        """Testa escaneamento ignorando arquivos ocultos."""
        # Criar arquivos normais e ocultos
        self._create_test_file("normal.xlsx")
        self._create_test_file(".hidden.xlsx")
        
        result = self.scanner.scan_folder(str(self.test_folder))
        
        # Deve encontrar apenas o arquivo normal
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "normal.xlsx")
        
    def test_scan_folder_with_temp_files(self):
        """Testa escaneamento ignorando arquivos temporários."""
        # Criar arquivos normais e temporários
        self._create_test_file("normal.xlsx")
        self._create_test_file("~temp.xlsx")
        self._create_test_file("temp~.xlsx")
        
        result = self.scanner.scan_folder(str(self.test_folder))
        
        # Deve encontrar apenas o arquivo normal
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "normal.xlsx")
        
    def test_scan_folder_large_number_of_files(self):
        """Testa escaneamento com muitos arquivos."""
        # Criar muitos arquivos
        for i in range(100):
            self._create_test_file(f"file_{i:03d}.xlsx")
            
        result = self.scanner.scan_folder(str(self.test_folder))
        
        self.assertEqual(len(result), 100)
        
        # Verificar se estão ordenados por nome
        names = [info.name for info in result]
        self.assertEqual(names, sorted(names))
        
    def test_scan_folder_with_permission_error(self):
        """Testa escaneamento com erro de permissão."""
        # Criar um arquivo de teste
        self._create_test_file("test.xlsx")
        
        # Usar mock para simular erro de permissão no método _analyze_file
        with patch.object(self.scanner, '_analyze_file', return_value=None) as mock_analyze:
            result = self.scanner.scan_folder(str(self.test_folder))
            
            # Verificar se o método foi chamado
            mock_analyze.assert_called()
            
            # Arquivo com erro deve ser ignorado
            self.assertEqual(len(result), 0)
        
    def test_scan_folder_with_unicode_names(self):
        """Testa escaneamento com nomes Unicode."""
        # Criar arquivos com nomes Unicode
        self._create_test_file("测试文件.xlsx")
        self._create_test_file("arquivo_português.xlsx")
        self._create_test_file("файл.xlsx")
        
        result = self.scanner.scan_folder(str(self.test_folder))
        
        self.assertEqual(len(result), 3)
        
        names = [info.name for info in result]
        self.assertIn("测试文件.xlsx", names)
        self.assertIn("arquivo_português.xlsx", names)
        self.assertIn("файл.xlsx", names)
        
    def test_scan_folder_return_type(self):
        """Testa tipo de retorno do escaneamento."""
        self._create_test_file("test.xlsx")
        
        result = self.scanner.scan_folder(str(self.test_folder))
        
        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], SpreadsheetInfo)
        
    def test_scan_folder_sorting(self):
        """Testa ordenação dos resultados."""
        # Criar arquivos em ordem não alfabética
        files = ["zebra.xlsx", "alpha.xlsx", "beta.xlsx"]
        for file in files:
            self._create_test_file(file)
            
        result = self.scanner.scan_folder(str(self.test_folder))
        
        # Verificar se estão ordenados alfabeticamente
        names = [info.name for info in result]
        expected = ["alpha.xlsx", "beta.xlsx", "zebra.xlsx"]
        self.assertEqual(names, expected)


class TestSpreadsheetScannerIntegration(unittest.TestCase):
    """Testes de integração para o SpreadsheetScanner."""
    
    def setUp(self):
        """Configuração inicial dos testes."""
        self.scanner = SpreadsheetScanner()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Limpeza após os testes."""
        shutil.rmtree(self.temp_dir)
        
    def test_real_world_scenario(self):
        """Testa cenário do mundo real."""
        # Criar estrutura de pastas realista
        subordinadas = Path(self.temp_dir) / "SUBORDINADAS"
        subordinadas.mkdir()
        
        # Criar subpastas
        (subordinadas / "2024").mkdir()
        (subordinadas / "2024" / "Janeiro").mkdir()
        (subordinadas / "2024" / "Fevereiro").mkdir()
        (subordinadas / "Backup").mkdir()
        
        # Criar arquivos diversos
        files_to_create = [
            "Vendas_Janeiro_2024.xlsx",
            "Relatório_Mensal.xls",
            "2024/Janeiro/Detalhado_Jan.xlsx",
            "2024/Fevereiro/Detalhado_Fev.xlsx",
            "Backup/Backup_Vendas.xlsx",
            "~temp_file.xlsx",  # Temporário - deve ser ignorado
            ".hidden_file.xlsx",  # Oculto - deve ser ignorado
            "documento.pdf",  # Não Excel - deve ser ignorado
            "planilha.csv",  # CSV - deve ser ignorado
        ]
        
        for file_path in files_to_create:
            full_path = subordinadas / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(f"Conteúdo de {file_path}")
            
        # Executar escaneamento
        result = self.scanner.scan_folder(str(subordinadas))
        
        # Verificar resultados
        self.assertEqual(len(result), 5)  # Apenas arquivos Excel válidos
        
        expected_files = [
            "Backup_Vendas.xlsx",
            "Detalhado_Fev.xlsx",
            "Detalhado_Jan.xlsx",
            "Relatório_Mensal.xls",
            "Vendas_Janeiro_2024.xlsx"
        ]
        
        actual_files = [info.name for info in result]
        self.assertEqual(sorted(actual_files), sorted(expected_files))
        
        # Verificar propriedades dos arquivos
        for info in result:
            self.assertTrue(info.is_excel)
            self.assertGreater(info.size_bytes, 0)
            self.assertIsInstance(info.last_modified, datetime)


if __name__ == '__main__':
    unittest.main()