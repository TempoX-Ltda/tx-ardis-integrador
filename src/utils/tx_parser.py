from dataclasses import dataclass
from argparse import ArgumentParser


@dataclass
class TxArgs:
    host: str
    user: str
    password: str
    verbose: bool

def get_tx_parser(version = None):
    tx_parser = ArgumentParser(
        prog='tx',
        description='Esse utilitário permite a comunicação com a API do software MES TX.'
    )

    tx_parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s' + version
    )

    tx_parser.add_argument(
        '--verbose',
        action='store_true'
    )

    tx_parser.add_argument(
        '--host',
        type=str,
        help='Endereço IP da API Ex.: http://localhost:6543/',
        required=True
    )

    tx_parser.add_argument(
        '-u', '--user',
        type=str,
        help='Usuario que será utilizado para acessar a API',
        required=True
    )

    tx_parser.add_argument(
        '-p', '--password',
        type=str,
        help='Senha do usuário',
        required=True
    )

    return tx_parser