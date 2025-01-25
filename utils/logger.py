# logger.py

import logging
import traceback
import os

class Logger:
    """
    Classe Logger para manipular logs do projeto.
    """

    @staticmethod
    def capture_error(error: Exception) -> None:
        """
        Registra um erro com traceback no arquivo 'error_log.log'.
        """
        logger = logging.getLogger('my_project_logger')
        logger.setLevel(logging.ERROR)

        handler = logging.FileHandler('error_log.log', encoding='utf-8')
        handler.setLevel(logging.ERROR)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # Evita múltiplos handlers duplicados
        if not logger.handlers:
            logger.addHandler(handler)

        error_message = f'Ocorreu um erro: {str(error)}'
        traceback_message = traceback.format_exc()
        logger.error(f'{error_message}\nTraceback:\n{traceback_message}')

        # Remove o handler para não duplicar em cada chamada
        logger.removeHandler(handler)

    @staticmethod
    def get_logger(level=logging.INFO) -> logging.Logger:
        """
        Retorna um logger configurado com um dado nível (INFO por padrão).
        """
        logger = logging.getLogger('my_project_logger_base')
        logger.setLevel(level)

        # Verifica se já existem handlers para evitar duplicados
        if not logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        return logger
