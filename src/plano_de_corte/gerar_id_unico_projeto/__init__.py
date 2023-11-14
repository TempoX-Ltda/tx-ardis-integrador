import logging
from dataclasses import dataclass
from io import TextIOWrapper
from argparse import ArgumentParser, FileType
from typing import Callable, Optional

from tx_parser import TxArgs

from utils.tx_sdk import TxSDK

logger = logging.getLogger('tx')

@dataclass
class GerarIdUnicoProjetoArgs(TxArgs):
    
    # É a própria função que será executada
    func: Callable
    dst_file: Optional[TextIOWrapper] = None
    

def add_subparser_to(main_parser: ArgumentParser):
    
    subparsers = main_parser.add_subparsers()

    subparser_gerar_id_projeto = subparsers.add_parser(
        'gerar_id_unico_projeto'
    )

    subparser_gerar_id_projeto.add_argument(
        '-f', '--dst-file',
        type=FileType('w'),
        help='Arquivo onde será gravado o id',
        required=False
    )

    subparser_gerar_id_projeto.set_defaults(func=gerar_id_projeto)

def gerar_id_projeto(args):

    logger.debug('Iniciando processo `gerar_id_projeto`')
    
    args = GerarIdUnicoProjetoArgs(**vars(args))

    tx = TxSDK(args.host, args.user, args.password)

    id_projeto = tx.plano_de_corte.gerar_id_de_projeto()

    logger.debug('ID de projeto: %s', id_projeto)

    if args.dst_file:
        logger.debug('Argumento `--dst-file` foi passado, salvando id no arquivo %s', args.dst_file)
        with args.dst_file as file:
            file.write(str(id_projeto))

        logger.debug('Salvo com sucesso no arquivo')

    print(id_projeto)