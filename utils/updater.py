"""
Módulo responsável por checar atualizações do aplicativo e aplicar o update caso necessário.

Dependências:
- requests (para realizar o download e checar a versão)
- packaging (comparar versões)
- tkinter (exibir diálogo para o usuário confirmar a atualização)
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox

import requests
from packaging import version
from urllib.parse import urljoin

from utils.logger import Logger


###############################################################################
#                             CONSTANTES                                      #
###############################################################################

# URL base onde o executável e o arquivo de versão mais recente estão disponíveis.
UPDATE_URL = 'https://github.com/A-Assuncao/brumatti-s-intel/releases/latest/download/'

# Nome do arquivo que contém a versão mais recente (texto simples).
VERSION_FILE = 'latest_version.txt'


###############################################################################
#                        FUNÇÕES AUXILIARES DE UPDATE                         #
###############################################################################

def get_latest_version() -> str:
    """
    Obtém a versão mais recente disponível no servidor.

    Returns
    -------
    str
        Versão mais recente (ex: '0.0.2'), ou None em caso de falha.
    """
    try:
        response = requests.get(urljoin(UPDATE_URL, VERSION_FILE), timeout=10)
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException as e:
        Logger.capture_error(e)
        return None


def download_update(latest_version: str, target_path: str) -> bool:
    """
    Faz o download do executável de atualização para o caminho especificado.

    Parameters
    ----------
    latest_version : str
        Versão mais recente (ex: '0.0.2').
    target_path : str
        Caminho onde o arquivo será salvo (ex: 'canaime-preso-por-ala-0.0.2.exe').

    Returns
    -------
    bool
        True se o download for bem-sucedido, False em caso de erro.
    """
    try:
        download_url = urljoin(UPDATE_URL, f"canaime-preso-por-ala-{latest_version}.exe")
        response = requests.get(download_url, stream=True, timeout=20)
        response.raise_for_status()
        with open(target_path, 'wb') as out_file:
            for chunk in response.iter_content(chunk_size=8192):
                out_file.write(chunk)
        return True
    except requests.RequestException as e:
        Logger.capture_error(e)
        return False


def prompt_user_for_update(latest_version: str) -> bool:
    """
    Exibe uma caixa de diálogo ao usuário perguntando se deseja atualizar.

    Parameters
    ----------
    latest_version : str
        Versão mais recente disponível.

    Returns
    -------
    bool
        True se o usuário aceitar, False se recusar.
    """
    root = tk.Tk()
    root.withdraw()  # Oculta a janela principal
    result = messagebox.askyesno(
        "Atualização disponível",
        f"Uma nova versão ({latest_version}) está disponível. Deseja atualizar?"
    )
    root.destroy()
    return result


def check_and_update(current_version: str) -> bool:
    """
    Verifica se há atualização mais recente e, se houver,
    pergunta ao usuário se deseja aplicar a atualização.

    Caso o usuário aceite, o novo executável é baixado e
    o processo atual é encerrado após iniciar o executável atualizado.

    Parameters
    ----------
    current_version : str
        Versão atual do aplicativo (ex: '0.0.1').

    Returns
    -------
    bool
        True se a atualização foi iniciada/aplicada,
        False se não houve atualização ou se o usuário recusou.
    """
    # 1. Obter a versão mais recente
    latest_version = get_latest_version()
    if not latest_version:
        print("Não foi possível verificar atualizações.")
        Logger.get_logger().warning("Falha ao verificar atualizações.")
        return False

    # 2. Comparar com a versão atual
    if version.parse(latest_version) <= version.parse(current_version):
        print("Nenhuma atualização disponível.")
        return False

    print(f"Nova versão disponível: {latest_version}.")
    user_wants_update = prompt_user_for_update(latest_version)
    if not user_wants_update:
        print("Atualização recusada pelo usuário.")
        return False

    # 3. Baixar o executável para a pasta atual
    update_path = os.path.join(os.getcwd(), f'canaime-preso-por-ala-{latest_version}.exe')
    if download_update(latest_version, update_path):
        print(f"Atualização baixada em: {update_path}")
        Logger.get_logger().info(f"Atualização baixada: {update_path}")

        # 4. Iniciar o novo executável e encerrar o processo atual
        try:
            subprocess.Popen(update_path, shell=True)
            sys.exit(0)
        except Exception as e:
            Logger.capture_error(e)
            print("Erro ao tentar iniciar a nova versão.")
            return False
    else:
        print("Falha ao baixar a atualização.")
        Logger.get_logger().error("Falha no download da atualização.")
        return False

    return True
