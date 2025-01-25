# utils/helper.py

import time
import os
import msvcrt
from datetime import datetime


class Utils:
    """
    Classe de utilitários para tarefas comuns.
    """

    @staticmethod
    def calculate_age(birth_date: str) -> str:
        """
        Calcula a idade a partir de uma string de data de nascimento (dd/mm/yyyy).

        Parameters
        ----------
        birth_date : str
            Data de nascimento em formato dd/mm/yyyy.

        Returns
        -------
        str
            Idade calculada ou 'Não Informado' em caso de erro.
        """
        try:
            today = datetime.today()
            birthday = datetime.strptime(birth_date, '%d/%m/%Y')
            age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
            return str(age)
        except ValueError:
            return "Não Informado"

    @staticmethod
    def input_with_timeout(prompt: str, timeout: int) -> str:
        """
        Captura a entrada do usuário com timeout definido.

        Parameters
        ----------
        prompt : str
            Mensagem de prompt para o usuário.
        timeout : int
            Tempo máximo de espera (em segundos).

        Returns
        -------
        str
            Entrada do usuário.
        """
        print(prompt, end='', flush=True)
        end_time = time.time() + timeout
        input_str = ''
        while time.time() < end_time:
            if msvcrt.kbhit():
                char = msvcrt.getch()
                if char == b'\r':
                    break
                elif char == b'\b':
                    input_str = input_str[:-1]
                    print('\b \b', end='', flush=True)
                else:
                    input_str += char.decode('utf-8')
                    print(char.decode('utf-8'), end='', flush=True)
            time.sleep(0.1)
        print()  # Quebra de linha depois da entrada
        return input_str

    @staticmethod
    def countdown_timer(seconds: int) -> None:
        """
        Contagem regressiva que limpa a tela a cada segundo.

        Parameters
        ----------
        seconds : int
            Número de segundos para contar.
        """
        for i in range(seconds, 0, -1):
            print(i)
            time.sleep(1)
            os.system('cls' if os.name == 'nt' else 'clear')
