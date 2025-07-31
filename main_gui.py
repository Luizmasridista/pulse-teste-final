#!/usr/bin/env python3
"""Script principal para executar a interface gráfica do Pulse.

Este script inicializa e executa a aplicação desktop
com interface Tkinter para consolidação de planilhas.
"""

import sys
import os
from pathlib import Path

# Adicionar src ao path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    from gui.main_window import MainWindow
    from core import setup_logging, get_logger
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    print("Certifique-se de que todas as dependências estão instaladas.")
    sys.exit(1)


def main():
    """Função principal."""
    try:
        # Configurar logging
        setup_logging()
        logger = get_logger(__name__)
        
        logger.info("=" * 50)
        logger.info("INICIANDO PULSE - CONSOLIDADOR DE PLANILHAS")
        logger.info("=" * 50)
        
        # Verificar dependências
        try:
            import tkinter
            import openpyxl
            import pandas
        except ImportError as e:
            logger.error(f"Dependência não encontrada: {e}")
            print(f"Erro: Dependência não encontrada - {e}")
            print("\nInstale as dependências com:")
            print("pip install openpyxl pandas")
            return 1
            
        # Criar e executar aplicação
        logger.info("Criando janela principal...")
        app = MainWindow()
        
        logger.info("Iniciando interface gráfica...")
        app.run()
        
        logger.info("Aplicação encerrada normalmente")
        return 0
        
    except KeyboardInterrupt:
        print("\nAplicação interrompida pelo usuário")
        return 0
        
    except Exception as e:
        print(f"Erro fatal: {e}")
        if 'logger' in locals():
            logger.error(f"Erro fatal na aplicação: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())