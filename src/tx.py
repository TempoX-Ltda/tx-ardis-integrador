import sys
import logging
from logging.handlers import RotatingFileHandler
import tempfile

import PySimpleGUI as sg

from tx_parser import get_tx_parser
import plano_de_corte

__version__ = '1.0.2'

def setup_logger(verbose = False):
    log_file = tempfile.gettempdir() + '/send_ardis.log'

    formatter = logging.Formatter('%(asctime)s,%(msecs)d | %(name)s | %(levelname)s | %(message)s')

    logger = logging.getLogger('tx')
    logger.setLevel(logging.DEBUG)

    file_log_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2)
    file_log_handler.setLevel(logging.DEBUG)
    file_log_handler.setFormatter(formatter)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    stdout_handler.setFormatter(formatter)

    logger.addHandler(file_log_handler)
    logger.addHandler(stdout_handler)

    return logger

def parse_args(args):
    tx_parser = get_tx_parser(__version__)

    # Adiciona Subparser `plano_de_corte`
    plano_de_corte.add_subparser_to(tx_parser)

    # Interpreta os parâmetros passados
    parsed_args = tx_parser.parse_args(args)

    logger = setup_logger(verbose = parsed_args.verbose)

    logger.debug('args: %s', parsed_args)


    # Executa a função padrão que foi definida para o parser selecionado
    # https://docs.python.org/3/library/argparse.html#sub-commands
    # https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.set_defaults
    if hasattr(parsed_args, "func"):
        parsed_args.func(parsed_args)
    else:
        raise SystemExit

if __name__ == '__main__':
    # Quando o código for executado diretamente (sem ser por uma importação)

    sg.theme('Dark Blue 3')

    parse_args(sys.argv[1:])