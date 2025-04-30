import tempfile
from argparse import ArgumentParser
from pathlib import Path

from src.utils import get_version

parser = ArgumentParser(
    prog="tx-mes-cli",
    description="Realiza a integração com o sistema MES da TempoX.",
)
parser.add_argument(
    "-v", "--version", action="version", version="%(prog)s " + get_version()
)
parser.add_argument(
    "--host",
    type=str,
    help="Endereço IP da API Ex.: http://localhost:6543/",
    required=True,
)
parser.add_argument(
    "-u",
    "--user",
    type=str,
    help="Usuario que será utilizado para acessar a API",
    required=True,
)
parser.add_argument(
    "-p", "--password", type=str, help="Senha do usuário", required=True
)
parser.add_argument(
    "--timeout",
    type=float,
    help="Tempo limite para as requisições HTTP, em segundos.",
    default=None,
)
parser.add_argument(
    "--log-file",
    type=str,
    help="Caminho para o arquivo de log. Se não informado, o arquivo será temporário.",
    default=tempfile.gettempdir() + "/tx-mes-cli.log",
)

subparsers = parser.add_subparsers(
    title="subcommands",
    description="Operações disponíveis",
    dest="subcommand",
    required=True,
)

# Apontar Plano de Corte
apontar_plano_de_corte_parser = subparsers.add_parser(
    "apontar-plano-de-corte",
    help="Aponta plano de corte no MES",
)
apontar_plano_de_corte_parser.add_argument(
    "--cod-layout",
    type=str,
    help="Codigo do layout que será apontado",
    required=True,
)
apontar_plano_de_corte_parser.add_argument(
    "--tipo-apontamento",
    type=str,
    help="Tipo do apontamento",
    choices=["INICIO_OU_FIM", "INICIO_E_FIM"],
    required=True,
)

# Novo Plano de Corte
novo_plano_de_corte_parser = subparsers.add_parser(
    "novo-plano-de-corte",
    help="Cria novos planos de corte no MES",
)
novo_plano_de_corte_parser.add_argument(
    "--layouts-file",
    type=open,
    help="Arquivo csv contendo as informações de cada layout",
    required=True,
)
novo_plano_de_corte_parser.add_argument(
    "--parts-file",
    type=open,
    help="Arquivo csv contendo as informações de peça de cada layout",
    required=True,
)
novo_plano_de_corte_parser.add_argument(
    "--sep", type=str, help="Separador de campos dos arquivos csv", default=","
)
novo_plano_de_corte_parser.add_argument(
    "--figures-directory",
    type=Path,
    help="Diretório onde as figures de cada plano serão buscadas. O nome de cada arquivo deve ser igual ao código do plano, com extensão .png",
)

# Nova Ordem
nova_ordem_parser = subparsers.add_parser(
    "nova-ordem",
    help="Cria novas ordens no MES",
)
nova_ordem_parser.add_argument(
    "--sep", type=str, help="Separador de campos dos arquivos csv", default=","
)
nova_ordem_parser.add_argument(
    "--ordens-file",
    type=open,
    help="Arquivo csv contendo as informações de cada ordem",
    required=True,
)
nova_ordem_parser.add_argument(
    "--roteiros-file",
    type=open,
    help="Arquivo csv contendo as informações de roteiro de cada ordem",
    required=True,
)
nova_ordem_parser.add_argument(
    "--ids-unicos-file",
    type=open,
    help="Arquivo csv contendo os ids únicos de cada ordem",
    required=True,
)


def parse_args(args=None):
    parsed = parser.parse_args(args)

    return parsed
