from argparse import ArgumentParser

from . import gerar_id_unico_projeto

def add_subparser_to(main_parser: ArgumentParser):
    
    subparsers = main_parser.add_subparsers()

    subparser_plano_de_corte = subparsers.add_parser(
        'plano_de_corte'
    )

    # Adiciona subparser `gerar_id_unico_projeto`
    gerar_id_unico_projeto.add_subparser_to(subparser_plano_de_corte)
