"""Scanner de planilhas subordinadas.

Este módulo implementa a funcionalidade de descoberta e escaneamento
de planilhas subordinadas na pasta SUBORDINADAS.
"""

import os
import glob
import logging
from pathlib import Path
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from datetime import datetime

try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    from ..core import get_logger, config
    from ..core.exceptions import FileException
except ImportError:
    # Fallback para quando executado diretamente ou em testes
    def get_logger(name: str) -> logging.Logger:
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    class Config:
        def __init__(self):
            self.max_file_size = 100 * 1024 * 1024  # 100MB
            self.supported_extensions = ['.xlsx', '.xls']
            self.SUBORDINADAS_PATH = './SUBORDINADAS'
    
    config = Config()
    
    class FileException(Exception):
        """Exceção para erros relacionados a arquivos."""
        pass


@dataclass
class SpreadsheetInfo:
    """Informações sobre uma planilha encontrada."""
    name: str
    path: Path
    size: int
    modified_date: datetime
    extension: str
    is_valid: bool = False
    error_message: Optional[str] = None
    
    @property
    def size_bytes(self) -> int:
        """Retorna o tamanho em bytes."""
        return self.size
    
    @property
    def size_mb(self) -> float:
        """Retorna o tamanho em MB."""
        return self.size / (1024 * 1024)
    
    @property
    def is_excel(self) -> bool:
        """Verifica se é arquivo Excel."""
        return self.extension.lower() in {'.xlsx', '.xls'}
    
    @property
    def last_modified(self) -> datetime:
        """Alias para modified_date."""
        return self.modified_date
    
    @property
    def file_path(self) -> Path:
        """Alias para path."""
        return self.path
    
    def __str__(self) -> str:
        """Representação string."""
        size_str = f"{self.size_mb:.2f} MB" if self.size_mb >= 1 else f"{self.size / 1024:.2f} KB"
        return f"{self.name} ({size_str})"
    
    def __repr__(self) -> str:
        """Representação repr."""
        return f"SpreadsheetInfo(name='{self.name}', size={self.size}, extension='{self.extension}')"


class SpreadsheetScanner:
    """Scanner para descobrir planilhas subordinadas.
    
    Implementa o Passo 2 dos requisitos técnicos:
    - 2.1: Escanear pasta SUBORDINADAS
    - 2.2: Filtrar arquivos .xlsx/.xls
    """
    
    def __init__(self, subordinadas_path: Optional[str] = None):
        """Inicializa o scanner.
        
        Args:
            subordinadas_path: Caminho para a pasta SUBORDINADAS.
                              Se None, usa o configurado em config.
        """
        self.logger = get_logger(__name__)
        self.subordinadas_path = Path(subordinadas_path or config.SUBORDINADAS_PATH)
        self.supported_extensions = {'.xlsx', '.xls'}
        
    def scan_folder(self, folder_path: Optional[Union[str, Path]] = None) -> List[SpreadsheetInfo]:
        """Escaneia uma pasta em busca de planilhas.
        
        Args:
            folder_path: Caminho da pasta a ser escaneada. Se None, usa self.subordinadas_path.
        
        Returns:
            Lista de SpreadsheetInfo com as planilhas encontradas.
            
        Raises:
            FileException: Se a pasta não existir ou não for acessível.
        """
        target_path = Path(folder_path) if folder_path else self.subordinadas_path
        self.logger.info(f"Iniciando escaneamento da pasta: {target_path}")
        
        if not target_path.exists():
            raise FileException(f"Pasta não encontrada: {target_path}")
            
        if not target_path.is_dir():
            raise FileException(f"Caminho não é uma pasta: {target_path}")
            
        try:
            spreadsheets = []
            
            # Escanear todos os arquivos na pasta (recursivamente)
            for file_path in target_path.rglob('*'):
                if file_path.is_file():
                    spreadsheet_info = self._analyze_file(file_path)
                    if spreadsheet_info:
                        spreadsheets.append(spreadsheet_info)
                        
            self.logger.info(f"Escaneamento concluído. {len(spreadsheets)} planilhas encontradas.")
            return spreadsheets
            
        except PermissionError as e:
            raise FileException(f"Sem permissão para acessar a pasta: {e}")
        except Exception as e:
            raise FileException(f"Erro durante escaneamento: {e}")
    
    def _is_excel_file(self, filename: str) -> bool:
        """Verifica se o arquivo é uma planilha Excel suportada.
        
        Args:
            filename: Nome do arquivo.
            
        Returns:
            True se for arquivo Excel, False caso contrário.
        """
        return Path(filename).suffix.lower() in self.supported_extensions
    
    def _get_file_info(self, file_path: Union[str, Path]) -> SpreadsheetInfo:
        """Obtém informações de um arquivo.
        
        Args:
            file_path: Caminho do arquivo.
            
        Returns:
            SpreadsheetInfo com as informações do arquivo.
        """
        path = Path(file_path)
        stat = path.stat()
        
        return SpreadsheetInfo(
            name=path.name,
            path=path,
            size=stat.st_size,
            modified_date=datetime.fromtimestamp(stat.st_mtime),
            extension=path.suffix.lower()
        )
            
    def filter_spreadsheets(self, files: List[Path]) -> List[Path]:
        """Filtra apenas arquivos de planilha suportados.
        
        Args:
            files: Lista de caminhos de arquivos.
            
        Returns:
            Lista filtrada com apenas arquivos .xlsx/.xls.
        """
        filtered = []
        
        for file_path in files:
            if file_path.suffix.lower() in self.supported_extensions:
                filtered.append(file_path)
                self.logger.debug(f"Arquivo de planilha encontrado: {file_path.name}")
            else:
                self.logger.debug(f"Arquivo ignorado (extensão não suportada): {file_path.name}")
                
        return filtered
        
    def scan_with_pattern(self, pattern: str = "*.xlsx") -> List[SpreadsheetInfo]:
        """Escaneia usando padrão glob.
        
        Args:
            pattern: Padrão glob para busca (ex: '*.xlsx', '*.xls').
            
        Returns:
            Lista de SpreadsheetInfo encontradas.
        """
        self.logger.info(f"Escaneando com padrão: {pattern}")
        
        search_pattern = str(self.subordinadas_path / pattern)
        found_files = glob.glob(search_pattern)
        
        spreadsheets = []
        for file_path_str in found_files:
            file_path = Path(file_path_str)
            spreadsheet_info = self._analyze_file(file_path)
            if spreadsheet_info:
                spreadsheets.append(spreadsheet_info)
                
        return spreadsheets
        
    def get_all_spreadsheets(self) -> List[SpreadsheetInfo]:
        """Obtém todas as planilhas suportadas na pasta.
        
        Returns:
            Lista completa de planilhas .xlsx e .xls encontradas.
        """
        all_spreadsheets = []
        
        # Buscar por cada extensão suportada
        for ext in self.supported_extensions:
            pattern = f"*{ext}"
            spreadsheets = self.scan_with_pattern(pattern)
            all_spreadsheets.extend(spreadsheets)
            
        # Remover duplicatas (caso existam)
        unique_spreadsheets = []
        seen_paths = set()
        
        for spreadsheet in all_spreadsheets:
            if spreadsheet.path not in seen_paths:
                unique_spreadsheets.append(spreadsheet)
                seen_paths.add(spreadsheet.path)
                
        self.logger.info(f"Total de planilhas únicas encontradas: {len(unique_spreadsheets)}")
        return unique_spreadsheets
        
    def _analyze_file(self, file_path: Path) -> Optional[SpreadsheetInfo]:
        """Analisa um arquivo e cria SpreadsheetInfo.
        
        Args:
            file_path: Caminho do arquivo a ser analisado.
            
        Returns:
            SpreadsheetInfo se for um arquivo de planilha válido, None caso contrário.
        """
        try:
            # Ignorar arquivos ocultos (que começam com ponto)
            if file_path.name.startswith('.'):
                return None
                
            # Ignorar arquivos temporários (que começam ou terminam com ~)
            name_without_ext = file_path.stem  # Nome sem extensão
            if file_path.name.startswith('~') or name_without_ext.endswith('~'):
                return None
                
            # Verificar se é um arquivo de planilha suportado
            if file_path.suffix.lower() not in self.supported_extensions:
                return None
                
            # Obter informações do arquivo
            stat = file_path.stat()
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            
            spreadsheet_info = SpreadsheetInfo(
                name=file_path.name,
                path=file_path,
                size=stat.st_size,
                modified_date=modified_time,
                extension=file_path.suffix.lower(),
                is_valid=True  # Assumir válido por padrão, validação detalhada pode ser feita depois
            )
            
            self.logger.debug(f"Arquivo analisado: {spreadsheet_info.name} ({spreadsheet_info.size} bytes)")
            return spreadsheet_info
            
        except Exception as e:
            self.logger.warning(f"Erro ao analisar arquivo {file_path}: {e}")
            return None
            
    def get_statistics(self) -> Dict[str, int]:
        """Obtém estatísticas do escaneamento.
        
        Returns:
            Dicionário com estatísticas dos arquivos encontrados.
        """
        spreadsheets = self.get_all_spreadsheets()
        
        stats = {
            'total_files': len(spreadsheets),
            'xlsx_files': len([s for s in spreadsheets if s.extension == '.xlsx']),
            'xls_files': len([s for s in spreadsheets if s.extension == '.xls']),
            'total_size': sum(s.size for s in spreadsheets),
            'valid_files': len([s for s in spreadsheets if s.is_valid])
        }
        
        return stats