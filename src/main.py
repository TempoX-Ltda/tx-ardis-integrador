import logging
import os
import sys
import threading
import time
from argparse import Namespace
from logging.handlers import RotatingFileHandler

from src.arguments import parse_args
from src.subcommands.apontar_plano_de_corte import apontar_plano_de_corte_subcommand
from src.subcommands.nova_ordem import nova_ordem_subcommand
from src.subcommands.novo_plano_de_corte import novo_plano_de_corte_subcommand

if os.name == "nt":  # Verifica se o sistema operacional é Windows
    import ctypes

    import win32con
    import win32gui

    def set_console_active():
        # Obtém o identificador da janela do console atual
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            # Garante que a janela esteja visível
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            # Coloca a janela em primeiro plano
            win32gui.SetForegroundWindow(hwnd)


def setup_logger(parsed_args: Namespace):
    log_file = parsed_args.log_file
    log_dir = os.path.dirname(log_file)

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    formatter = logging.Formatter(
        "%(asctime)s,%(msecs)d | %(name)s | %(levelname)s | %(message)s"
    )

    logger = logging.getLogger("src")
    logger.setLevel(logging.DEBUG)

    file_log_handler = RotatingFileHandler(
        log_file, maxBytes=100 * 1024 * 1024, backupCount=2
    )
    file_log_handler.setLevel(logging.DEBUG)
    file_log_handler.setFormatter(formatter)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(formatter)

    logger.addHandler(file_log_handler)
    logger.addHandler(stdout_handler)

    return logger


def main(parsed_args: Namespace):
    if parsed_args.subcommand == "novo-plano-de-corte":
        novo_plano_de_corte_subcommand(parsed_args)
        return

    elif parsed_args.subcommand == "nova-ordem":
        nova_ordem_subcommand(parsed_args)
        return

    elif parsed_args.subcommand == "apontar-plano-de-corte":
        apontar_plano_de_corte_subcommand(parsed_args)
        return

    # Subcomando não implementado
    raise NotImplementedError(f"Subcomando {parsed_args.subcommands} não implementado")


if __name__ == "__main__":
    parsed_args = parse_args()

    logger = setup_logger(parsed_args)

    logger.debug("ParsedArgs: %s", parsed_args)

    try:
        main(parsed_args=parsed_args)
    except Exception:
        logger.exception("")

        if os.name == "nt":  # Torna a janela do console ativa se estiver no Windows
            try:
                set_console_active()
            except Exception as exc:
                logger.error("Erro ao ativar janela do console: %s", exc)

        logger.info("Log completo em: %s", parsed_args.log_file)
        logger.info("Pressione ENTER para encerrar o programa")
        input()

        sys.exit(1)

    if os.name == "nt":  # Torna a janela do console ativa se estiver no Windows
        try:
            set_console_active()
        except Exception as exc:
            logger.error("Erro ao ativar janela do console: %s", exc)

    logger.info("Log completo em: %s", parsed_args.log_file)

    logger.info("Finalizando automaticamente em 10 segundos...")
    logger.info("Pressione ENTER para finalizar agora")

    # Aguarda 10 segundos ou até o usuário pressionar ENTER
    input_thread = threading.Thread(target=input)
    input_thread.daemon = True
    input_thread.start()
    start_time = time.time()
    while True:
        if not input_thread.is_alive():
            break
        if time.time() - start_time >= 10:
            break
        time.sleep(0.1)

    sys.exit(0)
