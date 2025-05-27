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
# Apontar Plano de Corte NANXING
apontar_plano_de_corte_nanxing_parser = subparsers.add_parser(
    "apontar-plano-de-corte-nanxing",
    help="Aponta plano de corte da Nanxing no MES",
)
apontar_plano_de_corte_nanxing_parser.add_argument(
    "--caminho-arquivo",
    type=str,
    help="Caminho do arquivo que contem a informacao de apontamento, geralmente encontrado em: D:\\Network\\Cnc\\GNcFiles\\NClist.xml",
    required=True,
)
apontar_plano_de_corte_nanxing_parser.add_argument(
    "--tipo-apontamento",
    type=str,
    help="Tipo do apontamento",
    choices=["INICIO_OU_FIM", "INICIO_E_FIM"],
    required=True,
)
apontar_plano_de_corte_nanxing_parser.add_argument(
    "--caminho-arquivo-tempox",
    type=str,
    help="Caminho do arquivo que contem a informacao de apontamento, da tempox.tx",
    required=True,
)
apontar_plano_de_corte_nanxing_parser.add_argument(
    "--caminho_arquivo_tx_sem_registo_maquina",
    type=str,
    help="Caminho do arquivo que contem a informacao de apontamento, da tempox.tx sem registo da máquina",
    required=True,
)

# Apontar Leitura furadeira Nanxing
apontar_leitura_furadeira_nanxing_parser = subparsers.add_parser(
    "apontar-leitura-furadeira-nanxing",
    help="Aponta leitura da furaneira Nanxing",
)
apontar_leitura_furadeira_nanxing_parser.add_argument(
    "--caminho-arquivo",
    type=str,
    help="Caminho do arquivo que contem a informacao de leitura, geralmente encontrado em: D:\\Network\\Cnc\\GNcFiles\\NClist.xml",
    required=True,
)
apontar_leitura_furadeira_nanxing_parser.add_argument(
    "--id-recurso",
    type=int,
    help="numero de identificacao da maquina no MES",
    required=True,
)

# Apontar Leitura furadeira scm pratika
apontar_leitura_furadeira_scm_pratika_parser = subparsers.add_parser(
    "apontar-leitura-furadeira-scm-pratika",
    help="Aponta leitura da furaneira SCM PRATIKA",
)
apontar_leitura_furadeira_scm_pratika_parser.add_argument(
    "--caminho-arquivo",
    type=str,
    help="Caminho do arquivo que contem a informacao de leitura, geralmente encontrado em: D:\\Network\\Cnc\\GNcFiles\\NClist.xml",
    required=True,
)
apontar_leitura_furadeira_scm_pratika_parser.add_argument(
    "--id-recurso",
    type=int,
    help="numero de identificacao da maquina no MES",
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

# Plano SCM
apontar_plano_scm_parser = subparsers.add_parser(
    "apontar-plano-de-corte-scm",
    help="Aponta Plano de Corte da SCM cujo a maro e via ardis",
)
apontar_plano_scm_parser.add_argument(
    "--caminho-arquivo",
    type=str,
    help="Caminho do arquivo que contem a informacao do plano",
    required=True,
)
apontar_plano_scm_parser.add_argument(
    "--tipo-apontamento",
    type=str,
    help="Tipo do apontamento",
    choices=["INICIO_OU_FIM", "INICIO_E_FIM"],
    required=True,
)

def parse_args(args=None):
    parsed = parser.parse_args(args)

    return parsed
